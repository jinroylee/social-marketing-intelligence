"""Bounded TikTok oEmbed URL resolution with no retained TikTok response content."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode, urlsplit
from urllib.request import Request, urlopen

from ..contracts import (
    CollectedBatch, NormalizedBatch, ObservationDraft, RawObservation, RunLimits,
    SourcePolicy, SourceReference, UnresolvedCandidate,
)
from ..evidence import EvidenceError


_HANDLE = re.compile(r"[A-Za-z0-9._]{1,64}")
_VIDEO_ID = re.compile(r"[0-9]{1,30}")
_UNAVAILABLE_FIELDS = (
    "post_history", "follower_count", "view_count", "engagement_counts",
    "audience_geography", "sales_outcomes",
)


def _reference(value: str) -> SourceReference:
    """Accept only direct TikTok profile/video URLs and remove tracking parameters."""
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
    canonical = f"https://www.tiktok.com/@{handle}"
    if len(parts) == 1:
        return SourceReference(canonical, "tiktok", "profile", None, handle)
    if len(parts) == 3 and parts[1] == "video" and _VIDEO_ID.fullmatch(parts[2]):
        video_id = parts[2]
        return SourceReference(f"{canonical}/video/{video_id}", "tiktok", "video", video_id, handle)
    raise EvidenceError("invalid_tiktok_reference")


@dataclass(frozen=True)
class OEmbedHTTPResponse:
    status: int
    body: bytes


class TikTokOEmbedTransport:
    """Issue only the documented TikTok oEmbed GET with bounded time and bytes."""

    endpoint = "https://www.tiktok.com/oembed"
    timeout_seconds = 8

    def fetch(self, reference_url: str, max_bytes: int) -> OEmbedHTTPResponse:
        target = self.endpoint + "?" + urlencode({"url": reference_url})
        request = Request(target, headers={
            "Accept": "application/json", "User-Agent": "smi-ingestion/0.1",
        })
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                final = urlsplit(response.geturl())
                if final.scheme != "https" or final.hostname != "www.tiktok.com" or final.path != "/oembed":
                    raise EvidenceError("unexpected_source_redirect")
                if response.headers.get_content_type() != "application/json":
                    raise EvidenceError("invalid_source_content_type")
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise EvidenceError("response_too_large")
                return OEmbedHTTPResponse(response.status, body)
        except HTTPError as error:
            return OEmbedHTTPResponse(error.code, b"")


class TikTokOEmbedCollector:
    """Resolve up to ten supplied URLs; persist operational status, never response content."""

    adapter_id = "tiktok-oembed"
    provider_id = "tiktok-oembed"
    format_version = "oembed-json-v1"

    def __init__(
        self,
        transport: TikTokOEmbedTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self.transport = transport or TikTokOEmbedTransport()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _references(manifest: dict[str, Any]) -> tuple[SourceReference, ...]:
        if manifest.get("synthetic") or "policy" in manifest:
            raise EvidenceError("oembed_policy_is_fixed")
        values = manifest.get("references")
        if not isinstance(values, list) or not 1 <= len(values) <= 10:
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
        if not isinstance(index, int) or not 0 <= index <= len(references):
            raise EvidenceError("invalid_checkpoint")
        attempts_used = checkpoint.get("http_attempts_used", 0)
        if not isinstance(attempts_used, int) or not 0 <= attempts_used <= 10:
            raise EvidenceError("invalid_checkpoint")
        if checkpoint.get("halted"):
            return CollectedBatch((), checkpoint, False)
        if index == len(references):
            return CollectedBatch((), {"index": index}, True)
        attempt_budget = min(2, limits.max_requests, 10 - attempts_used)
        if attempt_budget < 1:
            raise EvidenceError("request_limit_reached")

        reference = references[index]
        attempts = 0
        response: OEmbedHTTPResponse | None = None
        outcome = "source_error"
        max_bytes = min(limits.max_bytes, 65_536)
        while attempts < attempt_budget:
            attempts += 1
            try:
                response = self.transport.fetch(reference.original, max_bytes)
            except EvidenceError as error:
                response = None
                outcome = "oversized_response" if error.code == "response_too_large" else "invalid_response"
                break
            except (TimeoutError, URLError, OSError):
                response = None
                if attempts < attempt_budget:
                    continue
                break
            if 500 <= response.status <= 599 and attempts < attempt_budget:
                continue
            if response.status == 200:
                outcome = "resolved"
            elif response.status in {400, 403, 404, 410}:
                outcome = "unavailable_or_private"
            elif response.status == 429:
                outcome = "rate_limited"
            else:
                outcome = "source_error"
            break

        captured_at = self.clock()
        if captured_at.tzinfo is None:
            raise EvidenceError("timestamp_requires_timezone")
        http_status = response.status if response else None
        halted = outcome in {"rate_limited", "source_error", "oversized_response", "invalid_response"}
        draft = ObservationDraft(
            source_item_key=reference.original,
            adapter_id=self.adapter_id,
            provider_id=self.provider_id,
            format_version=self.format_version,
            reference=reference,
            payload=response.body if outcome == "resolved" and response else b"",
            media_type="application/json",
            captured_at=captured_at,
            source_as_of=None,
            policy=SourcePolicy("tiktok-oembed-reference-only", True, False, True),
            synthetic=False,
            coverage={
                "requested_input": 1,
                "outcome": outcome,
                "http_status": http_status,
                "http_attempts": attempts,
                "unavailable_fields": list(_UNAVAILABLE_FIELDS),
                "truncated": False,
            },
            request_attempts=attempts,
        )
        next_checkpoint = {
            "index": index + 1, "http_attempts_used": attempts_used + attempts,
            "halted": halted,
        }
        return CollectedBatch((draft,), next_checkpoint, not halted and index + 1 == len(references))


class _VideoIdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.video_id: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "blockquote" and self.video_id is None:
            self.video_id = dict(attrs).get("data-video-id")


class TikTokOEmbedMapper:
    """Validate transient oEmbed data without writing TikTok-returned creator facts."""

    version = "v1"
    supported_format = "oembed-json-v1"

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        if (observation.format_version != self.supported_format or observation.synthetic
                or observation.policy.can_retain):
            raise ValueError("unsupported_oembed_observation")
        if observation.coverage.get("outcome") != "resolved":
            return NormalizedBatch((), (), ())
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get("provider_name") != "TikTok":
            raise ValueError("invalid_oembed_response")
        expected_type = "video" if observation.reference.resource_kind == "video" else "rich"
        if data.get("type") != expected_type or not isinstance(data.get("html"), str):
            raise ValueError("invalid_oembed_response")
        author_url = data.get("author_url")
        if not isinstance(author_url, str) or _reference(author_url).resource_kind != "profile":
            raise ValueError("invalid_oembed_author")
        unresolved = [UnresolvedCandidate("account", "$.author_url", "no_stable_account_id")]
        if expected_type == "video":
            parser = _VideoIdParser()
            parser.feed(data["html"])
            if parser.video_id and parser.video_id != observation.reference.native_id_hint:
                raise ValueError("video_id_mismatch")
            if parser.video_id is None:
                unresolved.append(UnresolvedCandidate(
                    "content", "$.html@data-video-id", "video_id_not_corroborated"
                ))
        return NormalizedBatch((), (), (), unresolved=tuple(unresolved))
