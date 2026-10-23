"""One gated keyword route through public tasks and the external HTTPS boundary."""

import io
import json
from urllib.request import OpenerDirector

from smi_tasks import AcquisitionTasks, LiveDiscoveryConfig, OfflineRoute, OfflineTaskWorker
from test_tasks import HUMAN, WORKER, setup_task
from test_keyword_discovery import approved_task


ROUTE = 'brightdata-tiktok-keyword'


def live_setup(stack, tmp_path):
    tasks, _, evidence, manifest = setup_task(stack, tmp_path)
    manifest.write_text(json.dumps({'adapter': ROUTE, 'provider_id': 'brightdata',
        'format_version': 'tiktok-posts-2026-10-23', 'synthetic': False,
        'policy': {'context_id': 'test-authorized-source', 'can_process': True,
                   'can_retain': True, 'can_display': True}}))
    return AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, 'brightdata-keyword-v1'),
                            authority=tasks.authority, live_discovery_enabled=True), evidence


def http_boundary(monkeypatch, responses):
    requests = []
    original = OpenerDirector.open

    def send(opener, request, data=None, timeout=None):
        from urllib.parse import urlsplit
        if urlsplit(request.full_url).hostname != 'api.brightdata.com':
            return original(opener, request, data, timeout)
        requests.append(request)
        reply = responses.pop(0)
        status, value = reply[:2]
        response = io.BytesIO(json.dumps(value).encode())
        response.status = status
        response.headers = reply[2] if len(reply) > 2 else {}
        return response

    monkeypatch.setattr(OpenerDirector, 'open', send)
    return requests


def test_live_route_stays_unavailable_without_explicit_runtime_gates(stack, tmp_path, monkeypatch):
    tasks, evidence = live_setup(stack, tmp_path)
    requests = http_boundary(monkeypatch, [])
    task_id = approved_task(tasks)
    waiting = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert waiting['outcome'] is None
    assert waiting['progress']['reason'] == 'live_discovery_disabled'
    assert requests == []
    assert waiting['publication_ids'] == []
    assert LiveDiscoveryConfig().enabled is False


def enabled():
    return LiveDiscoveryConfig(enabled=True, operation_authorized=True,
                               source_use_authorized=True, api_key='dummy-secret')


def live_costs(tasks, ceiling_amount='10'):
    from smi_costs import CostScope, UsageAccounting
    from test_costs import START, END

    costs = UsageAccounting(tasks.db, task_attribution=tasks.resolve_cost_attribution)
    costs.configure_scope(CostScope('live-oct', 'brightdata', 'tiktok-keyword', 'metered', 'USD', START, END,
        unit='declared-record-bound', rate_version='operator-test-only', unit_rate='1',
        measurement_basis='provider_reported'), HUMAN)
    costs.configure_route(ROUTE, 'live-oct', HUMAN, max_units='1')
    costs.configure_ceiling('live-oct', HUMAN, amount=ceiling_amount, currency='USD', period_start=START, period_end=END)
    return costs


def post(**changes):
    return {'url': 'https://www.tiktok.com/@example/video/1234', 'post_id': '1234',
        'profile_id': '9876', 'profile_username': 'example', 'description': 'Daily sunscreen review',
        'create_time': '2026-10-03T00:00:00Z', 'play_count': 42, **changes}


