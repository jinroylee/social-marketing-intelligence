"""Trusted daily offline discovery through public schedule/task/HTTP operations."""

from datetime import datetime

import pytest

from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_tasks import AcquisitionTasks, TaskAuthority
from smi_tasks.schedules import ScheduledDiscovery
from test_keyword_discovery import discovery_setup
from test_tasks import HUMAN, WORKER


class Clock:
    def __init__(self, at='2026-10-04T00:00:00+00:00'):
        self.at = datetime.fromisoformat(at)

    def __call__(self):
        return self.at


def scheduled(stack, tmp_path, *, clock=None):
    tasks, evidence, response = discovery_setup(stack, tmp_path)
    authority = TaskAuthority(schedule_operators=frozenset({HUMAN.actor_id}),
                              schedule_automations=frozenset({WORKER.actor_id}))
    owner = ScheduledDiscovery(AcquisitionTasks(tasks.db, route=tasks.route, authority=authority), clock=clock or Clock())
    owner.migrate()
    return owner, tasks, evidence, response


def config(**changes):
    return {'timezone': 'Asia/Seoul', 'daily_at': '09:00', 'lookback_days': 7, 'daily_allowance': 50,
            'keywords': [{'key': 'sunscreen', 'query': 'sunscreen review', 'subject_ids': ['product:sunscreen']}], **changes}


def test_operator_versions_configuration_separate_from_actor_labels_and_monitoring(stack, tmp_path):
    owner, tasks, _, _ = scheduled(stack, tmp_path)
    with pytest.raises(EvidenceError, match='schedule_operator_authority_required'):
        owner.configure(config(), ActorContext('local', 'other-human', 'human'), expected_version=0)
    with pytest.raises(EvidenceError, match='schedule_operator_authority_required'):
        owner.configure(config(), ActorContext('local', HUMAN.actor_id, 'automation'), expected_version=0)
    saved = owner.configure(config(), HUMAN, expected_version=0)
    assert saved['version'] == 1
    assert saved['document'] == config()
    assert saved['accounting_timezone'] == 'Asia/Seoul'
    assert saved['cadence'] == 'daily-local-v1'
    assert saved['live_activation'] is False
    assert saved['allowance_enforcement'] == 'not_installed'
    assert tasks.list(HUMAN) == []
    reopened = ScheduledDiscovery(AcquisitionTasks(tasks.db)).read(HUMAN)
    assert reopened['configurations'] == saved['configurations']
    second = owner.configure(config(daily_allowance=70), HUMAN, expected_version=1)
    assert second['version'] == 2
    assert len(second['configurations']) == 2
    assert second['configurations'][0]['document']['daily_allowance'] == 50
    with pytest.raises(EvidenceError, match='schedule_configuration_conflict'):
        owner.configure(config(), HUMAN, expected_version=1)
    with pytest.raises(EvidenceError, match='schedule_accounting_timezone_fixed'):
        owner.configure(config(timezone='UTC'), HUMAN, expected_version=2)


