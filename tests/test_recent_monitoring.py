from __future__ import annotations

import json
import socket
from datetime import datetime, timezone

import pytest

from smi_ingestion.evidence_sets import ActorContext
from smi_monitoring.recent import OfflineXRoute, RecentMonitoring
from test_monitoring_planning import monitoring as monitoring_fixture
from test_campaigns import campaigns as campaigns_fixture


monitoring = monitoring_fixture
campaigns = campaigns_fixture


@pytest.fixture(autouse=True)
def no_external_io(monkeypatch):
    connect = socket.socket.connect

    def loopback_only(sock, address):
        if isinstance(address, tuple) and address[0] not in {'127.0.0.1', 'localhost', '::1'}:
            raise AssertionError('External I/O is forbidden')
        return connect(sock, address)

    monkeypatch.setattr(socket.socket, 'connect', loopback_only)


OPERATOR = ActorContext('local', 'monitoring-operator', 'human')
READER = ActorContext('local', 'reader', 'human')
NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
END = '2026-10-28T12:00:00+00:00'
POLICY = {'context_id': 'offline-x', 'can_process': True, 'can_display': True, 'can_retain': True,
          'expires_at': None, 'revoked': False}
SETTINGS = {'query': 'cushion', 'cadence_minutes': 60, 'window_minutes': 120, 'max_records': 10,
            'retention_hours': 24, 'source_policy_id': 'offline-x'}
RECORD = {'capture_id': 'capture-11', 'native_id': '11', 'text': 'A cushion <sample>',
          'published_at': '2026-10-28T10:30:00+00:00', 'captured_at': '2026-10-28T11:00:00+00:00',
          'metric_measured_at': '2026-10-28T11:00:00+00:00', 'metrics': {'like_count': 4}}


def fixture_route(tmp_path, records=None, coverage='complete'):
    path = tmp_path / 'recent-x.json'
    path.write_text(json.dumps({'coverage': coverage, 'records': [RECORD] if records is None else records}))
    return OfflineXRoute(path)


def configured(stack, tmp_path, **kwargs):
    store = RecentMonitoring(stack[0], route=fixture_route(tmp_path), operators=frozenset({OPERATOR.actor_id}), clock=lambda: NOW, **kwargs)
    store.migrate()
    store.set_policy(POLICY, OPERATOR, expected_version=0)
    store.configure('cushion', SETTINGS, OPERATOR, expected_version=0, request_id='topic-1')
    return store


def test_offline_poll_reopens_stable_captures_and_logical_window_without_kb(stack, tmp_path, monkeypatch):
    def external_io_forbidden(*args, **kwargs):
        raise AssertionError('External I/O is forbidden')
    monkeypatch.setattr(socket, 'create_connection', external_io_forbidden)
    store = configured(stack, tmp_path)
    result = store.poll('cushion', END, OPERATOR)
    assert result['status'] == 'collected'
    window = store.read_window(result['window_id'], READER)
    assert window['coverage']['collection_status'] == 'complete'
    assert window['coverage']['market_coverage'] == 'unknown'
    observation = window['observations'][0]
    assert observation['native_id'] == '11'
    assert observation['source_reference'] == 'https://x.com/i/status/11'
    assert observation['captured_at'] == '2026-10-28T11:00:00+00:00'
    assert observation['published_at'] == '2026-10-28T10:30:00+00:00'
    assert observation['imported_at'] == END
    assert observation['body']['text'] == 'A cushion <sample>'
    assert observation['body']['metrics'] == {'like_count': 4}
    reopened = RecentMonitoring(stack[0], operators=frozenset({OPERATOR.actor_id}), clock=lambda: NOW)
    assert reopened.read_window(result['window_id'], READER) == window
    assert reopened.poll('cushion', END, OPERATOR)['status'] == 'duplicate'
    assert reopened.timeline('cushion', READER)['observations'] == [observation]
    assert reopened.read_topic('cushion', READER)['version'] == 1


