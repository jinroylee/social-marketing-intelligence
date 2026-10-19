from __future__ import annotations

import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import FieldCandidate, NormalizedBatch, SourcePolicy
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader, SnapshotImporter
from test_cli import _cli


SAMPLE = Path(__file__).parents[1] / "examples/curated/jp-kbeauty-tiktok-2026-10-05"
MANIFEST = SAMPLE / "snapshot-manifest.json"
DATA = json.loads((SAMPLE / "observations.json").read_text())
DATASET = DATA["dataset_id"]
HUMAN = ActorContext("local", "test-marketer", "human")
POLICY = SourcePolicy("local-test", True, True, True)


def altered_snapshot(tmp_path, change, *, synthetic=True):
    data = copy.deepcopy(DATA)
    if synthetic:
        data["synthetic"] = True
        data["dataset_type"] = "synthetic_snapshot"
        data["dataset_id"] = "synthetic-snapshot-test"
    change(data)
    payload = json.dumps(data, ensure_ascii=False).encode()
    (tmp_path / "observations.json").write_bytes(payload)
    manifest = json.loads(MANIFEST.read_text())
    manifest.update(dataset_id=data["dataset_id"], sha256=hashlib.sha256(payload).hexdigest())
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path


def table_count(db, table):
    # Test-owned names only; never use this helper with user input.
    from psycopg import sql
    with db.connect() as connection:
        return connection.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))).fetchone()["n"]


def import_sample(stack, policy=POLICY):
    db, evidence, _, _ = stack
    SnapshotImporter(evidence).import_snapshot(MANIFEST, HUMAN, policy)
    return EvidenceSetReader(db).read(DATASET, HUMAN)


def test_empty_database_import_has_exact_members_lineage_and_support_without_network(stack, monkeypatch):
    import urllib.request

    def forbidden(*args, **kwargs):
        pytest.fail("offline import attempted a source request")

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", forbidden)
    result = import_sample(stack)
    assert result["coverage"] == {
        "scope": "selected_posts", "total_members": 19, "available_members": 19,
        "unavailable_members": 0, "original_accounts": 17,
    }
    assert table_count(stack[0], "canonical_entities") == 36
    account_ids = set()
    for member, source in zip(result["members"], DATA["records"], strict=True):
        assert member["observation_id"] != source["provenance"]["source_observation_id"]
        assert member["origin_observation_id"] == source["provenance"]["source_observation_id"]
        assert member["origin_run_id"] == source["provenance"]["run_id"]
        assert member["captured_at"] == source["captured_at"]
        assert member["source_as_of"] is None
        assert member["recorded_at"] != source["captured_at"]
        fields = {a["field"]: a for a in member["assertions"]}
        assert fields["caption"]["value"] == source["caption"]
        assert fields["published_at"]["value"] == source["published_at"]
        assert all(a["assertion_id"] and a["locator"] for a in member["assertions"])
        assert fields["caption"]["native_id"] == source["post_id"]
        assert fields["author_account"]["value"]["native_id"] == source["author"]["platform_id"]
        account_ids.add(fields["handle"]["subject_id"])
        assert member["adapter"] == "snapshot-json"
        assert member["method"]["mapper_key"] == "snapshot-json:v1"
        assert member["coverage"]["origin"]["adapter"] == "tiktok-web"
        assert member["coverage"]["annotations"] == {"basis": "development_annotation", "values": source["curation"]}
        assert not (set(source["curation"]) & fields.keys())
        metrics = {m["definition"]: m for m in member["metrics"]}
        assert metrics["tiktok.web.views.v1"]["value"] == source["metrics"]["views"]
        assert all(m["metric_id"] and m["precision"] == "exact" for m in member["metrics"])
    assert len(account_ids) == 17
    assert next(m for m in result["members"][0]["metrics"] if m["native_name"] == "shareCount")["value"] == 0


def test_concurrent_and_repeat_imports_are_idempotent_and_do_not_restore_revoked_policy(stack):
    db, evidence, runner, _ = stack
    importer = SnapshotImporter(evidence)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(lambda _: importer.import_snapshot(MANIFEST, HUMAN, POLICY), range(2)))
    assert sorted(r["status"] for r in reports) == ["duplicate", "imported"]
    assert len({r["run_id"] for r in reports}) == 1
    result = EvidenceSetReader(db).read(DATASET, HUMAN)
    original = result["members"][0]
    assert runner.replay(original["observation_id"])["status"] == "duplicate"
    evidence.revoke(original["observation_id"])
    importer.import_snapshot(MANIFEST, HUMAN, POLICY)
    assert EvidenceSetReader(db).read(DATASET, HUMAN)["members"][0]["availability"] == "unavailable"
    assert table_count(db, "source_observations") == 19
    assert table_count(db, "field_assertions") == 95
    assert table_count(db, "metric_observations") == 76


