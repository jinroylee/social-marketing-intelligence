"""Frozen support reads with live source-policy checks and workspace isolation."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from ..db import Database
from ..evidence import EvidenceError, policy_allows, policy_from_json
from .access import ActorContext


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == int(value) else str(value)
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


class EvidenceSetReader:
    """Read exact imported assertions, including inactive historical derivations."""

    def __init__(self, db: Database, workspace_id: str = "local"):
        self.db = db
        self.workspace_id = workspace_id

    def list_sets(self, actor: ActorContext, *, include_synthetic: bool = False) -> list[dict[str, Any]]:
        """List workspace-scoped dataset metadata without returning source values."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT dataset_id,digest,manifest,synthetic,imported_at FROM evidence_sets "
                "WHERE workspace_id=%s AND (NOT synthetic OR %s) ORDER BY imported_at,dataset_id",
                (self.workspace_id, include_synthetic),
            ).fetchall()
        return [{"dataset_id": row["dataset_id"], "digest": row["digest"], "synthetic": row["synthetic"],
                 "posts": row["manifest"]["expected_posts"], "accounts": row["manifest"]["expected_accounts"],
                 "imported_at": row["imported_at"].isoformat()} for row in rows]

    def statuses(
        self, dataset_id: str, actor: ActorContext, *, include_synthetic: bool = False, connection=None,
    ) -> dict[str, dict[str, bool]]:
        """Expose content-free support health for dependent-store cleanup.

        A caller-owned transaction holds source/derivation share locks until its
        dependent writes commit, preventing policy withdrawal racing those writes.
        """
        actor.require_workspace(self.workspace_id)
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            dataset = connection.execute(
                "SELECT synthetic,manifest FROM evidence_sets WHERE workspace_id=%s AND dataset_id=%s",
                (self.workspace_id, dataset_id),
            ).fetchone()
            if dataset is None:
                raise EvidenceError("evidence_set_not_found")
            if dataset["synthetic"] and not include_synthetic:
                raise EvidenceError("synthetic_evidence_excluded")
            rows = connection.execute(
                "SELECT m.observation_id,o.policy,d.active FROM evidence_set_members m "
                "JOIN source_observations o ON o.id=m.observation_id JOIN derivations d ON d.id=m.derivation_id "
                "WHERE m.workspace_id=%s AND m.dataset_id=%s FOR SHARE OF o,d",
                (self.workspace_id, dataset_id),
            ).fetchall()
            if len(rows) != dataset["manifest"]["expected_posts"]:
                raise EvidenceError("evidence_set_incomplete")
            return {str(row["observation_id"]): {
                **{f"can_{purpose}": policy_allows(policy_from_json(row["policy"]), purpose)
                   for purpose in ("display", "process", "retain")},
                "current": row["active"],
            } for row in rows}

    def read(
        self, dataset_id: str, actor: ActorContext, *,
        purpose: Literal["display", "process"] = "display", include_synthetic: bool = False,
    ) -> dict[str, Any]:
        """Return pinned support or tombstones; process reads never use display permission.

        Source policy is checked at each read. Caller identity must be supplied by
        a trusted application boundary; this API does not authenticate a network user.
        """
        actor.require_workspace(self.workspace_id)
        if purpose not in {"display", "process"}:
            raise EvidenceError("invalid_evidence_purpose")
        with self.db.connect() as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            dataset = connection.execute(
                "SELECT * FROM evidence_sets WHERE workspace_id=%s AND dataset_id=%s",
                (self.workspace_id, dataset_id),
            ).fetchone()
            if dataset is None:
                raise EvidenceError("evidence_set_not_found")
            if dataset["synthetic"] and not include_synthetic:
                raise EvidenceError("synthetic_evidence_excluded")
            rows = connection.execute(
                "SELECT m.*,o.reference,o.provider_id,o.adapter_id,o.captured_at,o.source_as_of,"
                "o.ingested_at,o.policy,o.coverage,d.active,d.mapper_key,d.policy_version,"
                "d.created_at AS derived_at FROM evidence_set_members m "
                "JOIN source_observations o ON o.id=m.observation_id "
                "JOIN derivations d ON d.id=m.derivation_id "
                "WHERE m.workspace_id=%s AND m.dataset_id=%s ORDER BY m.position",
                (self.workspace_id, dataset_id),
            ).fetchall()
            if len(rows) != dataset["manifest"]["expected_posts"]:
                raise EvidenceError("evidence_set_incomplete")
            members = []
            for row in rows:
                policy = policy_from_json(row["policy"])
                member = {
                    "position": row["position"], "observation_id": str(row["observation_id"]),
                    "derivation_id": str(row["derivation_id"]),
                    "origin_observation_id": str(row["origin_observation_id"]),
                    "origin_run_id": str(row["origin_run_id"]),
                    "availability": "available" if policy_allows(policy, purpose) else "unavailable",
                }
                members.append(member)
                if member["availability"] == "unavailable":
                    member["reason"] = "source_policy_denied"
                    continue
                fields = connection.execute(
                    "SELECT f.id::text AS assertion_id,f.entity_id::text AS subject_id,f.field,f.state,"
                    "f.value,f.reason,f.source_locator AS locator,e.platform,e.namespace,e.kind,e.native_id "
                    "FROM field_assertions f JOIN external_identities e ON e.entity_id=f.entity_id "
                    "WHERE f.derivation_id=%s ORDER BY e.kind,f.field,f.source_locator",
                    (row["derivation_id"],),
                ).fetchall()
                metrics = connection.execute(
                    "SELECT id::text AS metric_id,entity_id::text AS subject_id,definition,native_name,value,"
                    "raw_display,precision,unit,measured_at,source_locator AS locator "
                    "FROM metric_observations WHERE derivation_id=%s ORDER BY definition,source_locator",
                    (row["derivation_id"],),
                ).fetchall()
                member.update({
                    "source_reference": row["reference"], "provider": row["provider_id"],
                    "adapter": row["adapter_id"], "captured_at": row["captured_at"],
                    "source_as_of": row["source_as_of"], "recorded_at": row["ingested_at"],
                    "policy": asdict(policy), "coverage": row["coverage"],
                    "method": {"mapper_key": row["mapper_key"], "policy_version": row["policy_version"],
                               "derived_at": row["derived_at"]},
                    "support_status": "current" if row["active"] else "superseded_review_required",
                    "assertions": fields, "metrics": metrics,
                })
        available = sum(member["availability"] == "available" for member in members)
        return _json_value({
            "dataset_id": dataset_id, "workspace_id": self.workspace_id, "digest": dataset["digest"],
            "manifest": dataset["manifest"], "synthetic": dataset["synthetic"],
            "importer_version": dataset["importer_version"], "imported_by": dataset["imported_by"],
            "imported_at": dataset["imported_at"], "run_id": str(dataset["run_id"]), "purpose": purpose,
            "coverage": {"scope": "selected_posts", "total_members": len(members),
                         "available_members": available, "unavailable_members": len(members) - available,
                         "original_accounts": dataset["manifest"]["expected_accounts"]},
            "members": members,
        })