def test_authorized_query_dispatches_bounded_https_and_publishes_real_schema_with_delayed_cost(stack, tmp_path, monkeypatch):
    from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope
    from urllib.parse import parse_qs, urlsplit

    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()])])
    task_id = approved_task(tasks)
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['returned_records'] == 1
    assert completed['coverage']['eligible_records'] == 1
    assert completed['coverage']['published_members'] == 1
    assert completed['coverage']['requests_used'] == 1
    sent = requests[0]
    assert sent.get_method() == 'POST'
    assert urlsplit(sent.full_url).hostname == 'api.brightdata.com'
    assert parse_qs(urlsplit(sent.full_url).query) == {'dataset_id': ['gd_lu702nij2f790tmv9h'],
        'type': ['discover_new'], 'discover_by': ['keyword'], 'format': ['json'], 'include_errors': ['true']}
    assert json.loads(sent.data) == {'input': [{'search_keyword': 'sunscreen review', 'num_of_posts': 1}], 'limit_per_input': 1}
    publication = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN)
    member = publication['members'][0]
    assert member['synthetic'] is False
    assert member['captured_at'] is None
    assert {a['namespace'] for a in member['assertions']} == {'brightdata:tiktok-posts'}
    assert member['metrics'][0]['definition'] == 'brightdata.tiktok.play_count.v1'
    assert member['metrics'][0]['value'] == 42
    assert member['metrics'][0]['measured_at'] is None
    assert len(KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='live-results')['members']) == 1
    operation = costs.list(HUMAN, task_id=task_id)[0]
    assert operation['actuals']['amount'] is None
    assert operation['actuals']['synthetic'] is False
    assert operation['limits']['billing_state'] == 'awaiting_final_measurement'
    assert operation['admission']['state'] == 'dispatched'
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'
    assert 'dummy-secret' not in json.dumps(completed) + json.dumps(operation) + repr(enabled())


def test_pending_snapshot_resumes_gets_without_paid_post_reissue_and_counts_each_request(stack, tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    at = [datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)]
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [(202, {'snapshot_id': 'sd_safe123'}),
        (200, {'snapshot_id': 'sd_safe123', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'running'}),
        (200, {'snapshot_id': 'sd_safe123', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'ready'}),
        (200, [post()])])
    task_id = approved_task(tasks)
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), clock=lambda: at[0]).run_one(task_id, WORKER)
    pending = worker()
    assert pending['progress']['code'] == 'provider_pending'
    assert pending['progress']['resumable'] is True
    assert 'sd_safe123' not in json.dumps(pending)
    at[0] += timedelta(seconds=10)
    assert worker()['progress']['code'] == 'provider_pending'
    at[0] += timedelta(seconds=10)
    assert worker()['progress']['code'] == 'provider_pending'
    completed = worker()
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['requests_used'] == 4
    assert [r.get_method() for r in requests] == ['POST', 'GET', 'GET', 'GET']
    assert requests[-1].full_url == 'https://api.brightdata.com/datasets/v3/snapshot/sd_safe123?format=json'
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '4'
    assert completed['coverage']['bytes_used'] == sum(len(json.dumps(value).encode()) for value in [
        {'snapshot_id': 'sd_safe123'},
        {'snapshot_id': 'sd_safe123', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'running'},
        {'snapshot_id': 'sd_safe123', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'ready'}, [post()]])


import pytest


@pytest.mark.parametrize(('config', 'reason'), [
    (LiveDiscoveryConfig(enabled=True), 'live_operation_authorization_required'),
    (LiveDiscoveryConfig(enabled=True, operation_authorized=True), 'live_source_use_authorization_required'),
    (LiveDiscoveryConfig(enabled=True, operation_authorized=True, source_use_authorized=True), 'live_discovery_credentials_required'),
    (enabled(), 'live_discovery_cost_configuration_required')])
def test_runtime_prerequisites_refuse_without_http_or_fabricated_cost(stack, tmp_path, monkeypatch, config, reason):
    tasks, evidence = live_setup(stack, tmp_path)
    requests = http_boundary(monkeypatch, [])
    task_id = approved_task(tasks)
    waiting = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=config).run_one(task_id, WORKER)
    assert waiting['progress']['reason'] == reason
    assert waiting['outcome'] is None
    assert requests == []


