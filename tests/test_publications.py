from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch, ObservationDraft, RunLimits, SourcePolicy, SourceReference
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgePublications


HUMAN = ActorContext('local', 'operator', 'human')
WORKER = ActorContext('local', 'offline-publication-worker', 'automation')


def ingest_account(stack, *, native_id='account-1', policy=None, synthetic=False):
    db, evidence, _, _ = stack
    run_id = evidence.start_run(Path('offline-input.json'), 'offline-digest', 'offline-test', RunLimits())
    observation = evidence.save(run_id, 0, ObservationDraft(
        native_id, 'offline-test', 'simulated-source', 'v1', SourceReference('https://example.test/account/' + native_id),
        b'{}', 'application/json', datetime(2026, 10, 1, tzinfo=timezone.utc), None,
        policy or SourcePolicy('local-test', True, True, True), synthetic,
        {'scope': 'one_account', 'unavailable_fields': ['audience_geography', 'fee', 'availability']},
    ), {'index': 1}, complete=True)
    key = ExternalKey('test', 'public', 'account', native_id)
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((key,), (
        FieldCandidate(key, 'handle', 'not_returned', None, '$.handle'),
    ), ()), 'offline-test:v1')
    evidence.finish(run_id, 'completed')
    return run_id, observation


def test_source_only_publication_reopens_exact_fresh_ingestion_with_unknown_attributes(stack):
    db, _, _, _ = stack
    run_id, observation = ingest_account(stack)
    support = IngestedEvidence(db).select_run(run_id, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    created = publications.publish(support, WORKER, request_id='publication-1')

    reopened = KnowledgePublications(db).read(created['publication_id'], HUMAN)
    assert reopened['producer'] == {'actor_id': 'offline-publication-worker', 'kind': 'automation'}
    assert reopened['published_at']
    assert reopened['coverage'] == {'scope': 'selected_ingested_support', 'members': 1, 'interpretations': 0}
    member = reopened['members'][0]
    assert member['observation_id'] == observation.id
    assert member['captured_at'] == '2026-10-01T00:00:00+00:00'
    assert member['source_as_of'] is None
    assert member['method']['mapper_key'] == 'offline-test:v1'
    assert member['assertions'][0]['state'] == 'not_returned'
    assert member['assertions'][0]['value'] is None
    assert member['assertions'][0]['native_id'] == 'account-1'
    assert reopened['interpretations'] == []
    assert publications.list(HUMAN)[0]['publication_id'] == created['publication_id']


def test_concurrent_retries_preserve_one_publication_and_changed_payload_conflicts(stack):
    from concurrent.futures import ThreadPoolExecutor

    import pytest

    from smi_ingestion.evidence import EvidenceError

    db, _, _, _ = stack
    first_run, _ = ingest_account(stack)
    second_run, _ = ingest_account(stack, native_id='account-2')
    first = IngestedEvidence(db).select_run(first_run, HUMAN)
    second = IngestedEvidence(db).select_run(second_run, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: publications.publish(first, WORKER, request_id='retry'), range(2)))
    assert len({r['publication_id'] for r in results}) == 1
    assert sorted(r['status'] for r in results) == ['duplicate', 'published']
    with pytest.raises(EvidenceError, match='publication_request_conflict'):
        publications.publish(second, WORKER, request_id='retry')
    with pytest.raises(EvidenceError, match='publication_request_conflict'):
        publications.publish(first, HUMAN, request_id='retry')
    assert len(publications.list(HUMAN)) == 1


