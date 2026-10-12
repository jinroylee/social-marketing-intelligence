from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from smi_ingestion.adapters.json_fixture import JsonFixtureMapper
from smi_ingestion.canonical import CanonicalReader
from smi_ingestion.contracts import CollectedBatch, ExternalKey, ObservationDraft, RunLimits, SourcePolicy, SourceReference
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.references import parse_reference
EXAMPLES = Path(__file__).parents[1] / "examples" / "synthetic"


POST = ExternalKey("tiktok", "fixture:public", "content", "fixture-post-1")


def _manifest(tmp_path: Path, *, adapter="fixture-json", provider="synthetic-api", captured="2026-09-10T12:00:00Z", policy=None, items=None) -> Path:
    payload = {
        "adapter": adapter,
        "provider_id": provider,
        "format_version": "v1",
        "synthetic": True,
        "captured_at": captured,
        "policy": policy or {"context_id": "synthetic-test", "can_process": True, "can_retain": True, "can_display": True, "expires_at": None},
        "items": items or [{"path": "post.json" if adapter == "fixture-json" else "post.html", "reference": "synthetic://post/fixture-post-1"}],
    }
    for item in payload["items"]:
        source = EXAMPLES / item["path"]
        target = tmp_path / item["path"]
        if not target.exists():
            target.write_bytes(source.read_bytes())
    path = tmp_path / f"{adapter}-{provider}.json"
    path.write_text(json.dumps(payload))
    return path


def _observation_id(db, run_id: str) -> str:
    with db.connect() as connection:
        return str(connection.execute("SELECT id FROM source_observations WHERE run_id=%s", (run_id,)).fetchone()["id"])


def test_reference_is_unverified_and_preserves_large_id():
    source = "https://www.tiktok.com/@maronayannyan/video/7632620458235530504"
    reference = parse_reference(source)
    assert reference.native_id_hint == "7632620458235530504"
    assert reference.handle_hint == "maronayannyan"
    assert isinstance(reference.native_id_hint, str)
    assert parse_reference("https://tiktok.com.evil.test/@name/video/123").platform is None
    assert parse_reference("https://tiktok.com/@name/video/123extra").native_id_hint is None
    assert parse_reference("https://WWW.TIKTOK.COM/@name/video/123").native_id_hint == "123"


def test_two_formats_share_identity_with_separate_provenance_and_safe_replay(stack):
    db, evidence, runner, _ = stack
    json_run = runner.ingest(EXAMPLES / "json-manifest.json")
    html_run = runner.ingest(EXAMPLES / "html-manifest.json")
    assert json_run["status"] == html_run["status"] == "completed"
    reader = CanonicalReader(db)
    assert reader.entity(POST) is None
    entity = reader.entity(POST, include_synthetic=True)
    assert entity["fields"]["caption"]["value"] == "Synthetic cushion sample"
    assert len(entity["fields"]["caption"]["provenance"]) == 2
    assert {source["source_reference"] for source in entity["fields"]["caption"]["provenance"]} == {"synthetic://post/fixture-post-1"}
    assert [metric["value"] for metric in reader.metrics(POST, True)] == [1000, 1050]
    first_id = _observation_id(db, json_run["run_id"])
    assert runner.replay(first_id)["status"] == "duplicate"
    assert len(reader.metrics(POST, True)) == 2
    assert reader.entity(POST, True)["id"] == entity["id"]


def test_refresh_keeps_history_and_missing_does_not_erase(stack, tmp_path):
    db, _, runner, _ = stack
    first = _manifest(tmp_path)
    assert runner.ingest(first)["status"] == "completed"
    data = json.loads((tmp_path / "post.json").read_text())
    data["video"]["metrics"]["views"] = 0
    data["video"].pop("caption")
    (tmp_path / "post.json").write_text(json.dumps(data))
    second = _manifest(tmp_path, captured="2026-09-12T12:00:00Z")
    assert runner.ingest(second)["status"] == "completed"
    reader = CanonicalReader(db)
    assert [metric["value"] for metric in reader.metrics(POST, True)] == [1000, 0]
    assert reader.entity(POST, True)["fields"]["caption"]["value"] == "Synthetic cushion sample"


