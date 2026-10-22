"""Avoidance through admitted tasks, real persistence and governed KB reads."""

from datetime import datetime, timezone

import pytest

from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker
from smi_ingestion.adapters.keyword_fixture import KeywordFixtureCollector
from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope
from test_keyword_discovery import approved_task, discovery_setup
from test_tasks import HUMAN, WORKER


class SimulatedSource:
    """Count actual simulated source requests at the collector I/O boundary."""

    def __init__(self, task):
        self.source = KeywordFixtureCollector(task['scope']['discovery'], task['scope']['route_version'])
        self.requests = 0

    def collect(self, manifest, checkpoint, limits):
        self.requests += 1
        return self.source.collect(manifest, checkpoint, limits)


def history_setup(stack, tmp_path, *, records=None, age=86400, revision='canonical-v1'):
    from smi_tasks import DiscoveryPolicy

    tasks, evidence, response = discovery_setup(stack, tmp_path, records)
    route = OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(max_capture_age_seconds=age, processing_revision=revision))
    return AcquisitionTasks(tasks.db, route=route, authority=tasks.authority), evidence, response


def run(tasks, evidence, task_id, *, now='2026-10-04T13:00:00+00:00', **options):
    source = SimulatedSource(tasks.read(task_id, HUMAN))
    result = OfflineTaskWorker(tasks.db, evidence.root, collector=source,
        clock=lambda: datetime.fromisoformat(now).astimezone(timezone.utc), **options).run_one(task_id, WORKER)
    return result, source.requests


def test_fresh_exact_query_skips_source_and_publication_after_restart(stack, tmp_path):
    tasks, evidence, _ = history_setup(stack, tmp_path)
    first, calls = run(tasks, evidence, approved_task(tasks))
    assert calls == 1 and first['outcome'] == 'usable_update'
    old = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='pinned-before-skip', include_synthetic=True)
    task_id = approved_task(tasks, request_id='repeat')
    second, calls = run(AcquisitionTasks(tasks.db), evidence, task_id)
    assert calls == 0
    assert second['outcome'] == 'no_usable_update'
    assert second['coverage']['requests_used'] == 0
    assert second['coverage']['published_members'] == 0
    assert second['publication_ids'] == []
    history = second['discovery_history']
    assert history['decision'] == 'skip'
    assert history['reason'] == 'unchanged_fresh_published'
    assert history['prior_task_id'] == first['task_id']
    assert history['prior_publication_id'] == first['publication_ids'][0]
    assert history['freshness'] == 'fresh'
    assert history['policy'] == {'max_capture_age_seconds': 86400, 'processing_revision': 'canonical-v1'}
    assert AcquisitionTasks(tasks.db).read(task_id, HUMAN) == second
    assert KnowledgeQueries(tasks.db).read(old['result_id'], HUMAN, include_synthetic=True) == old


def test_processing_revision_reprocesses_without_relabeling_mapper_or_refreshing_capture(stack, tmp_path):
    tasks, evidence, _ = history_setup(stack, tmp_path)
    first, _ = run(tasks, evidence, approved_task(tasks))
    pinned = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='before-reprocessing', include_synthetic=True)
    from smi_tasks import DiscoveryPolicy
    revised = AcquisitionTasks(tasks.db, authority=tasks.authority, route=OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(86400, processing_revision='canonical-reprocess-oct-v2')))
    updated, calls = run(revised, evidence, approved_task(revised, request_id='reprocess'))
    assert calls == 1
    assert updated['outcome'] == 'usable_update'
    assert updated['publication_ids'] != first['publication_ids']
    capture = updated['discovery_history']['captures'][0]
    assert capture['captured_at'] == '2026-10-04T12:00:00+00:00'
    assert capture['method']['mapper_key'] == 'offline-keyword-json:v1'
    assert capture['method']['policy_version'] == 'canonical-reprocess-oct-v2'
    assert KnowledgeQueries(tasks.db).read(pinned['result_id'], HUMAN, include_synthetic=True) == pinned
    repeated, calls = run(revised, evidence, approved_task(revised, request_id='reprocessed-repeat'))
    assert calls == 0 and repeated['discovery_history']['reason'] == 'unchanged_fresh_published'


