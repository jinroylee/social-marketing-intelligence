"""Task-local history; governed source/publication owners retain evidence values."""

from contextlib import nullcontext
from dataclasses import asdict
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any

from psycopg import Connection

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.support import IngestedEvidence, SupportReference
from smi_knowledge import KnowledgePublications

from .policy import DiscoveryPolicy


def _references(document: list[dict[str, Any]]) -> tuple[SupportReference, ...]:
    return tuple(SupportReference(s['observation_id'], s['derivation_id'], tuple(s['assertion_ids']), tuple(s['metric_ids'])) for s in document)


class DiscoveryHistory:
    """Persist inspectable decisions without owning source copies or task authority.

    Mutations join the worker's fenced transaction. Comparing a prior publication
    never adopts its receipt, run or support as a new task's published result.
    """

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db, self.workspace_id = db, workspace_id
        self.evidence = IngestedEvidence(db, workspace_id)
        self.publications = KnowledgePublications(db, workspace_id)

    def migrate(self) -> None:
        """Install history after task, source and publication schemas."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def decide(self, task_id: str, scope: dict[str, Any], limits: dict[str, int], mapper_key: str,
               actor: ActorContext, *, now: datetime, connection: Connection) -> str:
        """Record one stable decision for this admitted task before retrieval.

        Exact query/subjects/window, input configuration, hard bounds and mapper/
        processing versions are compared. Every selected capture must be known,
        nonfuture, fresh and currently published; skips never advance capture age.
        """
        actor.require_workspace(self.workspace_id)
        if not isinstance(now, datetime) or now.utcoffset() is None:
            raise EvidenceError('invalid_discovery_clock')
        prior_decision = connection.execute('SELECT decision FROM discovery_history WHERE task_id=%s AND workspace_id=%s', (task_id, self.workspace_id)).fetchone()
        if prior_decision:
            return prior_decision['decision']
        policy = scope.get('discovery_policy')
        if policy is not None:
            DiscoveryPolicy(**policy).validate()
        query = scope['discovery']
        key = hashlib.sha256(json.dumps({'route': scope['route'], 'query': query}, sort_keys=True).encode()).hexdigest()
        context = {'manifest_hash': scope['manifest_hash'], 'route_version': scope['route_version'],
                   'mapper_key': mapper_key, 'processing_revision': policy['processing_revision'] if policy else 'canonical-v1',
                   'limits': limits, 'input': scope.get('discovery_context')}
        prior = connection.execute("SELECT * FROM discovery_history WHERE workspace_id=%s AND query_key=%s AND decision='retrieve' ORDER BY sequence DESC LIMIT 1", (self.workspace_id, key)).fetchone()
        decision, reason, freshness = 'retrieve', 'no_prior_retrieval', 'unknown'
        # A newer permitted capture cannot erase a withdrawal of an older
        # exact query/input. Consult matching historical bases before reuse.
        input_filter = "retrieval_context->'input'=%s" if context['input'] else "retrieval_context->>'manifest_hash'=%s"
        input_value = Jsonb(context['input']) if context['input'] else context['manifest_hash']
        candidates = connection.execute(
            "SELECT * FROM discovery_history WHERE workspace_id=%s AND query_key=%s AND decision='retrieve' "
            "AND support<>'[]'::jsonb AND " + input_filter + ' ORDER BY sequence DESC',
            (self.workspace_id, key, input_value)).fetchall()
        denied = None
        for candidate in candidates:
            basis = self.evidence.read(_references(candidate['support']), actor, purpose='process', include_synthetic=True, connection=connection)
            if any(m['availability'] != 'available' for m in basis):
                denied = candidate
                break
        if denied:
            prior = denied
            decision, reason, freshness = 'skip', 'prior_support_unavailable', 'unavailable'
        elif prior:
            reason = 'prior_incomplete_or_failed'
            references = _references(prior['support'])
            members = self.evidence.read(references, actor, purpose='process', include_synthetic=True, connection=connection) if references else []
            if context != prior['retrieval_context']:
                reason = 'retrieval_or_processing_context_changed'
            elif policy is None:
                reason = 'freshness_policy_unconfigured'
            elif prior['processing_complete'] and members:
                if any(m['support_status'] != 'current' for m in members):
                    reason, freshness = 'prior_support_superseded', 'unavailable'
                elif not self.publications.usable_publications(references, actor, include_synthetic=True, connection=connection):
                    reason, freshness = 'prior_support_not_published', 'unavailable'
                elif any(m['captured_at'] is None for m in members):
                    reason, freshness = 'capture_time_unknown', 'unknown'
                else:
                    captures = [datetime.fromisoformat(m['captured_at']) for m in members]
                    if any(capture > now for capture in captures):
                        reason, freshness = 'capture_time_in_future', 'unknown'
                    elif any(now - capture > timedelta(seconds=policy['max_capture_age_seconds']) for capture in captures):
                        reason, freshness = 'capture_stale', 'stale'
                    else:
                        decision, reason, freshness = 'skip', 'unchanged_fresh_published', 'fresh'
        elif policy is None:
            reason = 'freshness_policy_unconfigured'
        connection.execute('INSERT INTO discovery_history(task_id,workspace_id,query_key,query_scope,retrieval_context,policy,decision,reason,freshness,prior_task_id,prior_publication_id,decided_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (task_id, self.workspace_id, key, Jsonb(query), Jsonb(context), Jsonb(policy) if policy else None, decision, reason, freshness,
             prior['task_id'] if prior else None, (prior['usable_publication_ids'][0] if prior['usable_publication_ids'] else prior['publication_id']) if prior else None, now))
        return decision

    def record_support(self, task_id: str, support: tuple[SupportReference, ...], actor: ActorContext, *, connection: Connection) -> None:
        """Retain exact source references before unchanged-publication filtering."""
        actor.require_workspace(self.workspace_id)
        connection.execute('UPDATE discovery_history SET support=%s WHERE task_id=%s AND workspace_id=%s',
                           (Jsonb([asdict(s) for s in support]), task_id, self.workspace_id))

    def complete(self, task_id: str, actor: ActorContext, *, outcome: str, failure: dict[str, str] | None,
                 publication_id: str | None, coverage: dict[str, Any], connection: Connection) -> None:
        """Join the actual terminal task transaction without inventing a receipt."""
        actor.require_workspace(self.workspace_id)
        row = connection.execute('SELECT support FROM discovery_history WHERE task_id=%s AND workspace_id=%s', (task_id, self.workspace_id)).fetchone()
        if row is None:
            return
        references = _references(row['support'])
        processing_complete = (outcome in {'usable_update', 'no_usable_update'} and not failure
                    and coverage.get('collected_observations') == len(references) > 0
                    and coverage.get('remaining_inputs') == 0)
        usable = self.publications.usable_publications(references, actor, include_synthetic=True, connection=connection) if references else ()
        connection.execute('UPDATE discovery_history SET processing_complete=%s,usable_publication_ids=%s,outcome=%s,failure=%s,publication_id=%s,completed_at=now() WHERE task_id=%s AND workspace_id=%s',
                           (processing_complete, Jsonb(list(usable)), outcome, Jsonb(failure) if failure else None, publication_id, task_id, self.workspace_id))

    def read(self, task_id: str, actor: ActorContext, *, connection: Connection | None = None) -> dict[str, Any] | None:
        """Read history and governed capture/identity/method context after restart."""
        actor.require_workspace(self.workspace_id)
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            row = connection.execute('SELECT * FROM discovery_history WHERE task_id=%s AND workspace_id=%s', (task_id, self.workspace_id)).fetchone()
            if row is None:
                return None
            basis_task_id = row['prior_task_id'] if row['decision'] == 'skip' else row['task_id']
            basis = connection.execute('SELECT support FROM discovery_history WHERE task_id=%s AND workspace_id=%s', (basis_task_id, self.workspace_id)).fetchone()
            references = _references(basis['support']) if basis else ()
            members = self.evidence.read(references, actor, include_synthetic=True, connection=connection) if references else []
            usable = self.publications.usable_publications(references, actor, include_synthetic=True, connection=connection) if references else ()
        captures = []
        for member in members:
            capture = {'observation_id': member['observation_id'], 'derivation_id': member['derivation_id'],
                       'availability': member['availability'], 'support_status': member['support_status']}
            if member['availability'] == 'available':
                identities = {(f['platform'], f['namespace'], f['kind'], f['native_id']) for f in member['assertions'] + member['metrics']}
                capture.update(captured_at=member['captured_at'], source_as_of=member['source_as_of'], ingested_at=member['ingested_at'], method=member['method'],
                               source_identities=[dict(zip(('platform', 'namespace', 'kind', 'native_id'), key)) for key in sorted(identities)],
                               metric_definitions=sorted({m['definition'] for m in member['metrics']}))
            captures.append(capture)
        return {'decision': row['decision'], 'reason': row['reason'], 'freshness': row['freshness'], 'policy': row['policy'],
                'query_scope': row['query_scope'], 'retrieval_context': row['retrieval_context'], 'decided_at': row['decided_at'].isoformat(),
                'prior_task_id': str(row['prior_task_id']) if row['prior_task_id'] else None,
                'prior_publication_id': str(row['prior_publication_id']) if row['prior_publication_id'] else None,
                'publication_id': str(row['publication_id']) if row['publication_id'] else None,
                'processing_complete': row['processing_complete'], 'usable_publication_ids': list(usable),
                'recorded_usable_publication_ids': row['usable_publication_ids'],
                'capture_basis_task_id': str(basis_task_id),
                'outcome': row['outcome'], 'failure': row['failure'], 'captures': captures}