def test_approximate_count_and_conflicting_provider_caption(stack, tmp_path):
    db, _, runner, _ = stack
    runner.ingest(EXAMPLES / "json-manifest.json")
    path = _manifest(tmp_path, adapter="fixture-html", provider="second-provider")
    html = (tmp_path / "post.html").read_text().replace("1,050", "1.2K").replace("Synthetic cushion sample", "Different synthetic caption")
    (tmp_path / "post.html").write_text(html)
    assert runner.ingest(path)["status"] == "completed"
    reader = CanonicalReader(db)
    assert reader.entity(POST, True)["fields"]["caption"]["state"] == "conflict"
    metrics = reader.metrics(POST, True)
    assert metrics[-1]["precision"] == "approximate"
    assert metrics[-1]["raw_display"] == "1.2K"


def test_nonretained_evidence_processes_once_but_cannot_replay(stack, tmp_path):
    db, evidence, runner, _ = stack
    policy = {"context_id": "transient", "can_process": True, "can_retain": False, "can_display": True, "expires_at": None}
    result = runner.ingest(_manifest(tmp_path, policy=policy))
    assert result["status"] == "completed"
    obs_id = _observation_id(db, result["run_id"])
    assert evidence.get(obs_id).payload_path is None
    assert not list(evidence.root.glob("*.bin"))
    assert len(CanonicalReader(db).metrics(POST, True)) == 1
    with pytest.raises(EvidenceError, match="replay_unavailable"):
        runner.replay(obs_id)


def test_revocation_removes_current_evidence_and_payload(stack):
    db, evidence, runner, _ = stack
    run = runner.ingest(EXAMPLES / "json-manifest.json")
    obs_id = _observation_id(db, run["run_id"])
    path = Path(evidence.get(obs_id).payload_path)
    assert path.exists()
    evidence.revoke(obs_id)
    assert not path.exists()
    assert CanonicalReader(db).entity(POST, True) is None
    with pytest.raises(EvidenceError, match="evidence_unavailable"):
        runner.replay(obs_id)


def test_expired_evidence_is_not_read_or_replayed(stack):
    db, evidence, runner, _ = stack
    run = runner.ingest(EXAMPLES / "json-manifest.json")
    obs_id = _observation_id(db, run["run_id"])
    with db.connect() as connection:
        policy = connection.execute("SELECT policy FROM source_observations WHERE id=%s", (obs_id,)).fetchone()["policy"]
        policy["expires_at"] = "2000-01-01T00:00:00+00:00"
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(policy), obs_id))
    assert CanonicalReader(db).entity(POST, True) is None
    with pytest.raises(EvidenceError, match="evidence_unavailable"):
        runner.replay(obs_id)
    assert evidence.expire() == 1


def test_record_limit_is_partial_without_second_read(stack, tmp_path):
    db, _, runner, _ = stack
    path = _manifest(tmp_path, items=[{"path": "post.json"}, {"path": "post.html"}])
    result = runner.ingest(path, RunLimits(max_records=1))
    assert result["status"] == "partial"
    assert result["records_used"] == 1
    assert result["issues"][0]["code"] == "record_limit_reached"
    with db.connect() as connection:
        assert connection.execute("SELECT count(*) AS n FROM source_observations WHERE run_id=%s", (result["run_id"],)).fetchone()["n"] == 1


def test_request_limit_still_caps_local_collector_calls(stack, tmp_path):
    _, _, runner, _ = stack
    path = _manifest(tmp_path, items=[{"path": "post.json"}, {"path": "post.html"}])
    result = runner.ingest(path, RunLimits(max_requests=1))
    assert result["status"] == "partial"
    assert result["records_used"] == result["requests_used"] == 1
    assert result["issues"][0]["code"] == "request_limit_reached"


def test_resume_maps_durably_saved_observation_without_collecting_again(stack):
    db, evidence, runner, registry = stack
    path = EXAMPLES / "json-manifest.json"
    manifest, digest = runner._manifest(path)
    run_id = evidence.start_run(path, digest, "fixture-json", RunLimits())
    collector, _ = registry.resolve("fixture-json")
    batch = collector.collect(manifest, {"index": 0}, RunLimits())
    evidence.save(run_id, 0, batch.items[0], batch.next_checkpoint)
    assert runner.resume(run_id)["status"] == "completed"
    assert CanonicalReader(db).metrics(POST, True)[0]["value"] == 1000


def test_manifest_change_rejects_resume(stack, tmp_path):
    _, evidence, runner, _ = stack
    path = _manifest(tmp_path)
    _, digest = runner._manifest(path)
    run_id = evidence.start_run(path, digest, "fixture-json", RunLimits())
    path.write_text(path.read_text() + " ")
    with pytest.raises(EvidenceError, match="input_changed"):
        runner.resume(run_id)