def test_withdrawal_removes_retained_copy_and_prevents_reimport_under_a_new_capture(stack, tmp_path):
    store = configured(stack, tmp_path)
    first = store.poll('cushion', END, OPERATOR)
    store.withdraw('11', OPERATOR)
    assert store.read_window(first['window_id'], READER)['observations'][0]['body'] is None
    route = fixture_route(tmp_path, [{**RECORD, 'capture_id': 'fresh-looking-capture'}])
    later = RecentMonitoring(stack[0], route=route, operators=frozenset({OPERATOR.actor_id}), clock=lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc))
    second = later.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)
    assert later.read_window(second['window_id'], READER)['coverage']['withdrawn_records'] == 1
    assert len(later.timeline('cushion', READER)['observations']) == 1
    assert later.timeline('cushion', READER)['observations'][0]['state'] == 'source_withdrawn'


def test_missing_fields_partial_bounds_and_original_acquisition_remain_visible(stack, tmp_path):
    store = configured(stack, tmp_path)
    records = [{**RECORD, 'captured_at': None, 'metric_measured_at': None, 'metrics': {}},
               {**RECORD, 'capture_id': 'unknown-publication', 'native_id': '12', 'published_at': None},
               {**RECORD, 'capture_id': 'outside', 'native_id': '13', 'published_at': END, 'captured_at': END}]
    store.route = fixture_route(tmp_path, records)
    result = store.poll('cushion', END, OPERATOR)
    window = store.read_window(result['window_id'], READER)
    assert window['coverage']['collection_status'] == 'partial'
    assert window['coverage']['unassessable_records'] == 1
    assert window['coverage']['selected_records'] == 1
    observation = store.timeline('cushion', READER)['observations'][0]
    assert observation['missing_fields'] == ['captured_at', 'metric_measured_at', 'like_count', 'repost_count', 'reply_count', 'view_count']
    assert observation['acquisition']['route'] == 'offline-x-json'
    assert observation['acquisition']['synthetic'] is True
    assert observation['metric_definitions']['like_count'].startswith('X public likes')
    assert store.read_observation(observation['observation_id'], READER) == observation


@pytest.mark.parametrize('change,purpose,available', [({'can_display': False}, 'display', False),
    ({'can_display': False}, 'process', True), ({'can_process': False}, 'process', False),
    ({'can_process': False}, 'display', True), ({'can_retain': False}, 'display', False),
    ({'revoked': True}, 'display', False), ({'expires_at': '2026-10-28T12:00:00Z'}, 'display', False)])
def test_current_permissions_govern_detail_and_retention_recovery_cannot_restore(stack, tmp_path, change, purpose, available):
    store = configured(stack, tmp_path)
    first = store.poll('cushion', END, OPERATOR)
    observation_id = store.read_window(first['window_id'], READER)['observations'][0]['observation_id']
    store.set_policy({**POLICY, **change}, OPERATOR, expected_version=1)
    assert (store.read_observation(observation_id, READER, purpose=purpose)['body'] is not None) is available
    store.set_policy(POLICY, OPERATOR, expected_version=2)
    purged = 'can_retain' in change or 'revoked' in change or 'expires_at' in change
    assert (store.read_observation(observation_id, READER)['body'] is None) is purged
    assert store.poll('cushion', END, OPERATOR)['status'] == 'duplicate'
    assert (store.read_observation(observation_id, READER)['body'] is None) is purged


def test_retention_uses_original_capture_and_never_refreshes_import_on_later_window(stack, tmp_path):
    store = configured(stack, tmp_path)
    store.configure('cushion', {**SETTINGS, 'window_minutes': 180}, OPERATOR, expected_version=1, request_id='longer')
    first = store.poll('cushion', END, OPERATOR)
    original = store.read_window(first['window_id'], READER)['observations'][0]
    store.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    second = store.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)
    assert store.read_window(second['window_id'], READER)['observations'][0] == original
    store.clock = lambda: datetime(2026, 10, 29, 11, tzinfo=timezone.utc)
    expired = store.read_observation(original['observation_id'], READER)
    assert expired['body'] is None and expired['state'] == 'retention_expired'
    assert expired['imported_at'] == END
    store.clock = lambda: NOW
    assert store.poll('cushion', END, OPERATOR)['status'] == 'duplicate'
    assert store.read_observation(original['observation_id'], READER)['body'] is None


