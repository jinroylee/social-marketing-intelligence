from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, SnapshotImporter
from smi_knowledge import Catalog, KnowledgeStore
from smi_knowledge.extraction import Interpretation, extract, validate_support
from test_cli import _cli
from test_evidence_sets import DATASET, HUMAN, MANIFEST, POLICY


CATALOG_PATH = Path(__file__).parents[1] / "examples/catalogs/beauty-v1.json"
CATALOG = Catalog.load(CATALOG_PATH)
CATALOG_ID = CATALOG.document["catalog_id"]


@pytest.fixture
def knowledge(stack):
    db, evidence, _, _ = stack
    store = KnowledgeStore(db)
    store.migrate()
    store.migrate()
    SnapshotImporter(evidence).import_snapshot(MANIFEST, HUMAN, POLICY)
    store.register_catalog(CATALOG, HUMAN)
    return store


def test_real_sample_has_exact_provenance_family_specificity_and_provisional_status(knowledge):
    report = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    result = knowledge.read(report["run_id"], HUMAN)
    assert report["coverage"]["processed"] == 19
    assert report["coverage"]["unavailable"] == 0
    source = knowledge.evidence.read(DATASET, HUMAN)
    captions = {a["assertion_id"]: a["value"] for m in source["members"] for a in m["assertions"] if a["field"] == "caption"}
    target_posts = set()
    for claim in result["interpretations"]:
        assert claim["state"] == "supported"
        assert claim["basis"] == "derived"
        assert claim["review_status"] == "provisional"
        span = claim["span"]
        assert captions[claim["source_assertion_id"]][span["start"]:span["end"]] == span["text"]
        assert claim["source_reference"].startswith("https://www.tiktok.com/")
        assert claim["published_at"] and claim["captured_at"]
        if claim["predicate"] == "product_mention" and claim["value"]["product_id"] == "aprilskin-hero-cushion":
            target_posts.add(claim["subject_id"])
            assert claim["value"]["specificity"] == "family"
            assert "shade" not in claim["value"]
    assert len(target_posts) == 6
    assert {c["predicate"] for c in result["interpretations"]} == {
        "brand_mention", "product_mention", "topic_mention", "script_evidence", "literal_marker"}


def test_retry_and_concurrent_prepare_keep_exact_run_and_claim_ids(knowledge):
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(lambda _: knowledge.prepare(DATASET, CATALOG_ID, HUMAN), range(2)))
    assert {r["status"] for r in reports} == {"prepared", "duplicate"}
    assert len({r["run_id"] for r in reports}) == 1
    run_id = reports[0]["run_id"]
    initial = knowledge.read(run_id, HUMAN)
    assert knowledge.prepare(DATASET, CATALOG_ID, HUMAN)["status"] == "duplicate"
    assert KnowledgeStore(knowledge.db).read(run_id, HUMAN) == initial


