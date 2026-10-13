from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

import pytest

from smi_ingestion.adapters.tiktok_oembed import (
    OEmbedHTTPResponse, TikTokOEmbedCollector, TikTokOEmbedMapper,
    TikTokOEmbedTransport, _reference,
)
from smi_ingestion.contracts import RunLimits
from smi_ingestion.evidence import EvidenceError


VIDEO = "https://www.tiktok.com/@synthetic_fixture_account/video/1234567890"
PROFILE = "https://www.tiktok.com/@synthetic_fixture_account"
CAPTURED = datetime(2026, 9, 29, 8, tzinfo=timezone.utc)


class FakeTransport:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls: list[tuple[str, int]] = []

    def fetch(self, reference_url: str, max_bytes: int) -> OEmbedHTTPResponse:
        self.calls.append((reference_url, max_bytes))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def _video_response(*, video_id="1234567890") -> OEmbedHTTPResponse:
    return OEmbedHTTPResponse(200, json.dumps({
        "type": "video", "provider_name": "TikTok", "author_name": "RETURNED_AUTHOR_SENTINEL",
        "author_url": PROFILE, "title": "RETURNED_TITLE_SENTINEL",
        "thumbnail_url": "https://example.invalid/RETURNED_THUMBNAIL_SENTINEL",
        "html": f'<blockquote data-video-id="{video_id}">RETURNED_HTML_SENTINEL</blockquote>',
    }).encode())


def _profile_response() -> OEmbedHTTPResponse:
    return OEmbedHTTPResponse(200, json.dumps({
        "type": "rich", "provider_name": "TikTok", "author_name": "RETURNED_AUTHOR_SENTINEL",
        "author_url": PROFILE, "title": "RETURNED_PROFILE_TITLE_SENTINEL",
        "html": '<blockquote data-unique-id="synthetic_fixture_account">RETURNED_HTML_SENTINEL</blockquote>',
    }).encode())


def _manifest(tmp_path: Path, *references: str) -> Path:
    path = tmp_path / "oembed-request.json"
    path.write_text(json.dumps({"adapter": "tiktok-oembed", "references": list(references)}))
    return path


def _install_fake(registry, transport: FakeTransport) -> None:
    registry._adapters["tiktok-oembed"] = (
        TikTokOEmbedCollector(transport, lambda: CAPTURED), TikTokOEmbedMapper()
    )


def test_only_direct_tiktok_profile_or_video_references_are_accepted():
    ref = _reference("https://m.tiktok.com/@synthetic_fixture_account/video/1234567890?lang=ja")
    assert ref.original == VIDEO
    assert ref.native_id_hint == "1234567890"
    assert _reference(PROFILE).resource_kind == "profile"
    for invalid in (
        "http://www.tiktok.com/@name", "https://tiktok.com.evil.test/@name",
        "https://www.tiktok.com:444/@name", "https://www.tiktok.com/@name/video/no-id",
        "https://www.tiktok.com/@name/live", "https://www.tiktok.com/%40name%2Fextra",
    ):
        with pytest.raises(EvidenceError, match="invalid_tiktok_reference"):
            _reference(invalid)


def test_transport_rejects_response_beyond_its_byte_limit(monkeypatch):
    class Headers:
        def get_content_type(self):
            return "application/json"

    class OversizedResponse:
        status = 200
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def geturl(self):
            return "https://www.tiktok.com/oembed"

        def read(self, size):
            return b"x" * size

    monkeypatch.setattr(
        "smi_ingestion.adapters.tiktok_oembed.open_no_redirect",
        lambda request, timeout: OversizedResponse(),
    )
    with pytest.raises(EvidenceError, match="response_too_large"):
        TikTokOEmbedTransport().fetch(PROFILE, max_bytes=10)


