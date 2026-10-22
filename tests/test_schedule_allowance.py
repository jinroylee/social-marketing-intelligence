"""Shared scheduled admission through public task, schedule and knowledge operations."""

from smi_ingestion.canonical import CanonicalReader
from smi_ingestion.contracts import ExternalKey
from smi_tasks import AcquisitionTasks, OfflineTaskWorker, TaskAuthority
from smi_tasks.schedules import ScheduledDiscovery
from test_keyword_discovery import discovery_setup, record
from test_schedules import Clock, config
from test_tasks import HUMAN, WORKER


def allowance_setup(stack, tmp_path, records, *, clock=None, allowance=1, keywords=None):
    tasks, evidence, response = discovery_setup(stack, tmp_path, records)
    tasks = AcquisitionTasks(tasks.db, route=tasks.route,
        authority=TaskAuthority(schedule_operators=frozenset({HUMAN.actor_id}),
                                schedule_automations=frozenset({WORKER.actor_id})))
    owner = ScheduledDiscovery(tasks, clock=clock or Clock())
    owner.configure(config(daily_allowance=allowance, **({'keywords': keywords} if keywords else {})), HUMAN, expected_version=0)
    return owner, tasks, evidence, response


def test_shared_allowance_excludes_new_canonical_posts_before_writes_and_reports_fewer_results(stack, tmp_path):
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one'), record('two')])
    occurrence = owner.tick(WORKER)['created_occurrences'][0]
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(occurrence['task_id'], WORKER)
    assert result['outcome'] == 'usable_update'
    assert result['coverage']['published_members'] == 1
    assert result['daily_allowance']['used'] == 1
    assert result['daily_allowance']['remaining'] == 0
    assert result['daily_allowance']['occurrence_counts'] == {'new_posts': 1, 'known_refreshes': 0,
        'deduplicated_posts': 0, 'limit_excluded_posts': 1, 'ineligible_posts': 0}
    assert result['coverage']['requests_used'] == 2
    assert CanonicalReader(tasks.db).entity(ExternalKey('tiktok', 'offline-keyword:public', 'content', 'two'), True) is None
    assert owner.read(HUMAN)['daily_allowance']['used'] == 1


def test_http_schedule_and_task_expose_current_allowance_and_legitimate_fewer_records(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import request, running

    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one'), record('two')])
    occurrence = owner.tick(WORKER)['created_occurrences'][0]
    OfflineTaskWorker(tasks.db, evidence.root).run_one(occurrence['task_id'], WORKER)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, schedule_clock=Clock())) as url:
        for path in ['/schedules', '/tasks/' + occurrence['task_id']]:
            status, _, page = request(url, path=path)
            assert status == 200
            assert 'Used: 1' in page
            assert 'Remaining: 0' in page
            assert 'Fewer records can be returned' in page
            assert 'limit_excluded_posts' in page
            assert 'Atomic new-post allowance enforcement is not installed' not in page


def test_competing_keyword_workers_deduplicate_and_share_one_daily_total(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from smi_ingestion.adapters.keyword_fixture import KeywordFixtureCollector
    from smi_knowledge import KnowledgeQueries, QueryScope

    keywords = [{'key': f'keyword-{i}', 'query': query, 'subject_ids': ['product:sunscreen']}
                for i, query in enumerate(['sunscreen', 'review', 'daily'])]
    records = [record(f'post-{i}') for i in range(5)]
    for i, item in enumerate(records):
        item['account']['id'] = item['video']['author_id'] = f'creator-{i}'
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, records, allowance=2, keywords=keywords)
    occurrences = owner.tick(WORKER)['created_occurrences']
    barrier = Barrier(3)

    def run(occurrence):
        task = tasks.read(occurrence['task_id'], HUMAN)
        class CompetingSource:
            first = True
            def collect(self, *args):
                if self.first:
                    self.first = False
                    barrier.wait(timeout=10)
                return KeywordFixtureCollector(task['scope']['discovery'], task['scope']['route_version']).collect(*args)
        return OfflineTaskWorker(tasks.db, evidence.root, collector=CompetingSource()).run_one(occurrence['task_id'], WORKER)

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(run, occurrences))
    results = [tasks.read(result['task_id'], HUMAN) for result in results]
    assert all(result['daily_allowance']['used'] == 2 for result in results)
    assert sum(result['daily_allowance']['occurrence_counts']['new_posts'] for result in results) == 2
    assert sum(result['daily_allowance']['occurrence_counts']['deduplicated_posts'] for result in results) == 4
    assert sum(result['daily_allowance']['occurrence_counts']['limit_excluded_posts'] for result in results) == 9
    assert all(result['coverage']['ingested_observations'] == 2 for result in results)
    assert len(KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='only-admitted', include_synthetic=True)['members']) <= 6
    for i in range(2, 5):
        assert CanonicalReader(tasks.db).entity(ExternalKey('tiktok', 'offline-keyword:public', 'content', f'post-{i}'), True) is None


