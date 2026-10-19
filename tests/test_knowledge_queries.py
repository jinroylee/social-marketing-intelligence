from __future__ import annotations

from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgePublications
from test_publications import HUMAN, WORKER, ingest_account


def publish_account(stack, request_id, **kwargs):
    db, _, _, _ = stack
    run_id, observation = ingest_account(stack, **kwargs)
    publications = KnowledgePublications(db)
    publications.migrate()
    publication = publications.publish(IngestedEvidence(db).select_run(run_id, HUMAN), WORKER, request_id=request_id)
    return publication, observation


def test_current_query_uses_only_published_support_and_keeps_source_only_unknowns(stack):
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    publish_account(stack, 'published')
    ingest_account(stack, native_id='pending-unpublished')
    queries = KnowledgeQueries(db)
    result = queries.search(QueryScope(platforms=('test',)), HUMAN, request_id='first')
    assert len(result['members']) == 1
    member = result['members'][0]
    assert member['assertions'][0]['native_id'] == 'account-1'
    assert member['assertions'][0]['state'] == 'not_returned'
    assert member['captured_at'] == '2026-10-01T00:00:00+00:00'
    assert member['freshness']['state'] == 'not_assessed'
    assert member['method']['mapper_key'] == 'offline-test:v1'
    assert result['coverage']['matched_members'] == 1
    assert 'not_complete_market_coverage' in result['unknowns']
    assert 'caption_interpretations_not_published' in member['unknowns']
    assert 'fee' in member['unknowns']
    assert 'audience_geography' in member['unknowns']
    assert 'source_as_of_unknown' in member['unknowns']
    assert result['manifest'][0]['assertion_ids'] == member['assertion_ids']
    assert result['manifest'][0]['method']['mapper_key'] == 'offline-test:v1'
    assert KnowledgeQueries(db).read(result['result_id'], HUMAN)['manifest'] == result['manifest']
    empty = queries.search(QueryScope(text='pending-unpublished'), HUMAN, request_id='absent')
    assert empty['members'] == []
    assert 'no_matching_permitted_published_support' in empty['unknowns']


def test_filters_capture_window_subject_and_freshness_without_renewing_old_capture(stack):
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    publication, _ = publish_account(stack, 'old', native_id='old-account')
    source = KnowledgePublications(db).read(publication['publication_id'], HUMAN)
    subject_id = source['members'][0]['assertions'][0]['subject_id']
    queries = KnowledgeQueries(db)
    scope = QueryScope(text='OLD-ACCOUNT', subject_ids=(subject_id,), platforms=('test',),
                       captured_from='2026-09-30T00:00:00+00:00', captured_to='2026-10-02T00:00:00+00:00', max_age_seconds=1)
    result = queries.search(scope, HUMAN, request_id='capture-filter')
    assert len(result['members']) == 1
    member = result['members'][0]
    assert member['freshness']['state'] == 'stale'
    assert member['freshness']['basis'] == 'source_capture'
    assert member['support_status'] == 'current'
    assert member['availability'] == 'available'
    assert member['ingested_at'] != member['captured_at']
    assert result['coverage']['stale_members'] == 1
    assert queries.search(QueryScope(captured_from='2026-10-02T00:00:00+00:00'), HUMAN, request_id='newer')['members'] == []
    assert queries.search(QueryScope(platforms=('another-platform',)), HUMAN, request_id='platform')['members'] == []
    assert queries.search(QueryScope(text='not-observed'), HUMAN, request_id='text')['members'] == []
    assert queries.search(QueryScope(subject_ids=('00000000-0000-0000-0000-000000000000',)), HUMAN, request_id='subject')['members'] == []