@pytest.mark.parametrize(("change", "code"), [
    (lambda d: d["records"].pop(), "snapshot_membership_mismatch"),
    (lambda d: d["records"][0].update(post_id=123), "invalid_snapshot_native_id"),
    (lambda d: d["records"][0]["author"].pop("platform_id"), "invalid_snapshot_native_id"),
    (lambda d: d["records"][0].update(url="https://www.tiktok.com/@wrong/video/123"), "snapshot_reference_mismatch"),
    (lambda d: d["records"][0].update(captured_at="2026-10-05"), "snapshot_timestamp_requires_timezone"),
    (lambda d: d["records"][0]["metrics"].update(views=True), "invalid_snapshot_metric_value"),
    (lambda d: d["records"][0]["provenance"].update(run_id="00000000-0000-0000-0000-000000000000"), "snapshot_run_not_declared"),
    (lambda d: d["records"].__setitem__(1, copy.deepcopy(d["records"][0])), "duplicate_snapshot_post"),
])
def test_invalid_input_publishes_nothing(stack, tmp_path, change, code):
    path = altered_snapshot(tmp_path, change)
    with pytest.raises(EvidenceError, match=code):
        SnapshotImporter(stack[1]).import_snapshot(path, HUMAN, POLICY)
    assert table_count(stack[0], "evidence_sets") == 0
    assert table_count(stack[0], "source_observations") == 0


def test_digest_and_same_identifier_mutation_fail_explicitly(stack, tmp_path):
    path = altered_snapshot(tmp_path, lambda d: None)
    importer = SnapshotImporter(stack[1])
    importer.import_snapshot(path, HUMAN, POLICY)
    (tmp_path / "observations.json").write_text('{}')
    with pytest.raises(EvidenceError, match="snapshot_digest_mismatch"):
        importer.import_snapshot(path, HUMAN, POLICY)
    path = altered_snapshot(tmp_path, lambda d: d["records"][0].update(caption="synthetic changed caption"))
    with pytest.raises(EvidenceError, match="dataset_version_conflict"):
        importer.import_snapshot(path, HUMAN, POLICY)
    assert table_count(stack[0], "source_observations") == 19


def test_failure_mid_import_rolls_back_rows_and_created_payloads(stack, monkeypatch):
    original_apply = CanonicalWriter.apply
    calls = 0

    def failing_apply(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise EvidenceError("injected_mapping_failure")
        return original_apply(self, *args, **kwargs)

    monkeypatch.setattr(CanonicalWriter, "apply", failing_apply)
    with pytest.raises(EvidenceError, match="injected_mapping_failure"):
        SnapshotImporter(stack[1]).import_snapshot(MANIFEST, HUMAN, POLICY)
    for table in ("ingestion_runs", "source_observations", "canonical_entities", "evidence_sets"):
        assert table_count(stack[0], table) == 0
    assert not list(stack[1].root.glob("*.bin"))


def test_later_rows_and_mapper_revision_do_not_replace_frozen_assertions(stack, tmp_path):
    db, evidence, runner, _ = stack
    original = import_sample(stack)
    # Unrelated fixture evidence and another set sharing real native identities cannot contaminate it.
    runner.ingest(SAMPLE.parents[1] / "synthetic/json-manifest.json")
    path = altered_snapshot(tmp_path, lambda d: d.update(dataset_id="another-real-set"), synthetic=False)
    SnapshotImporter(evidence).import_snapshot(path, HUMAN, POLICY)
    assert EvidenceSetReader(db).read(DATASET, HUMAN) == original
    member = original["members"][0]
    from smi_ingestion.contracts import ExternalKey
    post = ExternalKey("tiktok", "web:public", "content", DATA["records"][0]["post_id"])
    CanonicalWriter(db).apply(member["observation_id"], NormalizedBatch(
        (post,), (FieldCandidate(post, "caption", "removed", None, "$.caption"),), (),
    ), "test-correction:v2")
    pinned = EvidenceSetReader(db).read(DATASET, HUMAN)["members"][0]
    assert pinned["assertions"] == member["assertions"]
    assert pinned["support_status"] == "superseded_review_required"


@pytest.mark.parametrize(("policy_change", "hidden_purpose", "visible_purpose"), [
    ({"can_display": False}, "display", "process"),
    ({"can_process": False}, "process", "display"),
    ({"revoked": True}, "display", None),
    ({"expires_at": "2000-01-01T00:00:00+00:00"}, "display", None),
])
def test_policy_changes_redact_source_text_urls_metrics_and_annotations(stack, policy_change, hidden_purpose, visible_purpose):
    result = import_sample(stack)
    member = result["members"][0]
    policy = {**member["policy"], **policy_change}
    with stack[0].connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(policy), member["observation_id"]))
    reader = EvidenceSetReader(stack[0])
    hidden = reader.read(DATASET, HUMAN, purpose=hidden_purpose)
    tombstone = hidden["members"][0]
    assert tombstone["availability"] == "unavailable"
    assert set(tombstone) == {"position", "observation_id", "derivation_id", "origin_observation_id", "origin_run_id", "availability", "reason"}
    assert hidden["coverage"]["available_members"] == 18
    if visible_purpose:
        assert reader.read(DATASET, HUMAN, purpose=visible_purpose)["members"][0]["availability"] == "available"