def test_existing_caption_interpretations_publish_only_with_their_exact_source_support(stack):
    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import SnapshotImporter
    from smi_knowledge import KnowledgeStore
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
    frozen_before = knowledge.evidence.read(DATASET, HUMAN)
    publications = KnowledgePublications(db)
    created = publications.publish(support, WORKER, request_id='caption', interpretation_ids=(claim['id'],))
    reopened = publications.read(created['publication_id'], HUMAN)
    published_claim = reopened['interpretations'][0]
    assert published_claim['id'] == claim['id']
    assert published_claim['source_assertion_id'] == claim['source_assertion_id']
    assert published_claim['value'] == claim['value']
    assert published_claim['method_version'] == 'caption-literal-rules-v1'
    assert published_claim['run_id'] == prepared['run_id']
    assert published_claim['review_status'] == 'provisional'
    assert knowledge.evidence.read(DATASET, HUMAN) == frozen_before
    other = tuple(r for r in IngestedEvidence(db).select_run(imported['run_id'], HUMAN) if r.observation_id != claim['observation_id'])[:1]
    with pytest.raises(EvidenceError, match='publication_interpretation_support_mismatch'):
        publications.publish(other, WORKER, request_id='wrong-caption', interpretation_ids=(claim['id'],))
    assert len(publications.list(HUMAN)) == 1


def test_synthetic_publications_require_explicit_development_visibility(stack):
    import pytest

    from smi_ingestion.evidence import EvidenceError

    db, _, _, _ = stack
    run_id, _ = ingest_account(stack, synthetic=True)
    evidence = IngestedEvidence(db)
    assert evidence.select_run(run_id, HUMAN) == ()
    support = evidence.select_run(run_id, HUMAN, include_synthetic=True)
    publications = KnowledgePublications(db)
    publications.migrate()
    with pytest.raises(EvidenceError, match='synthetic_evidence_excluded'):
        publications.publish(support, WORKER, request_id='synthetic')
    assert publications.list(HUMAN) == []
    created = publications.publish(support, WORKER, request_id='synthetic', include_synthetic=True)
    assert publications.list(HUMAN) == []
    assert len(publications.list(HUMAN, include_synthetic=True)) == 1
    with pytest.raises(EvidenceError, match='synthetic_evidence_excluded'):
        publications.read(created['publication_id'], HUMAN)
    assert publications.read(created['publication_id'], HUMAN, include_synthetic=True)['members'][0]['synthetic']


