"""Selected recent evidence crosses normal ingestion/publication with parent policy."""

import json
import socket
from datetime import datetime, timedelta, timezone

import pytest

from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope
from smi_monitoring.recent import OfflineXRoute, RecentMonitoring
from smi_monitoring.promotion import MonitoringPromotion


OPERATOR = ActorContext('local', 'monitoring-operator', 'human')
READER = ActorContext('local', 'reader', 'human')
POLICY = {'context_id': 'offline-x', 'can_process': True, 'can_display': True,
          'can_retain': True, 'expires_at': None, 'revoked': False}


@pytest.fixture(autouse=True)
def forbidden_external_io(monkeypatch):
    calls = []
    original = socket.socket.connect
    def local_only(sock, address):
        if isinstance(address, tuple) and address[0] not in {'127.0.0.1', 'localhost', '::1'}:
            calls.append(address)
            raise AssertionError('External I/O forbidden')
        return original(sock, address)
    monkeypatch.setattr(socket.socket, 'connect', local_only)
    yield calls
    assert calls == []


def prepared(stack, tmp_path, *, records=None, settings=None):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    record = {'capture_id': 'original-label', 'native_id': '11', 'text': 'A cushion <sample>',
              'published_at': (now - timedelta(minutes=90)).isoformat(),
              'captured_at': (now - timedelta(hours=1)).isoformat(),
              'metric_measured_at': (now - timedelta(hours=1, minutes=5)).isoformat(),
              'metrics': {'like_count': 4, 'repost_count': 2}}
    path = tmp_path / 'recent.json'
    path.write_text(json.dumps({'coverage': 'complete', 'records': records or [record, {**record, 'native_id': '12', 'capture_id': 'unselected'}]}))
    recent = RecentMonitoring(stack[0], route=OfflineXRoute(path), operators=frozenset({OPERATOR.actor_id}), clock=lambda: now)
    recent.migrate()
    recent.set_policy(POLICY, OPERATOR, expected_version=0)
    recent.configure('cushion', {'query': 'cushion', 'cadence_minutes': 60, 'window_minutes': 120,
                               'max_records': 10, 'retention_hours': 24, 'source_policy_id': 'offline-x', **(settings or {})},
                     OPERATOR, expected_version=0, request_id='topic')
    window_id = recent.poll('cushion', now.isoformat(), OPERATOR)['window_id']
    window = recent.read_window(window_id, READER)
    promotion = MonitoringPromotion(recent, stack[1])
    promotion.migrate()
    return recent, promotion, window


def test_selected_capture_publishes_content_without_inventing_an_account_and_reopens(stack, tmp_path):
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]
    result = promotion.promote(window['window_id'], (selected['observation_id'],), OPERATOR, request_id='chosen')
    assert result['status'] == 'published'
    assert len(result['items']) == 1
    item = result['items'][0]
    assert item['monitoring_observation_id'] == selected['observation_id']
    assert stack[2].inspect(item['run_id'])['requests_used'] == 0
    publication = KnowledgePublications(stack[0]).read(item['publication_id'], READER, include_synthetic=True)
    member = publication['members'][0]
    assert member['captured_at'] == selected['captured_at']
    assert member['source_as_of'] is None
    assert member['coverage']['published_at'] == selected['published_at']
    assert member['source_reference'] == 'https://x.com/i/status/11'
    assert member['coverage']['monitoring_origin']['window_id'] == window['window_id']
    assert member['method']['mapper_key'] == 'monitoring-x:recent-x-content-v1'
    fields = {a['field']: a for a in member['assertions']}
    assert fields['caption']['value'] == 'A cushion <sample>'
    assert fields['author_account']['state'] == 'not_returned'
    assert fields['author_account']['value'] is None
    assert {(a['platform'], a['namespace'], a['kind'], a['native_id']) for a in member['assertions']} == {('x', 'public', 'content', '11')}
    assert {(m['definition'], m['native_name'], m['value'], m['measured_at']) for m in member['metrics']} == {
        ('x_public_like_count', 'like_count', 4, selected['metric_measured_at']),
        ('x_public_repost_count', 'repost_count', 2, selected['metric_measured_at'])}
    query = KnowledgeQueries(stack[0]).search(QueryScope(text='cushion'), READER, request_id='query', include_synthetic=True)
    assert len(query['members']) == 1
    assert len(KnowledgePublications(stack[0]).list(READER, include_synthetic=True)) == 1
    reopened = MonitoringPromotion(RecentMonitoring(stack[0], operators=recent.operators), stack[1])
    assert reopened.read(result['promotion_id'], READER)['items'] == result['items']
    retry = reopened.promote(window['window_id'], (selected['observation_id'],), OPERATOR, request_id='chosen')
    assert retry['promotion_id'] == result['promotion_id']
    assert retry['items'] == result['items']