@pytest.mark.parametrize("denied_count", [1, 19])
def test_new_request_recovers_denied_inputs_without_mutating_prior_run(knowledge, denied_count):
    members = knowledge.evidence.read(DATASET, HUMAN)["members"]
    with knowledge.db.connect() as connection:
        for member in members[:denied_count]:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s",
                               (Jsonb({**member["policy"], "can_process": False}), member["observation_id"]))
    first = knowledge.prepare(DATASET, CATALOG_ID, HUMAN, request_id="before-restoration")
    assert first["coverage"]["processed"] == 19 - denied_count
    with knowledge.db.connect() as connection:
        for member in members[:denied_count]:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s",
                               (Jsonb(member["policy"]), member["observation_id"]))
    old = knowledge.read(first["run_id"], HUMAN)
    assert knowledge.prepare(DATASET, CATALOG_ID, HUMAN, request_id="before-restoration")["run_id"] == first["run_id"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        refreshes = list(pool.map(lambda _: knowledge.prepare(DATASET, CATALOG_ID, HUMAN, request_id="after-restoration"), range(2)))
    assert {r["status"] for r in refreshes} == {"prepared", "duplicate"}
    assert len({r["run_id"] for r in refreshes}) == 1
    new = knowledge.read(refreshes[0]["run_id"], HUMAN)
    assert new["preparation_coverage"]["processed"] == 19
    assert new["interpretations"] and new["run_id"] != old["run_id"]
    assert knowledge.read(first["run_id"], HUMAN) == old


def test_migration_preserves_legacy_runs_and_allows_new_requests(knowledge):
    original = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    with knowledge.db.connect() as connection:
        connection.execute("ALTER TABLE knowledge_runs DROP COLUMN request_id")
        connection.execute("ALTER TABLE knowledge_runs ADD CONSTRAINT legacy_preparation_key "
                           "UNIQUE (workspace_id,dataset_id,catalog_id,method_version)")
    knowledge.migrate()
    knowledge.migrate()
    assert knowledge.read(original["run_id"], HUMAN)["request_id"] == "initial"
    assert knowledge.prepare(DATASET, CATALOG_ID, HUMAN)["run_id"] == original["run_id"]
    assert knowledge.prepare(DATASET, CATALOG_ID, HUMAN, request_id="refresh")["run_id"] != original["run_id"]


@pytest.mark.parametrize("change,purpose,purged", [
    ({"can_display": False}, "display", False),
    ({"can_process": False}, "process", False),
    ({"can_retain": False}, "display", True),
    ({"revoked": True}, "display", True),
    ({"expires_at": "2000-01-01T00:00:00+00:00"}, "display", True),
])
def test_policy_dependencies_hide_or_purge_values_and_copied_excerpts(knowledge, change, purpose, purged):
    run = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    first = knowledge.evidence.read(DATASET, HUMAN)["members"][0]
    with knowledge.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**first["policy"], **change}), first["observation_id"]))
    result = knowledge.read(run["run_id"], HUMAN, purpose=purpose)
    affected = [c for c in result["interpretations"] if c["observation_id"] == first["observation_id"]]
    assert affected and all(c["state"] == "unavailable" and "value" not in c and "span" not in c for c in affected)
    with knowledge.db.connect() as connection:
        rows = connection.execute("SELECT value,excerpt,support_state FROM knowledge_assertions WHERE observation_id=%s", (first["observation_id"],)).fetchall()
    assert all((r["value"] is None and r["excerpt"] is None and r["support_state"] == "withdrawn") == purged for r in rows)
    if change == {"can_process": False}:
        assert any(c["state"] == "supported" for c in knowledge.read(run["run_id"], HUMAN)["interpretations"] if c["observation_id"] == first["observation_id"])


def test_no_reconstruction_of_purged_claims_on_retry_or_permission_restore(knowledge):
    run = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    first = knowledge.evidence.read(DATASET, HUMAN)["members"][0]
    with knowledge.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**first["policy"], "can_retain": False}), first["observation_id"]))
    assert knowledge.reconcile(DATASET, HUMAN) > 0
    with knowledge.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(first["policy"]), first["observation_id"]))
    assert knowledge.prepare(DATASET, CATALOG_ID, HUMAN)["status"] == "duplicate"
    affected = [c for c in knowledge.read(run["run_id"], HUMAN)["interpretations"] if c["observation_id"] == first["observation_id"]]
    assert all(c["state"] == "unavailable" for c in affected)
    refreshed = knowledge.prepare(DATASET, CATALOG_ID, HUMAN, request_id="explicit-after-restoration")
    assert refreshed["run_id"] != run["run_id"]
    assert any(c["state"] == "supported" for c in knowledge.read(refreshed["run_id"], HUMAN)["interpretations"]
               if c["observation_id"] == first["observation_id"])
    assert all(c["state"] == "unavailable" for c in knowledge.read(run["run_id"], HUMAN)["interpretations"]
               if c["observation_id"] == first["observation_id"])