def test_http_shows_zero_request_avoidance_and_separate_prior_publication_after_restart(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, evidence, _ = history_setup(stack, tmp_path)
    first, _ = run(tasks, evidence, approved_task(tasks))
    second, _ = run(tasks, evidence, approved_task(tasks, request_id='http-repeat'))
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id)) as url:
        status, _, page = request(url, path='/tasks/' + second['task_id'])
        assert status == 200
        assert 'Discovery retrieval history' in page
        assert 'unchanged_fresh_published' in page
        assert 'No new publication was created by this avoidance decision' in page
        assert f'/tasks/{first["task_id"]}' in page
        assert f'/knowledge/publications/{first["publication_ids"][0]}?include_synthetic=yes' in page
        assert 'Daily sunscreen review' not in page


def test_fresh_already_published_no_update_can_back_a_later_skip_without_adopting_receipt(stack, tmp_path):
    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    first, _ = run(tasks, evidence, approved_task(tasks))
    unchanged, calls = run(tasks, evidence, approved_task(tasks, request_id='unconfigured-repeat'))
    assert calls == 1 and unchanged['outcome'] == 'no_usable_update'
    assert unchanged['publication_ids'] == []
    from smi_tasks import DiscoveryPolicy
    configured = AcquisitionTasks(tasks.db, authority=tasks.authority, route=OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(86400)))
    skipped, calls = run(configured, evidence, approved_task(configured, request_id='configured-repeat'))
    assert calls == 0
    assert skipped['discovery_history']['prior_task_id'] == unchanged['task_id']
    assert skipped['discovery_history']['prior_publication_id'] == first['publication_ids'][0]
    assert skipped['publication_ids'] == []
    assert configured.read_committed_publication(skipped['task_id'], HUMAN) is None


def test_stale_unchanged_retrievals_never_make_old_capture_fresh(stack, tmp_path):
    tasks, evidence, _ = history_setup(stack, tmp_path)
    first, _ = run(tasks, evidence, approved_task(tasks))
    for index in range(2):
        refreshed, calls = run(tasks, evidence, approved_task(tasks, request_id=f'stale-{index}'), now='2026-10-05T13:00:00+00:00')
        assert calls == 1 and refreshed['outcome'] == 'no_usable_update'
        assert refreshed['publication_ids'] == []
        assert refreshed['discovery_history']['reason'] == 'capture_stale'
        assert refreshed['discovery_history']['freshness'] == 'stale'
        assert refreshed['discovery_history']['captures'][0]['captured_at'] == '2026-10-04T12:00:00+00:00'
    assert len(KnowledgePublications(tasks.db).list(HUMAN, include_synthetic=True)) == 1
    assert tasks.read(first['task_id'], HUMAN)['publication_ids'] == first['publication_ids']


@pytest.mark.parametrize('capture', [None, '2026-10-05T00:00:00Z'])
def test_unknown_or_future_capture_is_not_freshened_by_import_or_publication(stack, tmp_path, capture):
    from test_keyword_discovery import record
    source = record('unknown-age')
    if capture is None:
        source.pop('captured_at')
    else:
        source['captured_at'] = capture
    tasks, evidence, _ = history_setup(stack, tmp_path, records=[source])
    first, _ = run(tasks, evidence, approved_task(tasks))
    repeated, calls = run(tasks, evidence, approved_task(tasks, request_id='unknown-repeat'))
    assert calls == 1 and repeated['outcome'] == 'no_usable_update'
    assert repeated['discovery_history']['reason'] == ('capture_time_unknown' if capture is None else 'capture_time_in_future')
    assert repeated['discovery_history']['freshness'] == 'unknown'
    assert repeated['publication_ids'] == []
    assert repeated['discovery_history']['captures'][0]['captured_at'] == (None if capture is None else '2026-10-05T00:00:00+00:00')
    assert first['outcome'] == 'usable_update'


def test_any_unknown_capture_prevents_fresh_skip_even_with_a_recent_maximum(stack, tmp_path):
    from test_keyword_discovery import record
    unknown = record('unknown')
    unknown.pop('captured_at')
    tasks, evidence, _ = history_setup(stack, tmp_path, records=[unknown, record('known')])
    run(tasks, evidence, approved_task(tasks))
    result, calls = run(tasks, evidence, approved_task(tasks, request_id='mixed-repeat'))
    assert calls == 2 and result['discovery_history']['reason'] == 'capture_time_unknown'
    assert result['coverage']['latest_captured_at'] == '2026-10-04T12:00:00+00:00'
    assert result['publication_ids'] == []


