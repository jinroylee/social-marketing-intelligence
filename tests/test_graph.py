from __future__ import annotations

from dataclasses import asdict

from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgePublications
from test_publications import HUMAN, WORKER, ingest_account


def publish_post(stack, *, native_id='post-1', platform='test', namespace='public', handle='same-handle', synthetic=False):
    db, _, _, _ = stack
    run_id, observation = ingest_account(stack, native_id=native_id, synthetic=synthetic)
    post = ExternalKey(platform, namespace, 'content', native_id)
    author = ExternalKey(platform, namespace, 'account', 'author-1')
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((post, author), (
        FieldCandidate(post, 'caption', 'observed', '<script>visible caption</script>', '$.caption'),
        FieldCandidate(post, 'author_account', 'observed', asdict(author), '$.author'),
        FieldCandidate(author, 'handle', 'observed', handle, '$.handle'),
        FieldCandidate(author, 'display_name', 'not_returned', None, '$.name'),
    ), ()), 'graph-fixture:v1')
    publications = KnowledgePublications(db)
    publications.migrate()
    publications.publish(IngestedEvidence(db).select_run(run_id, HUMAN, include_synthetic=synthetic), WORKER,
                         request_id=f'{platform}:{namespace}:{native_id}', include_synthetic=synthetic)
    return observation


def test_graph_search_and_one_hop_reopen_preserve_native_identity_and_support(stack):
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    observation = publish_post(stack)
    graph = KnowledgeGraph(db)
    graph.migrate()
    result = graph.search(GraphScope(text='same-handle', kinds=('account',)), HUMAN, request_id='graph-first')
    assert len(result['entities']) == 1
    author = result['entities'][0]
    assert author['identity'] == {'platform': 'test', 'namespace': 'public', 'kind': 'account', 'native_id': 'author-1'}
    assert author['label'] == 'same-handle'
    assert 'display_name:not_returned' in author['unknowns']
    detail = KnowledgeGraph(db).read(result['search_id'], HUMAN, entity_id=author['entity_id'])
    assert detail['selected']['identity'] == author['identity']
    assert len(detail['neighbors']) == 1
    assert detail['neighbors'][0]['identity']['native_id'] == 'post-1'
    edge = detail['relationships'][0]
    assert edge['predicate'] == 'author_account'
    assert edge['basis'] == 'observed'
    assert edge['support']['observation_id'] == observation.id
    assert edge['support']['method']['mapper_key'] == 'graph-fixture:v1'
    assert edge['support']['captured_at'] == '2026-10-01T00:00:00+00:00'
    assert edge['support']['source_as_of'] is None
    assert edge['assertion_id'] in detail['manifest'][0]['assertion_ids']
    assert detail['producer'] == {'actor_id': 'operator', 'kind': 'human'}
    assert detail['limitations'] == ['bounded_published_support', 'not_complete_market_coverage', 'adjacency_does_not_establish_identity_equivalence', 'mentions_do_not_establish_use_or_endorsement']


def publish_product_mention(stack, *, source_only_first=False):
    from smi_ingestion.evidence_sets import SnapshotImporter
    from smi_knowledge import KnowledgeStore
    from test_evidence_sets import DATASET, MANIFEST, POLICY
    from test_knowledge import CATALOG, CATALOG_ID

    db, evidence, _, _ = stack
    store = KnowledgeStore(db)
    store.migrate()
    imported = SnapshotImporter(evidence).import_snapshot(MANIFEST, HUMAN, POLICY)
    store.register_catalog(CATALOG, HUMAN)
    prepared = store.prepare(DATASET, CATALOG_ID, WORKER)
    claim = next(c for c in store.read(prepared['run_id'], HUMAN)['interpretations'] if c['predicate'] == 'product_mention')
    support = tuple(r for r in IngestedEvidence(db).select_run(imported['run_id'], HUMAN) if r.observation_id == claim['observation_id'])
    if source_only_first:
        KnowledgePublications(db).publish(support, WORKER, request_id='source-only-before-interpretation')
    KnowledgePublications(db).publish(support, WORKER, request_id='product-mention', interpretation_ids=(claim['id'],))
    return store.read_interpretations((claim['id'],), HUMAN)[0]