def test_denied_processing_and_retention_are_excluded_at_preparation(knowledge):
    members = knowledge.evidence.read(DATASET, HUMAN)["members"]
    with knowledge.db.connect() as connection:
        for member, field in zip(members, ("can_process", "can_retain")):
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], field: False}), member["observation_id"]))
    report = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    assert report["coverage"]["processed"] == 17
    assert report["coverage"]["unavailable"] == report["coverage"]["not_retained"] == 1
    result = knowledge.read(report["run_id"], HUMAN)
    assert not ({m["observation_id"] for m in members[:2]} & {c["observation_id"] for c in result["interpretations"]})


def test_superseded_source_requires_review_and_never_substitutes_new_caption(knowledge):
    report = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    first = knowledge.evidence.read(DATASET, HUMAN)["members"][0]
    source = next(a for a in first["assertions"] if a["field"] == "caption")
    key = ExternalKey(source["platform"], source["namespace"], source["kind"], source["native_id"])
    CanonicalWriter(knowledge.db).apply(first["observation_id"], NormalizedBatch(
        (key,), (FieldCandidate(key, "caption", "observed", "changed unrelated caption", "$.caption"),), (),
    ), "correction:v2")
    result = knowledge.read(report["run_id"], HUMAN)
    affected = [c for c in result["interpretations"] if c["observation_id"] == first["observation_id"]]
    assert affected and all(c["state"] == "review_required" and "value" not in c for c in affected)


def test_withdrawal_between_extraction_and_commit_rejects_stale_write(knowledge, monkeypatch):
    import smi_knowledge.store as store_module
    original = store_module.extract
    first = knowledge.evidence.read(DATASET, HUMAN)["members"][0]

    def withdraw_then_extract(caption, catalog):
        with knowledge.db.connect() as connection:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**first["policy"], "revoked": True}), first["observation_id"]))
        return original(caption, catalog)

    monkeypatch.setattr(store_module, "extract", withdraw_then_extract)
    with pytest.raises(EvidenceError, match="knowledge_support_changed"):
        knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    with knowledge.db.connect() as connection:
        assert connection.execute("SELECT count(*) AS n FROM knowledge_runs").fetchone()["n"] == 0


def test_catalog_version_workspace_and_human_registration_boundaries(knowledge):
    changed = copy.deepcopy(CATALOG.document)
    changed["brands"][0]["aliases"].append("another alias")
    with pytest.raises(EvidenceError, match="catalog_version_conflict"):
        knowledge.register_catalog(Catalog.from_document(changed), HUMAN)
    changed["catalog_id"] = "new-version"
    assert knowledge.register_catalog(Catalog.from_document(changed), HUMAN)["status"] == "registered"
    for actor in (ActorContext("foreign", "user", "human"), ActorContext("local", "agent", "automation")):
        with pytest.raises(EvidenceError, match="workspace_access_denied"):
            knowledge.register_catalog(CATALOG, actor)
    with pytest.raises(EvidenceError, match="workspace_access_denied"):
        knowledge.prepare(DATASET, CATALOG_ID, ActorContext("foreign", "user", "human"))


def test_generic_mentions_negation_comparison_and_uncertainty_are_not_positive_claims():
    for caption in ("ヒーロークッションは使っていません。", "ヒーロークッションとブラッククッションを比較。", "ヒーロークッションかもしれない。"):
        claims = extract(caption, CATALOG)
        products = [c for c in claims if c.predicate == "product_mention"]
        assert products and all(c.value["stance"] == "not_assessed" for c in products)
        assert all("efficacy" not in c.value and "audience" not in c.value and "sales" not in c.value for c in claims)
    generic = extract("#TIRTIR クッションファンデ", CATALOG)
    assert not any(c.predicate == "product_mention" for c in generic)
    assert any(c.predicate == "topic_mention" for c in generic)
    assert not any(c.predicate == "literal_marker" for c in extract("#product #prime Qoo100", CATALOG))


