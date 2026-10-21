"""Read pinned source support without substituting current canonical values."""

from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from ..db import Database
from ..evidence import EvidenceError, policy_allows, policy_from_json
from ..evidence_sets import ActorContext


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


@dataclass(frozen=True)
class SupportReference:
    """Exact source membership; IDs must belong to the nominated derivation."""

    observation_id: str
    derivation_id: str
    assertion_ids: tuple[str, ...]
    metric_ids: tuple[str, ...] = ()

    def __post_init__(self):
        try:
            if not isinstance(self.assertion_ids, tuple) or not isinstance(self.metric_ids, tuple):
                raise ValueError
            for value in (self.observation_id, self.derivation_id, *self.assertion_ids, *self.metric_ids):
                if str(uuid.UUID(value)) != value:
                    raise ValueError
            if (not self.assertion_ids and not self.metric_ids) or len(set(self.assertion_ids)) != len(self.assertion_ids) or len(set(self.metric_ids)) != len(self.metric_ids):
                raise ValueError
            if len(self.assertion_ids) + len(self.metric_ids) > 1000:
                raise ValueError
        except (ValueError, TypeError, AttributeError) as error:
            raise EvidenceError('invalid_support_reference') from error


class IngestedEvidence:
    """Public exact-support reader with current policy and source transaction locks."""

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db = db
        self.workspace_id = workspace_id

    def select_run(self, run_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> tuple[SupportReference, ...]:
        """Select up to 100 applied observations and their current exact assertions."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            run = connection.execute('SELECT id FROM ingestion_runs WHERE id=%s AND workspace_id=%s', (run_id, self.workspace_id)).fetchone()
            if run is None:
                raise EvidenceError('ingestion_run_not_found')
            rows = connection.execute(
                'SELECT o.id,d.id AS derivation_id FROM source_observations o JOIN derivations d ON d.observation_id=o.id '
                "WHERE o.run_id=%s AND o.status='applied' AND d.active AND (NOT o.synthetic OR %s) ORDER BY o.item_index LIMIT 101",
                (run_id, include_synthetic),
            ).fetchall()
            if len(rows) > 100:
                raise EvidenceError('support_selection_limit')
            references = []
            for row in rows:
                fields = connection.execute('SELECT id FROM field_assertions WHERE derivation_id=%s ORDER BY id', (row['derivation_id'],)).fetchall()
                metrics = connection.execute('SELECT id FROM metric_observations WHERE derivation_id=%s ORDER BY id', (row['derivation_id'],)).fetchall()
                if fields or metrics:
                    references.append(SupportReference(str(row['id']), str(row['derivation_id']), tuple(str(f['id']) for f in fields), tuple(str(m['id']) for m in metrics)))
        return tuple(references)

    def require_run_support(self, run_id: str, references: tuple[SupportReference, ...], actor: ActorContext, *,
                            include_synthetic: bool = False, connection=None) -> None:
        """Validate exact applied support's immutable run lineage without reading values.

        Historical publication recovery still needs this lineage after source
        policy withdrawal or derivation supersession. This grants no permission
        to process/display values or publish support. Caller transactions retain
        the source/derivation locks through their dependent commit.
        """
        actor.require_workspace(self.workspace_id)
        if not 1 <= len(references) <= 100 or len({r.observation_id for r in references}) != len(references):
            raise EvidenceError('invalid_support_selection')
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            for reference in references:
                row = connection.execute(
                    'SELECT o.synthetic FROM source_observations o JOIN ingestion_runs r ON r.id=o.run_id '
                    'JOIN derivations d ON d.observation_id=o.id '
                    "WHERE o.id=%s AND d.id=%s AND o.run_id=%s AND r.workspace_id=%s AND o.status='applied' FOR SHARE OF o,d",
                    (reference.observation_id, reference.derivation_id, run_id, self.workspace_id),
                ).fetchone()
                if row is None:
                    raise EvidenceError('ingested_support_run_mismatch')
                if row['synthetic'] and not include_synthetic:
                    raise EvidenceError('synthetic_evidence_excluded')
                fields = connection.execute('SELECT count(*) AS n FROM field_assertions WHERE derivation_id=%s AND id=ANY(%s::uuid[])',
                                            (reference.derivation_id, list(reference.assertion_ids))).fetchone()['n']
                metrics = connection.execute('SELECT count(*) AS n FROM metric_observations WHERE derivation_id=%s AND id=ANY(%s::uuid[])',
                                             (reference.derivation_id, list(reference.metric_ids))).fetchone()['n']
                if fields != len(reference.assertion_ids) or metrics != len(reference.metric_ids):
                    raise EvidenceError('invalid_support_reference')

    def read(
        self, references: tuple[SupportReference, ...], actor: ActorContext, *,
        purpose: Literal['display', 'process'] = 'display', include_synthetic: bool = False, connection=None,
    ) -> list[dict[str, Any]]:
        """Read only exact selected IDs; caller-owned transactions lock policy and derivations."""
        actor.require_workspace(self.workspace_id)
        if purpose not in {'display', 'process'}:
            raise EvidenceError('invalid_evidence_purpose')
        if not 1 <= len(references) <= 100 or len({r.observation_id for r in references}) != len(references):
            raise EvidenceError('invalid_support_selection')
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            members = []
            for reference in references:
                row = connection.execute(
                    'SELECT o.*,d.active,d.mapper_key,d.policy_version,d.created_at AS derived_at FROM source_observations o '
                    'JOIN ingestion_runs r ON r.id=o.run_id JOIN derivations d ON d.observation_id=o.id '
                    'WHERE o.id=%s AND d.id=%s AND r.workspace_id=%s FOR SHARE OF o,d',
                    (reference.observation_id, reference.derivation_id, self.workspace_id),
                ).fetchone()
                if row is None:
                    raise EvidenceError('ingested_support_not_found')
                if row['synthetic'] and not include_synthetic:
                    raise EvidenceError('synthetic_evidence_excluded')
                fields = connection.execute(
                    'SELECT f.id::text AS assertion_id,f.entity_id::text AS subject_id,f.field,f.state,f.value,f.reason,'
                    'f.source_locator AS locator,e.platform,e.namespace,e.kind,e.native_id FROM field_assertions f '
                    'JOIN external_identities e ON e.entity_id=f.entity_id WHERE f.derivation_id=%s AND f.id=ANY(%s::uuid[]) ORDER BY f.id',
                    (reference.derivation_id, list(reference.assertion_ids)),
                ).fetchall()
                metrics = connection.execute(
                    'SELECT m.id::text AS metric_id,m.entity_id::text AS subject_id,m.definition,m.native_name,m.value,m.raw_display,m.precision,m.unit,m.measured_at,'
                    'm.source_locator AS locator,e.platform,e.namespace,e.kind,e.native_id FROM metric_observations m '
                    'JOIN external_identities e ON e.entity_id=m.entity_id WHERE m.derivation_id=%s AND m.id=ANY(%s::uuid[]) ORDER BY m.id',
                    (reference.derivation_id, list(reference.metric_ids)),
                ).fetchall()
                if len(fields) != len(reference.assertion_ids) or len(metrics) != len(reference.metric_ids) or row['status'] != 'applied':
                    raise EvidenceError('invalid_support_reference')
                # A capture/mapping/selection identity, independent of new run UUIDs.
                # Keep the raw digest inside the source owner; consumers get only
                # the one-way identity needed to compare already published support.
                version = {'capture': [row[key] for key in (
                    'adapter_id', 'provider_id', 'format_version', 'reference', 'payload_hash',
                    'captured_at', 'source_as_of', 'synthetic', 'mapper_key', 'policy_version')],
                    'fields': sorted((f['field'], f['locator'], f['platform'], f['namespace'], f['kind'], f['native_id']) for f in fields),
                    'metrics': sorted((m['definition'], m['locator'], m['platform'], m['namespace'], m['kind'], m['native_id']) for m in metrics)}
                content_version = hashlib.sha256(json.dumps(_json_value(version), sort_keys=True, default=str).encode()).hexdigest()
                policy = policy_from_json(row['policy'])
                member = {**asdict(reference), 'support_status': 'current' if row['active'] else 'superseded_review_required',
                          'availability': 'available' if policy_allows(policy, purpose) else 'unavailable',
                          'policy': {f'can_{p}': policy_allows(policy, p) for p in ('process', 'display', 'retain')}}
                if member['availability'] == 'unavailable':
                    member['reason'] = 'source_policy_denied'
                else:
                    member.update(content_version=content_version, source_reference=row['reference'], run_id=str(row['run_id']), synthetic=row['synthetic'],
                                  provider=row['provider_id'], adapter=row['adapter_id'], captured_at=row['captured_at'],
                                  source_as_of=row['source_as_of'], ingested_at=row['ingested_at'], coverage=row['coverage'],
                                  policy={f'can_{p}': policy_allows(policy, p) for p in ('process', 'display', 'retain')},
                                  method={'mapper_key': row['mapper_key'], 'policy_version': row['policy_version'], 'derived_at': row['derived_at']},
                                  assertions=fields, metrics=metrics)
                members.append(member)
        return _json_value(members)
