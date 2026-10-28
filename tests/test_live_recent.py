"""Recent X public polling, policy and fake HTTPS with real PostgreSQL."""

import io
import json
from datetime import timedelta
from urllib.request import OpenerDirector

from smi_monitoring.polling import LiveXConfig, RecentPolling
from test_recent_monitoring import configured, OPERATOR, READER, NOW, END, no_external_io as no_external_io
from smi_ingestion.evidence_sets import ActorContext
from smi_costs import CostScope, UsageAccounting
from test_costs import START, END as PERIOD_END

WORKER = ActorContext('local', 'x-worker', 'automation')


def boundary(monkeypatch, replies):
    sent = []
    def send(opener, request, data=None, timeout=None):
        sent.append((request, timeout))
        reply = replies.pop(0)
        if callable(reply):
            reply = reply()
        status, body, *extra = reply
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        response = io.BytesIO(raw)
        response.status, response.headers = status, extra[0] if extra else {}
        return response
    monkeypatch.setattr(OpenerDirector, 'open', send)
    return sent


def response(**changes):
    return {'data': [{'id': '1234', 'text': 'A cushion sample', 'created_at': '2026-10-28T10:30:00Z',
                      'public_metrics': {'like_count': 4, 'repost_count': 2, 'reply_count': 0, 'quote_count': 0, 'bookmark_count': 1, 'impression_count': 100}}],
            'meta': {'result_count': 1}, **changes}


def enabled(**changes):
    return LiveXConfig(**{'enabled': True, 'operation_authorized': True, 'source_use_authorized': True,
                          'bearer_token': 'dummy-secret', **changes})


def setup_polling(stack, tmp_path, *, config=None, ceiling='10', clock=None):
    recent = configured(stack, tmp_path)
    recent.clock = clock or (lambda: NOW + timedelta(minutes=1))
    costs = UsageAccounting(stack[0])
    costs.migrate()
    costs.configure_scope(CostScope('recent-x', 'x', 'recent-search', 'metered', 'USD', START, PERIOD_END,
        unit='declared-post-bound', unit_rate='0.005', rate_version='test-only', measurement_basis='provider_reported'), OPERATOR)
    costs.configure_route('x-recent-search', 'recent-x', OPERATOR, max_units=10)
    costs.configure_ceiling('recent-x', OPERATOR, amount=ceiling, currency='USD', period_start=START, period_end=PERIOD_END)
    poller = RecentPolling(recent, config=config, workers=frozenset({WORKER.actor_id}))
    poller.migrate()
    poller.activate('cushion', OPERATOR, expected_topic_version=1, first_window_end=END, request_id='activate-1')
    return recent, poller, costs


def test_due_live_poll_requires_runtime_authority_and_reopens_one_window(stack, tmp_path, monkeypatch):
    recent, poller, costs = setup_polling(stack, tmp_path)
    sent = boundary(monkeypatch, [(200, response())])
    waiting = poller.run_due(WORKER)
    assert waiting['reason'] == 'live_x_disabled'
    assert sent == []
    poller = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}))
    result = poller.run_due(WORKER)
    assert result['status'] == 'collected'
    window = recent.read_window(result['window_id'], READER)
    assert window['observations'][0]['published_at'] == '2026-10-28T10:30:00+00:00'
    assert window['observations'][0]['captured_at'] is None
    assert window['observations'][0]['metric_measured_at'] is None
    assert window['observations'][0]['body']['metrics'] == {'like_count': 4, 'repost_count': 2, 'reply_count': 0}
    assert window['acquisition']['synthetic'] is False
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'
    reopened = RecentPolling(recent, workers=frozenset({WORKER.actor_id}))
    assert reopened.read('cushion', READER)['occurrences'][0]['window_id'] == result['window_id']
    assert reopened.run_due(WORKER)['status'] == 'not_due'
    assert len(sent) == 1
    assert 'dummy-secret' not in json.dumps(window) + repr(enabled())