def test_derived_mention_and_human_catalog_relationship_keep_distinct_basis_and_dates(stack):
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    claim = publish_product_mention(stack)
    graph = KnowledgeGraph(db)
    graph.migrate()
    result = graph.search(GraphScope(kinds=('product',)), HUMAN, request_id='product')
    product = result['entities'][0]
    assert product['identity'] == {'kind': 'product', 'reference_id': claim['value']['product_id']}
    detail = graph.read(result['search_id'], HUMAN, entity_id=product['entity_id'])
    assert {e['basis'] for e in detail['relationships']} == {'derived', 'human'}
    derived = next(e for e in detail['relationships'] if e['basis'] == 'derived')
    assert derived['interpretation']['id'] == claim['id']
    assert derived['interpretation']['span'] == claim['span']
    assert derived['interpretation']['method_version'] == 'caption-literal-rules-v1'
    assert derived['interpretation']['review_status'] == 'provisional'
    human = next(e for e in detail['relationships'] if e['basis'] == 'human')
    assert human['predicate'] == 'catalog_brand'
    assert human['catalog']['recorded_by'] == HUMAN.actor_id
    assert human['catalog']['recorded_at']
    assert human['catalog']['catalog_id'] == claim['catalog_id']
    assert human['support']['observation_id'] == claim['observation_id']
    assert {n['identity']['kind'] for n in detail['neighbors']} == {'content', 'brand'}
    by_name = graph.search(GraphScope(text=product['label'], kinds=('product',)), HUMAN, request_id='configured-name')
    assert by_name['entities'][0]['entity_id'] == product['entity_id']


def test_graph_bounds_identity_filters_empty_results_and_no_second_hop(stack):
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    for index in range(3):
        publish_post(stack, native_id=f'post-{index}')
    publish_post(stack, native_id='foreign-platform-post', platform='other')
    publish_post(stack, native_id='foreign-namespace-post', namespace='provider-private')
    graph = KnowledgeGraph(db)
    graph.migrate()
    authors = graph.search(GraphScope(text='same-handle', kinds=('account',)), HUMAN, request_id='same-handles')
    assert len(authors['entities']) == 3
    assert len({n['entity_id'] for n in authors['entities']}) == 3
    assert all(n['identity']['kind'] == 'account' for n in authors['entities'])
    narrowed = graph.search(GraphScope(text='same-handle', platforms=('test',), namespaces=('public',),
                                       kinds=('account',), neighbor_limit=2), HUMAN, request_id='narrowed')
    assert len(narrowed['entities']) == 1
    detail = graph.read(narrowed['search_id'], HUMAN, entity_id=narrowed['entities'][0]['entity_id'])
    assert len(detail['relationships']) == 2
    assert len(detail['neighbors']) == 2
    assert detail['current_coverage']['immediate_relationships'] == 3
    assert detail['current_coverage']['neighbor_limit_reached'] is True
    assert all(detail['selected']['entity_id'] in (e['source'], e['target']) for e in detail['relationships'])
    limited = graph.search(GraphScope(entity_limit=1, member_limit=2), HUMAN, request_id='limits')
    assert len(limited['entities']) == 1
    assert limited['coverage']['result_limit_reached'] is True
    assert limited['current_coverage']['entity_limit_reached'] is True
    assert graph.search(GraphScope(text='nonexistent-entity'), HUMAN, request_id='empty')['entities'] == []
    assert graph.search(GraphScope(captured_from='2026-10-02T00:00:00Z'), HUMAN, request_id='later')['entities'] == []


