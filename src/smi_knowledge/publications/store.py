"""Atomic publication membership; source copies stay with their existing owners."""

from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import nullcontext
from dataclasses import asdict
from typing import Any, Literal

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.support import IngestedEvidence, SupportReference

from ..store import KnowledgeStore


class KnowledgePublications:
    """Publish exact source support without requiring a frozen imported dataset."""

    method_version = 'ingested-support-publication-v1'

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db = db
        self.workspace_id = workspace_id
        self.evidence = IngestedEvidence(db, workspace_id)

    def migrate(self) -> None:
        """Install shared knowledge and publication tables after ingestion migrations."""
        KnowledgeStore(self.db, self.workspace_id).migrate()

    def publish(self, support: tuple[SupportReference, ...], actor: ActorContext, *, request_id: str,
                interpretation_ids: tuple[str, ...] = (), include_synthetic: bool = False) -> dict[str, Any]:
        """Commit one validated bounded selection, retaining the actual producer."""
        actor.require_workspace(self.workspace_id)
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError('invalid_publication_request_id')
        document = {'support': [asdict(reference) for reference in support],
                    'producer': {'actor_id': actor.actor_id, 'kind': actor.kind}, 'method_version': self.method_version,
                    'interpretation_ids': interpretation_ids, 'include_synthetic': include_synthetic}
        digest = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'publication:{self.workspace_id}:{request_id}',))
            existing = connection.execute('SELECT id,request_digest FROM knowledge_publications WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if existing:
                if existing['request_digest'] != digest:
                    raise EvidenceError('publication_request_conflict')
                return {'status': 'duplicate', 'publication_id': str(existing['id'])}
            members = self.evidence.read(support, actor, purpose='process', include_synthetic=include_synthetic, connection=connection)
            if any(m['availability'] != 'available' or m['support_status'] != 'current' for m in members):
                raise EvidenceError('publication_support_unavailable')
            interpretations = KnowledgeStore(self.db, self.workspace_id).read_interpretations(
                interpretation_ids, actor, purpose='process', include_synthetic=include_synthetic, connection=connection)
            selected_assertions = {(m['observation_id'], a['assertion_id']) for m in members for a in m['assertions']}
            for claim in interpretations:
                if (claim['observation_id'], claim['source_assertion_id']) not in selected_assertions:
                    raise EvidenceError('publication_interpretation_support_mismatch')
                if claim['state'] != 'supported':
                    raise EvidenceError('publication_interpretation_unavailable')
            publication_id = str(uuid.uuid4())
            coverage = {'scope': 'selected_ingested_support', 'members': len(members), 'interpretations': len(interpretations)}
            connection.execute(
                'INSERT INTO knowledge_publications(id,workspace_id,request_id,request_digest,method_version,producer_id,producer_kind,coverage,synthetic) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (publication_id, self.workspace_id, request_id, digest, self.method_version, actor.actor_id, actor.kind, Jsonb(coverage), any(m['synthetic'] for m in members)),
            )
            for position, reference in enumerate(support):
                connection.execute(
                    'INSERT INTO knowledge_publication_support(publication_id,position,observation_id,derivation_id,assertion_ids,metric_ids,content_version) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    (publication_id, position, reference.observation_id, reference.derivation_id, list(reference.assertion_ids), list(reference.metric_ids), members[position]['content_version']),
                )
            for position, identity in enumerate(interpretation_ids):
                connection.execute('INSERT INTO knowledge_publication_interpretations(publication_id,position,interpretation_id) VALUES (%s,%s,%s)',
                                   (publication_id, position, identity))
        return {'status': 'published', 'publication_id': publication_id}

    def unpublished(self, support: tuple[SupportReference, ...], actor: ActorContext, *, include_synthetic: bool = False) -> tuple[SupportReference, ...]:
        """Select captures/mappings not already usable in a committed publication.

        This compares source-owned capture identities, not entity counts or market
        novelty. A later capture or mapping is distinct. Current process policy and
        derivation health are required on both sides; withdrawn support cannot make
        a newly permitted capture appear already usable.
        """
        actor.require_workspace(self.workspace_id)
        if not support:
            return ()
        members = self.evidence.read(support, actor, purpose='process', include_synthetic=include_synthetic)
        if any(m['availability'] != 'available' or m['support_status'] != 'current' for m in members):
            raise EvidenceError('publication_support_unavailable')
        versions = {m['content_version'] for m in members}
        existing_versions = set()
        with self.db.connect() as connection:
            rows = connection.execute(
                'SELECT s.* FROM knowledge_publication_support s JOIN knowledge_publications p ON p.id=s.publication_id '
                'WHERE p.workspace_id=%s AND (NOT p.synthetic OR %s) AND (s.content_version=ANY(%s) OR s.content_version IS NULL)',
                (self.workspace_id, include_synthetic, list(versions)),
            ).fetchall()
            for row in rows:
                reference = SupportReference(str(row['observation_id']), str(row['derivation_id']), tuple(str(i) for i in row['assertion_ids']), tuple(str(i) for i in row['metric_ids']))
                member = self.evidence.read((reference,), actor, purpose='process', include_synthetic=include_synthetic, connection=connection)[0]
                if member['availability'] == 'available' and member['support_status'] == 'current':
                    existing_versions.add(member['content_version'])
                    if row['content_version'] is None:
                        connection.execute('UPDATE knowledge_publication_support SET content_version=%s WHERE publication_id=%s AND position=%s', (member['content_version'], row['publication_id'], row['position']))
        return tuple(reference for reference, member in zip(support, members) if member['content_version'] not in existing_versions)

    def list(self, actor: ActorContext, *, include_synthetic: bool = False, limit: int | None = None, newest_first: bool = False, connection=None) -> list[dict[str, Any]]:
        """List committed publication metadata within the trusted actor's workspace."""
        actor.require_workspace(self.workspace_id)
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 1000):
            raise EvidenceError('invalid_publication_limit')
        order = 'published_at DESC,id DESC' if newest_first else 'published_at,id'
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            rows = connection.execute('SELECT id,published_at,producer_id,producer_kind,coverage FROM knowledge_publications WHERE workspace_id=%s AND (NOT synthetic OR %s) ORDER BY ' + order + ' LIMIT %s', (self.workspace_id, include_synthetic, limit)).fetchall()
        return [{'publication_id': str(row['id']), 'published_at': row['published_at'].isoformat(),
                 'producer': {'actor_id': row['producer_id'], 'kind': row['producer_kind']}, 'coverage': row['coverage']} for row in rows]

    def read(self, publication_id: str, actor: ActorContext, *, purpose: Literal['display', 'process'] = 'display', include_synthetic: bool = False, connection=None) -> dict[str, Any]:
        """Reopen committed membership under current policy without replacing support."""
        actor.require_workspace(self.workspace_id)
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            row = connection.execute('SELECT * FROM knowledge_publications WHERE id=%s AND workspace_id=%s', (publication_id, self.workspace_id)).fetchone()
            if row is None:
                raise EvidenceError('knowledge_publication_not_found')
            if row['synthetic'] and not include_synthetic:
                raise EvidenceError('synthetic_evidence_excluded')
            rows = connection.execute('SELECT * FROM knowledge_publication_support WHERE publication_id=%s ORDER BY position', (publication_id,)).fetchall()
            references = tuple(SupportReference(str(r['observation_id']), str(r['derivation_id']), tuple(str(i) for i in r['assertion_ids']), tuple(str(i) for i in r['metric_ids'])) for r in rows)
            members = self.evidence.read(references, actor, purpose=purpose, include_synthetic=include_synthetic, connection=connection)
            interpretation_rows = connection.execute('SELECT interpretation_id FROM knowledge_publication_interpretations WHERE publication_id=%s ORDER BY position', (publication_id,)).fetchall()
            interpretations = KnowledgeStore(self.db, self.workspace_id).read_interpretations(
                tuple(str(r['interpretation_id']) for r in interpretation_rows), actor, purpose=purpose, include_synthetic=include_synthetic, connection=connection)
        return {'publication_id': publication_id, 'workspace_id': self.workspace_id, 'published_at': row['published_at'].isoformat(),
                'producer': {'actor_id': row['producer_id'], 'kind': row['producer_kind']}, 'method_version': row['method_version'],
                'coverage': row['coverage'], 'members': members, 'interpretations': interpretations,
                'current_coverage': {'available_members': sum(m['availability'] == 'available' for m in members),
                                     'unavailable_members': sum(m['availability'] != 'available' for m in members),
                                     'superseded_members': sum(m['support_status'] != 'current' for m in members)}}