def test_unavailable_topic_cannot_starve_other_due_topics(stack, tmp_path, monkeypatch):
    from test_recent_monitoring import SETTINGS, POLICY
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    recent.set_policy({**POLICY, 'context_id': 'other'}, OPERATOR, expected_version=0)
    recent.configure('other', {**SETTINGS, 'source_policy_id': 'other'}, OPERATOR, expected_version=0, request_id='other')
    poller.activate('other', OPERATOR, expected_topic_version=1, first_window_end=END, request_id='other-activation')
    recent.set_policy({**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
    sent = boundary(monkeypatch, [(200, response())])
    assert poller.run_due(WORKER)['reason'] == 'recent_x_collection_not_permitted'
    assert poller.run_due(WORKER)['status'] == 'collected'
    assert len(sent) == 1
    assert recent.read_topic('cushion', READER)['windows'] == []


def test_pending_response_is_retained_as_uncertain_attempt_with_no_reissue(stack, tmp_path, monkeypatch):
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    sent = boundary(monkeypatch, [(202, {'status': 'pending'})])
    result = poller.run_due(WORKER)
    assert result['status'] == 'uncertain'
    attempt = poller.read('cushion', READER)['occurrences'][0]
    assert attempt['acquisition']['requests'] == 1
    assert attempt['acquisition']['response_status'] == 202
    assert attempt['acquisition']['bytes_read'] == 21
    restarted = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}))
    assert restarted.run_due(WORKER)['status'] == 'uncertain'
    assert len(sent) == 1
    assert recent.read_topic('cushion', READER)['windows'] == []
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'


import pytest


@pytest.mark.parametrize(('config', 'reason'), [
    (LiveXConfig(enabled=True), 'live_x_operation_authorization_required'),
    (LiveXConfig(enabled=True, operation_authorized=True), 'live_x_source_use_authorization_required'),
    (LiveXConfig(enabled=True, operation_authorized=True, source_use_authorized=True), 'live_x_credentials_required')])
def test_missing_live_prerequisites_make_no_transport_attempt(stack, tmp_path, monkeypatch, config, reason):
    recent, poller, costs = setup_polling(stack, tmp_path, config=config)
    sent = boundary(monkeypatch, [])
    assert poller.run_due(WORKER)['reason'] == reason
    assert costs.list(READER) == []
    assert sent == []


@pytest.mark.parametrize(('reply', 'reason'), [
    ((200, b'x' * 65536), 'live_x_response_byte_limit'),
    ((200, b'{broken'), 'live_x_invalid_json'),
    ((200, response(meta={'result_count': 2})), 'live_x_response_record_limit'),
    ((200, {'data': [response()['data'][0]] * 11, 'meta': {'result_count': 11}}), 'live_x_response_record_limit'),
    ((200, response(data=[{'id': 'handle', 'text': 'cushion'}])), 'live_x_invalid_identity'),
    ((200, response(data=[{'id': '42', 'text': 'cushion', 'public_metrics': {'like_count': True}}])), 'invalid_recent_x_metrics'),
    ((200, response(errors=[{'detail': 'source-private-wording'}])), 'live_x_partial_error'),
    ((302, {'redirect': 'https://other.test'}), 'live_x_pending_or_http_uncertain')])
def test_failed_bounded_responses_stop_without_reissue_or_source_copy(stack, tmp_path, monkeypatch, reply, reason):
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    sent = boundary(monkeypatch, [reply])
    result = poller.run_due(WORKER)
    assert result['status'] == 'uncertain'
    assert result['reason'] == reason
    assert poller.run_due(WORKER)['status'] == 'uncertain'
    assert len(sent) == 1
    assert recent.timeline('cushion', READER)['observations'] == []
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'
    assert 'source-private-wording' not in json.dumps(poller.read('cushion', READER))


def test_single_page_request_pins_limits_and_incomplete_pagination(stack, tmp_path, monkeypatch):
    from urllib.parse import parse_qs, urlsplit
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    sent = boundary(monkeypatch, [(200, response(meta={'result_count': 1, 'next_token': 'opaque-token'}))])
    result = poller.run_due(WORKER)
    request, timeout = sent[0]
    assert request.get_method() == 'GET'
    assert urlsplit(request.full_url).hostname == 'api.x.com'
    assert parse_qs(urlsplit(request.full_url).query) == {'query': ['"cushion"'], 'max_results': ['10'], 'sort_order': ['recency'],
        'post.fields': ['created_at,public_metrics'], 'start_time': ['2026-10-28T10:00:00+00:00'], 'end_time': [END]}
    assert timeout == 15
    window = recent.read_window(result['window_id'], READER)
    assert window['acquisition']['pagination_remaining'] is True
    assert window['coverage']['collection_status'] == 'partial'
    assert 'opaque-token' not in json.dumps(window)
    assert len(sent) == 1


