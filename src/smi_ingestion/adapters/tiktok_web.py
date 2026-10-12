"""Bounded, direct public-page experiment for supplied TikTok references.

The page schema is not a stable API. A challenge or missing post history is an
explicit source outcome, never evidence that the creator has no posts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from ..contracts import (
    CollectedBatch, ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch,
    ObservationDraft, RawObservation, RunLimits, SourcePolicy, SourceReference,
    UnresolvedCandidate,
)
from ..evidence import EvidenceError


_HANDLE = re.compile(r"[A-Za-z0-9._]{1,64}")
_VIDEO_ID = re.compile(r"[0-9]{1,30}")
_POST_METRICS = {
    "playCount": "views", "diggCount": "likes", "commentCount": "comments",
    "shareCount": "shares", "collectCount": "saves",
}
_CORE_METRICS = ("playCount", "diggCount", "commentCount", "shareCount")
_WAF_MARKERS = (b"slardarwaf", b"waf-aiso", b"id=\"place_hold\"", b"please wait...")
_MAX_RESPONSE_BYTES = 1_048_576
_MAX_REFERENCES = 10
_MAX_ATTEMPTS = 10


def _reference(value: str) -> SourceReference:
    """Canonicalize a direct HTTPS profile/post URL, excluding redirects and embeds."""
    if not isinstance(value, str) or len(value) > 2048:
        raise EvidenceError("invalid_tiktok_reference")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise EvidenceError("invalid_tiktok_reference") from error
    if (parsed.scheme != "https" or parsed.hostname not in {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}
            or parsed.username or parsed.password or port is not None):
        raise EvidenceError("invalid_tiktok_reference")
    parts = parsed.path.strip("/").split("/")
    if not parts or not parts[0].startswith("@"):
        raise EvidenceError("invalid_tiktok_reference")
    handle = unquote(parts[0][1:])
    if not _HANDLE.fullmatch(handle):
        raise EvidenceError("invalid_tiktok_reference")
    base = f"https://www.tiktok.com/@{handle}"
    if len(parts) == 1:
        return SourceReference(base, "tiktok", "profile", None, handle)
    if len(parts) == 3 and parts[1] == "video" and _VIDEO_ID.fullmatch(parts[2]):
        return SourceReference(f"{base}/video/{parts[2]}", "tiktok", "video", parts[2], handle)
    raise EvidenceError("invalid_tiktok_reference")


def _returned_permalink(value: Any, expected_id: str) -> str | None:
    """Accept a source-returned video/photo link only when its ID corroborates the item."""
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (parsed.scheme != "https" or parsed.hostname not in {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}
            or parsed.username or parsed.password or port is not None):
        return None
    parts = parsed.path.strip("/").split("/")
    if (len(parts) != 3 or not parts[0].startswith("@") or parts[1] not in {"video", "photo"}
            or parts[2] != expected_id or not _VIDEO_ID.fullmatch(parts[2])):
        return None
    handle = unquote(parts[0][1:])
    if not _HANDLE.fullmatch(handle):
        return None
    return f"https://www.tiktok.com/@{handle}/{parts[1]}/{expected_id}"


@dataclass(frozen=True)
class WebHTTPResponse:
    status: int
    body: bytes
    content_type: str = "text/html"


class TikTokWebTransport:
    """Fetch one supplied public URL with a fixed timeout and response byte cap."""

    timeout_seconds = 8

    def fetch(self, reference_url: str, max_bytes: int) -> WebHTTPResponse:
        request = Request(reference_url, headers={
            "Accept": "text/html", "User-Agent": "smi-ingestion/0.1",
        })
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                # A redirect to a login, CDN, or different creator is not the
                # page the caller asked to inspect.
                if _reference(response.geturl()).original != reference_url:
                    raise EvidenceError("unexpected_source_redirect")
                content_type = response.headers.get_content_type()
                if content_type != "text/html":
                    raise EvidenceError("invalid_source_content_type")
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise EvidenceError("response_too_large")
                return WebHTTPResponse(response.status, body, content_type)
        except HTTPError as error:
            return WebHTTPResponse(error.code, b"")


class _EmbeddedJSON(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self.parts: list[str] = []
        self.value: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and dict(attrs).get("id") == "__UNIVERSAL_DATA_FOR_REHYDRATION__":
            self.active = True

    def handle_data(self, data: str) -> None:
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.active:
            self.value = "".join(self.parts)
            self.parts.clear()
            self.active = False


def _scope(body: bytes) -> dict[str, Any] | None:
    parser = _EmbeddedJSON()
    parser.feed(body.decode("utf-8", "replace"))
    if parser.value is None:
        return None
    data = json.loads(parser.value)
    scope = data.get("__DEFAULT_SCOPE__") if isinstance(data, dict) else None
    if not isinstance(scope, dict):
        raise ValueError("invalid_embedded_scope")
    return scope


def _is_nonnegative_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_timestamp(value: Any) -> bool:
    return isinstance(value, str) and value.isdigit() and 0 < int(value) <= 4_102_444_800


def _post_permalink(item: dict[str, Any], post_id: str) -> str | None:
    returned_url = item.get("shareUrl")
    share_info = item.get("shareInfo")
    if returned_url is None and isinstance(share_info, dict):
        returned_url = share_info.get("shareUrl")
    return _returned_permalink(returned_url, post_id)


def _posts(scope: dict[str, Any]) -> list[dict[str, Any]]:
    """Read only the observed embedded profile post list, never infer one."""
    block = scope.get("webapp.user-post")
    if not isinstance(block, dict):
        return []
    items = block.get("itemList")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _classify(reference: SourceReference, response: WebHTTPResponse | None) -> tuple[str, int]:
    if response is None:
        return "source_error", 0
    if response.status in {404, 410}:
        return "unavailable_or_private", 0
    if response.status in {403, 401}:
        return "challenge", 0
    if response.status == 429:
        return "rate_limited", 0
    if response.status != 200:
        return "source_error", 0
    if any(marker in response.body.lower() for marker in _WAF_MARKERS):
        return "challenge", 0
    try:
        scope = _scope(response.body)
    except (ValueError, UnicodeError, json.JSONDecodeError):
        return "invalid_response", 0
    if scope is None:
        return "partial_result", 0
    if reference.resource_kind == "video":
        detail = scope.get("webapp.video-detail")
        if not isinstance(detail, dict):
            return "partial_result", 0
        if detail.get("statusCode") not in {None, 0}:
            return "unavailable_or_private", 0
        item = detail.get("itemInfo", {}).get("itemStruct") if isinstance(detail.get("itemInfo"), dict) else None
        if not isinstance(item, dict) or item.get("id") != reference.native_id_hint:
            return "invalid_response", 0
        author = item.get("author")
        stats = item.get("stats")
        sufficient = (
            isinstance(author, dict) and isinstance(author.get("id"), str)
            and _valid_timestamp(item.get("createTime"))
            and isinstance(item.get("desc"), str)
            and isinstance(stats, dict)
            and all(_is_nonnegative_count(stats.get(name)) for name in _CORE_METRICS)
        )
        return ("resolved" if sufficient else "partial_result"), 1
    detail = scope.get("webapp.user-detail")
    info = detail.get("userInfo") if isinstance(detail, dict) else None
    user = info.get("user") if isinstance(info, dict) else None
    if isinstance(detail, dict) and detail.get("statusCode") not in {None, 0}:
        return "unavailable_or_private", 0
    if not isinstance(user, dict) or not isinstance(user.get("id"), str):
        return "partial_result", 0
    posts = _posts(scope)
    identified = {
        post["id"] for post in posts
        if isinstance(post.get("id"), str) and _VIDEO_ID.fullmatch(post["id"])
    }
    complete = {
        post["id"] for post in posts
        if isinstance(post.get("id"), str)
        and _VIDEO_ID.fullmatch(post["id"])
        and _post_permalink(post, post["id"]) is not None
        and isinstance(post.get("author"), dict)
        and post["author"].get("id") == user["id"]
        and isinstance(post.get("desc"), str)
        and _valid_timestamp(post.get("createTime"))
        and isinstance(post.get("stats"), dict)
        and all(_is_nonnegative_count(post["stats"].get(name)) for name in _CORE_METRICS)
    }
    return ("resolved" if len(complete) >= 10 else "partial_result"), len(identified)


class TikTokWebCollector:
    """Inspect at most ten direct references and ten total HTTP attempts per run."""

    adapter_id = "tiktok-web"
    provider_id = "tiktok-web-public-page"
    format_version = "embedded-html-v1"

    def __init__(
        self, transport: TikTokWebTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.transport = transport or TikTokWebTransport()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _references(manifest: dict[str, Any]) -> tuple[SourceReference, ...]:
        if manifest.get("synthetic") or "policy" in manifest:
            raise EvidenceError("web_policy_is_fixed")
        values = manifest.get("references")
        if not isinstance(values, list) or not 1 <= len(values) <= _MAX_REFERENCES:
            raise EvidenceError("invalid_reference_count")
        references = tuple(_reference(value) for value in values)
        if len({ref.original for ref in references}) != len(references):
            raise EvidenceError("duplicate_tiktok_reference")
        return references

    def collect(
        self, manifest: dict[str, Any], checkpoint: dict[str, Any], limits: RunLimits
    ) -> CollectedBatch:
        references = self._references(manifest)
        index = checkpoint.get("index", 0)
        attempts_used = checkpoint.get("http_attempts_used", 0)
        if (not isinstance(index, int) or isinstance(index, bool) or not 0 <= index <= len(references)
                or not isinstance(attempts_used, int) or isinstance(attempts_used, bool)
                or not 0 <= attempts_used <= _MAX_ATTEMPTS):
            raise EvidenceError("invalid_checkpoint")
        if checkpoint.get("halted"):
            return CollectedBatch((), checkpoint, False)
        if index == len(references):
            return CollectedBatch((), {"index": index}, True)
        attempt_budget = min(2, limits.max_requests, _MAX_ATTEMPTS - attempts_used)
        if attempt_budget < 1:
            raise EvidenceError("request_limit_reached")
        reference = references[index]
        attempts = 0
        response: WebHTTPResponse | None = None
        outcome = "source_error"
        posts_observed = 0
        while attempts < attempt_budget:
            attempts += 1
            try:
                response = self.transport.fetch(reference.original, min(limits.max_bytes, _MAX_RESPONSE_BYTES))
            except EvidenceError as error:
                outcome = "oversized_response" if error.code == "response_too_large" else "invalid_response"
                break
            except (TimeoutError, URLError, OSError):
                if attempts < attempt_budget:
                    continue
                break
            if 500 <= response.status <= 599 and attempts < attempt_budget:
                continue
            outcome, posts_observed = _classify(reference, response)
            break
        if response is not None and outcome == "source_error" and 500 <= response.status <= 599:
            response = WebHTTPResponse(response.status, b"")
        captured_at = self.clock()
        if captured_at.tzinfo is None:
            raise EvidenceError("timestamp_requires_timezone")
        halted = outcome in {"challenge", "rate_limited", "source_error", "oversized_response", "invalid_response"}
        draft = ObservationDraft(
            source_item_key=reference.original,
            adapter_id=self.adapter_id,
            provider_id=self.provider_id,
            format_version=self.format_version,
            reference=reference,
            payload=response.body if response and outcome in {"resolved", "partial_result"} else b"",
            media_type="text/html",
            captured_at=captured_at,
            source_as_of=None,
            # Public-page collection is an experiment, so keep source HTML transient.
            policy=SourcePolicy("tiktok-web-local-experiment", True, False, True),
            synthetic=False,
            coverage={
                "requested_input": 1, "outcome": outcome,
                "http_status": response.status if response else None,
                "http_attempts": attempts,
                "posts_observed": posts_observed,
                "unavailable_fields": (["comparison_grade_post_history"] if reference.resource_kind == "profile" and outcome != "resolved" else []),
                "truncated": False,
            },
            request_attempts=attempts,
        )
        next_checkpoint = {
            "index": index + 1, "http_attempts_used": attempts_used + attempts,
            "halted": halted,
        }
        return CollectedBatch((draft,), next_checkpoint, not halted and index + 1 == len(references))


class TikTokWebMapper:
    """Map corroborated embedded IDs and visible public counts into source-specific evidence."""

    version = "v1"
    supported_format = "embedded-html-v1"

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        if (observation.format_version != self.supported_format or observation.synthetic
                or observation.policy.can_retain):
            raise ValueError("unsupported_web_observation")
        if observation.coverage.get("outcome") not in {"resolved", "partial_result"}:
            return NormalizedBatch((), (), ())
        scope = _scope(payload)
        if scope is None:
            return NormalizedBatch((), (), (), unresolved=(
                UnresolvedCandidate(observation.reference.resource_kind or "account", "$", "embedded_data_missing"),
            ))
        if observation.reference.resource_kind == "video":
            detail = scope.get("webapp.video-detail")
            item_info = detail.get("itemInfo") if isinstance(detail, dict) else None
            item = item_info.get("itemStruct") if isinstance(item_info, dict) else None
            if not isinstance(item, dict) or item.get("id") != observation.reference.native_id_hint:
                raise ValueError("video_id_mismatch")
            return _normalize_items(observation, (item,), None)
        detail = scope.get("webapp.user-detail")
        info = detail.get("userInfo") if isinstance(detail, dict) else None
        user = info.get("user") if isinstance(info, dict) else None
        if not isinstance(user, dict) or not isinstance(user.get("id"), str):
            return NormalizedBatch((), (), (), unresolved=(
                UnresolvedCandidate("account", "$.webapp.user-detail.userInfo.user.id", "stable_id_missing"),
            ))
        return _normalize_items(observation, tuple(_posts(scope)), user)


def _normalize_items(
    observation: RawObservation, items: tuple[dict[str, Any], ...], user: dict[str, Any] | None,
) -> NormalizedBatch:
    namespace = "web:public"
    entities: list[ExternalKey] = []
    fields: list[FieldCandidate] = []
    metrics: list[MetricCandidate] = []
    unresolved: list[UnresolvedCandidate] = []
    seen_post_ids: set[str] = set()
    account_id = user.get("id") if user else None
    if isinstance(account_id, str) and account_id:
        account = ExternalKey("tiktok", namespace, "account", account_id)
        entities.append(account)
        handle = user.get("uniqueId")
        if isinstance(handle, str):
            fields.append(FieldCandidate(account, "handle", "observed", handle, "$.webapp.user-detail.userInfo.user.uniqueId"))
    else:
        account = None
    for index, item in enumerate(items):
        locator = (
            "$.webapp.video-detail.itemInfo.itemStruct"
            if observation.reference.resource_kind == "video"
            else f"$.webapp.user-post.itemList[{index}]"
        )
        post_id = item.get("id")
        if not isinstance(post_id, str) or not _VIDEO_ID.fullmatch(post_id):
            unresolved.append(UnresolvedCandidate("content", locator + ".id", "stable_id_missing"))
            continue
        if post_id in seen_post_ids:
            unresolved.append(UnresolvedCandidate("content", locator + ".id", "duplicate_post_id"))
            continue
        seen_post_ids.add(post_id)
        if observation.reference.resource_kind == "video" and post_id != observation.reference.native_id_hint:
            raise ValueError("video_id_mismatch")
        author = item.get("author")
        author_id = author.get("id") if isinstance(author, dict) else None
        if account and author_id != account_id:
            unresolved.append(UnresolvedCandidate("content", locator + ".author.id", "author_identity_mismatch"))
            continue
        if account is None and isinstance(author_id, str) and author_id:
            account = ExternalKey("tiktok", namespace, "account", author_id)
            entities.append(account)
            author_handle = author.get("uniqueId")
            if isinstance(author_handle, str):
                fields.append(FieldCandidate(account, "handle", "observed", author_handle, locator + ".author.uniqueId"))
        elif account is None:
            unresolved.append(UnresolvedCandidate("account", locator + ".author.id", "stable_id_missing"))
        post = ExternalKey("tiktok", namespace, "content", post_id)
        entities.append(post)
        if account:
            fields.append(FieldCandidate(post, "author_account", "observed", account.__dict__, locator + ".author.id"))
        caption = item.get("desc")
        if isinstance(caption, str):
            fields.append(FieldCandidate(post, "caption", "observed", caption, locator + ".desc"))
        timestamp = item.get("createTime")
        if _valid_timestamp(timestamp):
            published_at = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
            fields.append(FieldCandidate(post, "published_at", "observed", published_at, locator + ".createTime"))
        if observation.reference.resource_kind == "video":
            fields.append(FieldCandidate(post, "url", "observed", observation.reference.original, "$.requested_reference"))
        else:
            permalink = _post_permalink(item, post_id)
            fields.append(FieldCandidate(
                post, "url", "observed" if permalink else "not_returned", permalink,
                locator + (".shareUrl" if item.get("shareUrl") is not None else ".shareInfo.shareUrl"),
            ))
        stats = item.get("stats")
        if isinstance(stats, dict):
            for native_name, definition in _POST_METRICS.items():
                value = stats.get(native_name)
                if _is_nonnegative_count(value):
                    metrics.append(MetricCandidate(
                        post, f"tiktok.web.{definition}.v1", native_name, value,
                        str(value), "exact", "count", observation.captured_at,
                        locator + ".stats." + native_name,
                    ))
    if observation.reference.resource_kind == "profile" and observation.coverage.get("outcome") == "partial_result":
        reason = (
            "insufficient_recent_posts" if observation.coverage.get("posts_observed", 0) < 10
            else "incomplete_recent_post_evidence"
        )
        unresolved.append(UnresolvedCandidate("content", "$.webapp.user-post.itemList", reason))
    return NormalizedBatch(tuple(dict.fromkeys(entities)), tuple(fields), tuple(metrics), unresolved=tuple(unresolved))
