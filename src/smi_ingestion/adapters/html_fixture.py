"""Mapping for a saved synthetic HTML snapshot, without page fetching."""

from __future__ import annotations

import re
from html.parser import HTMLParser

from ..contracts import ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch, RawObservation, UnresolvedCandidate


class _PostParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.article: dict[str, str] = {}
        self.text: dict[str, str] = {}
        self.stack: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {k: v or "" for k, v in attrs}
        if tag == "article" and not self.article:
            self.article = attributes
        class_name = attributes.get("class")
        self.stack.append(class_name if class_name in {"handle", "caption", "views"} else None)

    def handle_endtag(self, tag: str) -> None:
        if self.stack:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1]:
            name = self.stack[-1]
            self.text[name] = self.text.get(name, "") + data


def _parse_views(display: str) -> tuple[int | float, str]:
    cleaned = display.strip().replace(",", "")
    if cleaned.isascii() and cleaned.isdecimal():
        return int(cleaned), "exact"
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([KkMm])", cleaned)
    if match:
        multiple = 1_000 if match.group(2).lower() == "k" else 1_000_000
        return float(match.group(1)) * multiple, "approximate"
    raise ValueError("invalid_views")


class HtmlFixtureMapper:
    version = "v1"
    supported_format = "v1"

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        if observation.format_version != self.supported_format or not observation.synthetic:
            raise ValueError("unsupported_format")
        parser = _PostParser()
        parser.feed(payload.decode("utf-8"))
        article = parser.article
        if article.get("data-platform") != "tiktok":
            raise ValueError("invalid_html_fixture")
        namespace = "fixture:public"
        account_key = ExternalKey("tiktok", namespace, "account", article["data-author-id"]) if article.get("data-author-id") else None
        post_key = ExternalKey("tiktok", namespace, "content", article["data-video-id"]) if article.get("data-video-id") else None
        handle = parser.text.get("handle")
        caption = parser.text.get("caption")
        fields = []
        unresolved = []
        if account_key:
            fields.append(FieldCandidate(account_key, "handle", "observed" if handle else "not_returned", handle, "article .handle"))
        else:
            unresolved.append(UnresolvedCandidate("account", "article@data-author-id", "missing_stable_id"))
        if post_key:
            fields.extend([
                FieldCandidate(post_key, "author_account", "observed" if account_key else "unavailable", {"platform": "tiktok", "namespace": namespace, "kind": "account", "native_id": account_key.native_id} if account_key else None, "article@data-author-id", None if account_key else "missing_stable_id"),
                FieldCandidate(post_key, "caption", "removed" if article.get("data-caption-state") == "removed" else "observed" if caption else "not_returned", None if article.get("data-caption-state") == "removed" else caption, "article .caption"),
                FieldCandidate(post_key, "published_at", "observed" if article.get("data-published-at") else "not_returned", article.get("data-published-at"), "article@data-published-at"),
            ])
        else:
            unresolved.append(UnresolvedCandidate("content", "article@data-video-id", "missing_stable_id"))
        metrics: list[MetricCandidate] = []
        if post_key and "views" in parser.text:
            raw = parser.text["views"].strip()
            value, precision = _parse_views(raw)
            metrics.append(MetricCandidate(post_key, "synthetic.views.v1", "views", value, raw, precision, "count", observation.source_as_of or observation.captured_at, "article .views"))
        elif post_key:
            fields.append(FieldCandidate(post_key, "metric:views", "not_returned", None, "article .views"))
        return NormalizedBatch(tuple(key for key in (account_key, post_key) if key), tuple(fields), tuple(metrics), unresolved=tuple(unresolved))