def test_saved_result_keeps_membership_after_new_publication_withdrawal_and_supersession(stack):
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, evidence, _, _ = stack
    first, observation = publish_account(stack, 'first')
    queries = KnowledgeQueries(db)
    original = queries.search(QueryScope(), HUMAN, request_id='before-update')
    second, _ = publish_account(stack, 'second', native_id='account-2')
    latest = queries.search(QueryScope(), HUMAN, request_id='after-update')
    assert len(latest['members']) == 2
    assert {m['publication_id'] for m in latest['manifest']} == {first['publication_id'], second['publication_id']}
    assert queries.search(QueryScope(), HUMAN, request_id='before-update')['manifest'] == original['manifest']
    key = ExternalKey('test', 'public', 'account', 'account-1')
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((key,), (
        FieldCandidate(key, 'handle', 'observed', 'NEW_VALUE_NOT_IN_OLD_RESULT', '$.handle'),
    ), ()), 'corrected:v2')
    superseded = queries.read(original['result_id'], HUMAN)
    assert superseded['manifest'] == original['manifest']
    assert superseded['current_coverage']['superseded_members'] == 1
    assert superseded['members'][0]['method']['mapper_key'] == 'offline-test:v1'
    evidence.revoke(observation.id)
    withdrawn = queries.read(original['result_id'], HUMAN)
    assert withdrawn['manifest'] == original['manifest']
    assert withdrawn['coverage'] == original['coverage']
    assert withdrawn['current_coverage']['unavailable_members'] == 1
    assert 'assertions' not in withdrawn['members'][0]
    assert 'source_reference' not in withdrawn['members'][0]
    assert len(queries.search(QueryScope(), HUMAN, request_id='after-withdrawal')['members']) == 1


def test_query_pins_published_interpretations_and_their_versions_without_inventing_missing_fields(stack):
    from smi_ingestion.evidence_sets import SnapshotImporter
    from smi_knowledge import KnowledgeQueries, KnowledgeStore, QueryScope
    from test_evidence_sets import DATASET, MANIFEST, POLICY
    from test_knowledge import CATALOG, CATALOG_ID

    db, evidence, _, _ = stack
    knowledge = KnowledgeStore(db)
    knowledge.migrate()
    imported = SnapshotImporter(evidence).import_snapshot(MANIFEST, HUMAN, POLICY)
    knowledge.register_catalog(CATALOG, HUMAN)
    prepared = knowledge.prepare(DATASET, CATALOG_ID, WORKER)
    claim = knowledge.read(prepared['run_id'], HUMAN)['interpretations'][0]
    support = tuple(r for r in IngestedEvidence(db).select_run(imported['run_id'], HUMAN) if r.observation_id == claim['observation_id'])
    publications = KnowledgePublications(db)
    publications.publish(support, WORKER, request_id='caption', interpretation_ids=(claim['id'],))
    result = KnowledgeQueries(db).search(QueryScope(), HUMAN, request_id='caption-query')
    assert result['manifest'][0]['interpretation_ids'] == [claim['id']]
    assert result['manifest'][0]['interpretations'][0]['method_version'] == 'caption-literal-rules-v1'
    assert result['interpretations'][0]['value'] == claim['value']
    evidence.revoke(claim['observation_id'])
    reopened = KnowledgeQueries(db).read(result['result_id'], HUMAN)
    assert reopened['interpretations'][0]['id'] == claim['id']
    assert reopened['interpretations'][0]['state'] == 'unavailable'
    assert 'value' not in reopened['interpretations'][0]


def test_local_search_pins_then_reopens_escaped_support_after_restart_and_withdrawal(stack):
    import re

    from smi_review import ReviewApp
    from test_review import request, running

    db, evidence, _, _ = stack
    _, observation = publish_account(stack, 'http', native_id='<script>source-account</script>')
    with running(ReviewApp(db)) as url:
        status, _, page = request(url, path='/knowledge/search')
        assert status == 200
        csrf = re.search(r'name="csrf" value="([^"]+)"', page)[1]
        status, headers, _ = request(url, 'POST', '/knowledge/search', {
            'csrf': csrf, 'request_id': 'http-query', 'text': 'script', 'platforms': 'test',
        })
        assert status == 303
        path = headers['Location']
        status, _, result = request(url, path=path)
        assert status == 200
        assert '&lt;script&gt;source-account&lt;/script&gt;' in result
        assert '<script>source-account</script>' not in result
        assert observation.id in result
        assert 'not_complete_market_coverage' in result
        assert 'not_assessed' in result
        assert 'Unknown' in result
    evidence.revoke(observation.id)
    with running(ReviewApp(db)) as url:
        status, _, result = request(url, path=path)
        assert status == 200
        assert 'Source support unavailable' in result
        assert observation.id in result
        assert 'example.test' not in result
        assert 'source-account' not in result