def test_changed_observation_preserves_source_identity_metrics_conflicts_and_older_pins(stack, tmp_path):
    import hashlib
    import json
    from smi_knowledge import KnowledgePublications
    from test_keyword_discovery import record

    item = record('same-post')
    item['video']['metrics'] = {'views': 17}
    tasks, evidence, response = history_setup(stack, tmp_path, records=[item])
    first, _ = run(tasks, evidence, approved_task(tasks))
    pinned = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='before-refresh', include_synthetic=True)
    item['video'].update(caption='Changed sunscreen review', metrics={'views': 23})
    item['captured_at'] = '2026-10-04T13:30:00Z'
    response.write_text(json.dumps({'records': [item]}))
    manifest = json.loads(tasks.route.manifest_path.read_text())
    manifest['response_sha256'] = hashlib.sha256(response.read_bytes()).hexdigest()
    tasks.route.manifest_path.write_text(json.dumps(manifest))
    updated, calls = run(tasks, evidence, approved_task(tasks, request_id='changed-source'), now='2026-10-04T14:00:00+00:00')
    assert calls == 1 and updated['outcome'] == 'usable_update'
    assert updated['discovery_history']['reason'] == 'retrieval_or_processing_context_changed'
    old_member = KnowledgePublications(tasks.db).read(first['publication_ids'][0], HUMAN, include_synthetic=True)['members'][0]
    new_member = KnowledgePublications(tasks.db).read(updated['publication_ids'][0], HUMAN, include_synthetic=True)['members'][0]
    assert [(m['definition'], m['value'], m['namespace'], m['native_id']) for m in old_member['metrics']] == [('synthetic.views.v1', 17, 'offline-keyword:public', 'same-post')]
    assert [(m['definition'], m['value'], m['namespace'], m['native_id']) for m in new_member['metrics']] == [('synthetic.views.v1', 23, 'offline-keyword:public', 'same-post')]
    assert [a['value'] for a in old_member['assertions'] if a['field'] == 'caption'] == ['Daily sunscreen review']
    assert [a['value'] for a in new_member['assertions'] if a['field'] == 'caption'] == ['Changed sunscreen review']
    assert KnowledgeQueries(tasks.db).read(pinned['result_id'], HUMAN, include_synthetic=True) == pinned
    again, calls = run(tasks, evidence, approved_task(tasks, request_id='changed-repeat'), now='2026-10-04T14:30:00+00:00')
    assert calls == 0 and again['outcome'] == 'no_usable_update'


def test_failed_source_work_remains_eligible_and_history_is_durable(stack, tmp_path):
    from smi_ingestion.evidence import EvidenceError
    tasks, evidence, _ = history_setup(stack, tmp_path)
    task_id = approved_task(tasks)
    class FailingSource:
        requests = 0
        def collect(self, *args):
            self.requests += 1
            raise EvidenceError('simulated_source_failure')
    source = FailingSource()
    failed = OfflineTaskWorker(tasks.db, evidence.root, collector=source).run_one(task_id, WORKER)
    assert source.requests == 1 and failed['outcome'] == 'failure'
    assert failed['discovery_history']['failure'] == {'phase': 'collection', 'code': 'simulated_source_failure'}
    recovered, calls = run(tasks, evidence, approved_task(tasks, request_id='recover-failed'))
    assert calls == 1 and recovered['outcome'] == 'usable_update'
    assert recovered['discovery_history']['reason'] == 'prior_incomplete_or_failed'
    assert AcquisitionTasks(tasks.db).read(task_id, HUMAN) == failed


def test_committed_skip_restarts_without_source_files_or_new_effects(stack, tmp_path):
    tasks, evidence, response = history_setup(stack, tmp_path)
    run(tasks, evidence, approved_task(tasks))
    task_id = approved_task(tasks, request_id='interrupted-skip')
    def interrupt(phase):
        if phase == 'discovery_skipped':
            raise RuntimeError('interrupt after decision before skip acknowledgment')
    with pytest.raises(RuntimeError, match='interrupt after decision'):
        run(tasks, evidence, task_id, before_commit=interrupt)
    interrupted = tasks.read(task_id, HUMAN)
    assert interrupted['outcome'] is None
    assert interrupted['discovery_history']['decision'] == 'skip'
    response.unlink()
    tasks.route.manifest_path.unlink()
    completed, calls = run(AcquisitionTasks(tasks.db), evidence, task_id)
    assert calls == 0 and completed['outcome'] == 'no_usable_update'
    assert completed['attempts'][0]['run_id'] == interrupted['attempts'][0]['run_id']
    assert completed['publication_ids'] == []