def test_edits_removal_restart_and_timezone_rollover_preserve_used_and_pinned_authority(stack, tmp_path):
    from datetime import datetime
    clock = Clock()
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one'), record('two')], clock=clock, allowance=1)
    original = owner.tick(WORKER)['created_occurrences'][0]
    OfflineTaskWorker(tasks.db, evidence.root).run_one(original['task_id'], WORKER)
    owner.configure(config(daily_allowance=2, keywords=[]), HUMAN, expected_version=1)
    assert owner.read(HUMAN)['daily_allowance']['used'] == 1
    owner.configure(config(daily_allowance=2, keywords=[{'key': 'new-key', 'query': 'review', 'subject_ids': ['product:sunscreen']}]), HUMAN, expected_version=2)
    restarted = ScheduledDiscovery(owner.tasks, clock=clock)
    second = restarted.tick(WORKER)['created_occurrences'][0]
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(second['task_id'], WORKER)
    assert result['daily_allowance']['used'] == 2
    assert result['daily_allowance']['occurrence_counts']['new_posts'] == 1
    assert result['daily_allowance']['occurrence_counts']['deduplicated_posts'] == 1
    old = tasks.read(original['task_id'], HUMAN)
    assert old['scope'] == original['task']['scope']
    assert old['scope']['schedule']['daily_allowance'] == 1
    assert old['daily_allowance']['limit'] == 2
    owner.configure(config(daily_allowance=1), HUMAN, expected_version=3)
    assert restarted.tick(WORKER)['created_occurrences'] == []
    assert restarted.read(HUMAN)['daily_allowance']['remaining'] == 0
    assert restarted.read(HUMAN)['daily_allowance']['used'] == 2
    clock.at = datetime.fromisoformat('2026-10-04T14:59:59+00:00')
    assert restarted.read(HUMAN)['daily_allowance']['accounting_day'] == '2026-10-04'
    clock.at = datetime.fromisoformat('2026-10-05T00:00:00+00:00')
    next_day = restarted.tick(WORKER)['created_occurrences'][0]
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(next_day['task_id'], WORKER)
    assert result['daily_allowance']['accounting_day'] == '2026-10-05'
    assert result['daily_allowance']['used'] == 0
    assert result['daily_allowance']['remaining'] == 1
    assert result['daily_allowance']['occurrence_counts']['known_refreshes'] == 2
    assert tasks.read(original['task_id'], HUMAN)['daily_allowance']['used'] == 2


def test_invalid_and_denied_results_leave_new_post_capacity_available(stack, tmp_path):
    from dataclasses import replace
    from smi_ingestion.adapters.keyword_fixture import KeywordFixtureCollector
    bad = record('invalid')
    bad['video']['metrics'] = {'views': -1}
    missing = record('missing')
    missing['video'].pop('id')
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [bad, missing, record('good'), record('denied')])
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    task = tasks.read(task_id, HUMAN)
    class PolicySource:
        def collect(self, *args):
            batch = KeywordFixtureCollector(task['scope']['discovery'], task['scope']['route_version']).collect(*args)
            if batch.items and batch.items[0].source_item_key == 'record:3':
                draft = batch.items[0]
                batch = replace(batch, items=(replace(draft, policy=replace(draft.policy, can_process=False)),))
            return batch
    result = OfflineTaskWorker(tasks.db, evidence.root, collector=PolicySource()).run_one(task_id, WORKER)
    assert result['outcome'] == 'partial_update'
    assert result['coverage']['published_members'] == 1
    assert result['daily_allowance']['used'] == 1
    assert result['daily_allowance']['occurrence_counts']['ineligible_posts'] == 1
    assert result['daily_allowance']['occurrence_counts']['limit_excluded_posts'] == 0
    for native in ['invalid', 'missing', 'denied']:
        assert CanonicalReader(tasks.db).entity(ExternalKey('tiktok', 'offline-keyword:public', 'content', native), True) is None


