from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError

import pytest

from smi_ingestion.adapters.bright_data import (
    BrightDataHTTPResponse, BrightDataTikTokCollector, BrightDataTikTokMapper,
    BrightDataTransport, _DATASETS, _profile_reference,
)
from smi_ingestion.contracts import ExternalKey, RunLimits
from smi_ingestion.evidence import EvidenceError


PROFILE = "https://www.tiktok.com/@synthetic_fixture_account"
CAPTURED = datetime(2026, 9, 30, 8, tzinfo=timezone.utc)


class FakeTransport:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def fetch(self, dataset_id, profile_url, num_of_posts, token, max_bytes):
        self.calls.append((dataset_id, profile_url, num_of_posts, token, max_bytes))
        return self._next()

    def progress(self, snapshot_id, token):
        self.calls.append(("progress", snapshot_id, token))
        return self._next()

    def snapshot(self, snapshot_id, token, max_bytes):
        self.calls.append(("snapshot", snapshot_id, token, max_bytes))
        return self._next()

    def _next(self):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def _profile_response(*, account_id="123456789"):
    return BrightDataHTTPResponse(200, json.dumps([{
        "account_id": account_id, "url": PROFILE, "nickname": "Synthetic creator",
        "biography": "Synthetic fixture", "followers": 0, "following": 3,
        "likes": 20, "videos_count": 2,
    }]).encode())


def _posts_response(*, permalink=PROFILE + "/video/7553300000000000000"):
    row = {
        "post_id": "7553300000000000000", "profile_url": PROFILE,
        "description": "Synthetic cushion post", "create_time": "2026-09-01T12:00:00Z",
        "play_count": 0, "comment_count": 2, "share_count": 1,
        "video_url": "https://tiktok.example.invalid/temporary-media.mp4",
    }
    if permalink is not None:
        row["post_url"] = permalink
    return BrightDataHTTPResponse(200, json.dumps([row]).encode())


def _manifest(tmp_path: Path, references=None, num_of_posts=10) -> Path:
    path = tmp_path / "brightdata-request.json"
    path.write_text(json.dumps({
        "adapter": "brightdata-tiktok", "references": references or [PROFILE],
        "num_of_posts": num_of_posts,
    }))
    return path


def _install(registry, transport: FakeTransport, token="synthetic-test-token"):
    collector = BrightDataTikTokCollector(transport, lambda: CAPTURED, lambda: token)
    registry._adapters["brightdata-tiktok"] = (collector, BrightDataTikTokMapper())


def test_only_direct_profiles_are_accepted():
    assert _profile_reference("https://m.tiktok.com/@synthetic_fixture_account?lang=ja").original == PROFILE
    for invalid in (
        "http://www.tiktok.com/@user", "https://www.tiktok.com.evil.test/@user",
        "https://www.tiktok.com:444/@user", "https://www.tiktok.com/@user/video/123",
        "https://www.tiktok.com/%40user", "https://www.tiktok.com/@user#fragment",
    ):
        with pytest.raises(EvidenceError, match="invalid_tiktok_profile_reference"):
            _profile_reference(invalid)


