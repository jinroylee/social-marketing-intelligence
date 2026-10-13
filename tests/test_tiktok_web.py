from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.error import URLError

import pytest

from smi_ingestion.adapters.tiktok_web import (
    TikTokWebCollector, TikTokWebMapper, TikTokWebTransport,
    WebHTTPResponse, _classify, _reference, _scope,
)
from smi_ingestion.contracts import RawObservation, RunLimits
from smi_ingestion.evidence import EvidenceError


PROFILE = "https://www.tiktok.com/@example_creator"
VIDEO = PROFILE + "/video/1234567890"
CAPTURED = datetime(2026, 9, 30, 9, tzinfo=timezone.utc)


def _page(scope: dict) -> WebHTTPResponse:
    embedded = json.dumps({"__DEFAULT_SCOPE__": scope})
    return WebHTTPResponse(200, (
        '<!doctype html><script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" '
        'type="application/json">' + embedded + "</script>"
    ).encode())


def _item(post_id: str = "1234567890", account_id: str = "stable-creator-id") -> dict:
    return {
        "id": post_id, "desc": "A public caption", "createTime": "1780233600",
        "author": {"id": account_id, "uniqueId": "example_creator"},
        "stats": {"playCount": 101, "diggCount": 12, "commentCount": 3,
                  "shareCount": 4, "collectCount": 5},
    }


def _video_page(item: dict | None = None) -> WebHTTPResponse:
    return _page({"webapp.video-detail": {
        "statusCode": 0, "itemInfo": {"itemStruct": item or _item()},
    }})


def _profile_page(count: int, *, permalinks: bool = False) -> WebHTTPResponse:
    items = [_item(str(1000000000 + n)) for n in range(count)]
    if permalinks:
        for item in items:
            item["shareUrl"] = f"{PROFILE}/video/{item['id']}"
    return _page({
        "webapp.user-detail": {"statusCode": 0, "userInfo": {
            "user": {"id": "stable-creator-id", "uniqueId": "example_creator"},
            "stats": {"followerCount": 42},
        }},
        "webapp.user-post": {"itemList": items},
    })


class FakeTransport:
    def __init__(self, *responses: WebHTTPResponse | Exception):
        self.responses = iter(responses)
        self.calls: list[tuple[str, int]] = []

    def fetch(self, reference_url: str, max_bytes: int) -> WebHTTPResponse:
        self.calls.append((reference_url, max_bytes))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def _observe(draft) -> RawObservation:
    return RawObservation(
        id="obs", run_id="run", source_item_key=draft.source_item_key,
        adapter_id=draft.adapter_id, provider_id=draft.provider_id,
        format_version=draft.format_version, reference=draft.reference,
        media_type=draft.media_type, captured_at=draft.captured_at,
        source_as_of=draft.source_as_of, ingested_at=CAPTURED,
        policy=draft.policy, synthetic=draft.synthetic, payload_hash="hash",
        payload_path=None, coverage=draft.coverage,
    )


def test_rejects_non_direct_or_unsafe_urls_before_network():
    assert _reference(VIDEO + "?lang=ja").original == VIDEO
    assert _reference(PROFILE).resource_kind == "profile"
    for invalid in (
        "http://www.tiktok.com/@example_creator",
        "https://tiktok.com.evil.invalid/@example_creator",
        "https://www.tiktok.com:444/@example_creator",
        "https://www.tiktok.com/@example_creator/video/not-a-number",
        "https://www.tiktok.com/@example_creator/live",
        "https://www.tiktok.com/%40example_creator%2Fvideo%2F1234567890",
    ):
        with pytest.raises(EvidenceError, match="invalid_tiktok_reference"):
            _reference(invalid)
    transport = FakeTransport()
    with pytest.raises(EvidenceError, match="invalid_tiktok_reference"):
        TikTokWebCollector(transport).collect({"references": ["https://evil.invalid/@x"]}, {}, RunLimits())
    assert transport.calls == []


def test_challenge_is_distinguished_from_success_and_not_retried():
    challenge = WebHTTPResponse(200, b'<html><p id="place_hold">Please wait...</p><script src="/waf-aiso/a.js"></script></html>')
    transport = FakeTransport(challenge)
    batch = TikTokWebCollector(transport, lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits(max_requests=20)
    )
    draft = batch.items[0]
    assert draft.coverage["outcome"] == "challenge"
    assert draft.coverage["posts_observed"] == 0
    assert draft.payload == b""
    assert draft.request_attempts == 1
    assert batch.complete is False
    assert len(transport.calls) == 1


def test_challenge_at_request_limit_does_not_add_limit_issue(stack, tmp_path):
    _, _, runner, registry = stack
    transport = FakeTransport(
        _video_page(),
        WebHTTPResponse(200, b'<html><p id="place_hold">Please wait...</p></html>'),
    )
    registry._adapters["tiktok-web"] = (
        TikTokWebCollector(transport, lambda: CAPTURED), TikTokWebMapper(),
    )
    manifest = tmp_path / "web.json"
    manifest.write_text(json.dumps({"adapter": "tiktok-web", "references": [VIDEO, PROFILE]}))
    report = runner.ingest(manifest, RunLimits(max_requests=2))
    assert report["status"] == "partial"
    assert report["requests_used"] == 2
    assert [item["outcome"] for item in report["source_results"]] == ["resolved", "challenge"]
    assert report["issues"] == []