@pytest.mark.parametrize('value', [
    {'url': 'https://www.tiktok.com/@example/video/1234', 'discovery_input': {'search_keyword': 'sunscreen review'}},
    post(post_id='5555'), post(profile_username='other'), post(profile_id=None), post(play_count=True),
    post(create_time='not-a-date'), post(description=None), post(error='provider-error'),
    post(create_time=123), post(create_time=[]), post(create_time={})])
def test_minimal_schema_and_conflicting_records_never_become_invented_usable_facts(stack, tmp_path, monkeypatch, value):
    from smi_knowledge import KnowledgeQueries, QueryScope

    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [value])])
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(approved_task(tasks), WORKER)
    assert completed['outcome'] == 'failure'
    assert completed['coverage']['returned_records'] == 1
    assert completed['coverage']['eligible_records'] == 0
    assert completed['coverage']['failed_records'] == 1
    assert completed['publication_ids'] == []
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='no-invention')['members'] == []
    assert len(requests) == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'


def test_lost_response_checkpoint_never_reissues_and_final_cost_reconciliation_does_not_restore_response(stack, tmp_path, monkeypatch):
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()])])
    task_id = approved_task(tasks)

    def lose(phase):
        if phase == 'evidence':
            raise RuntimeError('interrupt before response persistence')

    with pytest.raises(RuntimeError, match='interrupt'):
        OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), before_commit=lose).run_one(task_id, WORKER)
    retry = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    assert retry['outcome'] is None
    assert retry['progress']['reason'] == 'cost_operation_in_flight_or_uncertain'
    operation = costs.list(HUMAN, task_id=task_id)[0]
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    costs.reconcile_usage(operation['operation_id'], HUMAN, reconciliation_id='final-bill', measurement_id='bill',
        units='1', rate_version='operator-test-only', measured_at=now, reconciled_at=now,
        provenance='operator-test-final', evidence_id='simulated-final-report', outcome='succeeded',
        settle_admission=True, measurement_basis='provider_reported')
    reconciled = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    assert reconciled['progress']['reason'] == 'cost_operation_already_executed'
    assert reconciled['publication_ids'] == []
    assert len(requests) == 1


def test_http_reviews_live_contract_without_synthetic_or_readiness_claims_and_protects_server_config(stack, tmp_path, monkeypatch):
    from smi_review import ReviewApp
    from test_review import form, request, running

    tasks, evidence = live_setup(stack, tmp_path)
    live_costs(tasks)
    http_boundary(monkeypatch, [(200, [post()])])
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route,
                           live_discovery_enabled=True)) as url:
        page = request(url, path='/proposals/new')[2]
        assert 'Bright Data TikTok keyword discovery' in page
        assert 'Bounded offline keyword discovery' not in page
        supplied = form(page, '/proposals')
        supplied.update(purpose=['Find sunscreen evidence'], intent=['expansion'], subject_ids=['product:sunscreen'],
            search_queries=['sunscreen review'], published_from=['2026-10-01T00:00:00Z'], published_before=['2026-10-10T00:00:00Z'])
        assert request(url, 'POST', '/proposals', {**supplied, 'enabled': ['yes']})[0] == 422
        status, headers, _ = request(url, 'POST', '/proposals', supplied)
        assert status == 303
        detail = request(url, path=headers['Location'])[2]
        assert 'brightdata-keyword-caption-time-v1' in detail
        assert 'pinned synthetic response' not in detail
    task_id = approved_task(tasks, request_id='http-result')
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id)) as url:
        page = request(url, path='/tasks/' + task_id)[2]
        assert 'Bright Data TikTok keyword discovery' in page
        assert 'Synthetic development inputs' not in page
        assert 'capture_time_unknown' not in page  # first retrieval has no preceding capture basis
        assert completed['publication_ids'][0] in page