@pytest.mark.parametrize('change,purpose', [({'can_process': False}, 'process'), ({'can_display': False}, 'display'),
    ({'can_retain': False}, 'display'), ({'revoked': True}, 'display'),
    ({'expires_at': '2020-01-01T00:00:00+00:00'}, 'display')])
def test_parent_policy_governs_direct_kb_reads_without_promotion_synchronization(stack, tmp_path, change, purpose):
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]['observation_id']
    result = promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='selected')
    item = result['items'][0]
    query = KnowledgeQueries(stack[0]).search(QueryScope(text='cushion'), READER, request_id='before', include_synthetic=True)
    recent.set_policy({**POLICY, **change}, OPERATOR, expected_version=1)
    # Intentionally no promotion/recent reader between mutation and direct KB reads.
    publication = KnowledgePublications(stack[0]).read(item['publication_id'], READER, purpose=purpose, include_synthetic=True)
    assert publication['members'][0]['availability'] == 'unavailable'
    assert 'assertions' not in publication['members'][0]
    current = KnowledgeQueries(stack[0]).search(QueryScope(text='cushion'), READER, request_id='after', include_synthetic=True)
    assert current['members'] == []
    pinned = KnowledgeQueries(stack[0]).read(query['result_id'], READER, purpose=purpose, include_synthetic=True)
    assert pinned['members'][0]['availability'] == 'unavailable'
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    recovered = KnowledgePublications(stack[0]).read(item['publication_id'], READER, include_synthetic=True)
    purged = 'can_retain' in change or 'revoked' in change or 'expires_at' in change
    assert (recovered['members'][0]['availability'] == 'unavailable') is purged
    if purged:
        fresh_request = promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='new-request')
        assert fresh_request['items'][0]['publication_id'] == item['publication_id']
        assert fresh_request['status'] == 'unavailable'
        assert fresh_request['items'][0]['state'] == 'publication_unavailable'
        assert KnowledgePublications(stack[0]).read(item['publication_id'], READER, include_synthetic=True)['members'][0]['availability'] == 'unavailable'


def test_native_withdrawal_immediately_denies_promoted_kb_and_cannot_reconstruct(stack, tmp_path):
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]
    result = promotion.promote(window['window_id'], (selected['observation_id'],), OPERATOR, request_id='selected')
    recent.withdraw(selected['native_id'], OPERATOR)
    member = KnowledgePublications(stack[0]).read(result['items'][0]['publication_id'], READER, include_synthetic=True)['members'][0]
    assert member['availability'] == 'unavailable' and member['policy']['can_retain'] is False
    assert KnowledgeQueries(stack[0]).search(QueryScope(), READER, request_id='withdrawn', include_synthetic=True)['members'] == []
    assert promotion.promote(window['window_id'], (selected['observation_id'],), OPERATOR, request_id='again')['items'][0]['state'] == 'publication_unavailable'
    assert stack[1].get(result['items'][0]['observation_id']).payload_path is None


