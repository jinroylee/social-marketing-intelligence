"""One approved field through public proposal/task/KB and external HTTP operations."""

from dataclasses import replace
import io
import json
from email.message import Message
from urllib.parse import parse_qs, urlsplit
from urllib.request import OpenerDirector

from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker
from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope
from test_tasks import HUMAN, WORKER
from test_keyword_discovery import approved_task, proposal
from test_live_discovery import live_setup, live_costs, enabled, post


def boundary(monkeypatch, replies):
    calls = []
    original = OpenerDirector.open

    def send(opener, request, data=None, timeout=None):
        if urlsplit(request.full_url).hostname != 'api.brightdata.com':
            return original(opener, request, data, timeout)
        calls.append(request)
        status, value = replies.pop(0)
        response = io.BytesIO(json.dumps(value).encode())
        response.status = status
        request.response_read_limits = []
        source_read = response.read
        def bounded_read(size=-1):
            request.response_read_limits.append(size)
            return source_read(size)
        response.read = bounded_read
        response.geturl = lambda: request.full_url
        response.headers = Message()
        response.headers['Content-Type'] = 'application/json'
        return response

    monkeypatch.setattr(OpenerDirector, 'open', send)
    return calls


def configured(stack, tmp_path, **policy):
    from smi_tasks import SupplementationPolicy
    tasks, evidence = live_setup(stack, tmp_path)
    route = OfflineRoute(tasks.route.manifest_path, supplementation=SupplementationPolicy(**policy))
    tasks = AcquisitionTasks(tasks.db, route=route, authority=tasks.authority, live_discovery_enabled=True)
    costs = live_costs(tasks)
    costs.configure_route('brightdata-tiktok-profile', 'live-oct', HUMAN, max_units='1')
    return tasks, evidence, costs


def target(**changes):
    from smi_tasks import ProfileSupplement
    return ProfileSupplement(**{'profile_url': 'https://www.tiktok.com/@example', 'native_id': '9876', **changes})


def profile(**changes):
    return {'id': '9876', 'account_id': 'example', 'url': 'https://www.tiktok.com/@example',
            'nickname': 'Example creator', 'followers': 100, **changes}


def test_exact_approved_missing_nickname_uses_one_profile_call_and_publishes_separate_support(stack, tmp_path, monkeypatch):
    tasks, evidence, costs = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, [profile()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    completed = OfflineTaskWorker(tasks.db, evidence.root, live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['supplementation']['reason'] == 'field_observed'
    assert completed['supplementation']['decision'] == 'retrieve'
    assert completed['supplementation']['checks']['missingness'] == 'missing'
    assert completed['coverage']['requests_used'] == 2
    assert len(calls) == 2
    assert parse_qs(urlsplit(calls[1].full_url).query)['dataset_id'] == ['gd_l1villgoiiidt09ci']
    assert json.loads(calls[1].data) == {'input': [{'url': 'https://www.tiktok.com/@example'}],
        'limit_per_input': 1, 'custom_output_fields': 'id|account_id|url|nickname'}
    publication = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN)
    assert len(publication['members']) == 2
    primary, extra = publication['members']
    assert {a['namespace'] for a in primary['assertions']} == {'brightdata:tiktok-posts'}
    assert [(a['namespace'], a['native_id'], a['field'], a['value']) for a in extra['assertions']] == [
        ('tiktok:public', '9876', 'nickname', 'Example creator')]
    assert extra['metrics'] == []
    assert extra['captured_at'] is None
    assert extra['run_id'] == primary['run_id'] == completed['attempts'][0]['run_id']
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '2'
    assert len(KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='supplemented')['members']) == 2
    assert OfflineTaskWorker(tasks.db, evidence.root, live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER) == completed
    assert len(calls) == 2


def test_profile_response_failure_stops_without_losing_primary_support_or_liability(stack, tmp_path, monkeypatch):
    tasks, evidence, costs = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, [profile(id='5555')])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['outcome'] == 'partial_update'
    assert completed['supplementation']['state'] == 'stopped'
    assert completed['supplementation']['reason'] == 'source_failure'
    assert completed['coverage']['published_members'] == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '2'
    OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert len(calls) == 2