def test_valid_out_of_scope_return_is_counted_without_claiming_source_failure_or_useful_update(stack, tmp_path, monkeypatch):
    tasks, evidence = live_setup(stack, tmp_path)
    live_costs(tasks)
    http_boundary(monkeypatch, [(200, [post(create_time='2026-09-01T00:00:00Z')])])
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(approved_task(tasks), WORKER)
    assert completed['outcome'] == 'no_usable_update'
    assert completed['coverage']['returned_records'] == 1
    assert completed['coverage']['eligible_records'] == 0
    assert completed['coverage']['failed_records'] == 0
    assert completed['coverage']['remaining_inputs'] == 0
    assert completed['discovery_history']['processing_complete'] is False


@pytest.mark.parametrize('response', [(301, {'location': 'https://elsewhere.invalid/dummy-secret'}),
    (401, {'error': 'dummy-secret'}), (429, {'error': 'rate limited'}), (500, {'error': 'dummy-secret'}),
    (202, {'snapshot_id': '../../invalid'}),
    (202, {'snapshot_id': 'sd_bad_delay'}, {'Retry-After': '9' * 5000}), (200, {'unexpected': 'dummy-secret'}),
    (200, [post(), post(post_id='5555')]), (200, ['x' * 70000])])
def test_ambiguous_or_unbounded_response_retains_liability_and_never_blindly_retries(stack, tmp_path, monkeypatch, response):
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    requests = http_boundary(monkeypatch, [response])
    task_id = approved_task(tasks)
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    waiting = worker()
    assert waiting['outcome'] is None
    assert waiting['progress']['code'] == 'provider_operation_ambiguous'
    assert waiting['progress']['resumable'] is False
    assert waiting['coverage']['requests_used'] == 1
    assert worker()['outcome'] is None
    assert len(requests) == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'
    assert 'dummy-secret' not in json.dumps(waiting) + json.dumps(costs.list(HUMAN, task_id=task_id))


def test_exhausted_shared_ceiling_and_source_policy_both_stop_before_https(stack, tmp_path, monkeypatch):
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks, '0')
    requests = http_boundary(monkeypatch, [])
    waiting = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(approved_task(tasks), WORKER)
    assert waiting['progress']['reason'] == 'cost_allowance_exhausted'
    assert requests == []
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '0'
    document = json.loads(tasks.route.manifest_path.read_text())
    document['policy']['can_process'] = False
    tasks.route.manifest_path.write_text(json.dumps(document))
    other = approved_task(tasks, request_id='disallowed')
    denied = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(other, WORKER)
    assert denied['progress']['reason'] == 'source_policy_disallows_discovery'
    assert costs.list(HUMAN, task_id=other) == []
    assert requests == []


def test_unknown_capture_prevents_false_fresh_reuse_while_unchanged_publication_is_truthful(stack, tmp_path, monkeypatch):
    from smi_tasks import DiscoveryPolicy

    tasks, evidence = live_setup(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(tasks.route.manifest_path, tasks.route.version,
        discovery_policy=DiscoveryPolicy(86400, 'canonical-v1')), authority=tasks.authority, live_discovery_enabled=True)
    live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()]), (200, [post()])])
    first = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(approved_task(tasks), WORKER)
    second = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(approved_task(tasks, request_id='repeat'), WORKER)
    assert first['outcome'] == 'usable_update'
    assert second['outcome'] == 'no_usable_update'
    assert second['coverage']['unchanged_members'] == 1
    assert second['discovery_history']['reason'] == 'capture_time_unknown'
    assert second['discovery_history']['retrieval_context']['mapper_key'] == 'brightdata-tiktok-keyword:v1'
    assert second['publication_ids'] == []
    assert len(requests) == 2


def test_prepared_support_recovers_without_manifest_credentials_or_new_dispatch(stack, tmp_path, monkeypatch):
    tasks, evidence = live_setup(stack, tmp_path)
    live_costs(tasks)
    requests = http_boundary(monkeypatch, [(200, [post()])])
    task_id = approved_task(tasks)

    def interrupt(view):
        if view['progress']['phase'] == 'publication_prepared':
            raise RuntimeError('prepared')

    with pytest.raises(RuntimeError, match='prepared'):
        OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), on_progress=interrupt).run_one(task_id, WORKER)
    tasks.route.manifest_path.unlink()
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert len(requests) == 1
    assert len(completed['publication_ids']) == 1