def test_window_identity_survives_topic_edits_and_concurrent_retries(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from smi_ingestion.evidence import EvidenceError
    store = configured(stack, tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: store.poll('cushion', END, OPERATOR), range(2)))
    assert {r['status'] for r in results} == {'collected', 'duplicate'}
    assert len({r['window_id'] for r in results}) == 1
    store.configure('cushion', {**SETTINGS, 'query': 'different', 'window_minutes': 60, 'cadence_minutes': 30}, OPERATOR, expected_version=1, request_id='topic-2')
    retry = store.poll('cushion', '2026-10-28T21:00:00+09:00', OPERATOR)
    assert retry['window_id'] == results[0]['window_id']
    historical = store.read_window(retry['window_id'], READER)
    assert historical['coverage']['query'] == 'cushion'
    assert historical['window_start'] == '2026-10-28T10:00:00+00:00'
    assert len(store.read_topic('cushion', READER)['revisions']) == 2
    assert store.configure('cushion', SETTINGS, OPERATOR, expected_version=0, request_id='topic-1')['status'] == 'duplicate'
    with pytest.raises(EvidenceError, match='version_conflict'):
        store.configure('cushion', SETTINGS, OPERATOR, expected_version=1, request_id='stale')
    with pytest.raises(EvidenceError, match='request_conflict'):
        store.configure('cushion', {**SETTINGS, 'query': 'changed'}, OPERATOR, expected_version=0, request_id='topic-1')


def test_record_cap_deduplicates_captures_and_preserves_partial_empty_coverage(stack, tmp_path):
    store = configured(stack, tmp_path)
    store.configure('cushion', {**SETTINGS, 'max_records': 1}, OPERATOR, expected_version=1, request_id='one')
    store.route = fixture_route(tmp_path, [RECORD, RECORD, {**RECORD, 'capture_id': 'second', 'native_id': '12'}])
    first = store.poll('cushion', END, OPERATOR)
    window = store.read_window(first['window_id'], READER)
    assert len(window['observations']) == 1 and window['coverage']['record_limit_reached'] is True
    assert window['coverage']['duplicate_records'] == 1
    store.route = fixture_route(tmp_path, [], 'missing')
    store.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    missing = store.read_window(store.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)['window_id'], READER)
    assert missing['coverage']['collection_status'] == 'missing'
    assert missing['coverage']['field_coverage'] == 'not_assessable'
    assert missing['observations'] == []
    assert len(store.timeline('cushion', READER)['observations']) == 1


def test_poll_authority_and_recent_window_validation_apply_to_retries(stack, tmp_path):
    from smi_ingestion.evidence import EvidenceError
    store = configured(stack, tmp_path)
    store.poll('cushion', END, OPERATOR)
    with pytest.raises(EvidenceError, match='monitoring_operator_required'):
        store.poll('cushion', END, READER)
    for end in ('2026-10-28T12:30:00Z', '2026-10-28T13:00:00Z', '2020-01-01T00:00:00Z', '2026-10-28T12:00:00'):
        with pytest.raises(EvidenceError):
            store.poll('cushion', end, OPERATOR)
    assert len(store.read_topic('cushion', READER)['windows']) == 1