def test_policy_change_during_io_discards_source_but_keeps_admission(stack, tmp_path, monkeypatch):
    from test_recent_monitoring import POLICY
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    def changed():
        recent.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
        return 200, response()
    sent = boundary(monkeypatch, [changed])
    assert poller.run_due(WORKER)['status'] == 'discarded'
    assert recent.timeline('cushion', READER)['observations'] == []
    assert poller.run_due(WORKER)['status'] == 'discarded'
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'
    assert len(sent) == 1


def test_competing_due_workers_and_lost_backend_cannot_commit_stale_response(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    started, release = Event(), Event()
    backend = []
    def observe(stage, connection):
        if stage == 'cost_dispatch':
            backend.append(connection.info.backend_pid)
    first = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}), transaction_observer=observe)
    def blocked():
        started.set()
        assert release.wait(10)
        return 200, response()
    sent = boundary(monkeypatch, [blocked])
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(first.run_due, WORKER)
        assert started.wait(10)
        assert poller.run_due(WORKER)['status'] == 'busy'
        with stack[0].connect() as control:
            control.execute('SELECT pg_terminate_backend(%s)', (backend[0],))
        assert poller.run_due(WORKER)['status'] == 'uncertain'
        release.set()
        assert pending.result(timeout=10)['status'] == 'ownership_lost'
    assert len(sent) == 1
    assert recent.read_topic('cushion', READER)['windows'] == []
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'


def test_policy_is_rechecked_after_real_cost_contention(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from smi_costs import DeferredProviderOperationAdapter
    from test_recent_monitoring import POLICY
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    held, release, attempting = Event(), Event(), Event()
    def hold(connection):
        held.set()
        assert release.wait(10)
        return 'test_scope_hold'
    def observe(stage, connection):
        if stage == 'prepared':
            attempting.set()
    poller = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}), transaction_observer=observe)
    sent = boundary(monkeypatch, [])
    with ThreadPoolExecutor(max_workers=2) as pool:
        blocker = pool.submit(DeferredProviderOperationAdapter(costs, 'recent-x', max_units=10).execute, WORKER,
            request_id='held-cost', method='test-only', call=lambda bound: None, dispatch_guard=hold)
        assert held.wait(10)
        pending = pool.submit(poller.run_due, WORKER)
        assert attempting.wait(10)
        recent.set_policy({**POLICY, 'revoked': True}, OPERATOR, expected_version=1)
        release.set()
        assert blocker.result(timeout=10)['status'] == 'refused'
        assert pending.result(timeout=10)['reason'] == 'recent_x_collection_not_permitted'
    assert sent == []
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0'
    assert recent.timeline('cushion', READER)['observations'] == []


def test_slow_trickle_stops_at_elapsed_deadline_without_filling_body(stack, tmp_path, monkeypatch):
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    ticks, reads = [0], []
    class Trickle(io.BytesIO):
        status, headers = 200, {}
        def read(self, *args):
            raise AssertionError('Whole-body read defeats the deadline')
        def read1(self, size):
            reads.append(size)
            ticks[0] += 8
            return b' '
    monkeypatch.setattr(OpenerDirector, 'open', lambda *args, **kwargs: Trickle())
    poller = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}), monotonic=lambda: ticks[0])
    result = poller.run_due(WORKER)
    assert result['reason'] == 'live_x_elapsed_limit'
    assert len(reads) == 3
    receipt = poller.read('cushion', READER)['occurrences'][0]['acquisition']
    assert receipt['bytes_read'] == 3
    assert receipt['elapsed_seconds'] == 24
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'


def test_historical_offline_window_retries_before_current_age_and_configuration(stack, tmp_path):
    from test_recent_monitoring import SETTINGS
    recent = configured(stack, tmp_path)
    original = recent.poll('cushion', END, OPERATOR)
    recent.clock = lambda: NOW + timedelta(days=30)
    recent.route = None
    recent.configure('cushion', {**SETTINGS, 'cadence_minutes': 1440}, OPERATOR, expected_version=1, request_id='changed')
    assert recent.poll('cushion', END, OPERATOR) == {'status': 'duplicate', 'window_id': original['window_id']}