def test_operator_can_query_and_reopen_exact_result_in_separate_process(stack):
    import json

    from test_cli import _cli

    db, evidence, _, _ = stack
    _, observation = publish_account(stack, 'cli')
    searched = _cli(db, evidence.root, 'search-knowledge', '--text', 'account-1', '--platform', 'test',
                    '--captured-from', '2026-09-01T00:00:00+00:00', '--max-age-seconds', '1',
                    '--request-id', 'cli-query', '--actor', 'named-searcher')
    assert searched.returncode == 0, searched.stdout + searched.stderr
    result = json.loads(searched.stdout)
    assert result['producer'] == {'actor_id': 'named-searcher', 'kind': 'human'}
    assert result['members'][0]['observation_id'] == observation.id
    reopened = _cli(db, evidence.root, 'inspect-query', result['result_id'])
    assert reopened.returncode == 0, reopened.stdout + reopened.stderr
    assert json.loads(reopened.stdout)['manifest'] == result['manifest']


def test_new_search_requires_process_rights_while_saved_display_result_can_remain_visible(stack):
    from dataclasses import asdict

    from psycopg.types.json import Jsonb

    from smi_knowledge import KnowledgeQueries, QueryScope

    db, evidence, _, _ = stack
    publication, observation = publish_account(stack, 'policy')
    queries = KnowledgeQueries(db)
    original = queries.search(QueryScope(), HUMAN, request_id='before-process-denial')
    policy = asdict(evidence.get(observation.id).policy)
    policy['can_process'] = False
    with db.connect() as connection:
        connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(policy), observation.id))
    assert KnowledgePublications(db).read(publication['publication_id'], HUMAN)['members'][0]['availability'] == 'available'
    current = queries.search(QueryScope(text='account-1'), HUMAN, request_id='after-process-denial')
    assert current['members'] == []
    assert current['coverage']['process_denied_members'] == 1
    historical = queries.read(original['result_id'], HUMAN)
    assert historical['members'][0]['availability'] == 'available'
    assert historical['members'][0]['assertions'][0]['native_id'] == 'account-1'
    assert queries.read(original['result_id'], HUMAN, purpose='process')['members'][0]['availability'] == 'unavailable'


def test_bounded_results_and_synthetic_opt_in_are_explicit_and_workspace_scoped(stack):
    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    publish_account(stack, 'one')
    publish_account(stack, 'two', native_id='account-2')
    run_id, synthetic = ingest_account(stack, native_id='development-only', synthetic=True)
    publications = KnowledgePublications(db)
    publications.publish(IngestedEvidence(db).select_run(run_id, HUMAN, include_synthetic=True), WORKER,
                         request_id='synthetic', include_synthetic=True)
    queries = KnowledgeQueries(db)
    limited = queries.search(QueryScope(limit=1), HUMAN, request_id='limited')
    assert len(limited['members']) == 1
    assert limited['coverage']['result_limit_reached'] is True
    assert limited['coverage']['publication_limit_reached'] is False
    assert limited['coverage']['publications_scanned'] == 2
    assert 'not_complete_market_coverage' in limited['unknowns']
    assert queries.search(QueryScope(text='development-only'), HUMAN, request_id='production')['members'] == []
    development = queries.search(QueryScope(text='development-only'), HUMAN, request_id='development', include_synthetic=True)
    assert development['members'][0]['observation_id'] == synthetic.id
    with pytest.raises(EvidenceError, match='synthetic_evidence_excluded'):
        queries.read(development['result_id'], HUMAN)
    foreign = ActorContext('foreign', 'reader', 'human')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        queries.search(QueryScope(), foreign, request_id='foreign')
    with pytest.raises(EvidenceError, match='knowledge_query_result_not_found'):
        KnowledgeQueries(db, 'foreign').read(limited['result_id'], foreign)
    assert KnowledgeQueries(db, 'foreign').search(QueryScope(), foreign, request_id='empty')['members'] == []