def test_graph_current_process_display_retention_withdrawal_and_supersession_hide_labels(stack):
    from dataclasses import asdict

    from psycopg.types.json import Jsonb

    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, evidence, _, _ = stack
    observation = publish_post(stack, handle='SECRET-GRAPH-HANDLE')
    graph = KnowledgeGraph(db)
    graph.migrate()
    saved = graph.search(GraphScope(), HUMAN, request_id='before-denial')
    author = next(n for n in saved['entities'] if n['identity']['kind'] == 'account')
    original_policy = asdict(evidence.get(observation.id).policy)
    for permission in ('can_process', 'can_display', 'can_retain'):
        policy = {**original_policy, permission: False}
        with db.connect() as connection:
            connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(policy), observation.id))
        reopened = KnowledgeGraph(db).read(saved['search_id'], HUMAN, entity_id=author['entity_id'])
        assert reopened['entities'] == []
        assert reopened['selected'] is None
        assert reopened['selection_status'] == 'unavailable'
        assert reopened['relationships'] == []
        assert reopened['neighbors'] == []
        assert 'SECRET-GRAPH-HANDLE' not in str(reopened)
        assert 'visible caption' not in str(reopened)
        assert 'example.test' not in str(reopened)
    with db.connect() as connection:
        connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(original_policy), observation.id))
    evidence.revoke(observation.id)
    assert graph.read(saved['search_id'], HUMAN)['current_coverage']['unavailable_or_superseded_members'] == 1


def test_graph_human_and_derived_adjacency_disappears_when_selected_source_is_denied(stack):
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, evidence, _, _ = stack
    claim = publish_product_mention(stack)
    graph = KnowledgeGraph(db)
    graph.migrate()
    saved = graph.search(GraphScope(kinds=('product',)), HUMAN, request_id='before-product-denial')
    product = saved['entities'][0]
    evidence.revoke(claim['observation_id'])
    reopened = KnowledgeGraph(db).read(saved['search_id'], HUMAN, entity_id=product['entity_id'])
    assert reopened['entities'] == []
    assert reopened['selection_status'] == 'unavailable'
    assert reopened['relationships'] == []
    assert product['label'] not in str(reopened)
    assert claim['span']['text'] not in str(reopened)


def test_graph_workspace_synthetic_retry_and_restart_keep_exact_pinned_selection(stack):
    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    publish_post(stack, native_id='development-only', synthetic=True)
    graph = KnowledgeGraph(db)
    graph.migrate()
    assert graph.search(GraphScope(), HUMAN, request_id='without-development')['entities'] == []
    saved = graph.search(GraphScope(), HUMAN, request_id='development', include_synthetic=True)
    assert len(saved['entities']) == 2
    with pytest.raises(EvidenceError, match='synthetic_evidence_excluded'):
        graph.read(saved['search_id'], HUMAN)
    publish_post(stack, native_id='new-publication')
    assert KnowledgeGraph(db).read(saved['search_id'], HUMAN, include_synthetic=True)['manifest'] == saved['manifest']
    assert graph.search(GraphScope(), HUMAN, request_id='development', include_synthetic=True)['manifest'] == saved['manifest']
    with pytest.raises(EvidenceError, match='graph_request_conflict'):
        graph.search(GraphScope(text='changed'), HUMAN, request_id='development', include_synthetic=True)
    with pytest.raises(EvidenceError, match='graph_request_conflict'):
        graph.search(GraphScope(), WORKER, request_id='development', include_synthetic=True)
    foreign = ActorContext('foreign', 'reader', 'human')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        graph.read(saved['search_id'], foreign, include_synthetic=True)
    with pytest.raises(EvidenceError, match='graph_search_not_found'):
        KnowledgeGraph(db, 'foreign').read(saved['search_id'], foreign, include_synthetic=True)
    assert KnowledgeGraph(db, 'foreign').search(GraphScope(), foreign, request_id='empty')['entities'] == []


