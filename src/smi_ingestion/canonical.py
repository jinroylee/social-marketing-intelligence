"""Shared identity, derivation, and evidence-aware canonical reads."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from psycopg.types.json import Jsonb

from .contracts import ExternalKey, NormalizedBatch
from .db import Database
from .evidence import EvidenceError, _allowed, _policy_from_json


def _key_params(key: ExternalKey, synthetic: bool) -> tuple[Any, ...]:
    return (key.platform, key.namespace, key.kind, key.native_id, synthetic)


class CanonicalWriter:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _entity_id(connection, key: ExternalKey, synthetic: bool) -> str:
        if key.kind not in {"account", "content"} or not key.native_id:
            raise ValueError("invalid_external_identity")
        lock_name = "|".join(str(value) for value in _key_params(key, synthetic))
        connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (lock_name,))
        row = connection.execute(
            "SELECT entity_id FROM external_identities WHERE platform=%s AND namespace=%s "
            "AND kind=%s AND native_id=%s AND synthetic=%s", _key_params(key, synthetic)
        ).fetchone()
        if row:
            return str(row["entity_id"])
        entity_id = str(uuid.uuid4())
        connection.execute(
            "INSERT INTO canonical_entities(id,kind,synthetic) VALUES (%s,%s,%s)",
            (entity_id, key.kind, synthetic)
        )
        connection.execute(
            "INSERT INTO external_identities(platform,namespace,kind,native_id,synthetic,entity_id) "
            "VALUES (%s,%s,%s,%s,%s,%s)", (*_key_params(key, synthetic), entity_id)
        )
        return entity_id

    def apply(
        self, observation_id: str, batch: NormalizedBatch, mapper_key: str,
        policy_version: str = "canonical-v1"
    ) -> dict[str, Any]:
        with self.db.connect() as connection:
            observation = connection.execute(
                "SELECT * FROM source_observations WHERE id=%s FOR UPDATE", (observation_id,)
            ).fetchone()
            if observation is None:
                raise EvidenceError("observation_not_found")
            if not _allowed(_policy_from_json(observation["policy"]), "process"):
                raise EvidenceError("processing_not_permitted")
            existing = connection.execute(
                "SELECT id FROM derivations WHERE observation_id=%s AND mapper_key=%s AND policy_version=%s",
                (observation_id, mapper_key, policy_version)
            ).fetchone()
            if existing:
                return {"status": "duplicate", "entities": 0, "fields": 0, "metrics": 0}
            connection.execute(
                "UPDATE derivations SET active=FALSE WHERE observation_id=%s AND active=TRUE",
                (observation_id,)
            )
            derivation_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO derivations(id,observation_id,mapper_key,policy_version) VALUES (%s,%s,%s,%s)",
                (derivation_id, observation_id, mapper_key, policy_version)
            )
            keys = set(batch.entities)
            keys.update(field.subject for field in batch.fields)
            keys.update(metric.subject for metric in batch.metrics)
            entity_ids = {
                key: self._entity_id(connection, key, observation["synthetic"])
                for key in sorted(keys, key=lambda k: (k.platform, k.namespace, k.kind, k.native_id))
            }
            for field in batch.fields:
                connection.execute(
                    "INSERT INTO field_assertions(id,derivation_id,entity_id,field,state,value,source_locator,reason) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (str(uuid.uuid4()), derivation_id, entity_ids[field.subject], field.field,
                     field.state, Jsonb(field.value) if field.value is not None else None,
                     field.locator, field.reason)
                )
            for metric in batch.metrics:
                connection.execute(
                    "INSERT INTO metric_observations(id,derivation_id,entity_id,definition,native_name,"
                    "value,raw_display,precision,unit,measured_at,source_locator) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (str(uuid.uuid4()), derivation_id, entity_ids[metric.subject], metric.definition,
                     metric.native_name, metric.value, metric.raw_display, metric.precision,
                     metric.unit, metric.measured_at, metric.locator)
                )
            for unresolved in batch.unresolved:
                connection.execute(
                    "INSERT INTO unresolved_candidates(id,derivation_id,kind,source_locator,reason) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (str(uuid.uuid4()), derivation_id, unresolved.kind, unresolved.locator, unresolved.reason)
                )
            return {
                "status": "applied", "entities": len(entity_ids),
                "fields": len(batch.fields), "metrics": len(batch.metrics),
                "unresolved": len(batch.unresolved)
            }


class CanonicalReader:
    def __init__(self, db: Database):
        self.db = db

    def _identity(self, connection, key: ExternalKey, include_synthetic: bool):
        return connection.execute(
            "SELECT entity_id,synthetic FROM external_identities WHERE platform=%s AND namespace=%s "
            "AND kind=%s AND native_id=%s AND (synthetic=FALSE OR %s=TRUE) "
            "ORDER BY synthetic LIMIT 1",
            (key.platform, key.namespace, key.kind, key.native_id, include_synthetic)
        ).fetchone()

    @staticmethod
    def _visible(row: dict[str, Any]) -> bool:
        return _allowed(_policy_from_json(row["policy"]), "display")

    def entity(self, key: ExternalKey, include_synthetic: bool = False) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            identity = self._identity(connection, key, include_synthetic)
            if identity is None:
                return None
            rows = connection.execute(
                "SELECT f.field,f.state,f.value,f.reason,f.source_locator,o.id AS observation_id,"
                "o.provider_id,o.reference,o.captured_at,o.source_as_of,o.policy "
                "FROM field_assertions f JOIN derivations d ON d.id=f.derivation_id "
                "JOIN source_observations o ON o.id=d.observation_id "
                "WHERE f.entity_id=%s AND d.active=TRUE",
                (identity["entity_id"],)
            ).fetchall()
        rows = [row for row in rows if self._visible(row)]
        if not rows and not self.metrics(key, include_synthetic):
            return None
        by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_field[row["field"]].append(row)
        fields: dict[str, Any] = {}
        for name, candidates in by_field.items():
            by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in candidates:
                if row["state"] in {"observed", "removed"}:
                    by_provider[row["provider_id"]].append(row)
            selected = []
            conflict = False
            for provider_rows in by_provider.values():
                known_source_times = [row["source_as_of"] is not None for row in provider_rows]
                # Mixed time semantics cannot safely be ordered by import or capture time.
                if any(known_source_times) and not all(known_source_times):
                    selected.extend(provider_rows)
                    conflict |= len({repr(row["value"]) for row in provider_rows}) > 1
                else:
                    timestamp = (lambda row: row["source_as_of"]) if all(known_source_times) else (lambda row: row["captured_at"])
                    if any(timestamp(row) is None for row in provider_rows):
                        selected.extend(provider_rows)
                        conflict |= len({repr(row["value"]) for row in provider_rows}) > 1
                    else:
                        latest = max(timestamp(row) for row in provider_rows)
                        current = [row for row in provider_rows if timestamp(row) == latest]
                        selected.extend(current)
                        conflict |= len({repr(row["value"]) for row in current}) > 1
            observed = [row for row in selected if row["state"] == "observed"]
            unique_values = {repr(row["value"]) for row in observed}
            conflict |= len(unique_values) > 1
            provenance = [
                {"observation_id": str(row["observation_id"]), "provider": row["provider_id"],
                 "source_reference": row["reference"],
                 "locator": row["source_locator"], "captured_at": row["captured_at"].isoformat() if row["captured_at"] else None}
                for row in selected
            ]
            fields[name] = {
                "value": observed[0]["value"] if observed and not conflict else None,
                "state": "conflict" if conflict else "observed" if observed else "removed" if selected else "unknown",
                "provenance": provenance,
            }
        return {"id": str(identity["entity_id"]), "key": key.__dict__, "synthetic": identity["synthetic"], "fields": fields}

    def metrics(self, key: ExternalKey, include_synthetic: bool = False) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            identity = self._identity(connection, key, include_synthetic)
            if identity is None:
                return []
            rows = connection.execute(
                "SELECT m.definition,m.native_name,m.value,m.raw_display,m.precision,m.unit,m.measured_at,"
                "m.source_locator,o.id AS observation_id,o.provider_id,o.reference,o.captured_at,o.policy "
                "FROM metric_observations m JOIN derivations d ON d.id=m.derivation_id "
                "JOIN source_observations o ON o.id=d.observation_id "
                "WHERE m.entity_id=%s AND d.active=TRUE ORDER BY o.captured_at NULLS LAST,o.ingested_at",
                (identity["entity_id"],)
            ).fetchall()
        result = []
        for row in rows:
            if not self._visible(row):
                continue
            value = row["value"]
            if isinstance(value, Decimal):
                value = int(value) if value == int(value) else float(value)
            result.append({
                "definition": row["definition"], "native_name": row["native_name"],
                "value": value, "raw_display": row["raw_display"], "precision": row["precision"],
                "unit": row["unit"], "measured_at": row["measured_at"].isoformat() if row["measured_at"] else None,
                "captured_at": row["captured_at"].isoformat() if row["captured_at"] else None,
                "observation_id": str(row["observation_id"]), "provider": row["provider_id"],
                "source_reference": row["reference"],
                "locator": row["source_locator"]
            })
        return result