def test_retry_conflict_and_invalid_scopes_do_not_change_a_pinned_result(stack):
    from concurrent.futures import ThreadPoolExecutor

    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    publish_account(stack, 'one')
    queries = KnowledgeQueries(db)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: queries.search(QueryScope(), WORKER, request_id='concurrent'), range(2)))
    assert results[0]['result_id'] == results[1]['result_id']
    with pytest.raises(EvidenceError, match='knowledge_query_request_conflict'):
        queries.search(QueryScope(text='changed'), WORKER, request_id='concurrent')
    with pytest.raises(EvidenceError, match='knowledge_query_request_conflict'):
        queries.search(QueryScope(), HUMAN, request_id='concurrent')
    for scope in ({'limit': 0}, {'limit': 101}, {'subject_ids': ('not-a-uuid',)}, {'platforms': ('test',) * 11},
                  {'captured_from': '2026-01-01'}, {'captured_from': '2026-02-01T00:00:00Z', 'captured_to': '2026-01-01T00:00:00Z'},
                  {'max_age_seconds': -1}, {'max_age_seconds': True}, {'text': 'x' * 501}):
        with pytest.raises(EvidenceError, match='invalid_knowledge_query_scope'):
            QueryScope(**scope)
    assert queries.read(results[0]['result_id'], HUMAN)['producer'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}


def test_literal_search_matches_observed_values_without_joining_unrelated_fields(stack):
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    run_id, observation = ingest_account(stack)
    key = ExternalKey('test', 'public', 'account', 'account-1')
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((key,), (
        FieldCandidate(key, 'handle', 'observed', 'red alpha', '$.handle'),
        FieldCandidate(key, 'display_name', 'observed', 'blue beta', '$.name'),
    ), ()), 'values:v2')
    publications = KnowledgePublications(db)
    publications.migrate()
    publications.publish(IngestedEvidence(db).select_run(run_id, HUMAN), WORKER, request_id='literal')
    queries = KnowledgeQueries(db)
    assert len(queries.search(QueryScope(text='ALPHA'), HUMAN, request_id='observed')['members']) == 1
    for position, fragment in enumerate(('alpha", "blue', 'beta", "red')):
        assert queries.search(QueryScope(text=fragment), HUMAN, request_id=f'unrelated-{position}')['members'] == []


def test_publication_scan_bound_reports_truncation_without_claiming_full_kb_coverage(stack):
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    publish_account(stack, 'outside-scan', native_id='outside-scan')
    run_id, observation = ingest_account(stack, native_id='inside-scan')
    publications = KnowledgePublications(db)
    support = IngestedEvidence(db).select_run(run_id, HUMAN)
    for index in range(100):
        publications.publish(support, WORKER, request_id=f'bounded-{index}')
    result = KnowledgeQueries(db).search(QueryScope(), HUMAN, request_id='bounded-query')
    assert result['coverage']['publications_scanned'] == 100
    assert result['coverage']['publication_limit_reached'] is True
    assert len(result['members']) == 1
    assert result['members'][0]['observation_id'] == observation.id
    assert 'not_complete_market_coverage' in result['unknowns']


def test_metric_only_published_support_can_be_filtered_by_its_public_subject_identity(stack):
    from datetime import datetime, timezone

    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import ExternalKey, MetricCandidate, NormalizedBatch
    from smi_knowledge import KnowledgeQueries, QueryScope

    db, _, _, _ = stack
    run_id, observation = ingest_account(stack)
    key = ExternalKey('test', 'public', 'account', 'account-1')
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((key,), (), (
        MetricCandidate(key, 'test.followers.v1', 'followers', 17, '17', 'exact', 'count', datetime(2026, 10, 1, tzinfo=timezone.utc), '$.followers'),
    )), 'metrics:v2')
    publications = KnowledgePublications(db)
    publications.migrate()
    source = IngestedEvidence(db).select_run(run_id, HUMAN)
    publications.publish(source, WORKER, request_id='metric-only')
    queries = KnowledgeQueries(db)
    result = queries.search(QueryScope(platforms=('test',)), HUMAN, request_id='metric-query')
    assert len(result['members']) == 1
    assert result['members'][0]['metrics'][0]['value'] == 17
    assert result['manifest'][0]['metric_ids'] == list(source[0].metric_ids)
    assert result['manifest'][0]['assertion_ids'] == []
