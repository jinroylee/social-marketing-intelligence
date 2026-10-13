"""Durable source-shaped evidence and fetch checkpoints."""

from __future__ import annotations

import hashlib
import os
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from .contracts import ObservationDraft, RawObservation, RunLimits, SourcePolicy, SourceReference
from .db import Database


class EvidenceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _instant(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _policy_json(policy: SourcePolicy) -> dict[str, Any]:
    result = asdict(policy)
    if policy.expires_at:
        result["expires_at"] = policy.expires_at.isoformat()
    return result


def _policy_from_json(data: dict[str, Any]) -> SourcePolicy:
    return SourcePolicy(
        context_id=data["context_id"],
        can_process=data["can_process"],
        can_retain=data["can_retain"],
        can_display=data["can_display"],
        expires_at=_instant(data.get("expires_at")),
        revoked=data.get("revoked", False),
    )


def _allowed(policy: SourcePolicy, action: str) -> bool:
    return (
        not policy.revoked
        and (policy.expires_at is None or policy.expires_at > datetime.now(timezone.utc))
        and bool(getattr(policy, f"can_{action}"))
    )


def _observation(row: dict[str, Any]) -> RawObservation:
    return RawObservation(
        id=str(row["id"]), run_id=str(row["run_id"]),
        source_item_key=row["source_item_key"], adapter_id=row["adapter_id"],
        provider_id=row["provider_id"], format_version=row["format_version"],
        reference=SourceReference(
            row["reference"], row["platform_hint"], row["resource_kind_hint"],
            row["native_id_hint"], row["handle_hint"]
        ),
        media_type=row["media_type"], captured_at=row["captured_at"],
        source_as_of=row["source_as_of"], ingested_at=row["ingested_at"],
        policy=_policy_from_json(row["policy"]), synthetic=row["synthetic"],
        payload_hash=row["payload_hash"], payload_path=row["payload_path"],
        coverage=row["coverage"]
    )


class EvidenceStore:
    def __init__(self, db: Database, root: Path):
        self.db = db
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def start_run(self, manifest_path: Path, digest: str, adapter_id: str, limits: RunLimits) -> str:
        run_id = str(uuid.uuid4())
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO ingestion_runs(id, manifest_path, manifest_hash, adapter_id, limits) "
                "VALUES (%s, %s, %s, %s, %s)",
                (run_id, str(manifest_path.resolve()), digest, adapter_id, Jsonb(asdict(limits)))
            )
        return run_id

    def run(self, run_id: str) -> dict[str, Any]:
        with self.db.connect() as connection:
            row = connection.execute("SELECT * FROM ingestion_runs WHERE id=%s", (run_id,)).fetchone()
        if row is None:
            raise EvidenceError("run_not_found")
        return row

    def pending(self, run_id: str) -> list[RawObservation]:
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM source_observations WHERE run_id=%s AND status='pending' ORDER BY item_index",
                (run_id,)
            ).fetchall()
        return [_observation(row) for row in rows]

    def save(self, run_id: str, item_index: int, draft: ObservationDraft,
             checkpoint: dict[str, Any], *, complete: bool = False) -> RawObservation:
        """Commit an observation, its fetch checkpoint, and input completion together."""
        if not _allowed(draft.policy, "process"):
            raise EvidenceError("processing_not_permitted")
        if draft.request_attempts < 1:
            raise EvidenceError("invalid_request_attempts")
        with self.db.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM source_observations WHERE run_id=%s AND item_index=%s",
                (run_id, item_index)
            ).fetchone()
            if existing:
                return _observation(existing)
        observation_id = str(uuid.uuid4())
        digest = hashlib.sha256(draft.payload).hexdigest()
        path: Path | None = None
        if draft.policy.can_retain:
            path = self.root / f"{observation_id}.bin"
            temporary = self.root / f"{observation_id}.tmp"
            with temporary.open("xb") as output:
                output.write(draft.payload)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        try:
            with self.db.connect() as connection:
                run = connection.execute(
                    "SELECT limits,requests_used FROM ingestion_runs WHERE id=%s FOR UPDATE", (run_id,)
                ).fetchone()
                if run is None:
                    raise EvidenceError("run_not_found")
                if run["requests_used"] + draft.request_attempts > run["limits"]["max_requests"]:
                    raise EvidenceError("request_limit_reached")
                row = connection.execute(
                    "INSERT INTO source_observations(" 
                    "id,run_id,item_index,source_item_key,adapter_id,provider_id,format_version,"
                    "reference,platform_hint,resource_kind_hint,native_id_hint,handle_hint,media_type,"
                    "captured_at,source_as_of,policy,synthetic,payload_hash,payload_path,coverage) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                    (observation_id, run_id, item_index, draft.source_item_key, draft.adapter_id,
                     draft.provider_id, draft.format_version, draft.reference.original,
                     draft.reference.platform, draft.reference.resource_kind,
                     draft.reference.native_id_hint, draft.reference.handle_hint,
                     draft.media_type, draft.captured_at, draft.source_as_of,
                     Jsonb(_policy_json(draft.policy)), draft.synthetic, digest,
                     str(path) if path else None, Jsonb(draft.coverage))
                ).fetchone()
                connection.execute(
                    "UPDATE ingestion_runs SET checkpoint=%s, input_complete=%s, records_used=records_used+1, "
                    "bytes_used=bytes_used+%s,requests_used=requests_used+%s WHERE id=%s",
                    (Jsonb(checkpoint), complete, len(draft.payload), draft.request_attempts, run_id)
                )
            return _observation(row)
        except Exception:
            if path:
                path.unlink(missing_ok=True)
            raise

    def get(self, observation_id: str) -> RawObservation:
        with self.db.connect() as connection:
            row = connection.execute("SELECT * FROM source_observations WHERE id=%s", (observation_id,)).fetchone()
        if row is None:
            raise EvidenceError("observation_not_found")
        return _observation(row)

    def load(self, observation_id: str) -> tuple[RawObservation, bytes]:
        observation = self.get(observation_id)
        if not _allowed(observation.policy, "process"):
            raise EvidenceError("evidence_unavailable")
        if observation.payload_path is None:
            raise EvidenceError("replay_unavailable")
        path = Path(observation.payload_path)
        if path.parent.resolve() != self.root:
            raise EvidenceError("invalid_payload_path")
        try:
            payload = path.read_bytes()
        except FileNotFoundError as error:
            raise EvidenceError("payload_missing") from error
        if hashlib.sha256(payload).hexdigest() != observation.payload_hash:
            raise EvidenceError("payload_corrupt")
        return observation, payload

    def mark(self, observation_id: str, status: str) -> None:
        if status not in {"applied", "quarantined"}:
            raise ValueError("Invalid observation status")
        with self.db.connect() as connection:
            connection.execute("UPDATE source_observations SET status=%s WHERE id=%s", (status, observation_id))

    def issue(self, run_id: str, observation_id: str | None, code: str, message: str) -> None:
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO ingestion_issues(run_id,observation_id,code,message) VALUES (%s,%s,%s,%s)",
                (run_id, observation_id, code, message)
            )

    def finish(self, run_id: str, status: str) -> None:
        with self.db.connect() as connection:
            connection.execute("UPDATE ingestion_runs SET status=%s WHERE id=%s", (status, run_id))

    def revoke(self, observation_id: str) -> None:
        observation = self.get(observation_id)
        policy = _policy_json(observation.policy)
        policy["revoked"] = True
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE source_observations SET policy=%s,payload_path=NULL WHERE id=%s",
                (Jsonb(policy), observation_id)
            )
        if observation.payload_path:
            Path(observation.payload_path).unlink(missing_ok=True)

    def expire(self) -> int:
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT id FROM source_observations WHERE payload_path IS NOT NULL "
                "AND (policy->>'expires_at') IS NOT NULL "
                "AND (policy->>'expires_at')::timestamptz <= now()"
            ).fetchall()
        for row in rows:
            self.revoke(str(row["id"]))
        return len(rows)

    def reconcile_orphans(self, minimum_age_seconds: int = 60) -> int:
        """Remove only old, task-shaped files absent from committed metadata."""
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT payload_path FROM source_observations WHERE payload_path IS NOT NULL"
            ).fetchall()
        referenced = {str(Path(row["payload_path"]).resolve()) for row in rows}
        removed = 0
        for pattern in ("*.bin", "*.tmp"):
            for path in self.root.glob(pattern):
                try:
                    uuid.UUID(path.stem)
                except ValueError:
                    continue
                if str(path.resolve()) in referenced or time.time() - path.stat().st_mtime < minimum_age_seconds:
                    continue
                path.unlink(missing_ok=True)
                removed += 1
        return removed