def test_periodic_status_and_window_reopen_over_http_without_live_credentials(stack, tmp_path, monkeypatch):
    from smi_review import ReviewApp
    from test_review import request, running
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    original_open = OpenerDirector.open
    boundary(monkeypatch, [(200, response())])
    collected = poller.run_due(WORKER)
    # Restore the real loopback HTTP boundary after the simulated provider call.
    monkeypatch.setattr(OpenerDirector, 'open', original_open)
    app = ReviewApp(stack[0], monitoring_clock=lambda: NOW + timedelta(minutes=1))
    with running(app) as url:
        status, _, html = request(url, path='/monitoring/topics/cushion')
        assert status == 200
        assert 'Periodic X polling' in html
        assert '/monitoring/windows/' + collected['window_id'] in html
        assert '/costs/' + collected['operation_id'] in html
        assert 'dummy-secret' not in html
        status, _, html = request(url, path='/monitoring/windows/' + collected['window_id'])
        assert status == 200 and 'A cushion sample' in html


def test_encoded_request_bound_is_checked_before_admission(stack, tmp_path, monkeypatch):
    from smi_ingestion.evidence import EvidenceError
    from test_recent_monitoring import SETTINGS
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    poller.deactivate('cushion', OPERATOR)
    recent.configure('cushion', {**SETTINGS, 'query': '𠮷' * 200}, OPERATOR, expected_version=1, request_id='long-query')
    sent = boundary(monkeypatch, [])
    with pytest.raises(EvidenceError, match='live_x_request_byte_limit'):
        poller.activate('cushion', OPERATOR, expected_topic_version=2, first_window_end=END, request_id='long-activation')
    assert costs.list(READER) == []
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0'
    assert sent == []


def test_pending_identity_older_than_presentation_page_never_obtains_new_cost_dispatch(stack, tmp_path, monkeypatch):
    at = [NOW + timedelta(minutes=1)]
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled(), clock=lambda: at[0])
    poller.deactivate('cushion', OPERATOR)
    first_end = NOW - timedelta(hours=102)
    poller.activate('cushion', OPERATOR, expected_topic_version=1, first_window_end=first_end.isoformat(), request_id='old-first')
    sent = boundary(monkeypatch, [(202, {'status': 'pending'})] + [(200, {'meta': {'result_count': 0}})] * 101)
    original = poller.run_due(WORKER)
    at[0] += timedelta(seconds=2)
    poller.deactivate('cushion', OPERATOR)
    poller.activate('cushion', OPERATOR, expected_topic_version=1, first_window_end=(first_end + timedelta(hours=1)).isoformat(), request_id='skip-uncertain')
    for _ in range(101):
        assert poller.run_due(WORKER)['status'] == 'collected'
        at[0] += timedelta(seconds=2)
    assert original['occurrence_id'] not in {r['id'] for r in poller.read('cushion', READER)['occurrences']}
    poller.deactivate('cushion', OPERATOR)
    poller.activate('cushion', OPERATOR, expected_topic_version=1, first_window_end=first_end.isoformat(), request_id='backdated')
    replay = poller.run_due(WORKER)
    assert replay['occurrence_id'] == original['occurrence_id']
    assert replay['operation_id'] == original['operation_id']
    assert replay['status'] == 'uncertain'
    assert len(sent) == 102
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '5.1'


@pytest.mark.parametrize(('ceiling', 'reason'), [('0.05', 'cost_allowance_exhausted'), ('10', 'live_x_source_cooldown')])
def test_concurrent_topics_share_exact_allowance_without_extra_http(stack, tmp_path, monkeypatch, ceiling, reason):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from test_recent_monitoring import SETTINGS
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled(), ceiling=ceiling)
    recent.configure('other', SETTINGS, OPERATOR, expected_version=0, request_id='other')
    poller.activate('other', OPERATOR, expected_topic_version=1, first_window_end=END, request_id='other-activation')
    entered, release = Event(), Event()
    def blocking():
        entered.set()
        assert release.wait(10)
        return 200, response()
    sent = boundary(monkeypatch, [blocking])
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(poller.run_due, WORKER)
        assert entered.wait(10)
        second = pool.submit(poller.run_due, WORKER)
        assert second.result(timeout=10)['reason'] == reason
        release.set()
        assert first.result(timeout=10)['status'] == 'collected'
    assert len(sent) == 1
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'
    assert costs.allowance('recent-x', READER)['available_amount'] == ('0' if ceiling == '0.05' else '9.95')