def test_local_graph_journey_escapes_filters_neighbors_restarts_and_withholds_denied_support(stack):
    import re

    from smi_knowledge.graph import KnowledgeGraph
    from smi_review import ReviewApp
    from test_review import request, running

    db, evidence, _, _ = stack
    observation = publish_post(stack, handle='<script>graph-handle</script>')
    KnowledgeGraph(db).migrate()
    with running(ReviewApp(db, actor_id='named-graph-marketer')) as url:
        status, _, page = request(url, path='/knowledge/graph')
        assert status == 200
        csrf = re.search(r'name="csrf" value="([^"]+)"', page)[1]
        status, headers, _ = request(url, 'POST', '/knowledge/graph', {
            'csrf': csrf, 'request_id': 'http-graph', 'text': 'graph-handle', 'kinds': 'account', 'neighbor_limit': '1',
        })
        assert status == 303
        path = headers['Location']
        status, _, page = request(url, path=path)
        assert status == 200
        assert '&lt;script&gt;graph-handle&lt;/script&gt;' in page
        assert '<script>graph-handle</script>' not in page
        assert 'named-graph-marketer' in page
        selection = re.search(r'href="([^"]+entity=[a-f0-9]{64}[^"]*)"', page)[1].replace('&amp;', '&')
        status, _, detail = request(url, path=selection)
        assert status == 200
        assert 'Immediate relationships' in detail
        assert 'author_account' in detail
        assert 'observed' in detail
        assert observation.id in detail
        assert '&lt;script&gt;visible caption&lt;/script&gt;' in detail
        assert 'graph-fixture:v1' in detail
        assert '2026-10-01T00:00:00+00:00' in detail
        status, _, forged = request(url, 'POST', '/knowledge/graph', {
            'csrf': csrf, 'request_id': 'forged', 'actor_id': 'forged-actor', 'text': '<img src=x>',
        })
        assert status == 422
        assert 'forged-actor' not in forged
        assert '&lt;img src=x&gt;' in forged
        status, _, _ = request(url, 'POST', '/knowledge/graph', {'csrf': 'wrong', 'request_id': 'bad-csrf'})
        assert status == 422
        status, _, _ = request(url, 'POST', '/knowledge/graph', {'csrf': csrf, 'request_id': 'foreign-origin'}, {'Origin': 'https://evil.test'})
        assert status == 403
        status, headers, _ = request(url, 'POST', '/knowledge/graph', {'csrf': csrf, 'request_id': 'empty-http', 'text': 'no-such-entity'})
        assert status == 303
        assert 'No matching permitted entities' in request(url, path=headers['Location'])[2]
    evidence.revoke(observation.id)
    with running(ReviewApp(db)) as url:
        status, _, detail = request(url, path=selection)
        assert status == 200
        assert 'Selected entity unavailable' in detail
        assert 'visible caption' not in detail
        assert 'example.test' not in detail
        assert 'graph-handle' not in detail
    with running(ReviewApp(db, workspace_id='foreign')) as url:
        assert request(url, path=selection)[0] == 404


def test_graph_republished_interpretation_links_only_publication_that_contains_its_claim(stack):
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    claim = publish_product_mention(stack, source_only_first=True)
    graph = KnowledgeGraph(db)
    graph.migrate()
    saved = graph.search(GraphScope(kinds=('product',)), HUMAN, request_id='republished-claim')
    detail = graph.read(saved['search_id'], HUMAN, entity_id=saved['entities'][0]['entity_id'])
    derived = next(e for e in detail['relationships'] if e['basis'] == 'derived')
    supporting = KnowledgePublications(db).read(derived['support']['publication_id'], HUMAN)
    assert claim['id'] in [c['id'] for c in supporting['interpretations']]
    assert derived['support']['publication_context']['publication_time'] == supporting['published_at']
    assert len([e for e in detail['relationships'] if e['basis'] == 'derived']) == 1


def test_graph_publication_dates_belong_to_exact_content_subject_in_multi_post_observation(stack):
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    run_id, observation = ingest_account(stack)
    posts = [ExternalKey('test', 'public', 'content', f'dated-post-{i}') for i in (1, 2)]
    author = ExternalKey('test', 'public', 'account', 'dated-author')
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((*posts, author), (
        FieldCandidate(posts[0], 'published_at', 'observed', '2026-09-01T00:00:00Z', '$.posts[0].date'),
        FieldCandidate(posts[0], 'author_account', 'observed', asdict(author), '$.posts[0].author'),
        FieldCandidate(posts[1], 'published_at', 'observed', '2026-09-21T00:00:00Z', '$.posts[1].date'),
        FieldCandidate(posts[1], 'author_account', 'observed', asdict(author), '$.posts[1].author'),
    ), ()), 'multi-post:v1')
    KnowledgePublications(db).migrate()
    KnowledgePublications(db).publish(IngestedEvidence(db).select_run(run_id, HUMAN), WORKER, request_id='two-dates')
    graph = KnowledgeGraph(db)
    graph.migrate()
    saved = graph.search(GraphScope(kinds=('account',)), HUMAN, request_id='dated-graph')
    detail = graph.read(saved['search_id'], HUMAN, entity_id=saved['entities'][0]['entity_id'])
    neighbors = {n['entity_id']: n for n in detail['neighbors']}
    actual = {neighbors[e['source']]['identity']['native_id']: e['support']['source_published_at'] for e in detail['relationships']}
    assert actual == {'dated-post-1': '2026-09-01T00:00:00Z', 'dated-post-2': '2026-09-21T00:00:00Z'}
    assert detail['selected']['support'][0]['source_published_at'] is None