def test_http_human_approves_exact_profile_target_and_reads_actual_support(stack, tmp_path, monkeypatch):
    from smi_review import ReviewApp
    from test_review import form, request, running

    tasks, evidence, _ = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, [profile()])])
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route,
                           live_discovery_enabled=True)) as url:
        page = request(url, path='/proposals/new')[2]
        supplied = form(page, '/proposals')
        assert 'profile_url' in supplied and 'profile_native_id' in supplied
        supplied.update(purpose=['Fill nickname'], intent=['fill'], subject_ids=['product:sunscreen'],
            search_queries=['sunscreen review'], published_from=['2026-10-01T00:00:00Z'],
            published_before=['2026-10-10T00:00:00Z'], profile_url=['https://www.tiktok.com/@example'],
            profile_native_id=['9876'])
        assert request(url, 'POST', '/proposals', {**supplied, 'supplementation_policy': ['injected']})[0] == 422
        status, headers, _ = request(url, 'POST', '/proposals', supplied)
        assert status == 303
        proposal_path = headers['Location']
        review = request(url, path=proposal_path)[2]
        assert 'nickname' in review and 'https://www.tiktok.com/@example' in review and '9876' in review
        approval = form(review, proposal_path + '/approve')
        approval['reviewed'] = ['yes']
        status, headers, _ = request(url, 'POST', proposal_path + '/approve', approval)
        assert status == 303
        task_path = headers['Location']
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_path.split('/')[-1], WORKER)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id)) as url:
        page = request(url, path=task_path)[2]
        assert 'Selective supplementation' in page and 'field_observed' in page
        page = request(url, path=f'/knowledge/publications/{completed["publication_ids"][0]}')[2]
        assert 'Example creator' in page and 'nickname' in page and 'account_equivalence_unestablished' in page
    assert len(calls) == 2


import pytest


@pytest.mark.parametrize(('policy', 'target_id', 'authorized', 'ceiling_amount', 'reason'), [
    ({'expected_information_value': 0}, '9876', True, '10', 'insufficient_information_value'),
    ({'route': 'tiktok-oembed'}, '9876', True, '10', 'capability_unavailable'),
    ({}, '5555', True, '10', 'approved_profile_not_discovered'),
    ({}, '9876', False, '10', 'profile_supplementation_authorization_required'),
    ({}, '9876', True, '1', 'cost_allowance_exhausted'),
])
def test_pre_dispatch_stops_reopen_with_no_secondary_http(stack, tmp_path, monkeypatch,
        policy, target_id, authorized, ceiling_amount, reason):
    from test_costs import START, END
    tasks, evidence, costs = configured(stack, tmp_path, **policy)
    costs.configure_ceiling('live-oct', HUMAN, amount=ceiling_amount, currency='USD', period_start=START, period_end=END)
    calls = boundary(monkeypatch, [(200, [post()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target(native_id=target_id)))
    worker = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=authorized))
    completed = worker.run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['supplementation']['state'] == 'stopped'
    assert completed['supplementation']['reason'] == reason
    assert completed['coverage']['requests_used'] == 1
    assert len(calls) == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'
    assert worker.run_one(task_id, WORKER) == completed
    assert len(calls) == 1
    members = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='stopped')['members']
    assert all(a['field'] != 'nickname' for m in members for a in m['assertions'])


@pytest.mark.parametrize(('changes', 'reason'), [
    ({'max_requests': 1}, 'request_limit_reached'),
    ({'max_records': 1}, 'record_limit_reached'),
    ({'max_pages': 1}, 'record_limit_reached'),
])
def test_supplement_does_not_reset_original_request_record_or_page_limits(stack, tmp_path, monkeypatch, changes, reason):
    from smi_ingestion.contracts import RunLimits
    tasks, evidence, _ = configured(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=replace(tasks.route, limits=RunLimits(**changes)),
        authority=tasks.authority, live_discovery_enabled=True)
    calls = boundary(monkeypatch, [(200, [post()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == reason
    assert completed['coverage']['requests_used'] == 1
    assert len(calls) == 1


def test_unchanged_primary_evidence_stops_missing_field_retry_without_second_profile_call(stack, tmp_path, monkeypatch):
    tasks, evidence, costs = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (500, {'error': 'source failed'}), (200, [post()])])
    worker = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True))
    first = worker.run_one(approved_task(tasks, proposal(profile_supplement=target())), WORKER)
    assert first['supplementation']['reason'] == 'source_failure'
    task_id = approved_task(tasks, proposal(profile_supplement=target()), request_id='second')
    completed = worker.run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == 'unchanged_evidence'
    assert completed['outcome'] == 'no_usable_update'
    assert completed['publication_ids'] == []
    assert len(calls) == 3
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '3'


