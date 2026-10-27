"""Existing-KB alert context through public persisted operations and HTTP."""

import pytest

from test_recent_monitoring import OPERATOR, READER, no_external_io as recent_no_external_io
from test_quantitative_alerts import alerts, collect_pair
from test_knowledge_queries import publish_account
from test_campaigns import campaigns as campaigns_fixture


no_external_io = recent_no_external_io
campaigns = campaigns_fixture


@pytest.fixture(params=['quantitative', 'semantic'])
def alert_case(request, stack, tmp_path):
    if request.param == 'quantitative':
        recent, baseline, detection = collect_pair(stack, tmp_path)
        alert = alerts(recent).detect(detection, baseline, OPERATOR, request_id='volume')
    else:
        from test_semantic_alerts import collected, semantic
        recent, window = collected(stack, tmp_path)
        owner, _, model = semantic(recent)
        alert = owner.detect(window, OPERATOR, request_id='semantic')
        assert len(model.calls) == 1
        model.on_call = lambda: pytest.fail('Investigation called the detection model')
    return request.param, recent, alert


@pytest.fixture
def forbidden_transports(alert_case, monkeypatch):
    """Count forbidden calls at actual provider HTTP I/O seams after alert setup."""
    from smi_campaigns.responses.http import ResponsesHTTPTransport
    from smi_ingestion.adapters.bright_data import BrightDataTransport
    from smi_ingestion.adapters.tiktok_oembed import TikTokOEmbedTransport
    from smi_ingestion.adapters.tiktok_web import TikTokWebTransport
    import socket
    counts = {'external': 0, 'model': 0, 'acquisition': 0}

    def fail(name):
        def forbidden(*args, **kwargs):
            counts[name] += 1
            raise AssertionError(name + ' transport is forbidden during investigation')
        return forbidden

    connect = socket.socket.connect

    def local_only(sock, address):
        if isinstance(address, tuple) and address[0] not in {'127.0.0.1', 'localhost', '::1'}:
            return fail('external')()
        return connect(sock, address)

    monkeypatch.setattr(socket.socket, 'connect', local_only)
    monkeypatch.setattr(ResponsesHTTPTransport, 'create', fail('model'))
    for transport, method in ((BrightDataTransport, 'fetch'), (BrightDataTransport, 'fetch_profile_field'),
                              (BrightDataTransport, 'progress'), (BrightDataTransport, 'snapshot'),
                              (TikTokOEmbedTransport, 'fetch'), (TikTokWebTransport, 'fetch')):
        monkeypatch.setattr(transport, method, fail('acquisition'))
    yield counts
    assert counts == {'external': 0, 'model': 0, 'acquisition': 0}


def test_alert_context_pins_bounded_existing_kb_separately_from_recent_evidence(stack, tmp_path):
    from smi_monitoring.context import AlertInvestigations
    recent, baseline, detection = collect_pair(stack, tmp_path)
    alert = alerts(recent).detect(detection, baseline, OPERATOR, request_id='volume')
    publication, _ = publish_account(stack, 'old-context', native_id='cushion-context')
    owner = AlertInvestigations(recent)
    owner.migrate()
    saved = owner.investigate('quantitative', alert['alert_id'], READER, request_id='explain')
    assert saved['recent_evidence']['alert_id'] == alert['alert_id']
    assert saved['knowledge_context']['manifest'][0]['publication_id'] == publication['publication_id']
    assert saved['knowledge_context']['scope']['text'] == 'cushion'
    assert saved['knowledge_context']['scope']['limit'] == 20
    assert saved['knowledge_context']['members'][0]['captured_at'] == '2026-10-01T00:00:00+00:00'
    assert saved['explanation']['selected_context_members'] == 1
    assert 'causation' in saved['explanation']['uncertainty']
    assert 'entity equivalence' in saved['explanation']['uncertainty']
    assert saved['recent_dependencies'][1]['window_id'] == detection
    assert len(saved['recent_dependencies'][1]['observation_ids']) == 4
    publish_account(stack, 'later-context', native_id='cushion-later')
    reopened = AlertInvestigations(recent).read(saved['investigation_id'], READER)
    assert reopened['knowledge_context']['manifest'] == saved['knowledge_context']['manifest']
    assert reopened['explanation'] == saved['explanation']
    newer = owner.investigate('quantitative', alert['alert_id'], READER, request_id='new-investigation')
    assert len(newer['knowledge_context']['manifest']) == 2


