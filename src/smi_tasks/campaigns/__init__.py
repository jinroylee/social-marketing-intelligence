"""Save-first application composition for campaign recommendations and discovery."""

import hashlib
import json
import uuid

from psycopg.types.json import Jsonb

from smi_campaigns import CampaignStore
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from ..store import AcquisitionTasks
from ..notifications import CompletionInbox


class CampaignRecommendations:
    """Return a durable supported result independently of enrichment admission."""

    def __init__(self, campaigns: CampaignStore, tasks: AcquisitionTasks):
        self.campaigns, self.tasks = campaigns, tasks

    def recommend(self, campaign_id: str, brief_id: str, actor: ActorContext, *, ranked: bool = False, **options) -> dict:
        """Save through the campaign owner, then admit that exact coverage need.

        Retrying the same request reopens the saved decision before task admission;
        the shortlist identity also owns retries after interruption between commits.
        """
        operation = self.campaigns.recommend_ranked if ranked else self.campaigns.recommend
        saved = operation(campaign_id, brief_id, actor, **options)
        if saved.get('shortlist_id'):
            self.tasks.submit_campaign_discovery(saved['shortlist_id'], actor, include_synthetic=options.get('include_synthetic', False))
        return saved

    def read(self, shortlist_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict:
        """Reopen the immutable shortlist with current enrichment progress."""
        return {'shortlist': self.campaigns.read_shortlist(shortlist_id, actor, include_synthetic=include_synthetic),
                'enrichment': self.tasks.read_campaign_discovery(shortlist_id, actor)}

    def regeneration_offer(self, event_id: str, actor: ActorContext) -> dict:
        """Compose current campaign context and source-free action history for a completion."""
        event = CompletionInbox(self.tasks.db, self.tasks.workspace_id).read(event_id, actor)
        discovery = event['campaign_discovery']
        if discovery is None:
            raise EvidenceError('campaign_discovery_completion_not_found')
        source = self.campaigns.read_shortlist_context(discovery['shortlist_id'], actor)
        campaign = source['campaign']
        with self.tasks.db.connect() as connection:
            requests = connection.execute('SELECT request_id FROM campaign_regeneration_requests WHERE event_id=%s AND workspace_id=%s ORDER BY recorded_at,request_id',
                                          (event_id, self.tasks.workspace_id)).fetchall()
        return {'event': event, 'campaign': campaign, 'source_shortlist_id': discovery['shortlist_id'],
                'ranked': source['ranked'],
                'actions': [self.read_regeneration(r['request_id'], actor) for r in requests]}

    def read_regeneration(self, request_id: str, actor: ActorContext) -> dict:
        """Reopen human attribution and the exact source-free assessment outcome."""
        actor.require_workspace(self.tasks.workspace_id)
        with self.tasks.db.connect() as connection:
            row = connection.execute('SELECT * FROM campaign_regeneration_requests WHERE workspace_id=%s AND request_id=%s',
                                     (self.tasks.workspace_id, request_id)).fetchone()
        if row is None:
            raise EvidenceError('campaign_regeneration_not_found')
        return {'request_id': row['request_id'], 'event_id': str(row['event_id']),
                'source_shortlist_id': str(row['source_shortlist_id']), 'body': row['body'],
                'initiator': {'actor_id': row['initiator_id'], 'kind': 'human'},
                'producer': {'actor_id': row['producer_id'], 'kind': 'automation'}, 'ranked': row['ranked'],
                'outcome': row['outcome'], 'recorded_at': row['recorded_at'].isoformat()}

    def regenerate(self, event_id: str, actor: ActorContext, *, producer: ActorContext, brief_id: str,
                   expected_brief_version: int, expected_shortlist_version: int, request_id: str,
                   interpretation_id: str | None = None, include_synthetic: bool = False) -> dict:
        """Assess current context only after an explicit human action, then save a successor.

        Persist the exact body, actual actors and server-owned nested retry identity
        before assessment. Completed retries reopen before current brief/source checks;
        no transaction or lock spans model I/O. Campaigns fence both heads and support.
        """
        actor.require_workspace(self.tasks.workspace_id)
        producer.require_workspace(self.tasks.workspace_id)
        if actor.kind != 'human':
            raise EvidenceError('human_action_required')
        if producer.kind != 'automation':
            raise EvidenceError('automation_action_required')
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError('invalid_regeneration_request_id')
        event_id, brief_id = str(uuid.UUID(event_id)), str(uuid.UUID(brief_id))
        body = {'event_id': event_id, 'brief_id': brief_id, 'expected_brief_version': expected_brief_version,
                'expected_shortlist_version': expected_shortlist_version, 'interpretation_id': interpretation_id,
                'include_synthetic': include_synthetic, 'initiator': {'actor_id': actor.actor_id, 'kind': actor.kind},
                'producer': {'actor_id': producer.actor_id, 'kind': producer.kind}}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        with self.tasks.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',
                               (f'regeneration:{self.tasks.workspace_id}:{request_id}',))
            row = connection.execute('SELECT * FROM campaign_regeneration_requests WHERE workspace_id=%s AND request_id=%s',
                                     (self.tasks.workspace_id, request_id)).fetchone()
            if row:
                if row['request_digest'] != digest:
                    raise EvidenceError('campaign_regeneration_request_conflict')
                if row['outcome'] is not None:
                    return row['outcome']
                source_id, ranked, nested = str(row['source_shortlist_id']), row['ranked'], row['recommendation_request_id']
            else:
                self.tasks.authority.require_campaign(producer)
                event = CompletionInbox(self.tasks.db, self.tasks.workspace_id).read(event_id, actor)
                discovery = event['campaign_discovery']
                if discovery is None or discovery['regeneration_href'] is None:
                    raise EvidenceError('campaign_regeneration_unavailable')
                source_id = discovery['shortlist_id']
                source = self.campaigns.read_shortlist_context(source_id, actor)
                ranked = source['ranked']
                nested = 'regeneration:' + str(uuid.uuid4())
                connection.execute('INSERT INTO campaign_regeneration_requests(workspace_id,request_id,event_id,source_shortlist_id,request_digest,body,initiator_id,producer_id,ranked,recommendation_request_id) '
                                   'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (self.tasks.workspace_id, request_id, event_id, source_id, digest, Jsonb(body), actor.actor_id, producer.actor_id, ranked, nested))
        source = self.campaigns.read_shortlist_context(source_id, actor)
        saved = self.recommend(source['campaign']['campaign_id'], brief_id, producer, ranked=ranked,
            expected_brief_version=expected_brief_version, expected_shortlist_version=expected_shortlist_version,
            request_id=nested, interpretation_id=interpretation_id, include_synthetic=include_synthetic)
        outcome = {key: saved[key] for key in ('status', 'shortlist_id', 'version', 'assessment_id', 'reason', 'operation_id') if key in saved}
        # Concurrent retries may observe an in-flight ranked claim. Only its owner
        # or a later completed reopen records a terminal result.
        if outcome['status'] != 'in_progress':
            with self.tasks.db.connect() as connection:
                connection.execute('UPDATE campaign_regeneration_requests SET outcome=%s WHERE workspace_id=%s AND request_id=%s AND outcome IS NULL',
                                   (Jsonb(outcome), self.tasks.workspace_id, request_id))
            return self.read_regeneration(request_id, actor)['outcome']
        return outcome