@pytest.mark.parametrize('withdraw', [False, True])
def test_selected_profile_resumes_only_with_current_runtime_permission(stack, tmp_path, monkeypatch, withdraw):
    tasks, evidence, costs = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    dispatches = []

    def stop_before_secondary_dispatch(phase):
        if phase == 'cost_dispatch':
            dispatches.append(phase)
            if len(dispatches) == 2:
                raise RuntimeError('interrupt_selected_profile')

    with pytest.raises(RuntimeError, match='interrupt_selected_profile'):
        OfflineTaskWorker(tasks.db, evidence.root,
            live_discovery=replace(enabled(), profile_supplementation_authorized=True),
            before_commit=stop_before_secondary_dispatch).run_one(task_id, WORKER)
    assert tasks.read(task_id, HUMAN)['supplementation']['state'] == 'selected'
    if withdraw:
        evidence.revoke(tasks.read(task_id, HUMAN)['supplementation']['basis'][0]['observation_id'])
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=withdraw)).run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == ('source_support_unavailable' if withdraw else 'profile_supplementation_authorization_required')
    assert completed['coverage']['requests_used'] == 1
    assert len(calls) == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'


def test_profile_http_consumption_stays_inside_original_remaining_byte_budget(stack, tmp_path, monkeypatch):
    from smi_ingestion.contracts import RunLimits
    tasks, evidence, _ = configured(stack, tmp_path)
    cap = len(json.dumps([post()]).encode()) + 64
    tasks = AcquisitionTasks(tasks.db, route=replace(tasks.route, limits=RunLimits(max_bytes=cap)),
        authority=tasks.authority, live_discovery_enabled=True)
    calls = boundary(monkeypatch, [(200, [post()]), (200, [profile()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == 'source_failure'
    assert completed['coverage']['bytes_used'] == cap
    assert calls[1].response_read_limits == [64]
    assert completed['coverage']['requests_used'] == 2
    assert len(calls) == 2


@pytest.mark.parametrize(('rows', 'returned'), [([], 0), ([profile(), profile()], 2), ([profile(id='5555')], 1), ([profile(status='error')], 1)])
def test_profile_counts_only_actual_returned_and_eligible_records(stack, tmp_path, monkeypatch, rows, returned):
    tasks, evidence, _ = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, rows)])
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(
            approved_task(tasks, proposal(profile_supplement=target())), WORKER)
    assert completed['coverage']['returned_records'] == 1 + returned
    assert completed['coverage']['selection_eligible_records'] == 1
    assert completed['coverage']['admitted_records'] == 1
    assert completed['coverage']['published_members'] == 1
    assert completed['supplementation']['reason'] == 'source_failure'
    assert len(calls) == 2


@pytest.mark.parametrize(('age_days', 'freshness'), [(0, 'fresh'), (2, 'stale')])
def test_current_published_ordinary_profile_nickname_stops_with_source_capture_freshness(stack, tmp_path, monkeypatch, age_days, freshness):
    from smi_ingestion.contracts import RunLimits
    from smi_ingestion.support import IngestedEvidence

    tasks, evidence, costs = configured(stack, tmp_path)
    monkeypatch.setenv('BRIGHTDATA_API_TOKEN', 'dummy-secret')
    calls = boundary(monkeypatch, [(200, [profile(nickname='Already known')]), (200, [post()])])
    manifest = tmp_path / 'ordinary-profile.json'
    manifest.write_text(json.dumps({'adapter': 'brightdata-tiktok',
        'references': ['https://www.tiktok.com/@example'], 'num_of_posts': 1}))
    report = stack[2].ingest(manifest, RunLimits(max_requests=1))
    support = IngestedEvidence(tasks.db).select_run(report['run_id'], HUMAN)
    KnowledgePublications(tasks.db).publish(support, HUMAN, request_id='ordinary-profile')
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    from datetime import datetime, timedelta, timezone
    at = datetime.now(timezone.utc) + timedelta(days=age_days)
    completed = OfflineTaskWorker(tasks.db, evidence.root, clock=lambda: at,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == 'field_already_supported'
    assert completed['supplementation']['checks']['missingness'] == 'present'
    assert completed['supplementation']['checks']['freshness'] == freshness
    assert len(calls) == 2
    assert completed['coverage']['requests_used'] == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'
    values = KnowledgeQueries(tasks.db).search(QueryScope(text='9876'), HUMAN, request_id='retained')['members']
    assert [a['value'] for m in values for a in m['assertions'] if a['field'] == 'nickname'] == ['Already known']


def test_profile_support_withdrawal_is_visible_in_task_and_kb_without_refetch(stack, tmp_path, monkeypatch):
    tasks, evidence, _ = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, [profile()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    extra = completed['supplementation']['support'][0]['observation_id']
    evidence.revoke(extra)
    reopened = tasks.read(task_id, HUMAN)
    assert reopened['supplementation']['reason'] == 'field_observed'
    assert reopened['supplementation']['current_support'][0]['availability'] != 'available'
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='withdrawn')
    assert all(a['field'] != 'nickname' for m in result['members'] for a in m['assertions'])
    assert len(calls) == 2


def test_pending_profile_stops_without_polling_or_erasing_unknown_billing(stack, tmp_path, monkeypatch):
    tasks, evidence, costs = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (202, {'snapshot_id': 'opaque-profile-work'})])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    worker = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True))
    completed = worker.run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == 'source_failure'
    assert completed['supplementation']['source_outcome'] == 'provider_pending_unresumed'
    assert completed['supplementation']['resumable'] is False
    assert completed['outcome'] == 'partial_update'
    assert 'opaque-profile-work' not in json.dumps(completed)
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '2'
    assert worker.run_one(task_id, WORKER) == completed
    assert len(calls) == 2