def test_failed_canonical_commit_rolls_back_allowance_then_recovery_uses_same_observation(stack, tmp_path):
    import pytest
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one')])
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    def interrupt(phase):
        if phase == 'canonical':
            raise RuntimeError('controlled canonical interruption')
    with pytest.raises(RuntimeError, match='controlled canonical interruption'):
        OfflineTaskWorker(tasks.db, evidence.root, before_commit=interrupt).run_one(task_id, WORKER)
    interrupted = tasks.read(task_id, HUMAN)
    assert interrupted['daily_allowance']['used'] == 0
    assert interrupted['coverage']['collected_observations'] == 1
    assert CanonicalReader(tasks.db).entity(ExternalKey('tiktok', 'offline-keyword:public', 'content', 'one'), True) is None
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert result['daily_allowance']['used'] == 1
    assert result['daily_allowance']['occurrence_counts']['new_posts'] == 1
    assert result['attempts'][0]['run_id'] == interrupted['attempts'][0]['run_id']
    assert result['coverage']['requests_used'] == 1
    assert result['coverage']['published_members'] == 1


def test_lost_canonical_acknowledgment_and_receipt_recovery_never_consume_twice(stack, tmp_path):
    import pytest
    owner, tasks, evidence, response = allowance_setup(stack, tmp_path, [record('one')])
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    def interrupt(view):
        if view['progress']['phase'] == 'canonical_committed':
            raise RuntimeError('controlled lost acknowledgment')
    with pytest.raises(RuntimeError, match='controlled lost acknowledgment'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    assert tasks.read(task_id, HUMAN)['daily_allowance']['used'] == 1
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert result['daily_allowance']['occurrence_counts']['new_posts'] == 1
    response.unlink()
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == result


def test_competing_upgraded_old_occurrences_bootstrap_latest_applicable_cap_without_regression(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Event
    from smi_ingestion.adapters.keyword_fixture import KeywordFixtureCollector

    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one'), record('two')])
    first = owner.tick(WORKER)['created_occurrences'][0]
    owner.configure(config(daily_allowance=2, keywords=[{'key': 'second', 'query': 'review', 'subject_ids': ['product:sunscreen']}]), HUMAN, expected_version=1)
    second = owner.tick(WORKER)['created_occurrences'][0]
    # Fault/upgrade setup represents the queued ticket-21 database, with no ledger.
    with tasks.db.connect() as connection:
        connection.execute('DELETE FROM scheduled_post_days')
    barrier = Barrier(2)
    old_committed = Event()
    def run(occurrence):
        task = tasks.read(occurrence['task_id'], HUMAN)
        class Source:
            first = True
            def collect(self, *args):
                if self.first:
                    self.first = False
                    barrier.wait(timeout=10)
                    if occurrence['occurrence_id'] == second['occurrence_id']:
                        assert old_committed.wait(10)
                return KeywordFixtureCollector(task['scope']['discovery'], task['scope']['route_version']).collect(*args)
        def committed(view):
            if occurrence['occurrence_id'] == first['occurrence_id'] and view['progress']['phase'] == 'canonical_committed':
                old_committed.set()
        return OfflineTaskWorker(tasks.db, evidence.root, collector=Source(), on_progress=committed).run_one(occurrence['task_id'], WORKER)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, [second, first]))
    for result in results:
        reopened = tasks.read(result['task_id'], HUMAN)
        assert reopened['daily_allowance']['limit'] == 2
        assert reopened['daily_allowance']['allowance_version'] == 2
        assert reopened['daily_allowance']['used'] == 2
    assert tasks.read(first['task_id'], HUMAN)['scope']['schedule']['daily_allowance'] == 1


def test_competing_disjoint_posts_cannot_exceed_shared_allowance(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from smi_ingestion.adapters.keyword_fixture import KeywordFixtureCollector
    records = [record('one', caption='sunscreen'), record('two', caption='review')]
    records[1]['account']['id'] = records[1]['video']['author_id'] = 'other-creator'
    keywords = [{'key': query, 'query': query, 'subject_ids': ['product:sunscreen']} for query in ['sunscreen', 'review']]
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, records, keywords=keywords)
    occurrences = owner.tick(WORKER)['created_occurrences']
    barrier = Barrier(2)
    def run(occurrence):
        task = tasks.read(occurrence['task_id'], HUMAN)
        class Source:
            def collect(self, *args):
                barrier.wait(timeout=10)
                return KeywordFixtureCollector(task['scope']['discovery'], task['scope']['route_version']).collect(*args)
        return OfflineTaskWorker(tasks.db, evidence.root, collector=Source()).run_one(occurrence['task_id'], WORKER)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, occurrences))
    assert sorted(result['outcome'] for result in results) == ['no_usable_update', 'usable_update']
    assert sum(result['daily_allowance']['occurrence_counts']['new_posts'] for result in results) == 1
    assert sum(result['daily_allowance']['occurrence_counts']['limit_excluded_posts'] for result in results) == 1
    assert owner.read(HUMAN)['daily_allowance']['used'] == 1