def test_withdrawn_capture_cannot_be_reconstructed_by_identical_query_or_processing_revision(stack, tmp_path):
    import json
    from smi_tasks import DiscoveryPolicy
    tasks, evidence, _ = history_setup(stack, tmp_path)
    first, _ = run(tasks, evidence, approved_task(tasks))
    evidence.revoke(first['discovery_history']['captures'][0]['observation_id'])
    revised = AcquisitionTasks(tasks.db, authority=tasks.authority, route=OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(86400, processing_revision='canonical-new-policy')))
    result, calls = run(revised, evidence, approved_task(revised, request_id='withdrawn-reprocess'))
    assert calls == 0 and result['outcome'] == 'no_usable_update'
    assert result['discovery_history']['reason'] == 'prior_support_unavailable'
    assert result['discovery_history']['freshness'] == 'unavailable'
    assert result['discovery_history']['captures'][0]['availability'] == 'unavailable'
    assert result['publication_ids'] == []
    historical = AcquisitionTasks(tasks.db).read(first['task_id'], HUMAN)['discovery_history']
    assert historical['recorded_usable_publication_ids'] == first['publication_ids']
    assert historical['usable_publication_ids'] == []
    assert historical['outcome'] == 'usable_update'
    assert 'same-post' not in json.dumps(result) and 'creator-1' not in json.dumps(result)
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='withdrawn-history', include_synthetic=True)['members'] == []


def test_skip_preserves_daily_allowance_and_revised_processing_commits_without_new_debit(stack, tmp_path):
    from smi_tasks import TaskAuthority, DiscoveryPolicy
    from smi_tasks.schedules import ScheduledDiscovery
    from test_schedules import Clock, config
    tasks, evidence, _ = history_setup(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=tasks.route, authority=TaskAuthority(
        schedule_operators=frozenset({HUMAN.actor_id}), schedule_automations=frozenset({WORKER.actor_id})))
    schedule = ScheduledDiscovery(tasks, clock=Clock())
    schedule.configure(config(daily_allowance=1), HUMAN, expected_version=0)
    occurrence = schedule.tick(WORKER)['created_occurrences'][0]
    first, calls = run(tasks, evidence, occurrence['task_id'])
    assert calls == 1 and first['daily_allowance']['used'] == 1
    schedule.configure(config(daily_allowance=2, keywords=[{'key': 'renamed', 'query': 'sunscreen review',
        'subject_ids': ['product:sunscreen']}]), HUMAN, expected_version=1)
    second = schedule.tick(WORKER)['created_occurrences'][0]
    skipped, calls = run(tasks, evidence, second['task_id'])
    assert calls == 0 and skipped['publication_ids'] == []
    assert skipped['scope']['schedule']['occurrence_id'] == second['occurrence_id']
    assert skipped['scope']['schedule']['configuration_version'] == 2
    assert skipped['daily_allowance']['used'] == 1 and skipped['daily_allowance']['remaining'] == 1
    assert skipped['daily_allowance']['occurrence_counts'] == {'new_posts': 0, 'known_refreshes': 0,
        'deduplicated_posts': 0, 'limit_excluded_posts': 0, 'ineligible_posts': 0}
    revised = AcquisitionTasks(tasks.db, authority=tasks.authority, route=OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(86400, processing_revision='canonical-scheduled-v2')))
    schedule = ScheduledDiscovery(revised, clock=Clock())
    schedule.configure(config(daily_allowance=2, keywords=[{'key': 'processed', 'query': 'sunscreen review',
        'subject_ids': ['product:sunscreen']}]), HUMAN, expected_version=2)
    third = schedule.tick(WORKER)['created_occurrences'][0]
    refreshed, calls = run(revised, evidence, third['task_id'])
    assert calls == 1 and refreshed['outcome'] == 'usable_update'
    assert refreshed['daily_allowance']['used'] == 1
    assert refreshed['daily_allowance']['occurrence_counts']['deduplicated_posts'] == 1
    assert tasks.read(first['task_id'], HUMAN)['scope'] == first['scope']