def test_http_alert_opens_bounded_investigation_and_preserves_restart_and_errors(alert_case, forbidden_transports, stack, campaigns):
    from smi_monitoring.context import AlertInvestigations
    from smi_review import ReviewApp
    from test_review import form, request, running
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    publish_account(stack, 'context', native_id='cushion-<unsafe>')
    prefix = '/monitoring/alerts/' if kind == 'quantitative' else '/monitoring/semantic-alerts/'
    path = prefix + alert['alert_id']
    action = path + '/investigations'
    app = ReviewApp(stack[0], READER.actor_id, monitoring_clock=recent.clock)
    with running(app) as url:
        status, _, page = request(url, path=path)
        assert status == 200
        fields = form(page, action)
        fields['request_id'] = ['browser-context']
        for authority in ('actor_id', 'query', 'campaign_id', 'topic_key', 'enrichment', 'model', 'search_query'):
            status, _, page = request(url, 'POST', action, {**fields, authority: ['forged']})
            assert status == 422 and 'invalid_form' in page and 'browser-context' in page
        status, headers, page = request(url, 'POST', action, fields)
        assert status == 303, page
        saved_path = headers['Location']
        status, retry, _ = request(url, 'POST', action, fields)
        assert status == 303 and retry['Location'] == saved_path
    with running(ReviewApp(stack[0], READER.actor_id, monitoring_clock=recent.clock)) as url:
        status, _, page = request(url, path=saved_path)
        assert status == 200
        assert 'Recent monitoring evidence' in page and 'Existing KB context' in page and 'Derived explanation' in page
        assert 'cushion-&lt;unsafe&gt;' in page and 'cushion-<unsafe>' not in page
        assert '2026-10-01' in page and '2026-10-28' in page and 'causation' in page
    from smi_tasks import AcquisitionTasks
    assert AcquisitionTasks(stack[0]).list(READER) == []
    assert campaigns[0].list_campaigns(READER) == []


def test_missing_context_is_an_exact_saved_gap_without_external_fallback(alert_case, forbidden_transports, stack):
    from smi_monitoring.context import AlertInvestigations
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='missing')
    assert saved['knowledge_context']['manifest'] == []
    assert saved['gaps'] == ['existing_kb_context_missing']
    assert 'gap remains unresolved' in saved['explanation']['finding']
    publish_account(stack, 'new-context', native_id='cushion-new')
    assert owner.read(saved['investigation_id'], READER)['knowledge_context']['manifest'] == []
    assert owner.investigate(kind, alert['alert_id'], READER, request_id='missing')['explanation'] == saved['explanation']
    assert len(owner.investigate(kind, alert['alert_id'], READER, request_id='fresh')['knowledge_context']['manifest']) == 1


@pytest.mark.parametrize('permission', ['can_process', 'can_display', 'can_retain'])
def test_recent_dependency_loss_withholds_explanation_permanently_but_keeps_lineage(alert_case, forbidden_transports, stack, permission):
    from smi_monitoring.context import AlertInvestigations
    from test_recent_monitoring import POLICY
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    publish_account(stack, 'context', native_id='cushion-context')
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='saved')
    recent.set_policy({**POLICY, permission: False}, OPERATOR, expected_version=1)
    denied = owner.read(saved['investigation_id'], READER)
    assert denied['explanation'] is None and denied['explanation_withheld'] is True
    assert denied['recent_dependencies'] == saved['recent_dependencies']
    assert denied['knowledge_context']['manifest'] == saved['knowledge_context']['manifest']
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    assert owner.investigate(kind, alert['alert_id'], READER, request_id='saved')['explanation'] is None


def test_kb_withdrawal_or_derivation_supersession_never_substitutes_new_context(alert_case, forbidden_transports, stack):
    from smi_monitoring.context import AlertInvestigations
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    _, observation = publish_account(stack, 'context', native_id='cushion-original')
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='saved')
    key = ExternalKey('test', 'public', 'account', 'cushion-original')
    CanonicalWriter(stack[0]).apply(observation.id, NormalizedBatch((key,), (
        FieldCandidate(key, 'handle', 'observed', 'CORRECTED_SOURCE_VALUE', '$.handle'),
    ), ()), 'corrected:v2')
    superseded = owner.read(saved['investigation_id'], READER)
    assert superseded['explanation'] is None
    assert superseded['knowledge_context']['manifest'] == saved['knowledge_context']['manifest']
    publish_account(stack, 'replacement', native_id='cushion-replacement')
    stack[1].revoke(observation.id)
    denied = owner.read(saved['investigation_id'], READER)
    assert denied['explanation'] is None
    assert denied['knowledge_context']['manifest'] == saved['knowledge_context']['manifest']
    assert 'cushion-original' not in str(denied['knowledge_context'])
    assert 'CORRECTED_SOURCE_VALUE' not in str(denied)
    assert len(owner.investigate(kind, alert['alert_id'], READER, request_id='new')['knowledge_context']['manifest']) == 1


