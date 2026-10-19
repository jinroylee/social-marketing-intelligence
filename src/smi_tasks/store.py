"""Durable task/proposal admission; source and publication owners keep their data."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import uuid
from typing import Any

from psycopg.types.json import Jsonb

from smi_campaigns import CampaignStore
from smi_ingestion.contracts import RunLimits
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from .contracts import EnrichmentProposal, OfflineRoute, TaskAuthority


class AcquisitionTasks:
    """Submit and inspect bounded offline tasks in one trusted workspace."""

    scope_version = 'campaign-offline-v1'

    def __init__(self, db: Database, workspace_id: str = 'local', *, route: OfflineRoute | None = None, authority: TaskAuthority | None = None):
        self.db, self.workspace_id, self.route = db, workspace_id, route
        self.authority = authority or TaskAuthority()

    def migrate(self) -> None:
        """Install tasks after ingestion, knowledge and campaign migrations."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def submit_campaign(self, campaign_id: str, actor: ActorContext, *, brief_id: str, purpose: str, request_id: str) -> dict[str, Any]:
        """Persist acknowledgment before I/O; the trusted campaign establishes origin."""
        actor.require_workspace(self.workspace_id)
        self.authority.require_campaign(actor)
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

    def save_proposal(self, proposal: EnrichmentProposal, actor: ActorContext, *, request_id: str) -> dict[str, Any]:
        """Save an immutable supplied revision with executable fixture scope; submit no work."""
        actor.require_workspace(self.workspace_id)
        proposal.validate()
        self._request_id(request_id)
        if self.route is None:
            raise EvidenceError('offline_task_route_unconfigured')
        path, manifest_hash, manifest = self.route.snapshot()
        scope = {**asdict(proposal), 'route': 'fixture-json', 'route_version': self.route.version,
                 'manifest_hash': manifest_hash, 'references': [i.get('reference', '') for i in manifest['items']]}
        scope = json.loads(json.dumps(scope))
        limits = asdict(self.route.limits)
        digest = self._digest({'workspace_id': self.workspace_id, 'scope': scope, 'limits': limits,
                               'scope_version': 'assistant-offline-v1', 'manifest_path': str(path)})
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'proposal:{self.workspace_id}:{request_id}',))
            prior = connection.execute('SELECT * FROM enrichment_proposals WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior:
                if (prior['scope_digest'] != digest or prior['proposer_id'] != actor.actor_id or prior['proposer_kind'] != actor.kind):
                    raise EvidenceError('proposal_request_conflict')
                return {'status': 'duplicate', 'proposal_id': str(prior['id'])}
            proposal_id = str(uuid.uuid4())
            connection.execute('INSERT INTO enrichment_proposals(id,workspace_id,request_id,scope_digest,scope,scope_version,limits,manifest_path,manifest_hash,proposer_id,proposer_kind) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (proposal_id, self.workspace_id, request_id, digest, Jsonb(scope), 'assistant-offline-v1', Jsonb(limits), str(path), manifest_hash, actor.actor_id, actor.kind))
        return {'status': 'saved', 'proposal_id': proposal_id}

    @staticmethod
    def _request_id(request_id: str) -> None:
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError('invalid_task_request_id')

    @staticmethod
    def _digest(body: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

    def read_proposal(self, proposal_id: str, actor: ActorContext) -> dict[str, Any]:
        """Reopen the exact immutable revision, human approval and resulting task link."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM enrichment_proposals WHERE id=%s AND workspace_id=%s', (proposal_id, self.workspace_id)).fetchone()
            if row is None:
                raise EvidenceError('enrichment_proposal_not_found')
            approval = connection.execute('SELECT a.*,t.id AS task_id FROM enrichment_approvals a LEFT JOIN acquisition_tasks t ON t.approval_id=a.id WHERE a.proposal_id=%s', (proposal_id,)).fetchone()
        return {'proposal_id': str(row['id']), 'workspace_id': row['workspace_id'], 'scope_digest': row['scope_digest'],
                'scope_version': row['scope_version'], 'scope': row['scope'], 'limits': row['limits'],
                'proposer': {'actor_id': row['proposer_id'], 'kind': row['proposer_kind']}, 'created_at': row['created_at'].isoformat(),
                'approval': self._approval_view(approval) if approval else None}

    @staticmethod
    def _approval_view(row) -> dict[str, Any]:
        return {'approval_id': str(row['id']), 'request_id': row['request_id'], 'proposal_id': str(row['proposal_id']), 'scope_digest': row['scope_digest'],
                'approver': {'actor_id': row['approver_id'], 'kind': row['approver_kind']}, 'approved_at': row['approved_at'].isoformat(),
                'task_id': str(row['task_id']) if row.get('task_id') else None}

    def list_proposals(self, actor: ActorContext) -> list[dict[str, Any]]:
        """List the newest 100 saved revisions without inventing conversational content."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute('SELECT id,scope,created_at FROM enrichment_proposals WHERE workspace_id=%s ORDER BY created_at DESC,id DESC LIMIT 100', (self.workspace_id,)).fetchall()
        return [{'proposal_id': str(r['id']), 'purpose': r['scope']['purpose'], 'created_at': r['created_at'].isoformat()} for r in rows]

    def approve_proposal(self, proposal_id: str, actor: ActorContext, *, scope_digest: str, request_id: str) -> dict[str, Any]:
        """Record a configured human's explicit action on the reviewed revision digest."""
        actor.require_workspace(self.workspace_id)
        self.authority.require_approver(actor)
        self._request_id(request_id)
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'approval:{self.workspace_id}:{request_id}',))
            proposal = connection.execute('SELECT scope_digest FROM enrichment_proposals WHERE id=%s AND workspace_id=%s FOR UPDATE', (proposal_id, self.workspace_id)).fetchone()
            if proposal is None:
                raise EvidenceError('enrichment_proposal_not_found')
            if proposal['scope_digest'] != scope_digest:
                raise EvidenceError('proposal_scope_conflict')
            prior = connection.execute('SELECT * FROM enrichment_approvals WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior and (str(prior['proposal_id']) != proposal_id or prior['approver_id'] != actor.actor_id):
                raise EvidenceError('approval_request_conflict')
            existing = prior or connection.execute('SELECT * FROM enrichment_approvals WHERE proposal_id=%s', (proposal_id,)).fetchone()
            if existing:
                if existing['approver_id'] != actor.actor_id:
                    raise EvidenceError('proposal_already_approved')
                if existing['request_id'] != request_id:
                    raise EvidenceError('approval_request_conflict')
                return {'status': 'duplicate', 'approval_id': str(existing['id'])}
            approval_id = str(uuid.uuid4())
            connection.execute('INSERT INTO enrichment_approvals(id,proposal_id,workspace_id,request_id,scope_digest,approver_id,approver_kind) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                               (approval_id, proposal_id, self.workspace_id, request_id, scope_digest, actor.actor_id, actor.kind))
        return {'status': 'approved', 'approval_id': approval_id}

    def submit_approved(self, proposal_id: str, actor: ActorContext, *, approval_id: str, scope_digest: str, request_id: str) -> dict[str, Any]:
        """Submit only saved approved scope; one approval can acknowledge at most one task."""
        actor.require_workspace(self.workspace_id)
        self._request_id(request_id)
        body = {'proposal_id': proposal_id, 'approval_id': approval_id, 'scope_digest': scope_digest,
                'initiator': {'actor_id': actor.actor_id, 'kind': actor.kind}, 'origin': 'assistant'}
        digest = self._digest(body)
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'task:{self.workspace_id}:{request_id}',))
            approval = connection.execute('SELECT * FROM enrichment_approvals WHERE id=%s AND workspace_id=%s FOR UPDATE', (approval_id, self.workspace_id)).fetchone()
            if approval is None:
                raise EvidenceError('proposal_approval_required')
            if str(approval['proposal_id']) != proposal_id or approval['scope_digest'] != scope_digest:
                raise EvidenceError('proposal_scope_conflict')
            prior = connection.execute('SELECT id,request_digest FROM acquisition_tasks WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior:
                if prior['request_digest'] != digest:
                    raise EvidenceError('task_request_conflict')
                return {'status': 'duplicate', 'task_id': str(prior['id'])}
            prior = connection.execute('SELECT id,request_digest,request_id FROM acquisition_tasks WHERE approval_id=%s', (approval_id,)).fetchone()
            if prior:
                if prior['request_digest'] != digest or prior['request_id'] != request_id:
                    raise EvidenceError('task_request_conflict')
                return {'status': 'duplicate', 'task_id': str(prior['id'])}
            proposal = connection.execute('SELECT * FROM enrichment_proposals WHERE id=%s AND workspace_id=%s', (proposal_id, self.workspace_id)).fetchone()
            # Review pins configuration as well as words. A replaced fixture must
            # receive a fresh proposal, rather than changing approved work silently.
            _, manifest_hash, _ = OfflineRoute(Path(proposal['manifest_path']), proposal['scope']['route_version'], RunLimits(**proposal['limits'])).snapshot()
            if manifest_hash != proposal['manifest_hash']:
                raise EvidenceError('proposal_input_changed')
            task_id = str(uuid.uuid4())
            connection.execute('INSERT INTO acquisition_tasks(id,workspace_id,request_id,request_digest,origin,approval_id,initiator_id,initiator_kind,scope_version,scope,limits,manifest_path,manifest_hash) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (task_id, self.workspace_id, request_id, digest, 'assistant', approval_id, actor.actor_id, actor.kind,
                                proposal['scope_version'], Jsonb(proposal['scope']), Jsonb(proposal['limits']), proposal['manifest_path'], proposal['manifest_hash']))
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
            approval = connection.execute('SELECT proposal_id FROM enrichment_approvals WHERE id=%s', (row['approval_id'],)).fetchone() if row['approval_id'] else None
            attempts = connection.execute('SELECT * FROM acquisition_attempts WHERE task_id=%s ORDER BY number', (task_id,)).fetchall()
            publications = connection.execute('SELECT publication_id FROM acquisition_task_publications WHERE task_id=%s ORDER BY publication_id', (task_id,)).fetchall()
        return {'task_id': task_id, 'workspace_id': self.workspace_id, 'request_id': row['request_id'],
                'origin': row['origin'], 'initiator': {'actor_id': row['initiator_id'], 'kind': row['initiator_kind']},
                'scope_version': row['scope_version'], 'scope': row['scope'], 'limits': row['limits'], 'attempt_limit': row['attempt_limit'],
                'status': row['status'], 'outcome': row['outcome'], 'coverage': row['coverage'],
                'failure': {'phase': row['failure_phase'], 'code': row['failure_code']} if row['failure_code'] else None,
                'submitted_at': row['submitted_at'].isoformat(), 'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None,
                'proposal_approval': self.read_proposal(str(approval['proposal_id']), actor)['approval'] if approval else None,
                'publication_ids': [str(p['publication_id']) for p in publications],
                'attempts': [{'attempt_id': str(a['id']), 'number': a['number'], 'run_id': str(a['run_id']),
                              'producer': {'actor_id': a['producer_id'], 'kind': a['producer_kind']}, 'phases': a['phases'],
                              'started_at': a['started_at'].isoformat(), 'finished_at': a['finished_at'].isoformat() if a['finished_at'] else None} for a in attempts]}