def test_actor_scope_import_authority_and_synthetic_visibility(stack, tmp_path):
    importer = SnapshotImporter(stack[1])
    for actor in (ActorContext("foreign", "marketer", "human"), ActorContext("local", "", "human"),
                  ActorContext("local", "agent", "automation")):
        with pytest.raises(EvidenceError, match="workspace_access_denied"):
            importer.import_snapshot(MANIFEST, actor, POLICY)
    with pytest.raises(EvidenceError, match="processing_not_permitted"):
        importer.import_snapshot(MANIFEST, HUMAN, replace(POLICY, can_process=False))
    path = altered_snapshot(tmp_path, lambda d: None)
    importer.import_snapshot(path, HUMAN, POLICY)
    reader = EvidenceSetReader(stack[0])
    with pytest.raises(EvidenceError, match="workspace_access_denied"):
        reader.read("synthetic-snapshot-test", ActorContext("foreign", "marketer", "human"))
    with pytest.raises(EvidenceError, match="synthetic_evidence_excluded"):
        reader.read("synthetic-snapshot-test", HUMAN)
    assert reader.read("synthetic-snapshot-test", HUMAN, include_synthetic=True)["synthetic"] is True


def test_missing_metric_stays_missing_and_zero_is_observed(stack, tmp_path):
    path = altered_snapshot(tmp_path, lambda d: d["records"][0]["metrics"].pop("views"))
    SnapshotImporter(stack[1]).import_snapshot(path, HUMAN, POLICY)
    member = EvidenceSetReader(stack[0]).read("synthetic-snapshot-test", HUMAN, include_synthetic=True)["members"][0]
    missing = next(a for a in member["assertions"] if a["field"] == "metric:views")
    assert (missing["state"], missing["value"], missing["reason"]) == ("not_returned", None, "absent_from_snapshot")
    assert next(m for m in member["metrics"] if m["native_name"] == "shareCount")["value"] == 0


def test_cli_import_and_reopen_in_new_process_preserve_exact_bindings(stack, tmp_path):
    db = stack[0]
    evidence_dir = tmp_path / "cli"
    imported = _cli(db, evidence_dir, "import-snapshot", str(MANIFEST))
    assert imported.returncode == 0, imported.stdout + imported.stderr
    first = _cli(db, evidence_dir, "inspect-set", DATASET)
    second = _cli(db, evidence_dir, "inspect-set", DATASET)
    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout) == json.loads(second.stdout)
    again = _cli(db, evidence_dir, "import-snapshot", str(MANIFEST))
    assert json.loads(again.stdout)["status"] == "duplicate"


def test_fresh_database_reproduces_native_identity_and_origin_membership(stack, tmp_path):
    import uuid
    from psycopg import sql
    from smi_ingestion.db import Database
    from smi_ingestion.evidence import EvidenceStore

    original = import_sample(stack)
    schema = "test_reset_" + uuid.uuid4().hex
    db = stack[0]
    with db.connect() as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        fresh_db = Database(db.dsn, schema)
        fresh_db.migrate()
        fresh_db.migrate()  # Migration is safe on an already initialized schema.
        SnapshotImporter(EvidenceStore(fresh_db, tmp_path / "fresh")).import_snapshot(MANIFEST, HUMAN, POLICY)
        fresh = EvidenceSetReader(fresh_db).read(DATASET, HUMAN)
        assert fresh["digest"] == original["digest"]
        assert fresh["coverage"] == original["coverage"]
        assert fresh["run_id"] != original["run_id"]
        for a, b in zip(original["members"], fresh["members"], strict=True):
            assert a["origin_observation_id"] == b["origin_observation_id"]
            assert a["observation_id"] != b["observation_id"]
            assert [(x["native_id"], x["field"], x["value"]) for x in a["assertions"]] == [
                (x["native_id"], x["field"], x["value"]) for x in b["assertions"]
            ]
    finally:
        with db.connect() as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_missing_members_fail_closed_and_manifest_cannot_hold_uncensored_content(stack, tmp_path):
    result = import_sample(stack)
    with stack[0].connect() as connection:
        connection.execute("DELETE FROM evidence_set_members WHERE observation_id=%s", (result["members"][0]["observation_id"],))
    with pytest.raises(EvidenceError, match="evidence_set_incomplete"):
        EvidenceSetReader(stack[0]).read(DATASET, HUMAN)
    path = altered_snapshot(tmp_path, lambda d: None)
    manifest = json.loads(path.read_text())
    manifest["caption_copy"] = "unfiltered source content"
    path.write_text(json.dumps(manifest))
    with pytest.raises(EvidenceError, match="invalid_snapshot_manifest_fields"):
        SnapshotImporter(stack[1]).import_snapshot(path, HUMAN, POLICY)