def test_blank_credentials_and_invalid_limits_fail_before_network(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport()
    _install(registry, transport, token=" ")
    missing = runner.ingest(_manifest(tmp_path))
    assert missing["status"] == "partial"
    assert missing["issues"][0]["code"] == "missing_brightdata_api_token"
    assert missing["requests_used"] == 0
    assert transport.calls == []

    _install(registry, transport)
    for references, posts, code in (
        ([PROFILE] * 4, 10, "invalid_reference_count"),
        ([PROFILE], 11, "invalid_post_count"),
        ([PROFILE, PROFILE], 10, "duplicate_tiktok_reference"),
        (["https://evil.test/@user"], 10, "invalid_tiktok_profile_reference"),
    ):
        report = runner.ingest(_manifest(tmp_path, references, posts))
        assert report["issues"][0]["code"] == code
    assert transport.calls == []


def test_profile_and_post_mapping_preserve_provenance_and_missingness(stack, tmp_path):
    db, evidence, runner, registry = stack
    transport = FakeTransport(_profile_response(), _posts_response())
    _install(registry, transport)
    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "completed"
    assert report["requests_used"] == report["observations"] == 2
    assert [call[0] for call in transport.calls] == [_DATASETS["profile"], _DATASETS["posts"]]
    assert [call[2] for call in transport.calls] == [10, 10]
    assert [call[3] for call in transport.calls] == ["synthetic-test-token"] * 2
    with db.connect() as connection:
        rows = connection.execute(
            "SELECT id,provider_id,format_version,payload_path,coverage,policy "
            "FROM source_observations ORDER BY item_index"
        ).fetchall()
    assert len(rows) == 2
    assert all(row["provider_id"] == "brightdata" and row["payload_path"] for row in rows)
    assert all(row["policy"]["context_id"].startswith("brightdata-unpublished-local-prototype") for row in rows)
    assert [row["coverage"]["dataset_kind"] for row in rows] == ["profile", "posts"]
    assert all(row["coverage"]["outcome"] == "resolved" for row in rows)
    assert all(row["format_version"] == "brightdata-tiktok-v1" for row in rows)
    assert evidence.load(str(rows[0]["id"]))[1]

    from smi_ingestion.canonical import CanonicalReader
    reader = CanonicalReader(db)
    account = reader.entity(ExternalKey("tiktok", "tiktok:public", "account", "123456789"))
    assert account["fields"]["handle"]["value"] == "synthetic_fixture_account"
    assert reader.metrics(ExternalKey("tiktok", "tiktok:public", "account", "123456789"))[0]["value"] == 0
    post = reader.entity(ExternalKey("tiktok", "tiktok:public", "content", "7553300000000000000"))
    assert post["fields"]["caption"]["value"] == "Synthetic cushion post"
    assert post["fields"]["post_url"]["value"] == PROFILE + "/video/7553300000000000000"
    assert post["fields"]["author_account"]["state"] == "unknown"
    assert post["fields"]["post_url"]["value"] != "https://tiktok.example.invalid/temporary-media.mp4"
    assert {metric["native_name"] for metric in reader.metrics(ExternalKey(
        "tiktok", "tiktok:public", "content", "7553300000000000000"
    ))} == {"play_count", "comment_count", "share_count"}


def test_documented_posts_shape_without_profile_url_uses_matching_permalink(stack, tmp_path):
    _, _, runner, registry = stack
    post_id = "7553300000000000000"
    documented_shape = BrightDataHTTPResponse(200, json.dumps([{
        "url": PROFILE + "/video/" + post_id,
        "description": "Synthetic documentation-shaped post",
        "post_id": post_id,
        "create_time": "2026-09-01T12:00:00.000Z",
        "digg_count": 12, "share_count": "344", "comment_count": 3,
        "play_count": 1234,
    }]).encode())
    _install(registry, FakeTransport(_profile_response(), documented_shape))
    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "completed"
    from smi_ingestion.canonical import CanonicalReader
    reader = CanonicalReader(stack[0])
    key = ExternalKey("tiktok", "tiktok:public", "content", post_id)
    post = reader.entity(key)
    assert post["fields"]["post_url"]["value"] == PROFILE + "/video/" + post_id
    assert post["fields"]["author_account"]["state"] == "unknown"
    share = next(metric for metric in reader.metrics(key) if metric["native_name"] == "share_count")
    assert share["value"] == 344


def test_replay_is_idempotent_for_retained_observation(stack, tmp_path):
    db, _, runner, registry = stack
    _install(registry, FakeTransport(_profile_response(), _posts_response()))
    report = runner.ingest(_manifest(tmp_path))
    with db.connect() as connection:
        row = connection.execute(
            "SELECT id FROM source_observations WHERE run_id=%s ORDER BY item_index LIMIT 1",
            (report["run_id"],),
        ).fetchone()
    assert runner.replay(str(row["id"]))["status"] == "duplicate"


def test_live_identity_fields_map_profile_and_post_authorship(stack, tmp_path):
    db, _, runner, registry = stack
    profile = json.loads(_profile_response().body)[0]
    profile.update(account_id="synthetic_fixture_account", id="123456789")
    post = json.loads(_posts_response().body)[0]
    post["profile_id"] = "123456789"
    _install(registry, FakeTransport(
        BrightDataHTTPResponse(200, json.dumps([profile]).encode()),
        BrightDataHTTPResponse(200, json.dumps([post]).encode()),
    ))

    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "completed"
    assert report["unresolved"] == 0
    from smi_ingestion.canonical import CanonicalReader
    reader = CanonicalReader(db)
    account_key = ExternalKey("tiktok", "tiktok:public", "account", "123456789")
    assert reader.entity(account_key)["fields"]["handle"]["value"] == "synthetic_fixture_account"
    assert len(reader.metrics(account_key)) == 4
    post_key = ExternalKey("tiktok", "tiktok:public", "content", post["post_id"])
    author = reader.entity(post_key)["fields"]["author_account"]
    assert author["value"]["native_id"] == "123456789"
    assert author["provenance"][0]["locator"] == "$[0].profile_id"
    with db.connect() as connection:
        rows = connection.execute(
            "SELECT coverage FROM source_observations WHERE run_id=%s ORDER BY item_index",
            (report["run_id"],),
        ).fetchall()
    assert rows[1]["coverage"]["corroborated_account_id"] == "123456789"


def test_numeric_handle_is_not_used_instead_of_live_profile_id(stack, tmp_path):
    db, _, runner, registry = stack
    numeric_profile = "https://www.tiktok.com/@123"
    profile = json.loads(_profile_response().body)[0]
    profile.update(account_id="123", id="987654321", url=numeric_profile)
    post = json.loads(_posts_response().body)[0]
    post.update(profile_url=numeric_profile, post_url=numeric_profile + "/video/" + post["post_id"],
                profile_id="987654321")
    _install(registry, FakeTransport(
        BrightDataHTTPResponse(200, json.dumps([profile]).encode()),
        BrightDataHTTPResponse(200, json.dumps([post]).encode()),
    ))
    report = runner.ingest(_manifest(tmp_path, [numeric_profile]))
    assert report["unresolved"] == 0
    with db.connect() as connection:
        accounts = connection.execute(
            "SELECT native_id FROM external_identities WHERE kind='account'"
        ).fetchall()
    assert accounts == [{"native_id": "987654321"}]


def test_conflicting_live_and_legacy_author_ids_reject_post(stack, tmp_path):
    db, _, runner, registry = stack
    post = json.loads(_posts_response().body)[0]
    post.update(author_id="123456789", profile_id="987654321")
    _install(registry, FakeTransport(
        _profile_response(), BrightDataHTTPResponse(200, json.dumps([post]).encode())
    ))
    report = runner.ingest(_manifest(tmp_path))
    assert report["unresolved"] == 1
    with db.connect() as connection:
        contents = connection.execute(
            "SELECT native_id FROM external_identities WHERE kind='content'"
        ).fetchall()
    assert contents == []


def test_missing_stable_identity_does_not_create_account_or_invent_post_owner(stack, tmp_path):
    db, _, runner, registry = stack
    _install(registry, FakeTransport(_profile_response(account_id="synthetic_fixture_account"), _posts_response()))
    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "completed"
    assert report["unresolved"] >= 1
    with db.connect() as connection:
        rows = connection.execute("SELECT kind,native_id FROM external_identities").fetchall()
    assert rows == [{"kind": "content", "native_id": "7553300000000000000"}]


def test_conflicting_author_id_rejects_entire_post_row(stack, tmp_path):
    db, _, runner, registry = stack
    row = json.loads(_posts_response().body)[0]
    row["author_id"] = "987654321"
    _install(registry, FakeTransport(_profile_response(), BrightDataHTTPResponse(
        200, json.dumps([row]).encode()
    )))
    report = runner.ingest(_manifest(tmp_path))
    assert report["unresolved"] >= 1
    with db.connect() as connection:
        rows = connection.execute("SELECT kind,native_id FROM external_identities").fetchall()
    assert rows == [{"kind": "account", "native_id": "123456789"}]


def test_post_url_requires_returned_matching_tiktok_permalink(stack, tmp_path):
    db, _, runner, registry = stack
    _install(registry, FakeTransport(_profile_response(), _posts_response(permalink=None)))
    report = runner.ingest(_manifest(tmp_path))
    assert {item["field"] for item in report["missing_fields"]} >= {"post_url"}
    with db.connect() as connection:
        row = connection.execute(
            "SELECT state,value FROM field_assertions WHERE field='post_url'"
        ).fetchone()
    assert row == {"state": "not_returned", "value": None}

    _install(registry, FakeTransport(_profile_response(), _posts_response(
        permalink=PROFILE + "/photo/7553300000000000000"
    )))
    report = runner.ingest(_manifest(tmp_path))
    with db.connect() as connection:
        row = connection.execute(
            "SELECT value FROM field_assertions f JOIN derivations d ON d.id=f.derivation_id "
            "JOIN source_observations o ON o.id=d.observation_id "
            "WHERE o.run_id=%s AND f.field='post_url'", (report["run_id"],)
        ).fetchone()
    assert row["value"] == PROFILE + "/photo/7553300000000000000"


def test_partial_rows_are_mapped_without_claiming_complete_evidence(stack, tmp_path):
    db, _, runner, registry = stack
    partial = BrightDataHTTPResponse(200, json.dumps([
        json.loads(_posts_response().body)[0], {"error": "synthetic provider error"},
    ]).encode())
    _install(registry, FakeTransport(_profile_response(), partial))
    report = runner.ingest(_manifest(tmp_path))
    assert report["source_results"][1]["outcome"] == "partial_rows"
    assert report["unresolved"] >= 1
    with db.connect() as connection:
        row = connection.execute(
            "SELECT coverage FROM source_observations ORDER BY item_index DESC LIMIT 1"
        ).fetchone()
    assert row["coverage"]["error_rows"] == 1


def test_http_202_persists_snapshot_without_second_paid_post(stack, tmp_path):
    db, _, runner, registry = stack
    transport = FakeTransport(
        BrightDataHTTPResponse(202, b'{"snapshot_id":"synthetic-snapshot"}'),
        BrightDataHTTPResponse(200, b'{"status":"running"}'),
    )
    _install(registry, transport)
    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "partial"
    assert report["requests_used"] == 2
    assert report["source_results"][0]["outcome"] == "pending_snapshot"
    assert report["source_results"][1]["outcome"] == "snapshot_running"
    assert [call[0] for call in transport.calls] == [_DATASETS["profile"], "progress"]
    with db.connect() as connection:
        row = connection.execute("SELECT coverage FROM source_observations ORDER BY item_index LIMIT 1").fetchone()
    assert row["coverage"]["snapshot_id"] == "synthetic-snapshot"


def test_pending_snapshot_resumes_after_cooldown_without_paid_retry(stack, tmp_path):
    _, _, runner, registry = stack
    now = [CAPTURED]
    transport = FakeTransport(
        BrightDataHTTPResponse(202, b'{"snapshot_id":"synthetic-snapshot"}'),
        BrightDataHTTPResponse(200, b'{"status":"running"}'),
        BrightDataHTTPResponse(200, b'{"status":"ready"}'),
        _profile_response(), _posts_response(),
    )
    registry._adapters["brightdata-tiktok"] = (
        BrightDataTikTokCollector(transport, lambda: now[0], lambda: "synthetic-test-token"),
        BrightDataTikTokMapper(),
    )
    first = runner.ingest(_manifest(tmp_path))
    assert first["status"] == "partial"
    assert first["requests_used"] == 2
    now[0] += timedelta(seconds=31)
    resumed = runner.resume(first["run_id"])
    assert resumed["status"] == "completed"
    assert resumed["requests_used"] == 5
    assert [call[0] for call in transport.calls] == [
        _DATASETS["profile"], "progress", "progress", "snapshot", _DATASETS["posts"]
    ]


def test_transport_failure_is_counted_once_and_never_retried(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(URLError("synthetic timeout"))
    _install(registry, transport)
    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "partial"
    assert report["requests_used"] == 1
    assert report["source_results"][0]["outcome"] == "source_error"
    assert len(transport.calls) == 1


def test_six_paid_calls_are_hard_cap_for_three_profiles(stack, tmp_path):
    _, _, runner, registry = stack
    refs = [f"https://www.tiktok.com/@synthetic_creator_{i}" for i in range(3)]
    responses = []
    for ref in refs:
        responses.extend((
            BrightDataHTTPResponse(200, json.dumps([{"account_id": "123", "url": ref}]).encode()),
            BrightDataHTTPResponse(200, json.dumps([{"post_id": "456", "profile_url": ref}]).encode()),
        ))
    transport = FakeTransport(*responses)
    _install(registry, transport)
    report = runner.ingest(_manifest(tmp_path, refs), RunLimits(max_requests=20))
    assert report["status"] == "completed"
    assert report["requests_used"] == report["observations"] == 6
    assert len(transport.calls) == 6


def test_request_limit_prevents_second_paid_call(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(_profile_response())
    _install(registry, transport)
    report = runner.ingest(_manifest(tmp_path), RunLimits(max_requests=1))
    assert report["status"] == "partial"
    assert report["requests_used"] == 1
    assert report["issues"][0]["code"] == "request_limit_reached"
    assert len(transport.calls) == 1


def test_payment_required_stops_before_posts_scrape(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(BrightDataHTTPResponse(402, b""))
    _install(registry, transport)
    report = runner.ingest(_manifest(tmp_path))
    assert report["status"] == "partial"
    assert report["source_results"][0]["outcome"] == "payment_required"
    assert report["requests_used"] == 1
    assert len(transport.calls) == 1


def test_transport_enforces_bytes_without_exposing_credential(monkeypatch):
    class Headers:
        def get_content_type(self):
            return "application/json"

    class Response:
        status = 200
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def geturl(self):
            return "https://api.brightdata.com/datasets/v3/scrape"

        def read(self, size):
            return b"x" * size

    monkeypatch.setattr("smi_ingestion.adapters.bright_data.open_no_redirect", lambda request, timeout: Response())
    with pytest.raises(EvidenceError, match="response_too_large") as captured:
        BrightDataTransport().fetch(_DATASETS["profile"], PROFILE, 10, "SECRET_SENTINEL", 10)
    assert "SECRET_SENTINEL" not in str(captured.value)


def test_transport_uses_documented_dataset_and_post_count_without_leaking_token(monkeypatch):
    class Headers:
        def get_content_type(self):
            return "text/plain"

    class Response:
        status = 200
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def geturl(self):
            return "https://api.brightdata.com/datasets/v3/scrape"

        def read(self, size):
            return b"[]"

    observed = {}

    def fake_open(request, timeout):
        observed["request"] = request
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr("smi_ingestion.adapters.bright_data.open_no_redirect", fake_open)
    result = BrightDataTransport().fetch(_DATASETS["posts"], PROFILE, 7, "SECRET_SENTINEL", 100)
    request = observed["request"]
    assert result == BrightDataHTTPResponse(200, b"[]")
    assert request.get_method() == "POST"
    assert "dataset_id=" + _DATASETS["posts"] in request.full_url
    assert "SECRET_SENTINEL" not in request.full_url
    assert json.loads(request.data) == [{"url": PROFILE, "num_of_posts": 7}]
    assert request.get_header("Authorization") == "Bearer SECRET_SENTINEL"
    assert observed["timeout"] == 65