def test_session_loss_fences_late_https_response_and_recovery_preserves_no_reissue(stack, tmp_path, monkeypatch):
    from smi_tasks import TaskExecutionLost
    tasks, evidence = live_setup(stack, tmp_path)
    live_costs(tasks)
    held = []
    requests = []

    def send(opener, request, data=None, timeout=None):
        requests.append(request)
        held[0].disconnect()
        response = io.BytesIO(json.dumps([post()]).encode())
        response.status = 200
        response.headers = {}
        return response

    monkeypatch.setattr(OpenerDirector, 'open', send)
    task_id = approved_task(tasks)
    with pytest.raises(TaskExecutionLost):
        OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), on_execution=held.append).run_one(task_id, WORKER)
    retry = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    assert retry['coverage']['collected_observations'] == 0
    assert retry['progress']['reason'] == 'cost_operation_in_flight_or_uncertain'
    assert retry['publication_ids'] == []
    assert len(requests) == 1


def test_pending_queries_stop_at_request_cap_and_schedule_admission_remains_offline(stack, tmp_path, monkeypatch):
    from smi_ingestion.contracts import RunLimits
    from smi_tasks import TaskAuthority
    from smi_tasks.schedules import ScheduledDiscovery
    from test_schedules import config, Clock

    tasks, evidence = live_setup(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(tasks.route.manifest_path, tasks.route.version,
        limits=RunLimits(1, 1, 1)), authority=tasks.authority, live_discovery_enabled=True)
    live_costs(tasks)
    requests = http_boundary(monkeypatch, [(202, {'snapshot_id': 'sd_pending'})])
    task_id = approved_task(tasks)
    OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    stopped = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    assert stopped['outcome'] == 'failure'
    assert stopped['failure']['code'] == 'request_limit_reached'
    assert stopped['coverage']['requests_used'] == 1
    owner = ScheduledDiscovery(AcquisitionTasks(tasks.db, route=tasks.route,
        authority=TaskAuthority(schedule_operators=frozenset({HUMAN.actor_id}))), clock=Clock())
    owner.configure(config(), HUMAN, expected_version=0)
    tick = owner.tick(HUMAN)
    assert tick['created_occurrences'][0]['status'] == 'refused'
    assert len(requests) == 1


@pytest.mark.parametrize('terminal', ['failed', 'canceled'])
def test_retry_after_is_persisted_and_checked_before_new_admission_or_http(stack, tmp_path, monkeypatch, terminal):
    from datetime import datetime, timedelta, timezone
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    at = [datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)]
    requests = http_boundary(monkeypatch, [(202, {'snapshot_id': 'sd_delayed'}, {'Retry-After': '30'}),
        (200, {'snapshot_id': 'sd_delayed', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': terminal})])
    task_id = approved_task(tasks)
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), clock=lambda: at[0]).run_one(task_id, WORKER)
    worker()
    waiting = worker()
    assert waiting['progress']['reason'] == 'provider_retry_not_due'
    assert waiting['progress']['retry_not_before'] == '2026-10-23T04:00:30+00:00'
    assert len(requests) == 1
    assert len(costs.list(HUMAN, task_id=task_id)) == 1
    at[0] += timedelta(seconds=30)
    failed = worker()
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'collection', 'code': 'provider_snapshot_' + terminal}
    assert failed['coverage']['returned_records'] == 0
    assert failed['coverage']['failed_records'] == 0
    assert len(requests) == 2
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '2'


def test_review_restart_reopens_existing_offline_receipt_after_manifest_disappears(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import request, running
    from test_tasks import submit

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    manifest.unlink()
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route)) as url:
        status, _, page = request(url, path='/tasks/' + completed['task_id'])
        assert status == 200
        assert completed['publication_ids'][0] in page


