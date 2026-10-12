"""Bounded Bright Data TikTok profile and recent-post collection for a local prototype.

The provider's response shape and Japan coverage require a live sample. This adapter
accepts only supplied profile URLs and never retries a paid scrape request.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..contracts import (
    CollectedBatch, ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch,
    ObservationDraft, RawObservation, RunLimits, SourcePolicy, SourceReference,
    UnresolvedCandidate,
)
from ..evidence import EvidenceError


_HANDLE = re.compile(r"[A-Za-z0-9._]{1,64}")
_NATIVE_ID = re.compile(r"[0-9]{1,30}")
_DATASETS = {
    "profile": "gd_l1villgoiiidt09ci",
    "posts": "gd_m7n5v2gq296pex2f5m",
}
_MAX_PROFILES = 3
_MAX_POSTS = 10
_MAX_PAID_REQUESTS = 2 * _MAX_PROFILES
_MAX_HTTP_REQUESTS = 4 * _MAX_PAID_REQUESTS
_MAX_RESPONSE_BYTES = 262_144
_SNAPSHOT_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_ERROR_CODE = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_POLICY = SourcePolicy("brightdata-unpublished-local-prototype-unverified", True, True, True)


def _profile_reference(value: str) -> SourceReference:
    """Canonicalize a supplied direct HTTPS profile URL without trusting its handle as identity."""
    if not isinstance(value, str) or len(value) > 2048:
        raise EvidenceError("invalid_tiktok_profile_reference")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise EvidenceError("invalid_tiktok_profile_reference") from error
    if (parsed.scheme != "https" or parsed.hostname not in {
        "tiktok.com", "www.tiktok.com", "m.tiktok.com"
    } or parsed.username or parsed.password or port is not None or parsed.fragment):
        raise EvidenceError("invalid_tiktok_profile_reference")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 1 or not parts[0].startswith("@") or not _HANDLE.fullmatch(parts[0][1:]):
        raise EvidenceError("invalid_tiktok_profile_reference")
    handle = parts[0][1:]
    return SourceReference(f"https://www.tiktok.com/@{handle}", "tiktok", "profile", None, handle)


@dataclass(frozen=True)
class BrightDataHTTPResponse:
    status: int
    body: bytes


def _provider_error_code(body: bytes) -> str | None:
    """Keep a short machine error code without persisting provider error text."""
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("error_code") or data.get("code")
    return value if isinstance(value, str) and _ERROR_CODE.fullmatch(value) else None


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        # Bearer credentials must never be forwarded to a redirected host.
        return None


def _open_no_redirect(request: Request, timeout: int):
    return build_opener(_RejectRedirects()).open(request, timeout=timeout)


class BrightDataTransport:
    """Make one fixed-endpoint scrape POST, bounding response time and body size."""

    endpoint = "https://api.brightdata.com/datasets/v3/scrape"
    timeout_seconds = 65

    def _request(self, path: str, token: str, max_bytes: int,
                 *, body: bytes | None = None, query: dict[str, str] | None = None,
                 timeout: int = 15) -> BrightDataHTTPResponse:
        target = "https://api.brightdata.com" + path
        if query:
            target += "?" + urlencode(query)
        request = Request(target, data=body, method="POST" if body is not None else "GET", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "smi-ingestion/0.1",
        })
        try:
            with _open_no_redirect(request, timeout=timeout) as response:
                final = urlsplit(response.geturl())
                if (final.scheme != "https" or final.hostname != "api.brightdata.com"
                        or final.path != path):
                    raise EvidenceError("unexpected_source_redirect")
                # The documented synchronous endpoint can label JSON output
                # as text/plain even when format=json is requested.
                if response.headers.get_content_type() not in {"application/json", "text/plain"}:
                    raise EvidenceError("invalid_source_content_type")
                result = response.read(max_bytes + 1)
                if len(result) > max_bytes:
                    raise EvidenceError("response_too_large")
                return BrightDataHTTPResponse(response.status, result)
        except HTTPError as error:
            return BrightDataHTTPResponse(error.code, error.read(max_bytes + 1)[:max_bytes])

    def fetch(
        self, dataset_id: str, profile_url: str, num_of_posts: int,
        token: str, max_bytes: int,
    ) -> BrightDataHTTPResponse:
        if dataset_id not in _DATASETS.values():
            raise EvidenceError("invalid_brightdata_dataset")
        if not token.strip():
            raise EvidenceError("missing_brightdata_api_token")
        input_row: dict[str, Any] = {"url": profile_url}
        if dataset_id == _DATASETS["posts"]:
            input_row["num_of_posts"] = num_of_posts
        # The current TikTok endpoint examples use a top-level input array.
        body = json.dumps([input_row]).encode("utf-8")
        return self._request("/datasets/v3/scrape", token, max_bytes, body=body,
                             query={"dataset_id": dataset_id, "format": "json",
                                    "include_errors": "true"}, timeout=self.timeout_seconds)

    def progress(self, snapshot_id: str, token: str) -> BrightDataHTTPResponse:
        if not _SNAPSHOT_ID.fullmatch(snapshot_id):
            raise EvidenceError("invalid_snapshot_id")
        return self._request(f"/datasets/v3/progress/{snapshot_id}", token, 4096)

    def snapshot(self, snapshot_id: str, token: str, max_bytes: int) -> BrightDataHTTPResponse:
        if not _SNAPSHOT_ID.fullmatch(snapshot_id):
            raise EvidenceError("invalid_snapshot_id")
        return self._request(f"/datasets/v3/snapshot/{snapshot_id}", token, max_bytes,
                             query={"format": "json"})


class BrightDataTikTokCollector:
    """Collect profile then posts for up to three supplied creators, six paid calls/run."""

    adapter_id = "brightdata-tiktok"
    provider_id = "brightdata"
    format_version = "brightdata-tiktok-v1"

    def __init__(
        self, transport: BrightDataTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        token_provider: Callable[[], str | None] | None = None,
    ):
        self.transport = transport or BrightDataTransport()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.token_provider = token_provider or (lambda: os.environ.get("BRIGHTDATA_API_TOKEN"))

    @staticmethod
    def _request(manifest: dict[str, Any]) -> tuple[tuple[SourceReference, ...], int]:
        if manifest.get("synthetic") or "policy" in manifest:
            raise EvidenceError("brightdata_policy_is_fixed")
        values = manifest.get("references")
        if not isinstance(values, list) or not 1 <= len(values) <= _MAX_PROFILES:
            raise EvidenceError("invalid_reference_count")
        references = tuple(_profile_reference(value) for value in values)
        if len({ref.original.casefold() for ref in references}) != len(references):
            raise EvidenceError("duplicate_tiktok_reference")
        post_count = manifest.get("num_of_posts", _MAX_POSTS)
        if isinstance(post_count, bool) or not isinstance(post_count, int) or not 1 <= post_count <= _MAX_POSTS:
            raise EvidenceError("invalid_post_count")
        return references, post_count

    def collect(
        self, manifest: dict[str, Any], checkpoint: dict[str, Any], limits: RunLimits
    ) -> CollectedBatch:
        references, post_count = self._request(manifest)
        index = checkpoint.get("index", 0)
        stage = checkpoint.get("stage", "profile")
        used = checkpoint.get("requests_used", 0)
        paid_used = checkpoint.get("paid_requests_used", 0)
        polls = checkpoint.get("progress_polls", 0)
        snapshot_id = checkpoint.get("snapshot_id")
        corroborated_account_id = checkpoint.get("account_id")
        kind = stage.split("_")[0] if isinstance(stage, str) else None
        phase = stage[len(kind):].lstrip("_") if kind else None
        if (isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= len(references)
                or kind not in _DATASETS or phase not in {"", "progress", "snapshot"}
                or isinstance(used, bool) or not isinstance(used, int)
                or not 0 <= used <= _MAX_HTTP_REQUESTS
                or isinstance(paid_used, bool) or not isinstance(paid_used, int)
                or not 0 <= paid_used <= _MAX_PAID_REQUESTS
                or isinstance(polls, bool) or not isinstance(polls, int) or not 0 <= polls <= 3
                or (phase and (not isinstance(snapshot_id, str) or not _SNAPSHOT_ID.fullmatch(snapshot_id)))
                or (corroborated_account_id is not None and _stable_id(corroborated_account_id) is None)):
            raise EvidenceError("invalid_checkpoint")
        if checkpoint.get("halted"):
            return CollectedBatch((), checkpoint, False)
        if index == len(references):
            return CollectedBatch((), checkpoint, True)
        if used >= _MAX_HTTP_REQUESTS or limits.max_requests < 1 or (not phase and paid_used >= _MAX_PAID_REQUESTS):
            raise EvidenceError("request_limit_reached")
        checked_at = self.clock()
        if checked_at.tzinfo is None:
            raise EvidenceError("timestamp_requires_timezone")
        if phase == "progress" and checkpoint.get("next_poll_after"):
            try:
                next_poll = datetime.fromisoformat(checkpoint["next_poll_after"])
            except (TypeError, ValueError) as error:
                raise EvidenceError("invalid_checkpoint") from error
            if next_poll.tzinfo is None:
                raise EvidenceError("invalid_checkpoint")
            if checked_at < next_poll:
                return CollectedBatch((), checkpoint, False)
        token = self.token_provider()
        if not isinstance(token, str) or not token.strip():
            raise EvidenceError("missing_brightdata_api_token")
        token = token.strip()
        reference = references[index]
        max_bytes = min(limits.max_bytes, _MAX_RESPONSE_BYTES)
        response: BrightDataHTTPResponse | None = None
        outcome = "source_error"
        error_rows = 0
        row_count = 0
        returned_account_id: str | None = None
        next_index = index
        next_stage = stage
        next_polls = polls
        next_snapshot = snapshot_id
        next_poll_after: str | None = None
        try:
            if phase == "progress":
                response = self.transport.progress(snapshot_id, token)
            elif phase == "snapshot":
                response = self.transport.snapshot(snapshot_id, token, max_bytes)
            else:
                response = self.transport.fetch(
                    _DATASETS[kind], reference.original, post_count, token, max_bytes
                )
            if len(response.body) > max_bytes:
                raise EvidenceError("response_too_large")
            if response.status == 200:
                data = json.loads(response.body)
                if phase == "progress":
                    status = data.get("status") if isinstance(data, dict) else None
                    if status in {"starting", "running"}:
                        next_polls += 1
                        outcome = "snapshot_running" if next_polls < 3 else "snapshot_pending_limit"
                        next_poll_after = (checked_at + timedelta(seconds=30)).isoformat()
                    elif status == "ready":
                        outcome = "snapshot_ready"
                        next_stage = f"{kind}_snapshot"
                    elif status in {"failed", "canceled"}:
                        outcome = "snapshot_failed"
                    else:
                        outcome = "invalid_response"
                elif not isinstance(data, list) or len(data) > (1 if kind == "profile" else post_count):
                    outcome = "unexpected_row_count"
                else:
                    row_count = len(data)
                    error_rows = sum(not isinstance(row, dict) or bool(row.get("error"))
                                     or bool(row.get("error_code")) or row.get("status") == "error"
                                     for row in data)
                    outcome = "provider_error" if not data or error_rows == len(data) else (
                        "partial_rows" if error_rows else "resolved"
                    )
                    if kind == "profile" and outcome == "resolved" and len(data) == 1:
                        row = data[0]
                        try:
                            returned_reference = _profile_reference(row.get("url"))
                        except EvidenceError:
                            returned_reference = None
                        if (returned_reference is not None
                                and returned_reference.original.casefold() == reference.original.casefold()):
                            returned_account_id = _profile_identity(row, returned_reference)[0]
                    next_index = index + (1 if kind == "posts" else 0)
                    next_stage = "posts" if kind == "profile" else "profile"
                    next_snapshot = None
                    next_polls = 0
            elif response.status == 202 and not phase:
                data = json.loads(response.body)
                candidate = data.get("snapshot_id") if isinstance(data, dict) else None
                if isinstance(candidate, str) and _SNAPSHOT_ID.fullmatch(candidate):
                    next_snapshot = candidate
                    outcome = "pending_snapshot"
                    next_stage = f"{kind}_progress"
                    next_polls = 0
                else:
                    outcome = "invalid_response"
            elif response.status in {401, 403}:
                outcome = "authentication_failed"
            elif response.status == 402:
                outcome = "payment_required"
            elif response.status == 429:
                outcome = "rate_limited"
            else:
                outcome = "source_error"
        except EvidenceError as error:
            outcome = "oversized_response" if error.code == "response_too_large" else "invalid_response"
        except (TimeoutError, URLError, OSError):
            outcome = "source_error"
        except (json.JSONDecodeError, UnicodeError):
            outcome = "invalid_response"

        captured_at = self.clock()
        if captured_at.tzinfo is None:
            raise EvidenceError("timestamp_requires_timezone")
        halted = outcome not in {
            "resolved", "partial_rows", "pending_snapshot", "snapshot_running", "snapshot_ready"
        }
        next_checkpoint = {
            "index": next_index, "stage": next_stage,
            "requests_used": used + 1,
            "paid_requests_used": paid_used + (0 if phase else 1),
            "progress_polls": next_polls, "snapshot_id": next_snapshot,
            "next_poll_after": next_poll_after, "halted": halted,
            "account_id": returned_account_id if kind == "profile" and outcome == "resolved"
            else (corroborated_account_id if kind == "posts" and next_stage != "profile" else None),
        }
        payload = response.body if response and response.status == 200 and phase != "progress" and outcome in {
            "resolved", "partial_rows"
        } else b""
        draft = ObservationDraft(
            source_item_key=f"{reference.original}#{stage}#{used + 1}",
            adapter_id=self.adapter_id, provider_id=self.provider_id,
            format_version=self.format_version, reference=reference,
            payload=payload, media_type="application/json", captured_at=captured_at,
            source_as_of=None, policy=_POLICY, synthetic=False,
            coverage={
                "requested_input": 1, "dataset_kind": kind, "request_phase": phase or "scrape",
                "dataset_id": _DATASETS[kind], "outcome": outcome,
                "http_status": response.status if response else None,
                "provider_error_code": _provider_error_code(response.body)
                if response and response.status >= 400 else None,
                "http_attempts": 1, "requested_posts": post_count if kind == "posts" else None,
                "row_count": row_count, "error_rows": error_rows,
                "snapshot_id": next_snapshot or snapshot_id, "truncated": outcome == "oversized_response",
                "corroborated_account_id": corroborated_account_id if kind == "posts" else None,
            },
            request_attempts=1,
        )
        return CollectedBatch(
            (draft,), next_checkpoint,
            not halted and next_index == len(references) and next_stage == "profile",
        )


def _stable_id(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    candidate = str(value) if isinstance(value, (str, int)) else ""
    return candidate if _NATIVE_ID.fullmatch(candidate) else None


def _profile_identity(
    row: dict[str, Any], reference: SourceReference,
) -> tuple[str | None, str, str | None]:
    """Resolve current or legacy profile IDs without mistaking a numeric handle for an ID."""
    source = "id" if row.get("id") is not None else "account_id"
    native_id = _stable_id(row.get(source))
    if native_id is None:
        return None, source, "missing_stable_id"
    account_label = row.get("account_id")
    is_handle = (isinstance(account_label, (str, int))
                 and str(account_label).casefold() == (reference.handle_hint or "").casefold())
    if source == "id":
        # Live responses use account_id for the handle and id for the native ID;
        # legacy responses can instead use account_id for that same native ID.
        if account_label is not None and not is_handle and _stable_id(account_label) != native_id:
            return None, source, "profile_identity_mismatch"
    elif is_handle:
        return None, source, "ambiguous_stable_id"
    return native_id, source, None


def _number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 9_223_372_036_854_775_807 else None
    if isinstance(value, str) and value.isascii() and value.isdigit() and len(value) <= 19:
        number = int(value)
        return number if number <= 9_223_372_036_854_775_807 else None
    return None


def _published_at(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.isoformat() if parsed.tzinfo else None


def _post_permalink(value: Any, profile: SourceReference, post_id: str) -> str | None:
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (parsed.scheme != "https" or parsed.hostname not in {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}
            or parsed.username or parsed.password or port is not None or parsed.fragment):
        return None
    parts = parsed.path.strip("/").split("/")
    if (len(parts) != 3 or parts[0].casefold() != f"@{profile.handle_hint}".casefold()
            or parts[1] not in {"video", "photo"} or parts[2] != post_id):
        return None
    return f"https://www.tiktok.com/@{profile.handle_hint}/{parts[1]}/{post_id}"


class BrightDataTikTokMapper:
    """Map documented provider fields, leaving uncertain identity and gaps unresolved."""

    version = "v2"
    supported_format = "brightdata-tiktok-v1"

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        if (observation.format_version != self.supported_format or observation.synthetic
                or observation.provider_id != "brightdata"):
            raise ValueError("unsupported_brightdata_observation")
        if observation.coverage.get("outcome") not in {"resolved", "partial_rows"}:
            return NormalizedBatch((), (), ())
        data = json.loads(payload)
        if not isinstance(data, list):
            raise ValueError("invalid_brightdata_response")
        stage = observation.coverage.get("dataset_kind")
        if stage not in _DATASETS:
            raise ValueError("invalid_brightdata_dataset")
        entities: list[ExternalKey] = []
        fields: list[FieldCandidate] = []
        metrics: list[MetricCandidate] = []
        unresolved: list[UnresolvedCandidate] = []
        for index, row in enumerate(data):
            locator = f"$[{index}]"
            unresolved_kind = "account" if stage == "profile" else "content"
            if not isinstance(row, dict) or row.get("error") or row.get("error_code") or row.get("status") == "error":
                unresolved.append(UnresolvedCandidate(unresolved_kind, locator, "provider_error_row"))
                continue
            if stage == "profile":
                try:
                    returned_profile = _profile_reference(row.get("url"))
                except EvidenceError:
                    unresolved.append(UnresolvedCandidate("account", locator, "missing_or_invalid_profile_url"))
                    continue
                if returned_profile.original.casefold() != observation.reference.original.casefold():
                    unresolved.append(UnresolvedCandidate("account", locator, "profile_reference_mismatch"))
                    continue
                self._profile(row, locator, observation, entities, fields, metrics, unresolved)
            else:
                profile_url = row.get("profile_url")
                if profile_url is not None:
                    try:
                        returned_profile = _profile_reference(profile_url)
                    except EvidenceError:
                        unresolved.append(UnresolvedCandidate("content", locator, "missing_or_invalid_profile_url"))
                        continue
                    if returned_profile.original.casefold() != observation.reference.original.casefold():
                        unresolved.append(UnresolvedCandidate("content", locator, "profile_reference_mismatch"))
                        continue
                else:
                    post_id = _stable_id(row.get("post_id"))
                    has_matching_permalink = any(
                        _post_permalink(row.get(name), observation.reference, post_id or "")
                        for name in ("post_url", "url")
                    )
                    if not has_matching_permalink:
                        unresolved.append(UnresolvedCandidate("content", locator, "profile_not_corroborated"))
                        continue
                self._post(row, locator, observation, entities, fields, metrics, unresolved)
        return NormalizedBatch(tuple(dict.fromkeys(entities)), tuple(fields), tuple(metrics),
                               unresolved=tuple(unresolved))

    @staticmethod
    def _field(fields: list[FieldCandidate], key: ExternalKey, name: str,
               value: Any, locator: str) -> None:
        fields.append(FieldCandidate(key, name, "observed" if value is not None else "not_returned",
                                     value, locator))

    @staticmethod
    def _metric(metrics: list[MetricCandidate], fields: list[FieldCandidate],
                key: ExternalKey, row: dict[str, Any], name: str,
                locator: str, measured_at: datetime | None) -> None:
        value = _number(row.get(name))
        if value is not None:
            metrics.append(MetricCandidate(
                key, f"brightdata.{name}.v1", name, value, str(value), "exact",
                "count", measured_at, f"{locator}.{name}",
            ))
        else:
            fields.append(FieldCandidate(
                key, f"metric:{name}", "not_returned" if name not in row else "unavailable",
                None, f"{locator}.{name}", None if name not in row else "invalid_source_value",
            ))

    def _profile(self, row: dict[str, Any], locator: str, observation: RawObservation,
                 entities: list[ExternalKey], fields: list[FieldCandidate],
                 metrics: list[MetricCandidate], unresolved: list[UnresolvedCandidate]) -> None:
        account_id, id_source, reason = _profile_identity(row, observation.reference)
        if account_id is None:
            unresolved.append(UnresolvedCandidate("account", f"{locator}.{id_source}", reason))
            return
        key = ExternalKey("tiktok", "tiktok:public", "account", account_id)
        entities.append(key)
        self._field(fields, key, "handle", observation.reference.handle_hint, f"{locator}.url")
        for name, source in (("nickname", "nickname"), ("biography", "biography"),
                             ("profile_url", "url")):
            value = row.get(source)
            self._field(fields, key, name, value if isinstance(value, str) else None,
                        f"{locator}.{source}")
        for name in ("followers", "following", "likes", "videos_count"):
            self._metric(metrics, fields, key, row, name, locator, observation.captured_at)

    def _post(self, row: dict[str, Any], locator: str, observation: RawObservation,
              entities: list[ExternalKey], fields: list[FieldCandidate],
              metrics: list[MetricCandidate], unresolved: list[UnresolvedCandidate]) -> None:
        post_id = _stable_id(row.get("post_id"))
        if post_id is None:
            unresolved.append(UnresolvedCandidate("content", f"{locator}.post_id", "missing_stable_id"))
            return
        author_id = _stable_id(row.get("author_id"))
        profile_id = _stable_id(row.get("profile_id"))
        if author_id and profile_id and author_id != profile_id:
            unresolved.append(UnresolvedCandidate("content", f"{locator}.profile_id",
                                                  "conflicting_author_ids"))
            return
        author_source = "author_id" if author_id or "profile_id" not in row else "profile_id"
        author_id = author_id or profile_id
        corroborated = _stable_id(observation.coverage.get("corroborated_account_id"))
        if author_id and corroborated and author_id != corroborated:
            unresolved.append(UnresolvedCandidate("content", f"{locator}.{author_source}",
                                                  "author_identity_mismatch"))
            return
        key = ExternalKey("tiktok", "tiktok:public", "content", post_id)
        entities.append(key)
        caption = row.get("description")
        self._field(fields, key, "caption", caption if isinstance(caption, str) else None,
                    f"{locator}.description")
        published = _published_at(row.get("create_time"))
        self._field(fields, key, "published_at", published, f"{locator}.create_time")
        # video_url in the documented response is a temporary CDN media URL.
        public_url = None
        permalink_field = None
        for name in ("post_url", "url"):
            public_url = _post_permalink(row.get(name), observation.reference, post_id)
            if public_url:
                permalink_field = name
                break
        fields.append(FieldCandidate(key, "post_url", "observed" if public_url else "not_returned",
                                     public_url, f"{locator}.{permalink_field or 'post_url'}"))
        if author_id:
            author = ExternalKey("tiktok", "tiktok:public", "account", author_id)
            entities.append(author)
            self._field(fields, key, "author_account", {
                "platform": "tiktok", "namespace": "tiktok:public", "kind": "account",
                "native_id": author_id,
            }, f"{locator}.{author_source}")
        else:
            fields.append(FieldCandidate(key, "author_account", "unavailable", None,
                                         f"{locator}.{author_source}", "missing_stable_id"))
        for name in ("play_count", "digg_count", "comment_count", "share_count", "collect_count"):
            self._metric(metrics, fields, key, row, name, locator, observation.captured_at)
