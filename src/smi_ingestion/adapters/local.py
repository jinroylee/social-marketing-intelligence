"""Bounded local-file collector used to prove the acquisition seam."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..contracts import CollectedBatch, ObservationDraft, RunLimits, SourcePolicy
from ..evidence import EvidenceError
from ..references import parse_reference


def parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise EvidenceError("timestamp_requires_timezone")
    return result


class LocalFileCollector:
    def __init__(self, adapter_id: str):
        self.adapter_id = adapter_id

    def collect(
        self, manifest: dict[str, Any], checkpoint: dict[str, Any], limits: RunLimits
    ) -> CollectedBatch:
        if not manifest.get("synthetic"):
            raise EvidenceError("local_fixtures_must_be_synthetic")
        items = manifest.get("items")
        if not isinstance(items, list) or not items:
            raise EvidenceError("empty_manifest")
        index = checkpoint.get("index", 0)
        if index >= len(items):
            return CollectedBatch((), {"index": index}, True)
        item = items[index]
        base = Path(manifest["_base"]).resolve()
        payload_path = (base / item["path"]).resolve()
        if not payload_path.is_relative_to(base):
            raise EvidenceError("input_outside_manifest_directory")
        if payload_path.stat().st_size > limits.max_bytes:
            raise EvidenceError("byte_limit_reached")
        with payload_path.open("rb") as source:
            payload = source.read(limits.max_bytes + 1)
        if len(payload) > limits.max_bytes:
            raise EvidenceError("byte_limit_reached")
        policy_data = manifest["policy"]
        policy = SourcePolicy(
            context_id=policy_data["context_id"],
            can_process=policy_data["can_process"],
            can_retain=policy_data["can_retain"],
            can_display=policy_data["can_display"],
            expires_at=parse_time(policy_data.get("expires_at")),
        )
        draft = ObservationDraft(
            source_item_key=item["path"],
            adapter_id=self.adapter_id,
            provider_id=manifest["provider_id"],
            format_version=manifest["format_version"],
            reference=parse_reference(item.get("reference", "")),
            payload=payload,
            media_type="application/json" if self.adapter_id == "fixture-json" else "text/html",
            captured_at=parse_time(item.get("captured_at", manifest.get("captured_at"))),
            source_as_of=parse_time(item.get("source_as_of")),
            policy=policy,
            synthetic=True,
            coverage={"requested_input": 1, "truncated": False},
        )
        return CollectedBatch((draft,), {"index": index + 1}, index + 1 >= len(items))