def test_current_policy_redacts_pinned_support_without_changing_publication_history(stack):
    db, evidence, _, _ = stack
    run_id, observation = ingest_account(stack, policy=SourcePolicy('source', True, True, False))
    support = IngestedEvidence(db).select_run(run_id, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    created = publications.publish(support, WORKER, request_id='policy')
    before = publications.read(created['publication_id'], HUMAN, purpose='process')
    assert before['members'][0]['assertions'][0]['native_id'] == 'account-1'
    display = publications.read(created['publication_id'], HUMAN)
    assert display['members'][0]['availability'] == 'unavailable'
    assert 'source_reference' not in display['members'][0]
    assert 'assertions' not in display['members'][0]
    evidence.revoke(observation.id)
    after = publications.read(created['publication_id'], HUMAN, purpose='process')
    assert after['members'][0]['availability'] == 'unavailable'
    assert 'assertions' not in after['members'][0]
    assert after['published_at'] == before['published_at']
    assert after['members'][0]['assertion_ids'] == before['members'][0]['assertion_ids']
    assert after['coverage'] == before['coverage']
    assert after['current_coverage'] == {'available_members': 0, 'unavailable_members': 1, 'superseded_members': 0}
    assert publications.publish(support, WORKER, request_id='policy')['status'] == 'duplicate'


def test_source_free_publication_recovery_validates_exact_run_lineage_after_withdrawal(stack):
    import json
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.support import SupportReference

    db, evidence, _, _ = stack
    run_id, observation = ingest_account(stack, native_id='private-source-wording')
    other_run, _ = ingest_account(stack, native_id='other-account')
    reader = IngestedEvidence(db)
    support = reader.select_run(run_id, HUMAN)
    other = reader.select_run(other_run, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    created = publications.publish(support, WORKER, request_id='recovery')
    original = publications.find_request('recovery', HUMAN)
    evidence.revoke(observation.id)

    metadata = publications.find_request('recovery', HUMAN)
    assert metadata == original
    assert metadata['publication_id'] == created['publication_id']
    assert metadata['support'] == [{'observation_id': support[0].observation_id, 'derivation_id': support[0].derivation_id,
                                    'assertion_ids': list(support[0].assertion_ids), 'metric_ids': []}]
    assert metadata['producer'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert metadata['interpretation_ids'] == []
    assert 'private-source-wording' not in json.dumps(metadata)
    assert 'source_reference' not in json.dumps(metadata)
    reader.require_run_support(run_id, support, HUMAN)
    with pytest.raises(EvidenceError, match='ingested_support_run_mismatch'):
        reader.require_run_support(other_run, support, HUMAN)
    changed = SupportReference(support[0].observation_id, support[0].derivation_id, other[0].assertion_ids)
    with pytest.raises(EvidenceError, match='invalid_support_reference'):
        reader.require_run_support(run_id, (changed,), HUMAN)
    foreign = ActorContext('foreign', 'reader', 'human')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        reader.require_run_support(run_id, support, foreign)
    assert KnowledgePublications(db, 'foreign').find_request('recovery', foreign) is None
    assert 'assertions' not in publications.read(created['publication_id'], HUMAN)['members'][0]


def test_local_publication_detail_reopens_and_redacts_after_restart(stack):
    from smi_review import ReviewApp
    from test_review import request, running

    db, evidence, _, _ = stack
    run_id, observation = ingest_account(stack, native_id='<script>account</script>')
    publications = KnowledgePublications(db)
    publications.migrate()
    created = publications.publish(IngestedEvidence(db).select_run(run_id, HUMAN), WORKER, request_id='http')
    path = '/knowledge/publications/' + created['publication_id']
    with running(ReviewApp(db)) as url:
        status, _, index = request(url, path='/knowledge/publications')
        assert status == 200
        assert path in index
        status, _, detail = request(url, path=path)
        assert status == 200
        assert '&lt;script&gt;account&lt;/script&gt;' in detail
        assert '<script>account</script>' not in detail
        assert observation.id in detail
        assert 'offline-publication-worker' in detail
        assert '2026-10-01' in detail
        assert 'Unknown' in detail
    evidence.revoke(observation.id)
    with running(ReviewApp(db)) as url:
        status, _, detail = request(url, path=path)
        assert status == 200
        assert observation.id in detail
        assert 'Source support unavailable' in detail
        assert 'example.test' not in detail
        assert '&lt;script&gt;account&lt;/script&gt;' not in detail


def test_operator_cli_publishes_a_bounded_run_selection_and_reopens_in_new_process(stack):
    import json

    from test_cli import _cli

    db, evidence, _, _ = stack
    run_id, observation = ingest_account(stack)
    assert _cli(db, evidence.root, 'migrate').returncode == 0
    result = _cli(db, evidence.root, 'publish-knowledge', run_id, '--request-id', 'cli', '--observation-id', observation.id, '--actor', 'named-operator')
    assert result.returncode == 0, result.stdout + result.stderr
    publication_id = json.loads(result.stdout)['publication_id']
    reopened = _cli(db, evidence.root, 'inspect-publication', publication_id)
    assert reopened.returncode == 0, reopened.stdout + reopened.stderr
    publication = json.loads(reopened.stdout)
    assert publication['members'][0]['observation_id'] == observation.id
    assert publication['producer'] == {'actor_id': 'named-operator', 'kind': 'human'}
    retry = _cli(db, evidence.root, 'publish-knowledge', run_id, '--request-id', 'cli', '--observation-id', observation.id, '--actor', 'named-operator')
    assert json.loads(retry.stdout)['publication_id'] == publication_id
    rejected = _cli(db, evidence.root, 'publish-knowledge', run_id, '--request-id', 'absent', '--observation-id', 'https://example.test/un-ingested')
    assert rejected.returncode == 1
    assert json.loads(rejected.stdout)['code'] == 'publication_observation_not_in_run'


def test_publication_rejects_withdrawn_or_un_ingested_members_atomically(stack):
    import uuid

    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.support import SupportReference

    db, evidence, _, _ = stack
    run_id, observation = ingest_account(stack)
    support = IngestedEvidence(db).select_run(run_id, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    absent = SupportReference(str(uuid.uuid4()), str(uuid.uuid4()), (str(uuid.uuid4()),))
    with pytest.raises(EvidenceError, match='ingested_support_not_found'):
        publications.publish((*support, absent), WORKER, request_id='partial')
    assert publications.list(HUMAN) == []
    evidence.revoke(observation.id)
    with pytest.raises(EvidenceError, match='publication_support_unavailable'):
        publications.publish(support, WORKER, request_id='withdrawn-before-commit')
    assert publications.list(HUMAN) == []


def test_superseded_support_and_later_publications_never_replace_original_membership(stack):
    from smi_review import ReviewApp
    from test_review import request, running

    db, _, _, _ = stack
    run_id, observation = ingest_account(stack)
    source = IngestedEvidence(db)
    support = source.select_run(run_id, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    original = publications.publish(support, WORKER, request_id='original')
    key = ExternalKey('test', 'public', 'account', 'account-1')
    CanonicalWriter(db).apply(observation.id, NormalizedBatch((key,), (
        FieldCandidate(key, 'handle', 'observed', 'NEW_CAPTION_DO_NOT_SUBSTITUTE', '$.handle'),
    ), ()), 'corrected:v2')
    replacement = source.select_run(run_id, HUMAN)
    publications.publish(replacement, WORKER, request_id='corrected')
    original_read = publications.read(original['publication_id'], HUMAN)
    assert original_read['members'][0]['support_status'] == 'superseded_review_required'
    assert original_read['members'][0]['assertion_ids'] == support[0].assertion_ids
    assert original_read['members'][0]['assertions'][0]['value'] is None
    assert original_read['members'][0]['method']['mapper_key'] == 'offline-test:v1'
    assert original_read['current_coverage']['superseded_members'] == 1
    assert len(publications.list(HUMAN)) == 2
    with running(ReviewApp(db)) as url:
        status, _, html = request(url, path='/knowledge/publications/' + original['publication_id'])
        assert status == 200 and 'Superseded support' in html
        assert 'NEW_CAPTION_DO_NOT_SUBSTITUTE' not in html


def test_foreign_workspace_cannot_publish_or_read_local_source_support(stack):
    import pytest

    from smi_ingestion.evidence import EvidenceError

    db, _, _, _ = stack
    run_id, _ = ingest_account(stack)
    support = IngestedEvidence(db).select_run(run_id, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    foreign = ActorContext('foreign', 'operator', 'human')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        publications.publish(support, foreign, request_id='forged')
    foreign_publications = KnowledgePublications(db, 'foreign')
    with pytest.raises(EvidenceError, match='ingested_support_not_found'):
        foreign_publications.publish(support, foreign, request_id='foreign')
    created = publications.publish(support, WORKER, request_id='local')
    with pytest.raises(EvidenceError, match='knowledge_publication_not_found'):
        foreign_publications.read(created['publication_id'], foreign)
    assert foreign_publications.list(foreign) == []


def test_publication_copy_purge_remains_a_tombstone_after_permission_restoration(stack):
    from dataclasses import asdict

    from psycopg.types.json import Jsonb

    from smi_ingestion.evidence_sets import SnapshotImporter
    from smi_knowledge import KnowledgeStore
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
    created = publications.publish(support, WORKER, request_id='purge', interpretation_ids=(claim['id'],))
    observation = evidence.get(claim['observation_id'])
    evidence.revoke(observation.id)
    withdrawn = publications.read(created['publication_id'], HUMAN)
    assert withdrawn['interpretations'][0]['state'] == 'unavailable'
    assert 'value' not in withdrawn['interpretations'][0]
    # Simulate a later policy grant; the evidence-owner raw copy remains purged.
    with db.connect() as connection:
        connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(asdict(observation.policy)), observation.id))
    retry = publications.publish(support, WORKER, request_id='purge', interpretation_ids=(claim['id'],))
    assert retry['status'] == 'duplicate'
    restored = publications.read(created['publication_id'], HUMAN)
    assert restored['interpretations'][0]['state'] == 'unavailable'
    assert 'value' not in restored['interpretations'][0]
    assert knowledge.read(prepared['run_id'], HUMAN)['interpretations'][0]['state'] == 'unavailable'


def test_legacy_import_upgrade_preserves_workspace_and_exact_support(stack):
    from smi_ingestion.evidence_sets import EvidenceSetReader, SnapshotImporter
    from test_evidence_sets import DATASET, MANIFEST, POLICY

    db, evidence, _, _ = stack
    actor = ActorContext('team', 'team-operator', 'human')
    imported = SnapshotImporter(evidence, 'team').import_snapshot(MANIFEST, actor, POLICY)
    before = EvidenceSetReader(db, 'team').read(DATASET, actor)
    # Recreate the previous schema shape, then apply the normal public migration.
    with db.connect() as connection:
        connection.execute('ALTER TABLE ingestion_runs DROP COLUMN workspace_id')
    db.migrate()
    publications = KnowledgePublications(db, 'team')
    publications.migrate()
    support = IngestedEvidence(db, 'team').select_run(imported['run_id'], actor)
    created = publications.publish(support[:1], actor, request_id='after-upgrade')
    reopened = publications.read(created['publication_id'], actor)
    assert reopened['members'][0]['observation_id'] == before['members'][0]['observation_id']
    assert reopened['members'][0]['derivation_id'] == before['members'][0]['derivation_id']
    assert EvidenceSetReader(db, 'team').read(DATASET, actor) == before


def test_source_only_publication_creates_no_retained_interpretation_copy(stack):
    db, evidence, _, _ = stack
    run_id, observation = ingest_account(stack, policy=SourcePolicy('transient', True, False, True))
    assert evidence.get(observation.id).payload_path is None
    publications = KnowledgePublications(db)
    publications.migrate()
    created = publications.publish(IngestedEvidence(db).select_run(run_id, HUMAN), WORKER, request_id='nonretained')
    reopened = publications.read(created['publication_id'], HUMAN)
    assert reopened['members'][0]['availability'] == 'available'
    assert not reopened['members'][0]['policy']['can_retain']
    assert reopened['interpretations'] == []
    evidence.revoke(observation.id)
    assert publications.read(created['publication_id'], HUMAN)['members'][0]['availability'] == 'unavailable'


def test_display_permission_cannot_authorize_new_publication(stack):
    from psycopg.types.json import Jsonb

    import pytest

    from smi_ingestion.evidence import EvidenceError

    db, _, _, _ = stack
    run_id, observation = ingest_account(stack)
    support = IngestedEvidence(db).select_run(run_id, HUMAN)
    publications = KnowledgePublications(db)
    publications.migrate()
    created = publications.publish(support, WORKER, request_id='before-process-denial')
    with db.connect() as connection:
        connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (
            Jsonb({'context_id': 'display-only', 'can_process': False, 'can_retain': True, 'can_display': True}), observation.id))
    with pytest.raises(EvidenceError, match='publication_support_unavailable'):
        publications.publish(support, WORKER, request_id='display-is-not-process')
    assert publications.read(created['publication_id'], HUMAN)['members'][0]['availability'] == 'available'
    assert publications.read(created['publication_id'], HUMAN, purpose='process')['members'][0]['availability'] == 'unavailable'
    assert len(publications.list(HUMAN)) == 1