def test_partial_selection_retains_honest_lineage_and_new_requests_reuse_existing_capture(stack, tmp_path):
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from smi_ingestion.evidence import EvidenceError
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]['observation_id']
    missing = str(uuid.uuid4())
    result = promotion.promote(window['window_id'], (selected, missing), OPERATOR, request_id='partial')
    assert result['status'] == 'partial'
    assert result['items'][1] == {'monitoring_observation_id': missing, 'state': 'not_in_window'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        retries = list(pool.map(lambda i: promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='repeat-' + str(i)), range(2)))
    assert all(r['items'][0]['publication_id'] == result['items'][0]['publication_id'] and r['items'][0]['state'] == 'publication_reused' for r in retries)
    assert len(KnowledgePublications(stack[0]).list(READER, include_synthetic=True)) == 1
    with pytest.raises(EvidenceError, match='promotion_request_conflict'):
        promotion.promote(window['window_id'], (missing,), OPERATOR, request_id='partial')
    with pytest.raises(EvidenceError, match='monitoring_operator_required'):
        promotion.promote(window['window_id'], (selected,), READER, request_id='forged')
    recent.set_policy({**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
    denied = promotion.promote(window['window_id'], (window['observations'][1]['observation_id'],), OPERATOR, request_id='denied')
    assert denied['status'] == 'unavailable' and denied['items'][0]['state'] == 'source_unavailable'


def test_http_explicit_selection_retry_protections_result_and_restart(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    recent, _, window = prepared(stack, tmp_path)
    app = ReviewApp(stack[0], OPERATOR.actor_id, monitoring_operator=True, monitoring_clock=recent.clock)
    path = '/monitoring/windows/' + window['window_id']
    action = path + '/promote'
    with running(app) as url:
        status, _, html = request(url, path=path)
        assert status == 200
        fields = form(html, action)
        assert 'Promote selected' in html
        assert fields.get('selected', []) == []
        fields['selected'] = [window['observations'][0]['observation_id']]
        for authority in ('actor_id', 'source_policy', 'route', 'clock', 'campaign_id'):
            assert request(url, 'POST', action, {**fields, authority: ['forged']})[0] == 422
        assert request(url, 'POST', action, {**fields, 'csrf': ['invalid']})[0] == 422
        assert request(url, 'POST', action, fields, headers={'Origin': 'https://external.invalid'})[0] == 403
        status, headers, html = request(url, 'POST', action, fields)
        assert status == 303, html
        result_path = headers['Location']
        assert request(url, 'POST', action, fields)[1]['Location'] == result_path
        _, _, html = request(url, path=result_path)
        assert 'published' in html and window['observations'][0]['observation_id'] in html
        assert window['observations'][1]['observation_id'] not in html
        assert 'A cushion' not in html
    restarted = ReviewApp(stack[0], OPERATOR.actor_id)
    with running(restarted) as url:
        status, _, html = request(url, path=result_path)
        assert status == 200 and 'Knowledge publication' in html
        assert request(url, 'POST', action, {**fields, 'csrf': [restarted.csrf]})[0] == 422


def test_source_change_while_promotion_waits_is_rechecked_before_any_canonical_effect(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import time
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]['observation_id']
    publications = KnowledgePublications(stack[0])
    with ThreadPoolExecutor(max_workers=1) as pool:
        with stack[0].connect() as blocker:
            publications.lock_current(OPERATOR, connection=blocker)
            future = pool.submit(promotion.promote, window['window_id'], (selected,), OPERATOR, request_id='blocked')
            # PostgreSQL blocker metadata synchronizes contention, never asserts product state.
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                with stack[0].connect() as observer:
                    waiting = observer.execute('SELECT 1 FROM pg_stat_activity WHERE %s=ANY(pg_blocking_pids(pid))', (blocker.info.backend_pid,)).fetchone()
                if waiting:
                    break
                time.sleep(.01)
            assert waiting
            recent.withdraw(window['observations'][0]['native_id'], OPERATOR)
        result = future.result(timeout=5)
    assert result['status'] == 'unavailable'
    assert result['items'] == [{'monitoring_observation_id': selected, 'state': 'source_unavailable'}]
    assert publications.list(READER, include_synthetic=True) == []


def test_parent_deadline_and_missing_source_fields_survive_without_fabricated_freshness(stack, tmp_path):
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]
    result = promotion.promote(window['window_id'], (selected['observation_id'],), OPERATOR, request_id='selected')
    observation = stack[1].get(result['items'][0]['observation_id'])
    assert observation.policy.expires_at.isoformat() == selected['retain_until']
    recent.configure('cushion', {**recent.read_topic('cushion', READER)['revisions'][-1]['document'], 'retention_hours': 1, 'window_minutes': 180},
                     OPERATOR, expected_version=1, request_id='shorten')
    recent.clock = lambda: datetime.fromisoformat(window['window_end']) + timedelta(hours=1)
    recent.poll('cushion', recent.clock().isoformat(), OPERATOR)
    # Poll itself shortens the original copy; direct KB reads need no promotion callback.
    member = KnowledgePublications(stack[0]).read(result['items'][0]['publication_id'], READER, include_synthetic=True)['members'][0]
    assert member['availability'] == 'unavailable'
    recent.clock = lambda: datetime.fromisoformat(window['window_end'])
    recent.configure('cushion', {**recent.read_topic('cushion', READER)['revisions'][-1]['document'], 'retention_hours': 24}, OPERATOR, expected_version=2, request_id='restore')
    assert promotion.promote(window['window_id'], (selected['observation_id'],), OPERATOR, request_id='again')['items'][0]['state'] == 'publication_unavailable'
    assert KnowledgePublications(stack[0]).read(result['items'][0]['publication_id'], READER, include_synthetic=True)['members'][0]['availability'] == 'unavailable'


def test_failed_result_commit_rolls_back_normal_ingestion_and_publication(stack, tmp_path):
    import psycopg
    recent, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]['observation_id']
    with stack[0].connect() as connection:
        connection.execute("ALTER TABLE monitoring_promotions ADD CONSTRAINT simulated_receipt_failure CHECK (outcome='fault_only')")
    with pytest.raises(psycopg.errors.CheckViolation):
        promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='retry')
    assert KnowledgePublications(stack[0]).list(READER, include_synthetic=True) == []
    assert list(stack[1].root.iterdir()) == []
    with stack[0].connect() as connection:
        connection.execute('ALTER TABLE monitoring_promotions DROP CONSTRAINT simulated_receipt_failure')
    result = promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='retry')
    assert result['status'] == 'published'
    assert promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='retry') == result