def test_video_embedded_id_date_caption_and_counts_map_to_one_post():
    transport = FakeTransport(_video_page())
    draft = TikTokWebCollector(transport, lambda: CAPTURED).collect(
        {"references": [VIDEO]}, {}, RunLimits(max_bytes=1_048_576)
    ).items[0]
    assert draft.coverage["outcome"] == "resolved"
    assert draft.coverage["posts_observed"] == 1
    assert draft.policy.can_retain is False
    assert draft.policy.can_display is True
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert {(key.kind, key.native_id) for key in mapped.entities} == {
        ("account", "stable-creator-id"), ("content", "1234567890"),
    }
    assert {field.field: field.value for field in mapped.fields if field.subject.kind == "content"} == {
        "author_account": {"platform": "tiktok", "namespace": "web:public", "kind": "account", "native_id": "stable-creator-id"},
        "caption": "A public caption", "published_at": "2026-05-31T13:20:00+00:00",
        "url": VIDEO,
    }
    assert {metric.native_name: metric.value for metric in mapped.metrics} == {
        "playCount": 101, "diggCount": 12, "commentCount": 3,
        "shareCount": 4, "collectCount": 5,
    }
    assert all(metric.measured_at == CAPTURED for metric in mapped.metrics)


def test_profile_with_fewer_than_ten_posts_is_explicitly_partial():
    draft = TikTokWebCollector(FakeTransport(_profile_page(3)), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits(max_bytes=1_048_576)
    ).items[0]
    assert draft.coverage["outcome"] == "partial_result"
    assert draft.coverage["posts_observed"] == 3
    assert draft.coverage["unavailable_fields"] == ["comparison_grade_post_history"]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert len([entity for entity in mapped.entities if entity.kind == "content"]) == 3
    assert len([metric for metric in mapped.metrics if metric.native_name == "playCount"]) == 3
    assert all(field.state == "not_returned" for field in mapped.fields if field.field == "url")
    assert any(candidate.reason == "insufficient_recent_posts" for candidate in mapped.unresolved)