def test_due_day_acknowledges_bounded_task_with_actual_authority_then_worker_publishes(stack, tmp_path):
    from smi_knowledge import KnowledgeQueries, QueryScope
    from smi_tasks import OfflineTaskWorker

    clock = Clock('2026-10-03T23:59:00+00:00')
    owner, tasks, evidence, _ = scheduled(stack, tmp_path, clock=clock)
    owner.configure(config(), HUMAN, expected_version=0)
    early = owner.tick(WORKER)
    assert early['created_occurrences'] == []
    assert tasks.list(HUMAN) == []
    clock.at = datetime.fromisoformat('2026-10-04T00:00:00+00:00')
    tick = owner.tick(WORKER)
    assert len(tick['created_occurrences']) == 1
    occurrence = tick['created_occurrences'][0]
    assert occurrence['status'] == 'submitted'
    assert occurrence['accounting_day'] == '2026-10-04'
    assert occurrence['context']['day_start'] == '2026-10-03T15:00:00+00:00'
    assert occurrence['context']['day_end'] == '2026-10-04T15:00:00+00:00'
    assert occurrence['context']['due_at'] == '2026-10-04T00:00:00+00:00'
    queued = tasks.read(occurrence['task_id'], HUMAN)
    assert queued['origin'] == 'schedule'
    assert queued['proposal_approval'] is None
    assert queued['initiator'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert queued['scope']['schedule']['occurrence_id'] == occurrence['occurrence_id']
    assert queued['scope']['schedule']['configuration_version'] == 1
    assert queued['scope']['schedule']['keyword_key'] == 'sunscreen'
    assert queued['scope']['schedule']['daily_allowance'] == 50
    assert queued['scope']['discovery'] == {'query': 'sunscreen review', 'subject_ids': ['product:sunscreen'],
        'published_from': '2026-09-27T00:00:00+00:00', 'published_before': '2026-10-04T00:00:00+00:00'}
    assert queued['limits']['max_records'] == 10
    assert queued['attempts'] == []
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(queued['task_id'], WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['requests_used'] == 1
    assert completed['coverage']['market_coverage'] == 'unknown'
    assert len(KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='scheduled', include_synthetic=True)['members']) == 1
    assert owner.read(HUMAN)['occurrences'][0]['task']['outcome'] == 'usable_update'
    assert owner.tick(WORKER)['created_occurrences'] == []
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(queued['task_id'], WORKER) == completed


def test_http_operator_configures_offline_schedule_then_acknowledges_tasks_without_origin_fields(stack, tmp_path):
    import json
    from smi_review import ReviewApp
    from test_review import form, request, running

    clock = Clock()
    owner, tasks, _, _ = scheduled(stack, tmp_path, clock=clock)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route,
                           schedule_operator=True, schedule_clock=clock)) as url:
        status, _, page = request(url, path='/schedules')
        assert status == 200
        assert 'Offline registered keyword discovery' in page
        assert 'Live activation is disabled' in page
        assert 'admission allowance' in page
        assert 'not installed' in page
        supplied = form(page, '/schedules')
        supplied.update(timezone=['Asia/Seoul'], daily_at=['09:00'], lookback_days=['7'], daily_allowance=['50'],
                        keywords=[json.dumps(config()['keywords'])])
        assert request(url, 'POST', '/schedules', {**supplied, 'origin': ['schedule']})[0] == 422
        assert owner.read(HUMAN)['version'] == 0
        assert request(url, 'POST', '/schedules', supplied)[0] == 303
        page = request(url, path='/schedules')[2]
        tick = form(page, '/schedules/tick')
        assert request(url, 'POST', '/schedules/tick', {**tick, 'actor': ['operator']})[0] == 422
        assert tasks.list(HUMAN) == []
        assert request(url, 'POST', '/schedules/tick', tick)[0] == 303
        task = tasks.list(HUMAN)[0]
        page = request(url, path='/schedules')[2]
        assert f'/tasks/{task["task_id"]}' in page
        assert 'queued' in page
        assert 'schedule-offline-v1' in request(url, path=f'/tasks/{task["task_id"]}')[2]
    app = ReviewApp(tasks.db, actor_id=HUMAN.actor_id, schedule_clock=clock)
    with running(app) as url:
        page = request(url, path='/schedules')[2]
        assert 'operator role' in page
        # Fresh CSRF belongs to the restarted server; supplied origin grants no role.
        assert request(url, 'POST', '/schedules/tick', {'csrf': [app.csrf]})[0] == 422
    assert len(tasks.list(HUMAN)) == 1