def test_time_expiry_is_enforced_by_independent_kb_reads_before_permission_recovery(stack, tmp_path):
    import time
    recent, promotion, window = prepared(stack, tmp_path)
    recent.set_policy({**POLICY, 'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()}, OPERATOR, expected_version=1)
    selected = window['observations'][0]['observation_id']
    result = promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='selected')
    time.sleep(1.05)
    member = KnowledgePublications(stack[0]).read(result['items'][0]['publication_id'], READER, include_synthetic=True)['members'][0]
    assert member['availability'] == 'unavailable'
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    assert KnowledgeQueries(stack[0]).search(QueryScope(text='cushion'), READER, request_id='expired', include_synthetic=True)['members'] == []


def test_expired_other_workspace_does_not_block_an_independent_publication_read(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from smi_ingestion.support import IngestedEvidence
    recent, promotion, window = prepared(stack, tmp_path)
    local = promotion.promote(window['window_id'], (window['observations'][0]['observation_id'],), OPERATOR, request_id='local')
    other_actor = ActorContext('other', OPERATOR.actor_id, 'human')
    other_recent = RecentMonitoring(stack[0], 'other', route=recent.route, operators=recent.operators, clock=recent.clock)
    other_recent.set_policy({**POLICY, 'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()}, other_actor, expected_version=0)
    other_recent.configure('other', recent.read_topic('cushion', READER)['revisions'][-1]['document'], other_actor, expected_version=0, request_id='other-topic')
    other_window = other_recent.poll('other', window['window_end'], other_actor)['window_id']
    other_capture = other_recent.read_window(other_window, other_actor)['observations'][0]['observation_id']
    other = MonitoringPromotion(other_recent, stack[1]).promote(other_window, (other_capture,), other_actor, request_id='other')
    references = IngestedEvidence(stack[0], 'other').select_run(other['items'][0]['run_id'], other_actor, include_synthetic=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with stack[0].connect() as blocker:
            IngestedEvidence(stack[0], 'other').read(references, other_actor, include_synthetic=True, connection=blocker)
            time.sleep(1.05)
            future = pool.submit(KnowledgePublications(stack[0]).read, local['items'][0]['publication_id'], READER, include_synthetic=True)
            # The other workspace holds share locks on expired support. A local
            # read must neither reconcile it nor wait for an unrelated purge.
            member = future.result(timeout=2)['members'][0]
            assert member['availability'] == 'available'
    expired = KnowledgePublications(stack[0], 'other').read(other['items'][0]['publication_id'], other_actor, include_synthetic=True)
    assert expired['members'][0]['availability'] == 'unavailable'


def test_unknown_capture_and_measurement_times_stay_unknown_in_published_support(stack, tmp_path):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    record = {'capture_id': 'unknown', 'native_id': '99', 'text': 'cushion with missing fields',
              'published_at': (now - timedelta(minutes=30)).isoformat(), 'captured_at': None,
              'metric_measured_at': None, 'metrics': {}}
    _, promotion, window = prepared(stack, tmp_path, records=[record])
    result = promotion.promote(window['window_id'], (window['observations'][0]['observation_id'],), OPERATOR, request_id='unknown')
    member = KnowledgePublications(stack[0]).read(result['items'][0]['publication_id'], READER, include_synthetic=True)['members'][0]
    assert member['captured_at'] is None and member['source_as_of'] is None
    assert member['coverage']['metric_measured_at'] is None
    assert member['metrics'] == []
    assert KnowledgeQueries(stack[0]).account_support(KnowledgeQueries(stack[0]).search(QueryScope(), READER, request_id='unknown-query', include_synthetic=True), READER)['members'][0]['account_keys'] == []


def test_promotion_cannot_collect_source_or_call_configured_model_transport(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    recent, promotion, window = prepared(stack, tmp_path)
    calls = {'acquisition': 0, 'model': 0}
    class ForbiddenRoute:
        def collect(self):
            calls['acquisition'] += 1
            raise AssertionError('Promotion cannot acquire')
    def forbidden_model(*args, **kwargs):
        calls['model'] += 1
        raise AssertionError('Promotion cannot call model')
    recent.route = ForbiddenRoute()
    app = ReviewApp(stack[0], OPERATOR.actor_id, recent_x_route=recent.route, monitoring_operator=True,
                    monitoring_clock=recent.clock, model_transport=forbidden_model)
    path = '/monitoring/windows/' + window['window_id']
    with running(app) as url:
        _, _, html = request(url, path=path)
        fields = form(html, path + '/promote')
        fields['selected'] = [window['observations'][0]['observation_id']]
        assert request(url, 'POST', path + '/promote', fields)[0] == 303
    assert calls == {'acquisition': 0, 'model': 0}


def test_new_promotion_request_cannot_label_independently_withdrawn_source_copy_usable(stack, tmp_path):
    _, promotion, window = prepared(stack, tmp_path)
    selected = window['observations'][0]['observation_id']
    first = promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='first')
    stack[1].revoke(first['items'][0]['observation_id'])
    assert KnowledgeQueries(stack[0]).search(QueryScope(), READER, request_id='source-revoked', include_synthetic=True)['members'] == []
    again = promotion.promote(window['window_id'], (selected,), OPERATOR, request_id='second')
    assert again['status'] == 'unavailable'
    assert again['items'][0]['state'] == 'publication_unavailable'
    assert again['items'][0]['publication_id'] == first['items'][0]['publication_id']


def test_policy_mutation_contending_with_inflight_mapping_governs_committed_kb_immediately(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import time
    recent, promotion, window = prepared(stack, tmp_path)
    gate = 'promotion-fault-gate:' + stack[0].schema
    with stack[0].connect() as connection:
        connection.execute("CREATE FUNCTION pause_selected_import() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(hashtext(TG_ARGV[0])); RETURN NEW; END $$")
        from psycopg import sql
        connection.execute(sql.SQL('CREATE TRIGGER pause_selected_import BEFORE INSERT ON source_observations FOR EACH ROW EXECUTE FUNCTION pause_selected_import({})').format(sql.Literal(gate)))
    def blocked_by(pid):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with stack[0].connect() as observer:
                row = observer.execute('SELECT pid FROM pg_stat_activity WHERE %s=ANY(pg_blocking_pids(pid))', (pid,)).fetchone()
            if row:
                return row['pid']
            time.sleep(.01)
        raise AssertionError('Expected PostgreSQL fault-gate contention')
    with ThreadPoolExecutor(max_workers=2) as pool:
        with stack[0].connect() as blocker:
            blocker.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (gate,))
            pending = pool.submit(promotion.promote, window['window_id'], (window['observations'][0]['observation_id'],), OPERATOR, request_id='inflight')
            importer_pid = blocked_by(blocker.info.backend_pid)
            policy_change = pool.submit(recent.set_policy, {**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
            blocked_by(importer_pid)
        result = pending.result(timeout=5)
        policy_change.result(timeout=5)
    # Neither promotion nor monitoring readers synchronize these direct reads.
    publication = KnowledgePublications(stack[0]).read(result['items'][0]['publication_id'], READER, include_synthetic=True)
    assert publication['members'][0]['availability'] == 'unavailable'
    assert KnowledgeQueries(stack[0]).search(QueryScope(), READER, request_id='after-inflight', include_synthetic=True)['members'] == []


def test_fixture_alias_and_fresh_request_cannot_restore_selected_or_unselected_purged_support(stack, tmp_path):
    recent, promotion, window = prepared(stack, tmp_path, settings={'window_minutes': 180})
    first = promotion.promote(window['window_id'], (window['observations'][0]['observation_id'],), OPERATOR, request_id='first')
    recent.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    document = json.loads(recent.route.path.read_text())
    for record in document['records']:
        record['capture_id'] = 'alias-' + record['native_id']
    recent.route.path.write_text(json.dumps(document))
    recent.clock = lambda: datetime.fromisoformat(window['window_end']) + timedelta(hours=1)
    next_window = recent.poll('cushion', recent.clock().isoformat(), OPERATOR)['window_id']
    retained = recent.read_window(next_window, READER)['observations']
    assert {r['observation_id'] for r in retained} == {r['observation_id'] for r in window['observations']}
    result = promotion.promote(next_window, tuple(r['observation_id'] for r in retained), OPERATOR, request_id='fresh-alias')
    assert result['status'] == 'unavailable'
    assert [i['state'] for i in result['items']] == ['publication_unavailable', 'source_unavailable']
    assert result['items'][0]['publication_id'] == first['items'][0]['publication_id']
    assert len(KnowledgePublications(stack[0]).list(READER, include_synthetic=True)) == 1
    assert KnowledgeQueries(stack[0]).search(QueryScope(), READER, request_id='after-alias', include_synthetic=True)['members'] == []