def test_profile_ten_post_threshold_requires_actual_embedded_post_ids():
    page = _profile_page(10, permalinks=True)
    assert _classify(_reference(PROFILE), page) == ("resolved", 10)
    draft = TikTokWebCollector(FakeTransport(page), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits(max_bytes=1_048_576)
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert len([key for key in mapped.entities if key.kind == "content"]) == 10
    assert not mapped.unresolved


def test_saves_are_optional_but_all_four_core_counts_are_required():
    item = _item()
    item["stats"].pop("collectCount")
    without_saves = _video_page(item)
    assert _classify(_reference(VIDEO), without_saves) == ("resolved", 1)
    draft = TikTokWebCollector(FakeTransport(without_saves), lambda: CAPTURED).collect(
        {"references": [VIDEO]}, {}, RunLimits()
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert {metric.native_name for metric in mapped.metrics} == {
        "playCount", "diggCount", "commentCount", "shareCount",
    }
    for core_name in ("playCount", "diggCount", "commentCount", "shareCount"):
        missing_core = _item()
        missing_core["stats"].pop(core_name)
        assert _classify(_reference(VIDEO), _video_page(missing_core)) == ("partial_result", 1)


def test_profile_post_url_requires_returned_matching_permalink():
    page = _profile_page(1)
    scope = _scope(page.body)
    assert scope is not None
    item = scope["webapp.user-post"]["itemList"][0]
    item["shareUrl"] = "https://www.tiktok.com/@example_creator/photo/1000000000?lang=ja"
    draft = TikTokWebCollector(FakeTransport(_page(scope)), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits()
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    urls = [field for field in mapped.fields if field.field == "url"]
    assert len(urls) == 1
    assert urls[0].value == "https://www.tiktok.com/@example_creator/photo/1000000000"
    item["shareUrl"] = "https://www.tiktok.com/@example_creator/video/9999999999"
    draft = TikTokWebCollector(FakeTransport(_page(scope)), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits()
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert [field.state for field in mapped.fields if field.field == "url"] == ["not_returned"]


def test_ten_ids_with_missing_counts_or_wrong_author_are_not_comparison_grade():
    page = _profile_page(10, permalinks=True)
    scope = _scope(page.body)
    assert scope is not None
    scope["webapp.user-post"]["itemList"][0]["stats"].pop("playCount")
    scope["webapp.user-post"]["itemList"][1]["author"]["id"] = "unrelated-creator"
    partial = _page(scope)
    assert _classify(_reference(PROFILE), partial) == ("partial_result", 10)
    draft = TikTokWebCollector(FakeTransport(partial), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits(max_bytes=1_048_576)
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert len([key for key in mapped.entities if key.kind == "content"]) == 9
    assert any(candidate.reason == "author_identity_mismatch" for candidate in mapped.unresolved)


def test_invalid_profile_rows_preserve_original_source_indices():
    scope = _scope(_profile_page(1, permalinks=True).body)
    scope["webapp.user-post"]["itemList"].insert(0, None)
    draft = TikTokWebCollector(FakeTransport(_page(scope)), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits()
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    caption = next(field for field in mapped.fields if field.field == "caption")
    assert caption.locator == "$.webapp.user-post.itemList[1].desc"
    assert all(metric.locator.startswith("$.webapp.user-post.itemList[1].")
               for metric in mapped.metrics)


@pytest.mark.parametrize("invalid", [False, True])
def test_missing_or_invalid_web_fields_are_reported(stack, tmp_path, invalid):
    _, _, runner, registry = stack
    item = _item()
    for container, name in ((item, "desc"), (item, "createTime"), (item["stats"], "shareCount")):
        if invalid:
            container[name] = []
        else:
            container.pop(name)
    registry._adapters["tiktok-web"] = (
        TikTokWebCollector(FakeTransport(_video_page(item)), lambda: CAPTURED), TikTokWebMapper(),
    )
    manifest = tmp_path / "web.json"
    manifest.write_text(json.dumps({"adapter": "tiktok-web", "references": [VIDEO]}))
    result = runner.ingest(manifest)
    assert result["status"] == "partial"
    assert result["missing_fields"] == [
        {"field": field, "state": "unavailable" if invalid else "not_returned", "count": 1}
        for field in ("caption", "metric:shares", "published_at")
    ]


def test_ten_posts_without_urls_or_with_duplicate_ids_do_not_resolve():
    without_urls = _profile_page(10)
    assert _classify(_reference(PROFILE), without_urls) == ("partial_result", 10)
    draft = TikTokWebCollector(FakeTransport(without_urls), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits()
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert any(candidate.reason == "incomplete_recent_post_evidence" for candidate in mapped.unresolved)
    scope = _scope(_profile_page(10, permalinks=True).body)
    assert scope is not None
    posts = scope["webapp.user-post"]["itemList"]
    posts[9] = dict(posts[8])
    duplicate = _page(scope)
    assert _classify(_reference(PROFILE), duplicate) == ("partial_result", 9)
    draft = TikTokWebCollector(FakeTransport(duplicate), lambda: CAPTURED).collect(
        {"references": [PROFILE]}, {}, RunLimits()
    ).items[0]
    mapped = TikTokWebMapper().normalize(_observe(draft), draft.payload)
    assert len([key for key in mapped.entities if key.kind == "content"]) == 9
    assert any(candidate.reason == "duplicate_post_id" for candidate in mapped.unresolved)


def test_video_requires_valid_publication_time_for_resolved_outcome():
    for bad_time in ("invalid", "0", "999999999999999999"):
        item = _item()
        item["createTime"] = bad_time
        assert _classify(_reference(VIDEO), _video_page(item)) == ("partial_result", 1)


def test_mismatched_post_id_never_creates_canonical_content():
    mismatched = _video_page(_item("9999999999"))
    draft = TikTokWebCollector(FakeTransport(mismatched), lambda: CAPTURED).collect(
        {"references": [VIDEO]}, {}, RunLimits()
    ).items[0]
    assert draft.coverage["outcome"] == "invalid_response"
    assert draft.payload == b""
    assert draft.coverage["posts_observed"] == 0


def test_transport_enforces_response_byte_limit_and_redirect(monkeypatch):
    class Headers:
        def get_content_type(self):
            return "text/html"

    class Response:
        status = 200
        headers = Headers()

        def __init__(self, final_url=PROFILE):
            self.final_url = final_url

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def geturl(self):
            return self.final_url

        def read(self, size):
            return b"x" * size

    monkeypatch.setattr("smi_ingestion.adapters.tiktok_web.open_no_redirect", lambda request, timeout: Response())
    with pytest.raises(EvidenceError, match="response_too_large"):
        TikTokWebTransport().fetch(PROFILE, 10)
    monkeypatch.setattr("smi_ingestion.adapters.tiktok_web.open_no_redirect", lambda request, timeout: Response(VIDEO))
    with pytest.raises(EvidenceError, match="unexpected_source_redirect"):
        TikTokWebTransport().fetch(PROFILE, 10)


def test_retries_only_transient_error_within_hard_run_request_cap():
    transport = FakeTransport(URLError("timeout"), _video_page())
    collector = TikTokWebCollector(transport, lambda: CAPTURED)
    batch = collector.collect({"references": [VIDEO]}, {}, RunLimits(max_requests=20))
    assert batch.items[0].request_attempts == 2
    assert batch.next_checkpoint["http_attempts_used"] == 2
    with pytest.raises(EvidenceError, match="request_limit_reached"):
        collector.collect({"references": [VIDEO]}, {"index": 0, "http_attempts_used": 10}, RunLimits(max_requests=20))
    assert len(transport.calls) == 2