def test_lost_profile_evidence_commit_never_reissues_dispatched_work(stack, tmp_path, monkeypatch):
    tasks, evidence, costs = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, [profile()])])
    task_id = approved_task(tasks, proposal(profile_supplement=target()))
    saves = []

    def interrupt(phase):
        if phase == 'evidence':
            saves.append(phase)
            if len(saves) == 2:
                raise RuntimeError('lost_profile_evidence')

    with pytest.raises(RuntimeError, match='lost_profile_evidence'):
        OfflineTaskWorker(tasks.db, evidence.root, before_commit=interrupt,
            live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['supplementation']['reason'] == 'cost_operation_in_flight_or_uncertain'
    assert completed['coverage']['published_members'] == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '2'
    assert len(calls) == 2


def test_recorded_live_schedule_keeps_primary_policy_without_inventing_profile_approval(stack, tmp_path, monkeypatch):
    from smi_ingestion.contracts import RunLimits
    from smi_tasks import SupplementationPolicy
    from smi_tasks.schedules import ScheduledDiscovery
    from test_live_schedules import live_schedule
    from test_schedules import Clock, config

    _, tasks, evidence = live_schedule(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=replace(tasks.route, supplementation=SupplementationPolicy(),
        limits=RunLimits(max_requests=1, max_records=1, max_pages=1)), authority=tasks.authority,
        live_discovery_enabled=True)
    costs = live_costs(tasks)
    owner = ScheduledDiscovery(tasks, clock=Clock())
    owner.configure(config(), HUMAN, expected_version=0, live=True)
    task_id = owner.tick(WORKER)['created_occurrences'][0]['task_id']
    calls = boundary(monkeypatch, [(200, [post()])])
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['supplementation']['reason'] == 'profile_target_not_approved'
    assert completed['coverage']['requests_used'] == 1
    assert completed['daily_allowance']['used'] == 1
    assert len(calls) == 1
    assert costs.allowance('live-oct', HUMAN)['outstanding_amount'] == '1'


def test_invalid_profile_envelope_retains_unknown_returned_count(stack, tmp_path, monkeypatch):
    tasks, evidence, _ = configured(stack, tmp_path)
    calls = boundary(monkeypatch, [(200, [post()]), (200, {'unexpected': 'envelope'})])
    completed = OfflineTaskWorker(tasks.db, evidence.root,
        live_discovery=replace(enabled(), profile_supplementation_authorized=True)).run_one(
            approved_task(tasks, proposal(profile_supplement=target())), WORKER)
    assert completed['coverage']['returned_records'] is None
    assert completed['coverage']['admitted_records'] == 1
    assert completed['supplementation']['reason'] == 'source_failure'
    assert len(calls) == 2