@pytest.mark.parametrize('change', ['withdraw', 'retention', 'expiry'])
def test_live_selected_copies_inherit_current_recent_lifecycle(stack, tmp_path, monkeypatch, change):
    from smi_monitoring.promotion import MonitoringPromotion
    from smi_knowledge import KnowledgePublications
    from test_recent_monitoring import POLICY
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    boundary(monkeypatch, [(200, response())])
    result = poller.run_due(WORKER)
    window = recent.read_window(result['window_id'], READER)
    promotion = MonitoringPromotion(recent, stack[1])
    promotion.migrate()
    promoted = promotion.promote(result['window_id'], (window['observations'][0]['observation_id'],), OPERATOR, request_id='selected-live')
    publication_id = promoted['items'][0]['publication_id']
    publication = KnowledgePublications(stack[0]).read(publication_id, READER)
    assert publication['members'][0]['synthetic'] is False
    assert publication['members'][0]['captured_at'] is None
    if change == 'withdraw':
        recent.withdraw('1234', OPERATOR)
    elif change == 'retention':
        recent.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
    else:
        recent.clock = lambda: NOW + timedelta(hours=25)
        assert recent.timeline('cushion', READER)['observations'][0]['body'] is None
    # Direct KB read, without reopening a promotion or window, honors the parent.
    assert KnowledgePublications(stack[0]).read(publication_id, READER)['members'][0]['availability'] == 'unavailable'
    history = poller.read('cushion', READER)
    assert history['occurrences'][0]['window_id'] == result['window_id']
    assert 'A cushion sample' not in json.dumps(history)


def test_final_provider_bill_reconciles_once_without_restoring_pending_response(stack, tmp_path, monkeypatch):
    from datetime import datetime, timezone
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    sent = boundary(monkeypatch, [(202, {'status': 'pending'})])
    result = poller.run_due(WORKER)
    measured = datetime.now(timezone.utc) + timedelta(seconds=1)
    final = dict(reconciliation_id='x-final', measurement_id='x-bill', units=2, rate_version='test-only',
        measured_at=measured.isoformat(), provenance='operator-test-final-report', reconciled_at=(measured + timedelta(seconds=1)).isoformat(),
        evidence_id='simulated-final-report', outcome='succeeded', settle_admission=True, commitment_ids=(), uncertainty_ids=(), measurement_basis='provider_reported')
    assert costs.reconcile_usage(result['operation_id'], OPERATOR, **final)['status'] == 'recorded'
    assert UsageAccounting(stack[0]).reconcile_usage(result['operation_id'], OPERATOR, **final)['status'] == 'duplicate'
    view = costs.read(result['operation_id'], READER)
    assert view['actuals']['amount'] == '0.01'
    assert view['limits']['billing_state'] == 'final_measurement_recorded'
    assert view['limits']['enforcement_basis'] == 'declared_source_commitment_only'
    assert view['allowance']['outstanding_amount'] == '0'
    assert poller.run_due(WORKER)['status'] == 'uncertain'
    assert len(sent) == 1
    assert recent.read_topic('cushion', READER)['windows'] == []


def test_activation_retries_reopen_before_current_policy_and_age(stack, tmp_path):
    from test_recent_monitoring import POLICY
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    original = poller.read('cushion', READER)['activations'][0]['id']
    recent.clock = lambda: NOW + timedelta(days=10)
    recent.set_policy({**POLICY, 'revoked': True}, OPERATOR, expected_version=1)
    assert poller.activate('cushion', OPERATOR, expected_topic_version=1, first_window_end=END, request_id='activate-1') == {'status': 'duplicate', 'activation_id': original}