def test_initial_fifty_is_one_total_across_ten_registered_keywords(stack, tmp_path):
    records = [record(f'{keyword}-{post}', caption=f'topic{keyword}') for keyword in range(10) for post in range(6)]
    keywords = [{'key': f'key-{i}', 'query': f'topic{i}', 'subject_ids': ['product:sunscreen']} for i in range(10)]
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, records, allowance=50, keywords=keywords)
    occurrences = owner.tick(WORKER)['created_occurrences']
    for occurrence in occurrences:
        OfflineTaskWorker(tasks.db, evidence.root).run_one(occurrence['task_id'], WORKER)
    view = owner.read(HUMAN)
    assert view['daily_allowance']['limit'] == 50
    assert view['daily_allowance']['used'] == 50
    assert view['daily_allowance']['remaining'] == 0
    assert view['daily_allowance']['counts']['limit_excluded_posts'] == 10
    assert sum(o['task']['coverage']['published_members'] for o in view['occurrences']) == 50


def test_denied_processing_does_not_take_capacity_from_a_later_valid_task(stack, tmp_path):
    from dataclasses import replace
    from smi_ingestion.adapters.keyword_fixture import KeywordFixtureCollector
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('denied'), record('good', caption='good')])
    first = owner.tick(WORKER)['created_occurrences'][0]
    task = tasks.read(first['task_id'], HUMAN)
    class DeniedSource:
        def collect(self, *args):
            batch = KeywordFixtureCollector(task['scope']['discovery'], task['scope']['route_version']).collect(*args)
            return replace(batch, items=tuple(replace(draft, policy=replace(draft.policy, can_process=False)) for draft in batch.items))
    denied = OfflineTaskWorker(tasks.db, evidence.root, collector=DeniedSource()).run_one(first['task_id'], WORKER)
    assert denied['outcome'] == 'failure'
    assert denied['daily_allowance']['used'] == 0
    assert denied['daily_allowance']['remaining'] == 1
    owner.configure(config(daily_allowance=1, keywords=[{'key': 'good', 'query': 'good', 'subject_ids': ['product:sunscreen']}]), HUMAN, expected_version=1)
    second = owner.tick(WORKER)['created_occurrences'][0]
    admitted = OfflineTaskWorker(tasks.db, evidence.root).run_one(second['task_id'], WORKER)
    assert admitted['daily_allowance']['used'] == 1
    assert admitted['coverage']['published_members'] == 1


def test_upgrade_migration_and_delayed_execution_keep_the_original_days_cap(stack, tmp_path):
    from datetime import datetime
    clock = Clock()
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one'), record('two')], clock=clock)
    first = owner.tick(WORKER)['created_occurrences'][0]
    owner.configure(config(daily_allowance=2), HUMAN, expected_version=1)
    with tasks.db.connect() as connection:
        connection.execute('DELETE FROM scheduled_post_days')
    tasks.migrate()
    upgraded = tasks.read(first['task_id'], HUMAN)
    assert upgraded['daily_allowance']['limit'] == 2
    assert upgraded['daily_allowance']['used'] == 0
    clock.at = datetime.fromisoformat('2026-10-05T00:00:00+00:00')
    owner.configure(config(daily_allowance=99), HUMAN, expected_version=2)
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(first['task_id'], WORKER)
    assert result['daily_allowance']['accounting_day'] == '2026-10-04'
    assert result['daily_allowance']['limit'] == 2
    assert result['daily_allowance']['used'] == 2
    assert owner.read(HUMAN)['daily_allowance']['limit'] == 99
    assert owner.read(HUMAN)['daily_allowance']['used'] == 0


def test_session_loss_at_canonical_admission_rolls_back_debit_and_fences_old_worker(stack, tmp_path):
    import pytest
    from smi_tasks import TaskExecutionLost
    owner, tasks, evidence, _ = allowance_setup(stack, tmp_path, [record('one')])
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    handles = []
    def disconnect(phase):
        if phase == 'canonical':
            handles[0].disconnect()
    with pytest.raises(TaskExecutionLost):
        OfflineTaskWorker(tasks.db, evidence.root, on_execution=handles.append, before_commit=disconnect).run_one(task_id, WORKER)
    assert tasks.read(task_id, HUMAN)['daily_allowance']['used'] == 0
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert result['daily_allowance']['used'] == 1
    assert result['daily_allowance']['occurrence_counts']['new_posts'] == 1
    assert result['coverage']['requests_used'] == 1