def test_live_shaped_video_and_profile_resolve_without_retaining_returned_content(stack, tmp_path):
    db, evidence, runner, registry = stack
    transport = FakeTransport(_video_response(), _profile_response(), _video_response(), _profile_response())
    _install_fake(registry, transport)
    request = _manifest(tmp_path, VIDEO, PROFILE)

    first = runner.ingest(request)
    second = runner.ingest(request)
    assert first["status"] == second["status"] == "completed"
    assert first["requests_used"] == second["requests_used"] == 2
    assert first["applied"] == second["applied"] == 2
    assert first["unresolved"] == second["unresolved"] == 2
    assert [result["outcome"] for result in first["source_results"]] == ["resolved", "resolved"]
    assert first["source_results"][0]["unavailable_fields"] == [
        "post_history", "follower_count", "view_count", "engagement_counts",
        "audience_geography", "sales_outcomes",
    ]
    assert [call[0] for call in transport.calls] == [VIDEO, PROFILE, VIDEO, PROFILE]

    with db.connect() as connection:
        observations = connection.execute(
            "SELECT reference,handle_hint,native_id_hint,payload_path,coverage FROM source_observations"
        ).fetchall()
        counts = {
            table: connection.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            for table in ("canonical_entities", "external_identities", "field_assertions", "metric_observations")
        }
    assert len(observations) == 4
    assert all(row["payload_path"] is None for row in observations)
    assert all(value == 0 for value in counts.values())
    durable = json.dumps({"observations": observations, "first": first, "second": second}, default=str)
    assert "RETURNED_" not in durable
    assert list(evidence.root.glob("*.bin")) == []
    with pytest.raises(EvidenceError, match="replay_unavailable"):
        runner.replay(_first_observation(db, first["run_id"]))


def _first_observation(db, run_id: str) -> str:
    with db.connect() as connection:
        row = connection.execute(
            "SELECT id FROM source_observations WHERE run_id=%s ORDER BY item_index LIMIT 1", (run_id,)
        ).fetchone()
    return str(row["id"])


def test_unavailable_reference_is_recorded_without_claiming_deletion(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(OEmbedHTTPResponse(404, b""))
    _install_fake(registry, transport)
    report = runner.ingest(_manifest(tmp_path, PROFILE))
    assert report["status"] == "completed"
    assert report["requests_used"] == 1
    assert report["source_results"][0]["outcome"] == "unavailable_or_private"
    assert report["source_results"][0]["http_status"] == 404
    assert report["unresolved"] == 0


def test_rate_limit_stops_without_retry_or_fetching_next_reference(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(OEmbedHTTPResponse(429, b""))
    _install_fake(registry, transport)
    report = runner.ingest(_manifest(tmp_path, VIDEO, PROFILE))
    assert report["status"] == "partial"
    assert report["requests_used"] == 1
    assert report["source_results"][0]["outcome"] == "rate_limited"
    assert len(transport.calls) == 1


def test_one_transient_retry_consumes_request_budget(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(URLError("timed out"), _video_response())
    _install_fake(registry, transport)
    report = runner.ingest(_manifest(tmp_path, VIDEO, PROFILE), RunLimits(max_requests=2))
    assert report["status"] == "partial"
    assert report["requests_used"] == 2
    assert report["records_used"] == 1
    assert report["issues"][0]["code"] == "request_limit_reached"
    assert len(transport.calls) == 2


def test_oembed_attempt_cap_cannot_be_raised_by_cli_limits(stack, tmp_path):
    _, _, runner, registry = stack
    references = [f"https://www.tiktok.com/@synthetic_fixture_account/video/{item}" for item in range(1, 7)]
    responses = [response for item in range(1, 7) for response in (
        URLError("timed out"), _video_response(video_id=str(item))
    )]
    transport = FakeTransport(*responses)
    _install_fake(registry, transport)
    report = runner.ingest(_manifest(tmp_path, *references), RunLimits(max_requests=20))
    assert report["status"] == "partial"
    assert report["requests_used"] == 10
    assert report["records_used"] == 5
    assert report["issues"][0]["code"] == "request_limit_reached"
    assert len(transport.calls) == 10


def test_wrong_video_identity_is_quarantined_without_canonical_write(stack, tmp_path):
    db, _, runner, registry = stack
    _install_fake(registry, FakeTransport(_video_response(video_id="123")))
    report = runner.ingest(_manifest(tmp_path, VIDEO))
    assert report["status"] == "partial"
    assert report["quarantined"] == 1
    assert report["source_results"][0]["mapping_status"] == "quarantined"
    assert report["issues"][0]["code"] == "normalization_failed"
    with db.connect() as connection:
        assert connection.execute("SELECT count(*) AS n FROM canonical_entities").fetchone()["n"] == 0


def test_invalid_batch_is_rejected_before_network(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport()
    _install_fake(registry, transport)
    report = runner.ingest(_manifest(tmp_path, VIDEO, "https://evil.test/@name"))
    assert report["status"] == "partial"
    assert report["issues"][0]["code"] == "invalid_tiktok_reference"
    assert transport.calls == []