def test_graph_source_only_metric_only_unpublished_and_superseded_support_remain_explicit(stack):
    from datetime import datetime, timezone

    from smi_ingestion.contracts import MetricCandidate
    from smi_knowledge.graph import GraphScope, KnowledgeGraph
    from test_knowledge_queries import publish_account

    db, _, _, _ = stack
    _, source_only = publish_account(stack, 'source-only')
    run_id, metric_only = ingest_account(stack, native_id='metric-account')
    key = ExternalKey('test', 'public', 'account', 'metric-account')
    CanonicalWriter(db).apply(metric_only.id, NormalizedBatch((key,), (), (
        MetricCandidate(key, 'test.followers.v1', 'followers', 17, '17', 'exact', 'count', datetime(2026, 10, 1, tzinfo=timezone.utc), '$.followers'),
    )), 'metrics:v2')
    KnowledgePublications(db).publish(IngestedEvidence(db).select_run(run_id, HUMAN), WORKER, request_id='metric-only')
    ingest_account(stack, native_id='NEVER-PUBLISHED')
    graph = KnowledgeGraph(db)
    graph.migrate()
    saved = graph.search(GraphScope(kinds=('account',)), HUMAN, request_id='incomplete-profiles')
    assert {n['identity']['native_id'] for n in saved['entities']} == {'account-1', 'metric-account'}
    incomplete = next(n for n in saved['entities'] if n['identity']['native_id'] == 'account-1')
    assert incomplete['label'] == 'account-1'
    assert 'handle:not_returned' in incomplete['unknowns']
    metric_node = next(n for n in saved['entities'] if n['identity']['native_id'] == 'metric-account')
    assert metric_node['attributes'] == []
    assert metric_node['metrics'][0]['value'] == 17
    CanonicalWriter(db).apply(source_only.id, NormalizedBatch((ExternalKey('test', 'public', 'account', 'account-1'),), (
        FieldCandidate(ExternalKey('test', 'public', 'account', 'account-1'), 'handle', 'observed', 'NEW-NOT-IN-OLD-GRAPH', '$.handle'),
    ), ()), 'corrected:v2')
    reopened = graph.read(saved['search_id'], HUMAN, entity_id=incomplete['entity_id'])
    assert reopened['selection_status'] == 'unavailable'
    assert reopened['current_coverage']['unavailable_or_superseded_members'] == 1
    assert [n['identity']['native_id'] for n in reopened['entities']] == ['metric-account']
    assert 'NEW-NOT-IN-OLD-GRAPH' not in str(reopened)


def test_graph_retries_concurrently_and_rejects_unbounded_or_forged_public_inputs(stack):
    from concurrent.futures import ThreadPoolExecutor

    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_knowledge.graph import GraphScope, KnowledgeGraph

    db, _, _, _ = stack
    publish_post(stack)
    graph = KnowledgeGraph(db)
    graph.migrate()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: graph.search(GraphScope(), HUMAN, request_id='concurrent'), range(2)))
    assert results[0]['search_id'] == results[1]['search_id']
    assert results[0]['manifest'] == results[1]['manifest']
    for scope in ({'member_limit': 101}, {'entity_limit': 0}, {'neighbor_limit': 51}, {'neighbor_limit': True},
                  {'kinds': ('creator',)}, {'namespaces': ('test',) * 11}, {'captured_from': '2026-01-01'}, {'text': 'x' * 501}):
        with pytest.raises(EvidenceError):
            GraphScope(**scope)
    with pytest.raises(EvidenceError, match='invalid_graph_entity'):
        graph.read(results[0]['search_id'], HUMAN, entity_id='forged-entity')
    unknown = graph.read(results[0]['search_id'], HUMAN, entity_id='0' * 64)
    assert unknown['selection_status'] == 'unavailable'
    assert unknown['selected'] is None