@pytest.mark.parametrize('time_field', ['captured_at', 'metric_measured_at'])
def test_source_time_and_file_bounds_fail_without_claiming_a_window(stack, tmp_path, time_field):
    from smi_ingestion.evidence import EvidenceError
    store = configured(stack, tmp_path)
    store.route = fixture_route(tmp_path, [{**RECORD, time_field: '2026-10-29T12:00:00Z'}])
    with pytest.raises(EvidenceError, match='source_time'):
        store.poll('cushion', END, OPERATOR)
    assert store.read_topic('cushion', READER)['windows'] == []
    path = tmp_path / 'recent-x.json'
    path.write_bytes(b' ' * 262145)
    with pytest.raises(EvidenceError, match='file_limit'):
        store.poll('cushion', END, OPERATOR)
    fixture_route(tmp_path, [RECORD] * 201)
    with pytest.raises(EvidenceError, match='file_record_limit'):
        store.poll('cushion', END, OPERATOR)
    assert store.read_topic('cushion', READER)['windows'] == []


def test_http_topic_poll_restart_and_current_policy_detail(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    store = configured(stack, tmp_path)
    app = ReviewApp(stack[0], OPERATOR.actor_id, recent_x_route=store.route, monitoring_operator=True, monitoring_clock=lambda: NOW)
    with running(app) as url:
        status, _, html = request(url, path='/monitoring/topics')
        assert status == 200 and 'Recent X' in html
        fields = form(html, '/monitoring/topics')
        fields.update(topic_key=['beauty'], settings=[json.dumps(SETTINGS)])
        status, headers, html = request(url, 'POST', '/monitoring/topics', fields)
        assert status == 303, html
        topic_path = headers['Location']
        _, _, html = request(url, path=topic_path)
        action = topic_path + '/poll'
        fields = form(html, action)
        fields['window_end'] = [END]
        status, headers, html = request(url, 'POST', action, fields)
        assert status == 303, html
        window_path = headers['Location']
        _, _, html = request(url, path=window_path)
        assert 'A cushion &lt;sample&gt;' in html and 'Market coverage: unknown' in html
        window_id = window_path.rsplit('/', 1)[1]
        observation_id = store.read_window(window_id, READER)['observations'][0]['observation_id']
        observation_path = '/monitoring/observations/' + observation_id
        store.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
        _, _, html = request(url, path=observation_path)
        assert 'A cushion' not in html and 'source_retention_unavailable' in html
        fields['actor_id'] = ['forged']
        assert request(url, 'POST', action, fields)[0] == 422
        assert request(url, 'POST', action, {**fields, 'csrf': ['invalid']})[0] == 422
        assert request(url, 'POST', action, fields, headers={'Origin': 'https://example.invalid'})[0] == 403
    restarted = ReviewApp(stack[0], OPERATOR.actor_id)
    with running(restarted) as url:
        status, _, html = request(url, path=window_path)
        assert status == 200 and 'A cushion' not in html and 'source_retention_unavailable' in html
        status, _, html = request(url, path=topic_path)
        assert status == 200 and window_path in html


def test_retention_purge_cannot_be_reconstructed_with_an_alias_capture_label(stack, tmp_path):
    store = configured(stack, tmp_path)
    store.configure('cushion', {**SETTINGS, 'window_minutes': 180}, OPERATOR, expected_version=1, request_id='overlap')
    first = store.poll('cushion', END, OPERATOR)
    original = store.read_window(first['window_id'], READER)['observations'][0]
    store.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
    store.set_policy(POLICY, OPERATOR, expected_version=2)
    store.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    store.route = fixture_route(tmp_path, [{**RECORD, 'capture_id': 'alias'}])
    second = store.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)
    restored = store.read_window(second['window_id'], READER)['observations'][0]
    assert restored['observation_id'] == original['observation_id']
    assert restored['body'] is None and restored['imported_at'] == END
    assert len(store.timeline('cushion', READER)['observations']) == 1
    store.clock = lambda: datetime(2026, 10, 28, 14, tzinfo=timezone.utc)
    store.configure('cushion', {**SETTINGS, 'window_minutes': 240}, OPERATOR, expected_version=2, request_id='new-capture-window')
    store.route = fixture_route(tmp_path, [{**RECORD, 'capture_id': 'new-source-capture', 'captured_at': '2026-10-28T13:30:00Z', 'text': 'Updated cushion'}])
    third = store.poll('cushion', '2026-10-28T14:00:00Z', OPERATOR)
    actual_new = store.read_window(third['window_id'], READER)['observations'][0]
    assert actual_new['observation_id'] != original['observation_id']
    assert actual_new['body']['text'] == 'Updated cushion'


