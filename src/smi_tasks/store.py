"""Durable task admission; campaign and source/publication owners keep their data."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import uuid
from typing import Any

from psycopg.types.json import Jsonb

from smi_campaigns import CampaignStore
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from .contracts import OfflineRoute


class AcquisitionTasks:
    """Submit and inspect bounded offline tasks in one trusted workspace."""

    scope_version = 'campaign-offline-v1'

    def __init__(self, db: Database, workspace_id: str = 'local', *, route: OfflineRoute | None = None):
        self.db, self.workspace_id, self.route = db, workspace_id, route

    def migrate(self) -> None:
        """Install tasks after ingestion, knowledge and campaign migrations."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def submit_campaign(self, campaign_id: str, actor: ActorContext, *, brief_id: str, purpose: str, request_id: str) -> dict[str, Any]:
        """Persist acknowledgment before I/O; the trusted campaign establishes origin."""
        actor.require_workspace(self.workspace_id)
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError('invalid_task_request_id')
        if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 1000:
            raise EvidenceError('invalid_task_purpose')
        if self.route is None:
            raise EvidenceError('offline_task_route_unconfigured')
        campaign = CampaignStore(self.db, self.workspace_id).read_campaign(campaign_id, actor)
        brief = next((b for b in campaign['briefs'] if b['id'] == brief_id), None)
        if brief is None:
            raise EvidenceError('campaign_brief_not_found')
        path, digest, manifest = self.route.snapshot()
        scope = {'campaign_id': campaign_id, 'brief_id': brief_id, 'brief_version': brief['version'],
                 'purpose': purpose, 'route': 'fixture-json', 'route_version': self.route.version,
                 'manifest_hash': digest, 'references': [item.get('reference', '') for item in manifest['items']]}
        limits = asdict(self.route.limits)
        body = {'scope': scope, 'scope_version': self.scope_version, 'limits': limits,
                'manifest_path': str(path), 'initiator': {'actor_id': actor.actor_id, 'kind': actor.kind}, 'origin': 'campaign'}
        request_digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'task:{self.workspace_id}:{request_id}',))
            prior = connection.execute('SELECT id,request_digest FROM acquisition_tasks WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior:
                if prior['request_digest'] != request_digest:
                    raise EvidenceError('task_request_conflict')
                return {'status': 'duplicate', 'task_id': str(prior['id'])}
            # Pin admission to a still-current brief without allowing a concurrent edit
            # to authorize work against a different campaign question.
            current = connection.execute('SELECT brief_version FROM campaigns WHERE id=%s AND workspace_id=%s FOR SHARE', (campaign_id, self.workspace_id)).fetchone()
            if current is None or current['brief_version'] != brief['version']:
                raise EvidenceError('brief_version_conflict')
            task_id = str(uuid.uuid4())
            connection.execute('INSERT INTO acquisition_tasks(id,workspace_id,request_id,request_digest,origin,campaign_id,brief_id,initiator_id,initiator_kind,scope_version,scope,limits,manifest_path,manifest_hash) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (task_id, self.workspace_id, request_id, request_digest, 'campaign', campaign_id, brief_id, actor.actor_id, actor.kind, self.scope_version, Jsonb(scope), Jsonb(limits), str(path), digest))
        return {'status': 'accepted', 'task_id': task_id}

    def list(self, actor: ActorContext) -> list[dict[str, Any]]:
        """List the newest 100 task acknowledgments in the configured workspace."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute('SELECT id,status,outcome,submitted_at FROM acquisition_tasks WHERE workspace_id=%s ORDER BY submitted_at DESC,id DESC LIMIT 100', (self.workspace_id,)).fetchall()
        return [{'task_id': str(r['id']), 'status': r['status'], 'outcome': r['outcome'], 'submitted_at': r['submitted_at'].isoformat()} for r in rows]

    def read(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        """Reopen exact task metadata and sanitized run/publication lineage after restart."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM acquisition_tasks WHERE id=%s AND workspace_id=%s', (task_id, self.workspace_id)).fetchone()
            if row is None:
                raise EvidenceError('acquisition_task_not_found')
            attempts = connection.execute('SELECT * FROM acquisition_attempts WHERE task_id=%s ORDER BY number', (task_id,)).fetchall()
            publications = connection.execute('SELECT publication_id FROM acquisition_task_publications WHERE task_id=%s ORDER BY publication_id', (task_id,)).fetchall()
        return {'task_id': task_id, 'workspace_id': self.workspace_id, 'request_id': row['request_id'],
                'origin': row['origin'], 'initiator': {'actor_id': row['initiator_id'], 'kind': row['initiator_kind']},
                'scope_version': row['scope_version'], 'scope': row['scope'], 'limits': row['limits'], 'attempt_limit': row['attempt_limit'],
                'status': row['status'], 'outcome': row['outcome'], 'coverage': row['coverage'],
                'failure': {'phase': row['failure_phase'], 'code': row['failure_code']} if row['failure_code'] else None,
                'submitted_at': row['submitted_at'].isoformat(), 'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None,
                'publication_ids': [str(p['publication_id']) for p in publications],
                'attempts': [{'attempt_id': str(a['id']), 'number': a['number'], 'run_id': str(a['run_id']),
                              'producer': {'actor_id': a['producer_id'], 'kind': a['producer_kind']}, 'phases': a['phases'],
                              'started_at': a['started_at'].isoformat(), 'finished_at': a['finished_at'].isoformat() if a['finished_at'] else None} for a in attempts]}
