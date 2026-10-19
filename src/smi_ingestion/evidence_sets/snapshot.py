"""Validate and normalize versioned TikTok caption exports without source calls."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ..contracts import ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch
from ..evidence import EvidenceError


FORMAT_VERSION = "tiktok-caption-snapshot-v1"
MAPPER_VERSION = "v1"
METRICS = {"views": "playCount", "likes": "diggCount", "comments": "commentCount", "shares": "shareCount"}
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class ValidatedSnapshot:
    """Validated export plus its trusted manifest; records retain original times and IDs."""

    manifest: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    collection_runs: tuple[str, ...]
    synthetic: bool


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceError(code)


def timestamp(value: Any) -> datetime:
    """Parse an explicit, timezone-aware source timestamp or fail with a safe code."""
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(result.tzinfo is not None, "snapshot_timestamp_requires_timezone")
        return result
    except (AttributeError, TypeError, ValueError) as error:
        raise EvidenceError("invalid_snapshot_timestamp") from error


def _uuid(value: Any) -> None:
    try:
        _require(isinstance(value, str) and str(uuid.UUID(value)) == value, "invalid_origin_reference")
    except (ValueError, TypeError, AttributeError) as error:
        raise EvidenceError("invalid_origin_reference") from error


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate_snapshot_key")
        result[key] = value
    return result


def decode_json(payload: bytes) -> dict[str, Any]:
    """Reject duplicate keys, non-finite numbers and non-object JSON roots."""
    def invalid_constant(value: str):
        raise EvidenceError("invalid_snapshot_number")
    try:
        result = json.loads(payload, object_pairs_hook=_object, parse_constant=invalid_constant)
    except (ValueError, UnicodeError) as error:
        raise EvidenceError("invalid_snapshot_json") from error
    _require(isinstance(result, dict), "invalid_snapshot_object")
    return result


def validate_record(record: Any, source_runs: tuple[str, ...]) -> None:
    """Validate one exported post; curation cannot supply missing source facts."""
    _require(isinstance(record, dict), "invalid_snapshot_record")
    _require(record.get("platform") == "tiktok", "unsupported_snapshot_platform")
    author = record.get("author")
    _require(isinstance(author, dict), "invalid_snapshot_author")
    for native_id in (record.get("post_id"), author.get("platform_id")):
        _require(isinstance(native_id, str) and re.fullmatch(r"[0-9]{1,30}", native_id) is not None,
                 "invalid_snapshot_native_id")
    handle = author.get("handle")
    _require(isinstance(handle, str) and re.fullmatch(r"[A-Za-z0-9._]{1,64}", handle) is not None,
             "invalid_snapshot_handle")
    url = record.get("url")
    _require(isinstance(url, str), "invalid_snapshot_url")
    parsed = urlsplit(url)
    _require(parsed.scheme == "https" and parsed.netloc == "www.tiktok.com"
             and parsed.path == f"/@{handle}/video/{record['post_id']}"
             and not parsed.query and not parsed.fragment, "snapshot_reference_mismatch")
    published = timestamp(record.get("published_at"))
    captured = timestamp(record.get("captured_at"))
    _require(published <= captured, "snapshot_time_order_invalid")
    _require(isinstance(record.get("caption"), str), "invalid_snapshot_caption")
    metrics = record.get("metrics")
    _require(isinstance(metrics, dict) and not (metrics.keys() - METRICS.keys()), "invalid_snapshot_metrics")
    for value in metrics.values():
        _require(type(value) is int and value >= 0, "invalid_snapshot_metric_value")
    provenance = record.get("provenance")
    _require(isinstance(provenance, dict), "invalid_snapshot_provenance")
    _require(provenance.get("adapter") == "tiktok-web"
             and provenance.get("provider") == "tiktok-web-public-page", "unsupported_snapshot_lineage")
    _uuid(provenance.get("source_observation_id"))
    _uuid(provenance.get("run_id"))
    _require(provenance["run_id"] in source_runs, "snapshot_run_not_declared")
    curation = record.get("curation", {})
    _require(isinstance(curation, dict), "invalid_snapshot_curation")
    _require(all(isinstance(k, str) and isinstance(v, (str, bool)) for k, v in curation.items()),
             "invalid_snapshot_curation")


def load_snapshot(manifest_path: Path) -> ValidatedSnapshot:
    """Read bounded local files and validate digest, membership and source references."""
    _require(manifest_path.stat().st_size <= 65536, "snapshot_manifest_too_large")
    manifest = decode_json(manifest_path.read_bytes())
    _require(set(manifest) == {"format_version", "dataset_id", "snapshot", "sha256", "namespace",
                               "expected_posts", "expected_accounts"}, "invalid_snapshot_manifest_fields")
    _require(manifest.get("format_version") == FORMAT_VERSION, "unsupported_snapshot_format")
    dataset_id = manifest.get("dataset_id")
    _require(isinstance(dataset_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", dataset_id)
             is not None, "invalid_dataset_id")
    _require(manifest.get("namespace") == "web:public", "unsupported_snapshot_namespace")
    for key in ("expected_posts", "expected_accounts"):
        _require(type(manifest.get(key)) is int and manifest[key] > 0, "invalid_snapshot_expected_count")
    name = manifest.get("snapshot")
    _require(isinstance(name, str) and bool(name), "invalid_snapshot_path")
    base = manifest_path.resolve().parent
    path = (base / name).resolve()
    _require(path.is_relative_to(base), "snapshot_outside_manifest_directory")
    _require(path.stat().st_size <= MAX_SNAPSHOT_BYTES, "snapshot_too_large")
    with path.open("rb") as source:
        payload = source.read(MAX_SNAPSHOT_BYTES + 1)
    _require(len(payload) <= MAX_SNAPSHOT_BYTES, "snapshot_too_large")
    _require(hashlib.sha256(payload).hexdigest() == manifest.get("sha256"), "snapshot_digest_mismatch")
    data = decode_json(payload)
    _require(data.get("dataset_id") == dataset_id, "snapshot_dataset_mismatch")
    _require(type(data.get("synthetic")) is bool, "invalid_snapshot_synthetic_state")
    expected_type = "synthetic_snapshot" if data["synthetic"] else "curated_real_world_snapshot"
    _require(data.get("dataset_type") == expected_type, "invalid_snapshot_type")
    runs = data.get("collection_runs")
    _require(isinstance(runs, list) and bool(runs), "invalid_snapshot_runs")
    for run in runs:
        _uuid(run)
    _require(len(set(runs)) == len(runs), "duplicate_snapshot_run")
    records = data.get("records")
    _require(isinstance(records, list) and len(records) == manifest["expected_posts"],
             "snapshot_membership_mismatch")
    for record in records:
        validate_record(record, tuple(runs))
    _require(len({r["post_id"] for r in records}) == len(records), "duplicate_snapshot_post")
    _require(len({r["provenance"]["source_observation_id"] for r in records}) == len(records),
             "duplicate_origin_observation")
    _require({r["provenance"]["run_id"] for r in records} == set(runs), "snapshot_unused_run")
    _require(len({r["author"]["platform_id"] for r in records}) == manifest["expected_accounts"],
             "snapshot_account_count_mismatch")
    return ValidatedSnapshot(manifest, tuple(records), tuple(runs), data["synthetic"])


def normalize_record(record: dict[str, Any]) -> NormalizedBatch:
    """Map exported source fields; curation labels remain development annotations."""
    account = ExternalKey("tiktok", "web:public", "account", record["author"]["platform_id"])
    post = ExternalKey("tiktok", "web:public", "content", record["post_id"])
    fields = [
        FieldCandidate(account, "handle", "observed", record["author"]["handle"], "$.author.handle"),
        FieldCandidate(post, "author_account", "observed", account.__dict__, "$.author.platform_id"),
        FieldCandidate(post, "caption", "observed", record["caption"], "$.caption"),
        FieldCandidate(post, "published_at", "observed", record["published_at"], "$.published_at"),
        FieldCandidate(post, "url", "observed", record["url"], "$.url"),
    ]
    metrics = []
    for name, native_name in METRICS.items():
        if name not in record["metrics"]:
            fields.append(FieldCandidate(post, f"metric:{name}", "not_returned", None,
                                         f"$.metrics.{name}", "absent_from_snapshot"))
            continue
        value = record["metrics"][name]
        metrics.append(MetricCandidate(
            post, f"tiktok.web.{name}.v1", native_name, value, str(value), "exact", "count",
            timestamp(record["captured_at"]), f"$.metrics.{name}",
        ))
    return NormalizedBatch((account, post), tuple(fields), tuple(metrics))