def test_pure_rules_reject_fabricated_spans_and_keep_unicode_offsets():
    caption = "🩵 APRILSKIN ヒーロークッション #PR"
    for claim in extract(caption, CATALOG):
        validate_support(claim, caption)
        assert caption[claim.start:claim.end] == claim.excerpt
    with pytest.raises(EvidenceError, match="invalid_interpretation_support"):
        validate_support(Interpretation("product_mention", {}, 0, 3, "not here"), caption)
    with pytest.raises(EvidenceError, match="invalid_interpretation_value"):
        validate_support(Interpretation("literal_marker", {"marker": "paid_contract"}, 0, 1, "🩵"), caption)


def test_other_category_and_market_uses_the_same_rules():
    catalog = Catalog.from_document({"catalog_id": "camping-de-v1", "version": "v1",
        "brands": [{"id": "stove-brand", "name": "Stove Brand", "aliases": ["Stove Brand"]}],
        "products": [{"id": "camp-stove", "brand_id": "stove-brand", "name": "Camp Stove", "specificity": "family", "aliases": ["Camp Stove"]}],
        "topics": [{"id": "fuel", "name": "Fuel", "aliases": ["Brennstoff"]}]})
    claims = extract("Stove Brand Camp Stove verwendet diesen Brennstoff", catalog)
    assert {c.predicate for c in claims} == {"brand_mention", "product_mention", "topic_mention"}


def test_ambiguous_aliases_and_multiple_products_preserve_alternatives():
    document = copy.deepcopy(CATALOG.document)
    document["products"][1]["aliases"].append("ヒーロークッション")
    catalog = Catalog.from_document(document)
    claims = [c for c in extract("ヒーロークッションとブラッククッション", catalog) if c.predicate == "product_mention"]
    assert len(claims) == 3
    ambiguous = [c for c in claims if c.excerpt == "ヒーロークッション"]
    assert len(ambiguous) == 2 and all(c.value["ambiguity"] == "multiple_catalog_products" for c in ambiguous)
    assert next(c for c in claims if c.excerpt == "ブラッククッション").value["product_id"] == "hera-black-cushion"


def test_review_packet_is_complete_pending_and_rechecks_withdrawn_support(knowledge):
    report = knowledge.prepare(DATASET, CATALOG_ID, HUMAN)
    packet = knowledge.review_packet(report["run_id"], HUMAN)
    assert len(packet["items"]) == 19
    assert packet["review_status"] == "pending_translation_assisted_review"
    assert all(i["translation"] is None and i["review"]["label"] is None for i in packet["items"])
    assert {i["case"] for i in packet["synthetic_challenges"]} == {"negation", "comparison", "uncertainty"}
    first = knowledge.evidence.read(DATASET, HUMAN)["members"][0]
    with knowledge.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**first["policy"], "revoked": True}), first["observation_id"]))
    packet = knowledge.review_packet(report["run_id"], HUMAN)
    assert packet["items"][0] == {"observation_id": first["observation_id"], "state": "unavailable"}


def test_cli_prepare_and_reopen_from_separate_process(stack, tmp_path):
    db, evidence, _, _ = stack
    assert _cli(db, evidence.root, "migrate").returncode == 0
    assert _cli(db, evidence.root, "import-snapshot", str(MANIFEST)).returncode == 0
    assert _cli(db, evidence.root, "register-catalog", str(CATALOG_PATH)).returncode == 0
    prepared = _cli(db, evidence.root, "prepare-knowledge", DATASET, CATALOG_ID)
    import json
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    run_id = json.loads(prepared.stdout)["run_id"]
    shown = _cli(db, evidence.root, "inspect-knowledge", run_id)
    packet = _cli(db, evidence.root, "review-packet", run_id)
    assert shown.returncode == packet.returncode == 0
    assert len(json.loads(packet.stdout)["items"]) == 19