def test_conflicting_native_post_within_one_response_is_not_two_captures(stack, tmp_path, monkeypatch):
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    item = response()['data'][0]
    sent = boundary(monkeypatch, [(200, response(data=[item, {**item, 'created_at': '2026-10-28T10:45:00Z'}], meta={'result_count': 2}))])
    result = poller.run_due(WORKER)
    assert result['status'] == 'discarded'
    assert result['reason'] == 'recent_x_capture_conflict'
    assert recent.timeline('cushion', READER)['observations'] == []
    assert len(sent) == 1


def test_source_rate_cooldown_is_shared_before_admission_and_expires(stack, tmp_path, monkeypatch):
    from test_recent_monitoring import SETTINGS
    at = [NOW + timedelta(minutes=1)]
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled(), clock=lambda: at[0])
    recent.configure('other', SETTINGS, OPERATOR, expected_version=0, request_id='other')
    poller.activate('other', OPERATOR, expected_topic_version=1, first_window_end=END, request_id='other-active')
    sent = boundary(monkeypatch, [(200, response()), (200, response())])
    assert poller.run_due(WORKER)['status'] == 'collected'
    refused = poller.run_due(WORKER)
    assert refused['reason'] == 'live_x_source_cooldown'
    assert len(sent) == 1
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'
    assert costs.read(refused['operation_id'], READER)['admission']['state'] == 'refused'
    at[0] += timedelta(seconds=2)
    resumed = poller.run_due(WORKER)
    assert resumed['status'] == 'collected'
    assert resumed['operation_id'] == refused['operation_id']
    assert len(sent) == 2
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.1'


def test_provider_rate_exhaustion_extends_shared_cooldown_without_reissuing_error(stack, tmp_path, monkeypatch):
    from test_recent_monitoring import SETTINGS
    at = [NOW + timedelta(minutes=1)]
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled(), clock=lambda: at[0])
    recent.configure('other', SETTINGS, OPERATOR, expected_version=0, request_id='other')
    poller.activate('other', OPERATOR, expected_topic_version=1, first_window_end=END, request_id='other-active')
    sent = boundary(monkeypatch, [(429, {'error': 'rate'}, {'retry-after': '1200'}), (200, response())])
    assert poller.run_due(WORKER)['status'] == 'uncertain'
    poller.deactivate('cushion', OPERATOR)
    at[0] += timedelta(seconds=900)
    refused = poller.run_due(WORKER)
    assert refused['reason'] == 'live_x_source_cooldown'
    assert len(sent) == 1
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0.05'
    at[0] += timedelta(seconds=300)
    assert poller.run_due(WORKER)['status'] == 'collected'
    assert len(sent) == 2


def test_lost_ownership_before_monetary_admission_dispatches_nothing(stack, tmp_path, monkeypatch):
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    def terminate(stage, connection):
        if stage == 'cost_dispatch':
            with stack[0].connect() as control:
                control.execute('SELECT pg_terminate_backend(%s)', (connection.info.backend_pid,))
    poller = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}), transaction_observer=terminate)
    sent = boundary(monkeypatch, [(200, response())])
    assert poller.run_due(WORKER)['status'] == 'ownership_lost'
    assert sent == []
    assert costs.allowance('recent-x', READER)['outstanding_amount'] == '0'
    successor = RecentPolling(recent, config=enabled(), workers=frozenset({WORKER.actor_id}))
    assert successor.run_due(WORKER)['status'] == 'collected'
    assert len(sent) == 1


def test_current_openapi_repost_metric_is_preserved_without_inventing_view_equivalence(stack, tmp_path, monkeypatch):
    recent, poller, costs = setup_polling(stack, tmp_path, config=enabled())
    boundary(monkeypatch, [(200, {'data': [{'id': '9876', 'text': 'cushion source sample', 'created_at': '2026-10-28T10:30:00Z',
        'public_metrics': {'repost_count': 7, 'reply_count': 3, 'like_count': 12, 'quote_count': 2, 'bookmark_count': 4, 'impression_count': 150}}],
        'meta': {'result_count': 1}})])
    result = poller.run_due(WORKER)
    record = recent.read_window(result['window_id'], READER)['observations'][0]
    assert record['body']['metrics'] == {'repost_count': 7, 'reply_count': 3, 'like_count': 12}
    assert 'view_count' in record['missing_fields']
    assert record['metric_measured_at'] is None
