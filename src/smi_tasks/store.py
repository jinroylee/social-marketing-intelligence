"""Durable task/proposal admission; source and publication owners keep their data."""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from contextlib import nullcontext
from typing import Any

from psycopg.types.json import Jsonb

from smi_campaigns import CampaignStore
from smi_costs import UsageAccounting
from smi_ingestion.contracts import RunLimits
from smi_ingestion.adapters.keyword_fixture import ROUTE
from smi_ingestion.adapters.tiktok_keyword import ROUTE as LIVE_ROUTE
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.support import IngestedEvidence, SupportReference
from smi_knowledge import KnowledgePublications, KnowledgeStore

from .contracts import EnrichmentProposal, OfflineRoute, TaskAuthority, execution_configuration_digest
from .execution import execution_is_running
from .discovery import DiscoveryHistory


class AcquisitionTasks:
    """Submit and inspect bounded offline tasks in one trusted workspace."""

    scope_version = 'campaign-offline-v1'

    def __init__(self, db: Database, workspace_id: str = 'local', *, route: OfflineRoute | None = None, authority: TaskAuthority | None = None, live_discovery_enabled: bool = False):
        self.db, self.workspace_id, self.route = db, workspace_id, route
        self.authority = authority or TaskAuthority()
        self.live_discovery_enabled = live_discovery_enabled

    def migrate(self) -> None:
        """Install tasks after ingestion, knowledge and campaign migrations."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())
        UsageAccounting(self.db, self.workspace_id).migrate()
        from .schedules import migrate
        migrate(self.db)
        DiscoveryHistory(self.db, self.workspace_id).migrate()

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
        if manifest['adapter'] != 'fixture-json':
            raise EvidenceError('keyword_discovery_requires_explicit_proposal_scope')
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
            CampaignStore(self.db, self.workspace_id).require_current_brief(
                campaign_id, brief_id, actor, expected_version=brief['version'], connection=connection)
            task_id = str(uuid.uuid4())
            connection.execute('INSERT INTO acquisition_tasks(id,workspace_id,request_id,request_digest,origin,campaign_id,brief_id,initiator_id,initiator_kind,scope_version,scope,limits,manifest_path,manifest_hash) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (task_id, self.workspace_id, request_id, request_digest, 'campaign', campaign_id, brief_id, actor.actor_id, actor.kind, self.scope_version, Jsonb(scope), Jsonb(limits), str(path), digest))
        return {'status': 'accepted', 'task_id': task_id}

    def submit_campaign_discovery(self, shortlist_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict[str, Any]:
        """Admit one exact saved coverage need under operator-owned campaign authority.

        The recommendation already committed. Persist refusals without changing it;
        retries reopen the original disposition before inspecting changed inputs.
        Only this trusted operation derives scope from the pinned human brief.
        """
        actor.require_workspace(self.workspace_id)
        self.authority.require_campaign(actor)
        shortlist_id = str(uuid.UUID(shortlist_id))
        campaigns = CampaignStore(self.db, self.workspace_id)
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'campaign-discovery:{self.workspace_id}:{shortlist_id}',))
            prior = connection.execute('SELECT * FROM campaign_discovery_requests WHERE shortlist_id=%s AND workspace_id=%s',
                                       (shortlist_id, self.workspace_id)).fetchone()
            if prior:
                if prior['initiator_id'] != actor.actor_id or prior['initiator_kind'] != actor.kind:
                    raise EvidenceError('campaign_discovery_actor_conflict')
            else:
                saved = campaigns.read_shortlist(shortlist_id, actor, include_synthetic=include_synthetic, purpose='process')
                coverage = saved['coverage_assessment']
                status, reason, task_id = 'refused', None, None
                try:
                    if coverage is None:
                        raise EvidenceError('campaign_coverage_unrecorded')
                    if coverage['result'] is None:
                        raise EvidenceError('campaign_coverage_support_unavailable')
                    if coverage['result']['sufficient']:
                        status = 'not_needed'
                    else:
                        brief = campaigns.require_current_brief(saved['campaign_id'], saved['brief_id'], actor,
                            expected_version=saved['execution_profile']['brief_version'], connection=connection)
                        if self.route is None:
                            raise EvidenceError('offline_task_route_unconfigured')
                        path, manifest_hash, manifest = self.route.snapshot()
                        if manifest['adapter'] != ROUTE:
                            raise EvidenceError('keyword_discovery_unavailable_supplied_reference_route')
                        policy = manifest.get('policy')
                        if not isinstance(policy, dict) or not all(policy.get(p) is True for p in ('can_process', 'can_retain')):
                            raise EvidenceError('source_policy_disallows_discovery')
                        document = brief['document']
                        if 'tiktok' not in document['platforms']:
                            raise EvidenceError('keyword_discovery_unavailable_campaign_platform')
                        catalog = KnowledgeStore(self.db, self.workspace_id).catalog(document['catalog_id'], actor)
                        # One declared literal name, never free-form objective/model text.
                        product = document['product_ids'][0] if document['product_ids'] else None
                        entries = catalog.document['products'] if product else catalog.document['brands']
                        subject = product or document['brand_id']
                        query = next(e['name'] for e in entries if e['id'] == subject)
                        end = datetime.fromisoformat(coverage['assessed_at'])
                        start = end - timedelta(days=30)
                        if document.get('publication_from'):
                            start = max(start, datetime.fromisoformat(document['publication_from'].replace('Z', '+00:00')))
                        if document.get('publication_to'):
                            end = min(end, datetime.fromisoformat(document['publication_to'].replace('Z', '+00:00')))
                        if start >= end:
                            raise EvidenceError('campaign_discovery_window_unavailable')
                        proposal = EnrichmentProposal('Fill saved campaign coverage', 'fill',
                            (('product:' if product else 'brand:') + subject,), (query,),
                            start.isoformat(), end.isoformat())
                        proposal.validate()
                        scope = {**proposal.document(), 'discovery': proposal.keyword_scope(),
                                 'campaign_id': saved['campaign_id'], 'brief_id': saved['brief_id'],
                                 'brief_version': brief['version'], 'shortlist_id': shortlist_id,
                                 'platforms': ['tiktok'], 'unsearched_platforms': [p for p in document['platforms'] if p != 'tiktok'],
                                 'coverage_profile': coverage['profile']['version'], 'coverage_assessed_at': coverage['assessed_at'],
                                 'query_derivation': coverage['profile']['discovery'], 'catalog_digest': catalog.digest,
                                 'route': ROUTE, 'route_version': self.route.version, 'manifest_hash': manifest_hash, 'references': []}
                        scope.update(self.route.discovery_configuration(manifest))
                        scope = json.loads(json.dumps(scope))
                        limits = asdict(self.route.limits)
                        scope['execution_digest'] = execution_configuration_digest(scope, limits, str(path))
                        # The disposition owns retries; callers cannot preclaim its nested task.
                        request_id = 'campaign-discovery:' + str(uuid.uuid4())
                        digest = self._digest({'scope': scope, 'limits': limits, 'manifest_path': str(path),
                                               'initiator': {'actor_id': actor.actor_id, 'kind': actor.kind}, 'origin': 'campaign'})
                        task_id = str(uuid.uuid4())
                        connection.execute('INSERT INTO acquisition_tasks(id,workspace_id,request_id,request_digest,origin,campaign_id,brief_id,initiator_id,initiator_kind,scope_version,scope,limits,manifest_path,manifest_hash) '
                                           "VALUES (%s,%s,%s,%s,'campaign',%s,%s,%s,%s,'campaign-coverage-discovery-v1',%s,%s,%s,%s)",
                                           (task_id, self.workspace_id, request_id, digest, saved['campaign_id'], saved['brief_id'],
                                            actor.actor_id, actor.kind, Jsonb(scope), Jsonb(limits), str(path), manifest_hash))
                        status = 'submitted'
                except EvidenceError as error:
                    reason = error.code
                connection.execute('INSERT INTO campaign_discovery_requests(shortlist_id,workspace_id,initiator_id,initiator_kind,status,reason,task_id) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                                   (shortlist_id, self.workspace_id, actor.actor_id, actor.kind, status, reason, task_id))
        return self.read_campaign_discovery(shortlist_id, actor)

    def read_campaign_discovery(self, shortlist_id: str, actor: ActorContext) -> dict[str, Any] | None:
        """Read the historical admission disposition and current worker waiting/outcome."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM campaign_discovery_requests WHERE shortlist_id=%s AND workspace_id=%s',
                                     (shortlist_id, self.workspace_id)).fetchone()
        if row is None:
            return None
        task_id = str(row['task_id']) if row['task_id'] else None
        return {'shortlist_id': str(row['shortlist_id']), 'status': row['status'], 'reason': row['reason'],
                'task_id': task_id, 'task': self.read(task_id, actor) if task_id else None,
                'initiator': {'actor_id': row['initiator_id'], 'kind': row['initiator_kind']},
                'recorded_at': row['recorded_at'].isoformat()}

    def submit_scheduled(self, occurrence_id: str, actor: ActorContext, *, connection=None) -> dict[str, Any]:
        """Admit only exact schedule-owner authority on its current occurrence transaction.

        The schedule owner creates and binds occurrences atomically with this task.
        No query, origin, keyword or accounting context is accepted from clients.
        """
        from .schedules import require_occurrence

        actor.require_workspace(self.workspace_id)
        self.authority.require_schedule_tick(actor)
        occurrence_id = str(uuid.UUID(occurrence_id))
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            context = require_occurrence(self.workspace_id, occurrence_id, actor, connection=connection)
            prior = connection.execute('SELECT id FROM acquisition_tasks WHERE workspace_id=%s AND schedule_occurrence_id=%s',
                                       (self.workspace_id, occurrence_id)).fetchone()
            if prior:
                return {'status': 'duplicate', 'task_id': str(prior['id'])}
            if self.route is None:
                raise EvidenceError('offline_task_route_unconfigured')
            path, manifest_hash, manifest = self.route.snapshot()
            if manifest['adapter'] != ROUTE:
                raise EvidenceError('keyword_discovery_unavailable_supplied_reference_route')
            policy = manifest.get('policy')
            if not isinstance(policy, dict) or not all(policy.get(p) is True for p in ('can_process', 'can_retain')):
                raise EvidenceError('source_policy_disallows_discovery')
            keyword = context['keyword']
            proposal = EnrichmentProposal('Registered scheduled keyword discovery', 'expansion',
                tuple(keyword['subject_ids']), (keyword['query'],), context['published_from'], context['published_before'])
            proposal.validate()
            scope = {**proposal.document(), 'discovery': proposal.keyword_scope(), 'schedule': context,
                     'route': ROUTE, 'route_version': self.route.version, 'manifest_hash': manifest_hash, 'references': []}
            scope.update(self.route.discovery_configuration(manifest))
            scope = json.loads(json.dumps(scope))
            limits = asdict(self.route.limits)
            scope['execution_digest'] = execution_configuration_digest(scope, limits, str(path))
            digest = self._digest({'scope': scope, 'limits': limits, 'manifest_path': str(path), 'origin': 'schedule'})
            task_id = str(uuid.uuid4())
            connection.execute('INSERT INTO acquisition_tasks(id,workspace_id,request_id,request_digest,origin,schedule_occurrence_id,initiator_id,initiator_kind,scope_version,scope,limits,manifest_path,manifest_hash) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (task_id, self.workspace_id, 'scheduled:' + occurrence_id, digest, 'schedule', occurrence_id,
                                actor.actor_id, actor.kind, 'schedule-offline-v1', Jsonb(scope), Jsonb(limits), str(path), manifest_hash))
        return {'status': 'accepted', 'task_id': task_id}

    def save_proposal(self, proposal: EnrichmentProposal, actor: ActorContext, *, request_id: str) -> dict[str, Any]:
        """Save an immutable supplied revision with exact executable offline scope; submit no work."""
        actor.require_workspace(self.workspace_id)
        proposal.validate()
        self._request_id(request_id)
        if self.route is None:
            raise EvidenceError('offline_task_route_unconfigured')
        path, manifest_hash, manifest = self.route.snapshot()
        if manifest['adapter'] == LIVE_ROUTE and self.live_discovery_enabled is not True:
            raise EvidenceError('live_discovery_disabled')
        scope = {**proposal.document(), 'route': manifest['adapter'], 'route_version': self.route.version,
                 'manifest_hash': manifest_hash, 'references': [i.get('reference', '') for i in manifest.get('items', [])]}
        if manifest['adapter'] in {ROUTE, LIVE_ROUTE}:
            scope['discovery'] = proposal.keyword_scope()
            scope.update(self.route.discovery_configuration(manifest))
        elif proposal.published_from is not None or proposal.published_before is not None:
            raise EvidenceError('keyword_discovery_unavailable_supplied_reference_route')
        scope = json.loads(json.dumps(scope))
        limits = asdict(self.route.limits)
        if manifest['adapter'] in {ROUTE, LIVE_ROUTE}:
            scope['execution_digest'] = execution_configuration_digest(scope, limits, str(path))
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
            if proposal['scope']['route'] == LIVE_ROUTE and self.live_discovery_enabled is not True:
                raise EvidenceError('live_discovery_disabled')
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
            task_id = str(row['id'])
            approval = connection.execute('SELECT proposal_id FROM enrichment_approvals WHERE id=%s', (row['approval_id'],)).fetchone() if row['approval_id'] else None
            attempts = connection.execute('SELECT * FROM acquisition_attempts WHERE task_id=%s ORDER BY number', (task_id,)).fetchall()
            publications = connection.execute('SELECT publication_id FROM acquisition_task_publications WHERE task_id=%s ORDER BY publication_id', (task_id,)).fetchall()
            running = execution_is_running(connection, row)
        progress = row['progress'] or {'phase': row['status']}
        coverage = dict(row['coverage'])
        publication_ids = [str(p['publication_id']) for p in publications]
        if row['outcome'] is None and progress.get('phase') == 'publication_prepared':
            try:
                committed = self.read_committed_publication(task_id, actor)
            except EvidenceError as error:
                if error.code != 'publication_request_conflict':
                    raise
                committed = None
                publication_ids = []
            if committed:
                progress = {'phase': 'publication_committed', 'publication_id': committed['publication_id']}
                coverage.update(published_members=committed['coverage']['members'], unpublished_members=0)
                publication_ids = [committed['publication_id']]
        from .schedules.allowance import ScheduledPostAllowance
        allowance = ScheduledPostAllowance(self.db, self.workspace_id).read(row['scope']['schedule']['accounting_day'], actor, occurrence_id=str(row['schedule_occurrence_id'])) if row['origin'] == 'schedule' else None
        return {'task_id': task_id, 'workspace_id': self.workspace_id, 'request_id': row['request_id'],
                'discovery_history': DiscoveryHistory(self.db, self.workspace_id).read(task_id, actor),
                'daily_allowance': allowance, 'origin': row['origin'], 'initiator': {'actor_id': row['initiator_id'], 'kind': row['initiator_kind']},
                'scope_version': row['scope_version'], 'scope': row['scope'], 'limits': row['limits'], 'attempt_limit': row['attempt_limit'],
                'status': row['status'], 'progress': progress, 'outcome': row['outcome'], 'coverage': coverage,
                'execution': {'state': 'completed' if row['outcome'] is not None else 'running' if running else 'queued' if row['status'] == 'queued' else 'waiting' if row['status'] == 'waiting' else 'recoverable',
                              'execution_id': str(row['execution_id']) if row['execution_id'] else None, 'owner': row['execution_actor']},
                'failure': {'phase': row['failure_phase'], 'code': row['failure_code']} if row['failure_code'] else None,
                'submitted_at': row['submitted_at'].isoformat(), 'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None,
                'proposal_approval': self.read_proposal(str(approval['proposal_id']), actor)['approval'] if approval else None,
                'publication_ids': publication_ids,
                'attempts': [{'attempt_id': str(a['id']), 'number': a['number'], 'run_id': str(a['run_id']),
                              'producer': {'actor_id': a['producer_id'], 'kind': a['producer_kind']}, 'resumed_by': a['resumed_by'], 'recovery_count': a['recovery_count'], 'publication_support': a['publication_support'], 'phases': a['phases'],
                              'started_at': a['started_at'].isoformat(), 'finished_at': a['finished_at'].isoformat() if a['finished_at'] else None} for a in attempts]}

    def read_committed_publication(self, task_id: str, actor: ActorContext, *, connection=None) -> dict[str, Any] | None:
        """Reopen only a publication receipted by this task's fenced worker commit.

        Exact durable prepared support must match both the publication and the
        attempt's ingestion run. Request text alone cannot authorize adoption;
        missing/mismatched ownership raises ``publication_request_conflict``.
        Source-free validation preserves historical effects after policy changes.
        """
        actor.require_workspace(self.workspace_id)
        task_id = str(uuid.UUID(task_id))
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            publication = KnowledgePublications(self.db, self.workspace_id).find_request(
                f'task:{task_id}', actor, include_synthetic=True, connection=connection)
            if publication is None:
                return None
            attempt = connection.execute(
                'SELECT a.* FROM acquisition_attempts a JOIN acquisition_tasks t ON t.id=a.task_id '
                'WHERE t.id=%s AND t.workspace_id=%s ORDER BY a.number DESC LIMIT 1', (task_id, self.workspace_id),
            ).fetchone()
            receipt = connection.execute('SELECT publication_id FROM acquisition_task_publications WHERE task_id=%s AND publication_id=%s',
                                         (task_id, publication['publication_id'])).fetchone()
            if (receipt is None or attempt is None or not attempt['publication_support']
                    or publication['support'] != attempt['publication_support'] or publication['interpretation_ids']):
                raise EvidenceError('publication_request_conflict')
            support = tuple(SupportReference(s['observation_id'], s['derivation_id'], tuple(s['assertion_ids']), tuple(s['metric_ids']))
                            for s in attempt['publication_support'])
            try:
                IngestedEvidence(self.db, self.workspace_id).require_run_support(
                    str(attempt['run_id']), support, actor, include_synthetic=True, connection=connection)
            except EvidenceError as error:
                raise EvidenceError('publication_request_conflict') from error
        return publication

    def resolve_cost_attribution(self, task_id: str, attempt_id: str, actor: ActorContext) -> dict[str, str]:
        """Validate source-free accounting references through the owning task interface."""
        try:
            task_id, attempt_id = str(uuid.UUID(task_id)), str(uuid.UUID(attempt_id))
        except (ValueError, TypeError, AttributeError):
            raise EvidenceError('cost_task_attribution_not_found') from None
        task = self.read(task_id, actor)
        if not any(a['attempt_id'] == attempt_id for a in task['attempts']):
            raise EvidenceError('cost_task_attribution_not_found')
        return {'task_id': task['task_id'], 'attempt_id': attempt_id}