def test_live_admission_requires_server_enablement_at_mutation_after_restart(stack, tmp_path):
    from smi_ingestion.evidence import EvidenceError
    from test_keyword_discovery import proposal
    tasks, _ = live_setup(stack, tmp_path)
    disabled = AcquisitionTasks(tasks.db, route=tasks.route, authority=tasks.authority)
    with pytest.raises(EvidenceError, match='live_discovery_disabled'):
        disabled.save_proposal(proposal(), WORKER, request_id='disabled-admission')
    assert disabled.list_proposals(HUMAN) == []


def test_pending_response_bytes_cannot_escape_the_original_cumulative_budget(stack, tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from smi_ingestion.contracts import RunLimits
    tasks, evidence = live_setup(stack, tmp_path)
    first = {'snapshot_id': 'sd_small'}
    cap = len(json.dumps(first).encode()) + 5
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(tasks.route.manifest_path, tasks.route.version,
        limits=RunLimits(3, 1, 1, cap)), authority=tasks.authority, live_discovery_enabled=True)
    live_costs(tasks)
    at = [datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)]
    requests = http_boundary(monkeypatch, [(202, first),
        (200, {'snapshot_id': 'sd_small', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'running'})])
    task_id = approved_task(tasks)
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), clock=lambda: at[0]).run_one(task_id, WORKER)
    worker()
    at[0] += timedelta(seconds=10)
    waiting = worker()
    assert waiting['coverage']['bytes_used'] == cap
    assert waiting['coverage']['requests_used'] == 2
    assert waiting['progress']['code'] == 'provider_operation_ambiguous'
    worker()
    assert len(requests) == 2


def test_network_exception_keeps_secret_out_of_errors_and_does_not_grant_retry(stack, tmp_path, monkeypatch):
    from urllib.error import URLError
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    requests = []

    def fail(opener, request, data=None, timeout=None):
        requests.append(request)
        assert timeout == 75
        raise URLError('dummy-secret')

    monkeypatch.setattr(OpenerDirector, 'open', fail)
    task_id = approved_task(tasks)
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled()).run_one(task_id, WORKER)
    waiting = worker()
    assert waiting['progress']['code'] == 'provider_operation_ambiguous'
    assert waiting['coverage']['requests_used'] == 1
    assert 'dummy-secret' not in json.dumps(waiting) + json.dumps(costs.list(HUMAN, task_id=task_id))
    worker()
    assert len(requests) == 1


def test_download_202_retains_same_snapshot_and_honors_delay_before_download_retry(stack, tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    tasks, evidence = live_setup(stack, tmp_path)
    costs = live_costs(tasks)
    at = [datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)]
    requests = http_boundary(monkeypatch, [(202, {'snapshot_id': 'sd_building'}),
        (200, {'snapshot_id': 'sd_building', 'dataset_id': 'gd_lu702nij2f790tmv9h', 'status': 'ready'}),
        (202, {'status': 'building', 'message': 'Snapshot is building, try again in 10s'}),
        (200, [post()])])
    task_id = approved_task(tasks)
    worker = lambda: OfflineTaskWorker(tasks.db, evidence.root, live_discovery=enabled(), clock=lambda: at[0]).run_one(task_id, WORKER)
    worker()
    at[0] += timedelta(seconds=10)
    worker()
    waiting = worker()
    assert waiting['progress']['code'] == 'provider_pending'
    assert waiting['progress']['resumable'] is True
    assert worker()['progress']['reason'] == 'provider_retry_not_due'
    assert len(requests) == 3
    at[0] += timedelta(seconds=10)
    completed = worker()
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['requests_used'] == 4
    assert [r.get_method() for r in requests] == ['POST', 'GET', 'GET', 'GET']
    assert requests[-1].full_url == requests[-2].full_url
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '4'