@pytest.mark.parametrize('field,value,code', [('max_records', 101, 'max_records'), ('window_minutes', 10081, 'window_minutes'),
    ('cadence_minutes', 0, 'cadence_minutes'), ('retention_hours', 721, 'retention_hours'), ('query', '', 'query')])
def test_operator_settings_have_finite_bounds(stack, tmp_path, field, value, code):
    from smi_ingestion.evidence import EvidenceError
    store = configured(stack, tmp_path)
    with pytest.raises(EvidenceError, match=code):
        store.configure('cushion', {**SETTINGS, field: value}, OPERATOR, expected_version=1, request_id='invalid')
    assert store.read_topic('cushion', READER)['version'] == 1


def test_capture_mutation_cannot_replace_original_and_pagination_is_bounded(stack, tmp_path):
    from smi_ingestion.evidence import EvidenceError
    store = configured(stack, tmp_path)
    store.configure('cushion', {**SETTINGS, 'window_minutes': 180}, OPERATOR, expected_version=1, request_id='overlap')
    first = store.poll('cushion', END, OPERATOR)
    original = store.read_window(first['window_id'], READER)
    store.clock = lambda: datetime(2026, 10, 28, 13, tzinfo=timezone.utc)
    store.route = fixture_route(tmp_path, [{**RECORD, 'capture_id': 'alias', 'text': 'Mutated cushion text'}])
    with pytest.raises(EvidenceError, match='capture_conflict'):
        store.poll('cushion', '2026-10-28T13:00:00Z', OPERATOR)
    assert store.read_window(first['window_id'], READER) == original
    assert len(store.read_topic('cushion', READER)['windows']) == 1
    assert store.timeline('cushion', READER, limit=1, offset=1)['observations'] == []
    for kwargs in ({'limit': 101}, {'offset': 20001}, {'purpose': 'retain'}):
        with pytest.raises(EvidenceError):
            store.timeline('cushion', READER, **kwargs)
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        store.read_window(first['window_id'], ActorContext('foreign', 'reader', 'human'))


def test_frozen_snapshot_investigation_is_unchanged_by_recent_poll_and_withdrawal(monitoring, tmp_path):
    from test_monitoring_planning import insight
    store, _ = monitoring
    created, prepared, before = insight(monitoring)
    recent = RecentMonitoring(store.db, route=fixture_route(tmp_path), operators=frozenset({OPERATOR.actor_id}), clock=lambda: NOW)
    recent.migrate()
    store.migrate()
    recent.set_policy(POLICY, OPERATOR, expected_version=0)
    recent.configure('cushion', SETTINGS, OPERATOR, expected_version=0, request_id='topic')
    recent.poll('cushion', END, OPERATOR)
    recent.withdraw('11', OPERATOR)
    assert store.read_insight(prepared['insight_id'], READER) == before
    assert store.read_investigation(created['investigation_id'], READER)['insight_version'] == 1
    assert before['coverage']['trend_status'] == 'not_assessable' and before['coverage']['baseline'] is None


def test_topic_history_cap_and_policy_refusal_are_visible_through_public_operations(stack, tmp_path):
    from smi_ingestion.evidence import EvidenceError
    store = configured(stack, tmp_path)
    for version in range(1, 100):
        store.configure('cushion', SETTINGS, OPERATOR, expected_version=version, request_id=f'edit-{version}')
    with pytest.raises(EvidenceError, match='revision_limit'):
        store.configure('cushion', SETTINGS, OPERATOR, expected_version=100, request_id='overflow')
    assert len(store.read_topic('cushion', READER)['revisions']) == 100
    store.set_policy({**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
    with pytest.raises(EvidenceError, match='collection_not_permitted'):
        store.poll('cushion', END, OPERATOR)
    assert store.read_topic('cushion', READER)['windows'] == []