def test_kb_policy_expiry_withholds_explanation_even_after_trusted_clock_recovery(alert_case, forbidden_transports, stack, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from smi_ingestion import evidence as source_time
    from smi_ingestion.contracts import SourcePolicy
    from smi_monitoring.context import AlertInvestigations
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    expiry = datetime.now(timezone.utc) + timedelta(days=1)
    publish_account(stack, 'expiring', native_id='cushion-expiring', policy=SourcePolicy('expiring', True, True, True, expires_at=expiry))
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='expiring')

    class ExpiredClock(datetime):
        @classmethod
        def now(cls, tz=None):
            value = expiry + timedelta(seconds=1)
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)

    with monkeypatch.context() as time:
        time.setattr(source_time, 'datetime', ExpiredClock)
        expired = owner.read(saved['investigation_id'], READER)
        assert expired['explanation'] is None
        assert 'cushion-expiring' not in str(expired['knowledge_context'])
    reopened = owner.read(saved['investigation_id'], READER)
    assert reopened['explanation'] is None
    assert reopened['knowledge_context']['manifest'] == saved['knowledge_context']['manifest']


def test_saved_context_keeps_exact_dependencies_after_native_withdrawal(alert_case, forbidden_transports, stack):
    from smi_monitoring.context import AlertInvestigations
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='saved')
    # For semantic detection this is an unresolved actual model input.
    recent.withdraw('13', OPERATOR)
    reopened = owner.read(saved['investigation_id'], READER)
    assert reopened['explanation'] is None
    assert reopened['recent_dependencies'] == saved['recent_dependencies']
    assert reopened['knowledge_context']['result_id'] == saved['knowledge_context']['result_id']


def test_context_requires_explicit_synthetic_selection_and_protects_retry_and_workspace(alert_case, forbidden_transports, stack):
    from concurrent.futures import ThreadPoolExecutor
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_monitoring.context import AlertInvestigations
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_publications import HUMAN, WORKER, ingest_account
    run_id, _ = ingest_account(stack, native_id='cushion-development', synthetic=True)
    KnowledgePublications(stack[0]).publish(IngestedEvidence(stack[0]).select_run(run_id, HUMAN, include_synthetic=True), WORKER, request_id='development', include_synthetic=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: owner.investigate(kind, alert['alert_id'], READER, request_id='concurrent'), range(2)))
    assert results[0]['investigation_id'] == results[1]['investigation_id']
    assert results[0]['knowledge_context']['manifest'] == []
    with pytest.raises(EvidenceError, match='request_conflict'):
        owner.investigate(kind, alert['alert_id'], OPERATOR, request_id='concurrent')
    with pytest.raises(EvidenceError, match='request_conflict'):
        owner.investigate(kind, alert['alert_id'], READER, request_id='concurrent', include_synthetic=True)
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='synthetic', include_synthetic=True)
    assert len(saved['knowledge_context']['manifest']) == 1
    with pytest.raises(EvidenceError, match='synthetic_evidence_excluded'):
        owner.read(saved['investigation_id'], READER)
    assert owner.read(saved['investigation_id'], READER, include_synthetic=True)['explanation'] == saved['explanation']
    with pytest.raises(EvidenceError, match='workspace'):
        owner.read(saved['investigation_id'], ActorContext('foreign', READER.actor_id, 'human'))
    with pytest.raises(EvidenceError, match='not_found'):
        AlertInvestigations(type(recent)(stack[0], 'foreign')).read(saved['investigation_id'], ActorContext('foreign', 'reader', 'human'))


