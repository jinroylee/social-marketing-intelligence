"""Explicit human-scoped enrichment of a saved assistant knowledge gap."""

import hashlib
import json
from pathlib import Path
import uuid

from psycopg.types.json import Jsonb

from smi_assistant import KnowledgeAssistant
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from ..contracts import EnrichmentProposal
from ..store import AcquisitionTasks
from ..notifications import CompletionInbox


class AssistantEnrichment:
    """Compose answer, exact proposal approval, task status and actual completion.

    Gap classification supplies a source-free purpose template. The human supplies
    exact subjects, query and publication window; no model gets acquisition authority.
    This owner writes only its linkage schema and calls the existing public owners.
    """

    def __init__(self, assistant: KnowledgeAssistant, tasks: AcquisitionTasks):
        if (assistant.workspace_id != tasks.workspace_id
                or (assistant.db.dsn, assistant.db.schema) != (tasks.db.dsn, tasks.db.schema)):
            raise EvidenceError('assistant_enrichment_context_mismatch')
        self.assistant, self.tasks = assistant, tasks

    def migrate(self) -> None:
        """Install source-free journey claims after the answer and task owners."""
        self.assistant.migrate()
        self.tasks.migrate()
        with self.tasks.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _answer(self, answer_id, actor, include_synthetic):
        actor.require_workspace(self.tasks.workspace_id)
        if type(include_synthetic) is not bool:
            raise EvidenceError('invalid_enrichment_visibility')
        if actor.kind != 'human':
            raise EvidenceError('human_action_required')
        answer = self.assistant.read(answer_id, actor, include_synthetic=include_synthetic)
        if answer['requested_by']['actor_id'] != actor.actor_id:
            raise EvidenceError('answer_requester_required')
        return answer

    @staticmethod
    def _gap(answer):
        if answer['status'] == 'empty':
            return 'missing_published_information'
        if answer['status'] != 'succeeded':
            return None
        if not answer['usable']:
            return 'published_support_unavailable'
        if 'stale_source_capture' in answer['limits']:
            return 'stale_published_information'
        if answer['limitation'] == 'ambiguous_question':
            return 'ambiguous_question_requires_explicit_scope'
        if answer['limitation'] == 'missing_information':
            return 'missing_published_information'
        return None

    def context(self, answer_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict:
        """Reopen one asker's answer, current gap and newest 100 saved journeys; do no work."""
        answer = self._answer(answer_id, actor, include_synthetic)
        with self.tasks.db.connect() as connection:
            rows = connection.execute('SELECT id FROM assistant_enrichment_requests WHERE workspace_id=%s AND answer_id=%s ORDER BY created_at DESC,id DESC LIMIT 100',
                                      (self.tasks.workspace_id, answer_id)).fetchall()
        return {'answer': answer, 'gap': self._gap(answer), 'journeys': [self.read(str(r['id']), actor, include_synthetic=include_synthetic) for r in rows]}

    def propose(self, answer_id: str, actor: ActorContext, *, request_id: str, intent: str,
                subject_ids: tuple[str, ...], search_query: str, published_from: str,
                published_before: str, include_synthetic: bool = False) -> dict:
        """Save an exact bounded keyword proposal for review, never approve or submit.

        A durable server-owned nested identity recovers interruption between the
        linkage claim and proposal save. Exact retries reopen existing revisions
        before current gap/route checks; changed scope or actor conflicts.
        """
        answer = self._answer(answer_id, actor, include_synthetic)
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError('invalid_enrichment_request_id')
        answer_id = str(uuid.UUID(answer_id))
        body = {'answer_id': answer_id, 'actor_id': actor.actor_id, 'intent': intent,
                'subject_ids': subject_ids, 'search_query': search_query, 'published_from': published_from,
                'published_before': published_before, 'include_synthetic': include_synthetic}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        with self.tasks.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'assistant-enrichment:{self.tasks.workspace_id}:{request_id}',))
            row = connection.execute('SELECT * FROM assistant_enrichment_requests WHERE workspace_id=%s AND request_id=%s', (self.tasks.workspace_id, request_id)).fetchone()
            if row:
                if row['request_digest'] != digest:
                    raise EvidenceError('assistant_enrichment_request_conflict')
            else:
                gap = self._gap(answer)
                if gap is None:
                    raise EvidenceError('assistant_knowledge_gap_required')
                if self.tasks.route is None or not self.tasks.route.capability()['query_discovery']:
                    raise EvidenceError('assistant_keyword_discovery_unavailable')
                proposal = EnrichmentProposal(f'Investigate assistant knowledge gap: {gap}', intent,
                    subject_ids, (search_query,), published_from, published_before)
                proposal.validate()
                row = connection.execute('INSERT INTO assistant_enrichment_requests(id,workspace_id,request_id,request_digest,answer_id,requester_id,include_synthetic,gap,proposal_body,proposal_request_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
                    (str(uuid.uuid4()), self.tasks.workspace_id, request_id, digest, answer_id, actor.actor_id, include_synthetic, gap,
                     Jsonb(proposal.document()), 'assistant-proposal:' + str(uuid.uuid4()))).fetchone()
        if row['proposal_id'] is None:
            proposer = ActorContext(self.tasks.workspace_id, 'knowledge-enrichment-assistant', 'automation')
            saved = self.tasks.find_proposal(row['proposal_request_id'], proposer)
            if saved is None:
                saved = self.tasks.save_proposal(EnrichmentProposal.from_document(row['proposal_body']), proposer, request_id=row['proposal_request_id'])
            with self.tasks.db.connect() as connection:
                connection.execute('UPDATE assistant_enrichment_requests SET proposal_id=%s WHERE id=%s AND proposal_id IS NULL', (saved['proposal_id'], row['id']))
        return self.read(str(row['id']), actor, include_synthetic=include_synthetic)

    def read(self, journey_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict:
        """Reopen exact proposal/task and durable current-policy completion without executing."""
        actor.require_workspace(self.tasks.workspace_id)
        with self.tasks.db.connect() as connection:
            row = connection.execute('SELECT * FROM assistant_enrichment_requests WHERE id=%s AND workspace_id=%s', (journey_id, self.tasks.workspace_id)).fetchone()
        if row is None:
            raise EvidenceError('assistant_enrichment_not_found')
        answer = self._answer(str(row['answer_id']), actor, include_synthetic)
        proposal = self.tasks.read_proposal(str(row['proposal_id']), actor) if row['proposal_id'] else None
        task_id = proposal['approval']['task_id'] if proposal and proposal['approval'] else None
        task = self.tasks.read(task_id, actor) if task_id else None
        completion = CompletionInbox(self.tasks.db, self.tasks.workspace_id).read_task(task_id, actor) if task_id else None
        return {'journey_id': str(row['id']), 'answer': answer, 'gap': row['gap'], 'request_id': row['request_id'],
                'proposal': proposal, 'task': task, 'completion': completion, 'created_at': row['created_at'].isoformat(),
                'pending_scope': row['proposal_body'] if proposal is None else None, 'include_synthetic': row['include_synthetic']}

    def approve(self, journey_id: str, actor: ActorContext, *, scope_digest: str, request_id: str,
                include_synthetic: bool = False) -> dict:
        """Apply an actual configured human approval, then acknowledge one exact task.

        The task owner's immutable approval request identity also recovers a saved
        approval without a submitted task. This action performs no acquisition.
        """
        journey = self.read(journey_id, actor, include_synthetic=include_synthetic)
        proposal = journey['proposal']
        if proposal is None:
            raise EvidenceError('assistant_proposal_not_saved')
        approval = self.tasks.approve_proposal(proposal['proposal_id'], actor, scope_digest=scope_digest, request_id=request_id)
        self.tasks.submit_approved(proposal['proposal_id'], actor, approval_id=approval['approval_id'], scope_digest=scope_digest,
                                   request_id=request_id)
        return self.read(journey_id, actor, include_synthetic=include_synthetic)