def test_mapper_revision_supersedes_without_duplicate_measurement(stack):
    db, _, runner, registry = stack
    run = runner.ingest(EXAMPLES / "json-manifest.json")
    obs_id = _observation_id(db, run["run_id"])
    collector, _ = registry.resolve("fixture-json")

    class RevisedMapper(JsonFixtureMapper):
        version = "v2"

    registry._adapters["fixture-json"] = (collector, RevisedMapper())
    assert runner.replay(obs_id)["status"] == "applied"
    assert runner.replay(obs_id)["status"] == "duplicate"
    assert len(CanonicalReader(db).metrics(POST, True)) == 1
    with db.connect() as connection:
        rows = connection.execute("SELECT active FROM derivations WHERE observation_id=%s", (obs_id,)).fetchall()
    assert sorted(row["active"] for row in rows) == [False, True]


def test_corrupt_payload_is_visible_failure(stack):
    db, evidence, runner, _ = stack
    run = runner.ingest(EXAMPLES / "json-manifest.json")
    obs_id = _observation_id(db, run["run_id"])
    Path(evidence.get(obs_id).payload_path).write_bytes(b"corrupt")
    with pytest.raises(EvidenceError, match="payload_corrupt"):
        runner.replay(obs_id)


def test_missing_stable_id_is_inspectable_without_inventing_identity(stack, tmp_path):
    db, _, runner, _ = stack
    path = _manifest(tmp_path)
    data = json.loads((tmp_path / "post.json").read_text())
    data["video"].pop("id")
    (tmp_path / "post.json").write_text(json.dumps(data))
    result = runner.ingest(path)
    assert result["status"] == "completed"
    assert result["unresolved"] == 1
    assert CanonicalReader(db).entity(POST, True) is None
    with db.connect() as connection:
        row = connection.execute("SELECT kind,reason FROM unresolved_candidates").fetchone()
    assert row == {"kind": "content", "reason": "missing_stable_id"}


def test_explicit_removal_suppresses_older_source_assertion(stack, tmp_path):
    db, _, runner, _ = stack
    path = _manifest(tmp_path)
    runner.ingest(path)
    data = json.loads((tmp_path / "post.json").read_text())
    data["video"].pop("caption")
    data["video"]["caption_state"] = "removed"
    (tmp_path / "post.json").write_text(json.dumps(data))
    runner.ingest(_manifest(tmp_path, captured="2026-09-12T12:00:00Z"))
    field = CanonicalReader(db).entity(POST, True)["fields"]["caption"]
    assert field["state"] == "removed"
    assert field["value"] is None


def test_malformed_second_item_preserves_first_and_reports_partial(stack, tmp_path):
    db, _, runner, _ = stack
    (tmp_path / "bad.json").write_text("not-json")
    path = _manifest(tmp_path, items=[{"path": "post.json"}, {"path": "bad.json"}])
    result = runner.ingest(path)
    assert result["status"] == "partial"
    assert result["applied"] == 1
    assert result["quarantined"] == 1
    assert result["issues"][0]["code"] == "normalization_failed"
    assert CanonicalReader(db).entity(POST, True) is not None


def test_byte_limit_rejects_input_before_storing_it(stack):
    db, _, runner, _ = stack
    result = runner.ingest(EXAMPLES / "json-manifest.json", RunLimits(max_bytes=10))
    assert result["status"] == "partial"
    assert result["observations"] == 0
    assert result["issues"][0]["code"] == "byte_limit_reached"


def test_runner_accepts_new_collector_without_fixture_manifest_fields(stack, tmp_path):
    db, _, runner, registry = stack
    raw = (EXAMPLES / "post.json").read_bytes()

    class FeedCollector:
        def collect(self, manifest, checkpoint, limits):
            if checkpoint.get("done"):
                return CollectedBatch((), {"done": True}, True)
            draft = ObservationDraft(
                "synthetic-feed-item", "fixture-feed", "synthetic-feed", "v1",
                SourceReference("fixture://feed/item"), raw, "application/json",
                datetime(2026, 9, 13, tzinfo=timezone.utc), None,
                SourcePolicy("synthetic-feed", True, True, True), True,
            )
            return CollectedBatch((draft,), {"done": True}, True)

    registry.register("fixture-feed", FeedCollector(), JsonFixtureMapper())
    manifest = tmp_path / "feed-request.json"
    manifest.write_text(json.dumps({"adapter": "fixture-feed", "query": {"term": "synthetic"}}))
    result = runner.ingest(manifest)
    assert result["status"] == "completed"
    assert CanonicalReader(db).entity(POST, True) is not None


