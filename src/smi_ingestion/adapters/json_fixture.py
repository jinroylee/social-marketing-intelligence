"""Mapping for the synthetic API-shaped JSON format."""

from __future__ import annotations

import json

from ..contracts import ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch, RawObservation, UnresolvedCandidate


class JsonFixtureMapper:
    version = "v1"
    supported_format = "v1"

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        if observation.format_version != self.supported_format or not observation.synthetic:
            raise ValueError("unsupported_format")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("invalid_fixture_objects")
        account = data.get("account") or {}
        post = data.get("video") or {}
        if not isinstance(account, dict) or not isinstance(post, dict):
            raise ValueError("invalid_fixture_objects")
        account_id = account.get("id")
        post_id = post.get("id")
        if account_id is not None and not isinstance(account_id, str):
            raise ValueError("native_ids_must_be_strings")
        if post_id is not None and not isinstance(post_id, str):
            raise ValueError("native_ids_must_be_strings")
        author_id = post.get("author_id")
        if account_id and author_id and account_id != author_id:
            raise ValueError("author_identity_mismatch")
        if author_id is not None and not isinstance(author_id, str):
            raise ValueError("native_ids_must_be_strings")
        namespace = "fixture:public"
        account_key = ExternalKey("tiktok", namespace, "account", account_id) if account_id else None
        author_key = ExternalKey("tiktok", namespace, "account", author_id) if author_id else None
        post_key = ExternalKey("tiktok", namespace, "content", post_id) if post_id else None
        entities = [key for key in (account_key, author_key, post_key) if key]
        unresolved = []
        if account_key is None:
            unresolved.append(UnresolvedCandidate("account", "$.account.id", "missing_stable_id"))
        if post_key is None:
            unresolved.append(UnresolvedCandidate("content", "$.video.id", "missing_stable_id"))
        fields = []
        if account_key:
            fields.append(FieldCandidate(account_key, "handle", "observed" if account.get("handle") is not None else "not_returned", account.get("handle"), "$.account.handle"))
        if post_key:
            fields.extend([
                FieldCandidate(post_key, "author_account", "observed" if author_key else "unavailable", {"platform": "tiktok", "namespace": namespace, "kind": "account", "native_id": author_id} if author_key else None, "$.video.author_id", None if author_key else "missing_stable_id"),
                FieldCandidate(post_key, "caption", "removed" if post.get("caption_state") == "removed" else "observed" if post.get("caption") is not None else "not_returned", None if post.get("caption_state") == "removed" else post.get("caption"), "$.video.caption"),
                FieldCandidate(post_key, "published_at", "observed" if post.get("published_at") else "not_returned", post.get("published_at"), "$.video.published_at"),
            ])
        metrics: list[MetricCandidate] = []
        metrics_data = post.get("metrics") or {}
        if not isinstance(metrics_data, dict):
            raise ValueError("invalid_metrics_object")
        if post_key and "views" in metrics_data:
            views = metrics_data["views"]
            if isinstance(views, bool) or not isinstance(views, int) or views < 0:
                raise ValueError("invalid_views")
            metrics.append(MetricCandidate(post_key, "synthetic.views.v1", "views", views, str(views), "exact", "count", observation.source_as_of or observation.captured_at, "$.video.metrics.views"))
        elif post_key:
            fields.append(FieldCandidate(post_key, "metric:views", "not_returned", None, "$.video.metrics.views"))
        return NormalizedBatch(tuple(dict.fromkeys(entities)), tuple(fields), tuple(metrics), unresolved=tuple(unresolved))