def test_fresh_skip_creates_no_synthetic_cost_operation_even_when_ceiling_is_exhausted(stack, tmp_path):
    from test_costs import accounting
    from test_cost_admission import ceiling
    tasks, evidence, _ = history_setup(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('offline-keyword-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    first, _ = run(tasks, evidence, approved_task(tasks))
    assert first['outcome'] == 'usable_update'
    skipped, calls = run(tasks, evidence, approved_task(tasks, request_id='no-new-cost'))
    assert calls == 0 and skipped['outcome'] == 'no_usable_update'
    assert costs.list(HUMAN, task_id=skipped['task_id']) == []
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.125'


@pytest.mark.parametrize('changed', ['query', 'subjects', 'window'])
def test_avoidance_never_broadens_an_exact_new_task_scope(stack, tmp_path, changed):
    from test_keyword_discovery import proposal
    tasks, evidence, _ = history_setup(stack, tmp_path)
    run(tasks, evidence, approved_task(tasks))
    scopes = {'query': proposal(search_queries=('sunscreen',)),
              'subjects': proposal(subject_ids=('product:sunscreen', 'product:foundation')),
              'window': proposal(published_before='2026-10-11T00:00:00Z')}
    result, calls = run(tasks, evidence, approved_task(tasks, scopes[changed], request_id='different-scope'))
    assert calls == 1
    assert result['discovery_history']['reason'] == 'no_prior_retrieval'
    assert result['discovery_history']['prior_task_id'] is None
    assert result['publication_ids'] == []
    assert result['scope']['discovery'] == scopes[changed].keyword_scope()


def test_existing_publication_before_history_upgrade_can_support_future_avoidance(stack, tmp_path):
    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    first, _ = run(tasks, evidence, approved_task(tasks))
    # Upgrade fixture only: the old installed version had no discovery table.
    with tasks.db.connect() as connection:
        connection.execute('DROP TABLE discovery_history')
    tasks.migrate()
    from smi_tasks import DiscoveryPolicy
    configured = AcquisitionTasks(tasks.db, authority=tasks.authority, route=OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(86400)))
    replay, calls = run(configured, evidence, approved_task(configured, request_id='first-after-upgrade'))
    assert calls == 1 and replay['outcome'] == 'no_usable_update'
    assert replay['discovery_history']['usable_publication_ids'] == first['publication_ids']
    skipped, calls = run(configured, evidence, approved_task(configured, request_id='second-after-upgrade'))
    assert calls == 0 and skipped['publication_ids'] == []
    assert configured.read_committed_publication(skipped['task_id'], HUMAN) is None


def test_new_capacity_retrieves_previously_excluded_query_records_instead_of_skipping_subset(stack, tmp_path):
    from smi_tasks import TaskAuthority
    from smi_tasks.schedules import ScheduledDiscovery
    from test_schedules import Clock, config
    from test_keyword_discovery import record
    tasks, evidence, _ = history_setup(stack, tmp_path, records=[record('admitted'), record('excluded')])
    tasks = AcquisitionTasks(tasks.db, route=tasks.route, authority=TaskAuthority(
        schedule_operators=frozenset({HUMAN.actor_id}), schedule_automations=frozenset({WORKER.actor_id})))
    schedule = ScheduledDiscovery(tasks, clock=Clock())
    schedule.configure(config(daily_allowance=1), HUMAN, expected_version=0)
    first, calls = run(tasks, evidence, schedule.tick(WORKER)['created_occurrences'][0]['task_id'])
    assert calls == 2 and first['daily_allowance']['used'] == 1
    assert first['daily_allowance']['occurrence_counts']['limit_excluded_posts'] == 1
    schedule.configure(config(daily_allowance=2, keywords=[{'key': 'retry', 'query': 'sunscreen review',
        'subject_ids': ['product:sunscreen']}]), HUMAN, expected_version=1)
    refreshed, calls = run(tasks, evidence, schedule.tick(WORKER)['created_occurrences'][0]['task_id'])
    assert calls == 2
    assert refreshed['outcome'] == 'usable_update'
    assert refreshed['daily_allowance']['used'] == 2
    assert refreshed['coverage']['published_members'] == 1


def test_older_withdrawn_input_stays_withheld_after_a_new_capture_then_old_input_reappears(stack, tmp_path):
    import hashlib
    import json
    from test_keyword_discovery import record
    tasks, evidence, response = history_setup(stack, tmp_path)
    original_response = response.read_bytes()
    original_manifest = tasks.route.manifest_path.read_bytes()
    first, _ = run(tasks, evidence, approved_task(tasks))
    evidence.revoke(first['discovery_history']['captures'][0]['observation_id'])
    item = record('post-1', caption='New sunscreen review')
    item['captured_at'] = '2026-10-04T13:30:00Z'
    response.write_text(json.dumps({'records': [item]}))
    manifest = json.loads(original_manifest)
    manifest['response_sha256'] = hashlib.sha256(response.read_bytes()).hexdigest()
    tasks.route.manifest_path.write_text(json.dumps(manifest))
    newer, calls = run(tasks, evidence, approved_task(tasks, request_id='new-permitted-capture'), now='2026-10-04T14:00:00+00:00')
    assert calls == 1 and newer['outcome'] == 'usable_update'
    response.write_bytes(original_response)
    tasks.route.manifest_path.write_bytes(original_manifest)
    repeated, calls = run(tasks, evidence, approved_task(tasks, request_id='old-withdrawn-reappears'))
    assert calls == 0 and repeated['outcome'] == 'no_usable_update'
    assert repeated['discovery_history']['reason'] == 'prior_support_unavailable'
    assert repeated['discovery_history']['prior_task_id'] == first['task_id']
    assert repeated['publication_ids'] == []


@pytest.mark.parametrize('phase', ['discovery_decision', 'discovery_skipped', 'completion'])
def test_session_loss_rolls_back_skip_effects_and_successor_keeps_one_terminal_outcome(stack, tmp_path, phase):
    from smi_tasks import TaskExecutionLost, CompletionInbox
    tasks, evidence, _ = history_setup(stack, tmp_path)
    run(tasks, evidence, approved_task(tasks))
    task_id = approved_task(tasks, request_id='lost-skip-session')
    executions = []
    def disconnect(commit_phase):
        if commit_phase == phase:
            executions[0].disconnect()
    with pytest.raises(TaskExecutionLost):
        run(tasks, evidence, task_id, on_execution=executions.append, before_commit=disconnect)
    interrupted = AcquisitionTasks(tasks.db).read(task_id, HUMAN)
    assert interrupted['outcome'] is None
    if phase == 'discovery_decision':
        assert interrupted['discovery_history'] is None
    else:
        assert interrupted['discovery_history']['outcome'] is None
    assert len([e for e in CompletionInbox(tasks.db).list(HUMAN) if e['task_id'] == task_id]) == 0
    recovered, calls = run(tasks, evidence, task_id)
    assert calls == 0 and recovered['outcome'] == 'no_usable_update'
    assert recovered['discovery_history']['outcome'] == 'no_usable_update'
    assert recovered['publication_ids'] == []
    assert len(recovered['attempts']) == 1
    assert len([e for e in CompletionInbox(tasks.db).list(HUMAN) if e['task_id'] == task_id]) == 1


@pytest.mark.parametrize(('age', 'revision'), [(True, 'canonical-v1'), (0, 'canonical-v1'), (31622401, 'canonical-v1'), (86400, '')])
def test_policy_is_explicit_validated_operator_configuration_not_supplied_proposal_authority(stack, tmp_path, age, revision):
    from smi_tasks import DiscoveryPolicy
    from smi_ingestion.evidence import EvidenceError
    from test_keyword_discovery import proposal
    tasks, _, _ = discovery_setup(stack, tmp_path)
    invalid = AcquisitionTasks(tasks.db, route=OfflineRoute(tasks.route.manifest_path,
        discovery_policy=DiscoveryPolicy(age, processing_revision=revision)), authority=tasks.authority)
    with pytest.raises(EvidenceError, match='invalid_discovery_policy'):
        invalid.save_proposal(proposal(), WORKER, request_id='invalid-policy')
    assert tasks.list_proposals(HUMAN) == [] and tasks.list(HUMAN) == []


def test_same_native_ids_in_other_source_namespace_do_not_avoid_or_merge_discovery(stack, tmp_path):
    from test_keyword_discovery import record
    from test_tasks import setup_task, submit
    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path, payload=record('shared-native'))
    first = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    assert first['outcome'] == 'usable_update'
    tasks, evidence, _ = history_setup(stack, tmp_path, records=[record('shared-native')])
    discovered, calls = run(tasks, evidence, approved_task(tasks))
    assert calls == 1 and discovered['outcome'] == 'usable_update'
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='separate-namespaces', include_synthetic=True)
    accounts = {(a['namespace'], a['subject_id']) for m in result['members'] for a in m['assertions'] if a['kind'] == 'account'}
    assert {namespace for namespace, _ in accounts} == {'fixture:public', 'offline-keyword:public'}
    assert len({identity for _, identity in accounts}) == 2