def test_concurrent_restart_and_edits_keep_one_occurrence_and_prior_authority(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    clock = Clock()
    owner, tasks, _, _ = scheduled(stack, tmp_path, clock=clock)
    owner.configure(config(), HUMAN, expected_version=0)
    barrier = Barrier(6)

    def tick(_):
        restarted = ScheduledDiscovery(owner.tasks, clock=clock)
        barrier.wait(timeout=5)
        return restarted.tick(WORKER)

    with ThreadPoolExecutor(max_workers=6) as executor:
        outcomes = list(executor.map(tick, range(6)))
    assert sum(len(result['created_occurrences']) for result in outcomes) == 1
    original = owner.read(HUMAN)['occurrences'][0]
    edited = config(daily_at='08:00', daily_allowance=70, keywords=[{'key': 'sunscreen',
                     'query': 'foundation', 'subject_ids': ['product:foundation']}])
    owner.configure(edited, HUMAN, expected_version=1)
    assert owner.tick(WORKER)['created_occurrences'] == []
    owner.configure(config(keywords=[]), HUMAN, expected_version=2)
    owner.configure(config(), HUMAN, expected_version=3)
    assert ScheduledDiscovery(owner.tasks, clock=clock).tick(WORKER)['created_occurrences'] == []
    assert tasks.read(original['task_id'], HUMAN)['scope']['schedule']['configuration_version'] == 1
    assert len(tasks.list(HUMAN)) == 1
    clock.at = datetime.fromisoformat('2026-10-05T00:00:00+00:00')
    tomorrow = owner.tick(WORKER)['created_occurrences'][0]
    assert tomorrow['accounting_day'] == '2026-10-05'
    assert tomorrow['configuration_version'] == 4
    assert tomorrow['task_id'] != original['task_id']
    assert owner.read_occurrence(original['occurrence_id'], HUMAN) == original
    assert owner.read(HUMAN)['accounting_timezone'] == 'Asia/Seoul'


def test_refused_day_is_historical_and_missed_days_do_not_replay_after_configuration_change(stack, tmp_path):
    clock = Clock()
    owner, tasks, _, _ = scheduled(stack, tmp_path, clock=clock)
    unavailable = ScheduledDiscovery(AcquisitionTasks(tasks.db, authority=owner.tasks.authority), clock=clock)
    unavailable.configure(config(), HUMAN, expected_version=0)
    first = unavailable.tick(WORKER)['created_occurrences'][0]
    assert first['status'] == 'refused'
    assert first['reason'] == 'offline_task_route_unconfigured'
    assert first['task_id'] is None
    assert tasks.list(HUMAN) == []
    owner.configure(config(daily_allowance=99), HUMAN, expected_version=1)
    assert owner.tick(WORKER)['created_occurrences'] == []
    clock.at = datetime.fromisoformat('2026-10-07T00:00:00+00:00')
    late = owner.tick(WORKER)
    assert late['missed_days_not_replayed'] == 2
    assert len(late['created_occurrences']) == 1
    assert late['created_occurrences'][0]['accounting_day'] == '2026-10-07'
    assert late['created_occurrences'][0]['context']['daily_allowance'] == 99
    assert owner.read_occurrence(first['occurrence_id'], HUMAN) == first
    assert len(owner.read(HUMAN)['occurrences']) == 2
    clock.at = datetime.fromisoformat('2026-10-06T00:00:00+00:00')
    with pytest.raises(EvidenceError, match='schedule_clock_regressed'):
        owner.tick(WORKER)
    assert len(tasks.list(HUMAN)) == 1


@pytest.mark.parametrize('changes', [
    {'keywords': [{'key': f'k{i}', 'query': str(i), 'subject_ids': ['product:sunscreen']} for i in range(11)]},
    {'keywords': [{'key': 'same', 'query': 'one', 'subject_ids': ['p']}, {'key': 'same', 'query': 'two', 'subject_ids': ['p']}]},
    {'keywords': [{'key': 'a', 'query': ' SAME ', 'subject_ids': ['p']}, {'key': 'b', 'query': 'same', 'subject_ids': ['p']}]},
    {'keywords': [{'key': 'a', 'query': 'one', 'subject_ids': []}]},
    {'keywords': [{'key': 'a', 'query': 'one', 'subject_ids': ['p'], 'origin': 'schedule'}]},
    {'daily_at': '24:00'}, {'timezone': 'not/a-zone'}, {'lookback_days': 0},
    {'daily_allowance': True}, {'live_activation': True},
])
def test_invalid_or_authority_bearing_configuration_never_changes_history(stack, tmp_path, changes):
    owner, tasks, _, _ = scheduled(stack, tmp_path)
    with pytest.raises(EvidenceError, match='invalid_keyword_schedule'):
        owner.configure(config(**changes), HUMAN, expected_version=0)
    assert owner.read(HUMAN)['version'] == 0
    assert tasks.list(HUMAN) == []


def test_ten_keywords_are_bounded_and_unconfigured_labels_cannot_forge_schedule_authority(stack, tmp_path):
    import uuid
    from smi_monitoring import MonitoringStore
    from test_keyword_discovery import approved_task

    owner, tasks, _, _ = scheduled(stack, tmp_path)
    monitoring = MonitoringStore(tasks.db)
    monitoring.migrate()
    keywords = [{'key': f'k{i}', 'query': f'registered {i}', 'subject_ids': ['product:sunscreen']} for i in range(10)]
    owner.configure(config(keywords=keywords), HUMAN, expected_version=0)
    forged = ActorContext('local', 'schedule-operator', 'automation')
    for actor in (forged, ActorContext('local', HUMAN.actor_id, 'automation'), ActorContext('local', WORKER.actor_id, 'human')):
        with pytest.raises(EvidenceError, match='schedule_tick_authority_required'):
            owner.tick(actor)
        with pytest.raises(EvidenceError, match='schedule_tick_authority_required'):
            owner.tasks.submit_scheduled(str(uuid.uuid4()), actor)
    with pytest.raises(EvidenceError, match='schedule_occurrence_not_found'):
        owner.tasks.submit_scheduled(str(uuid.uuid4()), WORKER)
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        owner.tick(ActorContext('foreign', WORKER.actor_id, 'automation'))
    assert tasks.list(HUMAN) == []
    tick = owner.tick(WORKER)
    assert len(tick['created_occurrences']) == 10
    assert len({row['task_id'] for row in tick['created_occurrences']}) == 10
    assert monitoring.list_investigations(HUMAN) == []
    # Exact on-demand human approval has independent scope beyond registered words.
    approved_id = approved_task(tasks, request_id='outside-registration')
    assert tasks.read(approved_id, HUMAN)['scope']['search_queries'] == ['sunscreen review']
    assert tasks.read(approved_id, HUMAN)['origin'] == 'assistant'
    assert len(tasks.list(HUMAN)) == 11


@pytest.mark.parametrize(('initial', 'due', 'repeated', 'day_start', 'day_end'), [
    ('2026-11-01T05:29:00+00:00', '2026-11-01T05:30:00+00:00', '2026-11-01T06:30:00+00:00',
     '2026-11-01T04:00:00+00:00', '2026-11-02T05:00:00+00:00'),
    ('2026-03-08T07:29:00+00:00', '2026-03-08T07:30:00+00:00', '2026-03-08T08:30:00+00:00',
     '2026-03-08T05:00:00+00:00', '2026-03-09T04:00:00+00:00'),
])
def test_timezone_overlap_and_gap_keep_one_local_day_and_explicit_boundaries(stack, tmp_path, initial, due, repeated, day_start, day_end):
    clock = Clock(initial)
    owner, _, _, _ = scheduled(stack, tmp_path, clock=clock)
    owner.configure(config(timezone='America/New_York', daily_at='01:30' if '11-01' in due else '02:30'), HUMAN, expected_version=0)
    assert owner.tick(WORKER)['created_occurrences'] == []
    clock.at = datetime.fromisoformat(due)
    occurrence = owner.tick(WORKER)['created_occurrences'][0]
    assert occurrence['context']['due_at'] == due
    assert occurrence['context']['day_start'] == day_start
    assert occurrence['context']['day_end'] == day_end
    clock.at = datetime.fromisoformat(repeated)
    assert owner.tick(WORKER)['created_occurrences'] == []


def test_scheduled_worker_uses_shared_cost_guard_and_never_reissues_an_uncertain_dispatch(stack, tmp_path):
    from test_costs import accounting
    from test_cost_admission import ceiling
    from smi_tasks import OfflineTaskWorker

    owner, tasks, evidence, response = scheduled(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('offline-keyword-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    owner.configure(config(), HUMAN, expected_version=0)
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']

    def interrupt(phase):
        if phase == 'cost_settlement':
            raise RuntimeError('schedule settlement lost')

    with pytest.raises(RuntimeError, match='schedule settlement lost'):
        OfflineTaskWorker(tasks.db, evidence.root, before_commit=interrupt).run_one(task_id, WORKER)
    response.unlink()
    waiting = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert waiting['outcome'] is None
    assert waiting['progress']['reason'] == 'cost_operation_in_flight_or_uncertain'
    assert waiting['coverage']['collected_observations'] == 0
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.125'
    assert costs.read(costs.list(HUMAN, task_id=task_id)[0]['operation_id'], HUMAN)['actuals']['amount'] is None
    assert owner.tick(WORKER)['created_occurrences'] == []
    assert len(tasks.list(HUMAN)) == 1


def test_scheduled_recovery_preserves_exact_publication_receipt_and_current_policy(stack, tmp_path):
    from smi_knowledge import KnowledgeQueries, QueryScope
    from smi_tasks import OfflineTaskWorker

    owner, tasks, evidence, response = scheduled(stack, tmp_path)
    owner.configure(config(), HUMAN, expected_version=0)
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']

    def interrupt(view):
        if view['progress']['phase'] == 'publication_committed':
            raise RuntimeError('schedule publication acknowledgment lost')

    with pytest.raises(RuntimeError, match='schedule publication acknowledgment lost'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    committed = tasks.read(task_id, HUMAN)
    receipt = tasks.read_committed_publication(task_id, HUMAN)
    evidence.revoke(receipt['support'][0]['observation_id'])
    response.unlink()
    tasks.route.manifest_path.unlink()
    recovered = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert recovered['outcome'] == 'usable_update'
    assert recovered['publication_ids'] == committed['publication_ids']
    assert recovered['attempts'][0]['publication_support'] == committed['attempts'][0]['publication_support']
    assert recovered['scope']['schedule'] == committed['scope']['schedule']
    assert tasks.read_committed_publication(task_id, HUMAN) == receipt
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='scheduled-withdrawn', include_synthetic=True)['members'] == []


def test_failed_task_admission_rolls_back_the_whole_tick_before_retry(stack, tmp_path):
    import psycopg

    owner, tasks, _, _ = scheduled(stack, tmp_path)
    keywords = [{'key': f'k{i}', 'query': str(i), 'subject_ids': ['product:sunscreen']} for i in range(2)]
    owner.configure(config(keywords=keywords), HUMAN, expected_version=0)
    # Fault setup only: a failure after the first task must roll back every acknowledgment.
    with tasks.db.connect() as connection:
        connection.execute("""CREATE FUNCTION reject_second_scheduled_task() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF NEW.scope->'schedule'->>'keyword_key' = 'k1' THEN RAISE EXCEPTION 'simulated admission failure'; END IF;
            RETURN NEW; END $$""")
        connection.execute('CREATE TRIGGER reject_second BEFORE INSERT ON acquisition_tasks FOR EACH ROW EXECUTE FUNCTION reject_second_scheduled_task()')
    with pytest.raises(psycopg.Error):
        owner.tick(WORKER)
    assert tasks.list(HUMAN) == []
    assert owner.read(HUMAN)['occurrences'] == []
    assert owner.read(HUMAN)['last_tick_at'] is None
    with tasks.db.connect() as connection:
        connection.execute('DROP TRIGGER reject_second ON acquisition_tasks')
    assert len(owner.tick(WORKER)['created_occurrences']) == 2


def test_queued_schedule_accounting_authority_is_part_of_the_execution_digest(stack, tmp_path):
    from psycopg.types.json import Jsonb
    from smi_tasks import OfflineTaskWorker

    owner, tasks, evidence, _ = scheduled(stack, tmp_path)
    owner.configure(config(), HUMAN, expected_version=0)
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    task = tasks.read(task_id, HUMAN)
    # Fault setup only: public operations cannot edit acknowledged task authority.
    task['scope']['schedule']['daily_allowance'] = 1000
    with tasks.db.connect() as connection:
        connection.execute('UPDATE acquisition_tasks SET scope=%s WHERE id=%s', (Jsonb(task['scope']), task_id))
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'collection', 'code': 'task_configuration_changed'}
    assert failed['coverage']['collected_observations'] == 0
    assert failed['publication_ids'] == []


@pytest.mark.parametrize(('route_kind', 'reason'), [
    ('supplied', 'keyword_discovery_unavailable_supplied_reference_route'),
    ('denied', 'source_policy_disallows_discovery'),
])
def test_schedule_refuses_non_discovery_or_policy_denied_routes_without_task(stack, tmp_path, route_kind, reason):
    from test_tasks import setup_task

    if route_kind == 'supplied':
        tasks, _, _, _ = setup_task(stack, tmp_path)
    else:
        tasks, _, _ = discovery_setup(stack, tmp_path,
            policy={'context_id': 'denied', 'can_process': False, 'can_retain': False, 'can_display': False})
    owner = ScheduledDiscovery(AcquisitionTasks(tasks.db, route=tasks.route,
        authority=TaskAuthority(schedule_operators=frozenset({HUMAN.actor_id}))), clock=Clock())
    owner.configure(config(), HUMAN, expected_version=0)
    refused = owner.tick(HUMAN)['created_occurrences'][0]
    assert refused['status'] == 'refused'
    assert refused['reason'] == reason
    assert refused['task_id'] is None
    assert tasks.list(HUMAN) == []