def test_duplicate_concurrent_apply_uses_one_derivation(stack):
    db, evidence, runner, registry = stack
    path = EXAMPLES / "json-manifest.json"
    manifest, digest = runner._manifest(path)
    run_id = evidence.start_run(path, digest, "fixture-json", RunLimits())
    collector, mapper = registry.resolve("fixture-json")
    batch = collector.collect(manifest, {"index": 0}, RunLimits())
    observation = evidence.save(run_id, 0, batch.items[0], batch.next_checkpoint)
    normalized = mapper.normalize(observation, batch.items[0].payload)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(runner.writer.apply, observation.id, normalized, "fixture-json:v1") for _ in range(2)]
        statuses = sorted(future.result()["status"] for future in futures)
    assert statuses == ["applied", "duplicate"]
    with db.connect() as connection:
        assert connection.execute("SELECT count(*) AS n FROM derivations").fetchone()["n"] == 1
        assert connection.execute("SELECT count(*) AS n FROM canonical_entities").fetchone()["n"] == 2


def test_orphan_cleanup_touches_only_old_unreferenced_evidence_files(stack):
    db, evidence, runner, _ = stack
    run = runner.ingest(EXAMPLES / "json-manifest.json")
    retained = Path(evidence.get(_observation_id(db, run["run_id"])).payload_path)
    orphan = evidence.root / "550e8400-e29b-41d4-a716-446655440000.bin"
    orphan.write_bytes(b"orphan")
    os.utime(orphan, (1, 1))
    unrelated = evidence.root / "user-file.bin"
    unrelated.write_bytes(b"keep")
    assert evidence.reconcile_orphans() == 1
    assert retained.exists()
    assert unrelated.exists()
    assert not orphan.exists()


def test_mismatched_author_id_is_quarantined(stack, tmp_path):
    _, _, runner, _ = stack
    path = _manifest(tmp_path)
    data = json.loads((tmp_path / "post.json").read_text())
    data["video"]["author_id"] = "different-account"
    (tmp_path / "post.json").write_text(json.dumps(data))
    report = runner.ingest(path)
    assert report["status"] == "partial"
    assert report["quarantined"] == 1
    assert report["issues"][0]["code"] == "normalization_failed"


def test_processing_denied_returns_partial_report_without_payload(stack, tmp_path):
    db, evidence, runner, _ = stack
    policy = {"context_id": "denied", "can_process": False, "can_retain": True, "can_display": True, "expires_at": None}
    report = runner.ingest(_manifest(tmp_path, policy=policy))
    assert report["status"] == "partial"
    assert report["observations"] == 0
    assert report["issues"][0]["code"] == "processing_not_permitted"
    assert not list(evidence.root.glob("*.bin"))


def test_invalid_metric_object_is_quarantined_and_reported(stack, tmp_path):
    _, _, runner, _ = stack
    path = _manifest(tmp_path)
    data = json.loads((tmp_path / "post.json").read_text())
    data["video"]["metrics"] = "unparseable"
    (tmp_path / "post.json").write_text(json.dumps(data))
    report = runner.ingest(path)
    assert report["status"] == "partial"
    assert report["quarantined"] == 1
    assert report["issues"][0]["code"] == "normalization_failed"


def test_display_denial_hides_processed_evidence(stack, tmp_path):
    db, _, runner, _ = stack
    policy = {"context_id": "internal-only", "can_process": True, "can_retain": True, "can_display": False, "expires_at": None}
    report = runner.ingest(_manifest(tmp_path, policy=policy))
    assert report["status"] == "completed"
    assert CanonicalReader(db).entity(POST, True) is None
    assert CanonicalReader(db).metrics(POST, True) == []


def test_source_time_beats_later_capture_when_measurements_are_comparable(stack, tmp_path):
    db, _, runner, _ = stack
    path = _manifest(tmp_path)
    first_manifest = json.loads(path.read_text())
    first_manifest["items"][0]["source_as_of"] = "2026-09-12T12:00:00Z"
    path.write_text(json.dumps(first_manifest))
    runner.ingest(path)
    data = json.loads((tmp_path / "post.json").read_text())
    data["video"]["caption"] = "Older source measurement"
    (tmp_path / "post.json").write_text(json.dumps(data))
    later_path = _manifest(tmp_path, captured="2026-09-13T12:00:00Z")
    later_manifest = json.loads(later_path.read_text())
    later_manifest["items"][0]["source_as_of"] = "2026-09-11T12:00:00Z"
    later_path.write_text(json.dumps(later_manifest))
    runner.ingest(later_path)
    assert CanonicalReader(db).entity(POST, True)["fields"]["caption"]["value"] == "Synthetic cushion sample"