def test_context_is_bounded_and_excludes_unpublished_or_unmatched_support(alert_case, forbidden_transports, stack):
    from smi_monitoring.context import AlertInvestigations
    from test_publications import ingest_account
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    for i in range(21):
        publish_account(stack, str(i), native_id=f'cushion-{i}')
    publish_account(stack, 'unrelated', native_id='unrelated-context')
    ingest_account(stack, native_id='cushion-unpublished')
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='bounded')
    assert len(saved['knowledge_context']['manifest']) == 20
    assert saved['knowledge_context']['coverage']['result_limit_reached'] is True
    assert saved['knowledge_context']['coverage']['publications_scanned'] == 22
    assert 'cushion-unpublished' not in str(saved)
    assert 'unrelated-context' not in str(saved)


def test_failed_context_commit_rolls_back_its_query_and_exact_retry_can_recover(alert_case, forbidden_transports, stack, monkeypatch):
    import uuid
    import psycopg
    from smi_ingestion.evidence import EvidenceError
    from smi_knowledge import KnowledgeQueries
    from smi_monitoring.context import AlertInvestigations
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    with stack[0].connect() as connection:
        connection.execute("CREATE FUNCTION fail_context() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'simulated context failure'; END $$")
        connection.execute('CREATE TRIGGER fail_context BEFORE INSERT ON monitoring_alert_investigations FOR EACH ROW EXECUTE FUNCTION fail_context()')
    identities = iter([uuid.UUID('10000000-0000-0000-0000-000000000001'), uuid.UUID('10000000-0000-0000-0000-000000000002')])
    with monkeypatch.context() as randomness:
        randomness.setattr(uuid, 'uuid4', lambda: next(identities))
        with pytest.raises(psycopg.Error):
            owner.investigate(kind, alert['alert_id'], READER, request_id='recover')
    with pytest.raises(EvidenceError, match='not_found'):
        owner.read('10000000-0000-0000-0000-000000000001', READER)
    with pytest.raises(EvidenceError, match='not_found'):
        KnowledgeQueries(stack[0]).read('10000000-0000-0000-0000-000000000002', READER)
    with stack[0].connect() as connection:
        connection.execute('DROP TRIGGER fail_context ON monitoring_alert_investigations')
    saved = owner.investigate(kind, alert['alert_id'], READER, request_id='recover')
    assert owner.read(saved['investigation_id'], READER)['explanation'] == saved['explanation']


@pytest.mark.parametrize('policy_owner', ['recent', 'knowledge'])
def test_source_mutation_waits_for_context_commit_then_withholds_explanation(alert_case, forbidden_transports, stack, policy_owner):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from smi_monitoring.context import AlertInvestigations
    from test_recent_monitoring import POLICY
    kind, recent, alert = alert_case
    owner = AlertInvestigations(recent)
    owner.migrate()
    _, observation = publish_account(stack, 'context', native_id='cushion-context')
    with stack[0].connect() as connection:
        connection.execute("CREATE FUNCTION pause_context() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(937432); RETURN NEW; END $$")
        connection.execute('CREATE TRIGGER pause_context BEFORE INSERT ON monitoring_alert_investigations FOR EACH ROW EXECUTE FUNCTION pause_context()')
    with stack[0].connect() as gate, ThreadPoolExecutor(max_workers=2) as pool:
        gate.execute('SELECT pg_advisory_xact_lock(937432)')
        investigation = pool.submit(owner.investigate, kind, alert['alert_id'], READER, request_id='race')
        deadline = time.monotonic() + 5
        pid = None
        while time.monotonic() < deadline:
            with stack[0].connect() as diagnostic:
                row = diagnostic.execute("SELECT pid FROM pg_locks WHERE locktype='advisory' AND objid=937432 AND NOT granted").fetchone()
            if row:
                pid = row['pid']
                break
            time.sleep(0.01)
        if pid is None:
            gate.commit()
        assert pid is not None, 'investigation did not reach injected commit pause'
        mutation = (pool.submit(recent.set_policy, {**POLICY, 'can_process': False}, OPERATOR, expected_version=1)
                    if policy_owner == 'recent' else pool.submit(stack[1].revoke, observation.id))
        blocked = False
        while time.monotonic() < deadline:
            with stack[0].connect() as diagnostic:
                blocked = diagnostic.execute('SELECT EXISTS (SELECT 1 FROM pg_stat_activity WHERE %s=ANY(pg_blocking_pids(pid))) AS blocked', (pid,)).fetchone()['blocked']
            if blocked:
                break
            time.sleep(0.01)
        gate.commit()
        saved = investigation.result(timeout=5)
        mutation.result(timeout=5)
        assert blocked, 'source mutation escaped dependent context commit'
    assert saved['explanation'] is not None
    assert owner.read(saved['investigation_id'], READER)['explanation'] is None
