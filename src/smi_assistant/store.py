"""Durable question claims with source-free exact-support selection and metered dispatch."""

import hashlib
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_campaigns.responses import ResponsesRoute, ResponsesTransport, execute_request
from smi_costs import UsageAccounting
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgeQueries, QueryScope

from .answers import LIMITS, METHOD_VERSION, SCHEMA_VERSION, request_document, require, support_facts, validate


class KnowledgeAssistant:
    """Ask one bounded published-KB question; exact request retries never redispatch.

    Compose the existing retrieval and shared Responses/accounting ports without
    acquisition authority. Configuration is trusted constructor input. Persist only
    the human question, exact support identities and source-free outcome metadata.
    """

    def __init__(self, db: Database, workspace_id: str = 'local', *, model_route: ResponsesRoute | None = None,
                 model_transport: ResponsesTransport | None = None, model_credential: str | None = None):
        self.db, self.workspace_id = db, workspace_id
        self.queries = KnowledgeQueries(db, workspace_id)
        self.model_route, self.model_transport, self.model_credential = model_route, model_transport, model_credential

    def migrate(self) -> None:
        """Install answer storage after knowledge and shared cost migrations."""
        self.queries.migrate()
        UsageAccounting(self.db, self.workspace_id).migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def ask(self, question: str, actor: ActorContext, *, request_id: str, scope: QueryScope | None = None,
            include_synthetic: bool = False) -> dict:
        """Save/reopen one human question, with visible no-support/config/failure outcomes.

        At most 20 published members and 100 exact facts enter one model call; JSON
        input is bounded to 128 KiB plus the route's whole-request bound. Interrupted
        claims remain in progress, never automatically reissued. A new request is
        explicit new work; neither questions nor evidence can authorize enrichment.
        """
        actor.require_workspace(self.workspace_id)
        require(actor.kind == 'human', 'human_action_required')
        try:
            require(isinstance(question, str) and bool(question.strip()) and '\x00' not in question
                    and len(question.encode('utf-8')) <= 4000, 'invalid_knowledge_question')
            require(isinstance(request_id, str) and bool(request_id.strip()) and '\x00' not in request_id
                    and len(request_id.encode('utf-8')) <= 200, 'invalid_answer_request_id')
        except UnicodeError:
            raise EvidenceError('invalid_knowledge_question') from None
        scope = scope if scope is not None else QueryScope(limit=20, max_age_seconds=2592000)
        require(isinstance(scope, QueryScope) and scope.limit <= 20 and type(include_synthetic) is bool, 'invalid_answer_scope')
        digest = hashlib.sha256(json.dumps({'question': question, 'scope': scope.document(), 'synthetic': include_synthetic,
            'actor': actor.actor_id, 'method': METHOD_VERSION}, sort_keys=True).encode()).hexdigest()
        config = {'method_version': METHOD_VERSION, 'schema_version': SCHEMA_VERSION,
                  'member_limit': 20, 'fact_limit': 100, 'input_byte_limit': 131072, 'model_status': 'not_requested'}
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'knowledge-answer:{self.workspace_id}:{request_id}',))
            prior = connection.execute('SELECT * FROM knowledge_answers WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior:
                require(prior['request_digest'] == digest, 'answer_request_conflict')
                answer_id = str(prior['id'])
            else:
                answer_id = str(uuid.uuid4())
                query = self.queries.search(scope, actor, request_id='answer:' + answer_id,
                    include_synthetic=include_synthetic, connection=connection)
                facts, truncated = support_facts(query)
                connection.execute('INSERT INTO knowledge_answers(id,workspace_id,request_id,request_digest,question,requested_by,query_result_id,include_synthetic,input_support_ids,input_truncated,status,configuration) '
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'in_progress',%s)",
                    (answer_id, self.workspace_id, request_id, digest, question, actor.actor_id, query['result_id'], include_synthetic,
                     [f['support_id'] for f in facts], truncated, Jsonb(config)))
        if prior:
            return self.read(answer_id, actor, include_synthetic=include_synthetic)
        outcome = {'status': 'empty', 'reason': 'no_permitted_published_facts', 'limitation': 'missing_information'}
        if facts:
            try:
                require(self.model_route is not None and self.model_transport is not None, 'model_route_unavailable')
                require(isinstance(self.model_credential, str) and bool(self.model_credential.strip()), 'model_credential_unavailable')
                config = {**config, **self.model_route.document(), 'model_status': 'requested'}
                require(getattr(self.model_transport, 'execution_mode', 'simulated') == self.model_route.execution_mode, 'model_transport_classification_mismatch')
                if self.model_route.execution_mode == 'provider':
                    require(getattr(self.model_transport, 'enabled', False) is True, 'model_live_disabled')
                request = request_document(self.model_route, question, facts)
                require(len(request['input'][0]['content'][0]['text'].encode('utf-8')) <= 131072, 'answer_context_bound_exceeded')
                with self.db.connect() as connection:
                    connection.execute('UPDATE knowledge_answers SET configuration=%s WHERE id=%s', (Jsonb(config), answer_id))
                def attach_operation(operation_id):
                    with self.db.connect() as connection:
                        connection.execute('UPDATE knowledge_answers SET operation_id=%s WHERE id=%s', (operation_id, answer_id))
                # The initiating human is the actual cost actor; generated authorship
                # is separately labelled by the method, not a forged human statement.
                outcome = execute_request(self.model_route, self.model_transport, self.model_credential,
                    UsageAccounting(self.db, self.workspace_id), actor, operation_request='answer:' + answer_id,
                    method_version=METHOD_VERSION, request=request,
                    validate=lambda response: validate(response, {f['support_id'] for f in facts}), attach_operation=attach_operation,
                    dispatch_guard=lambda connection: None if self._inputs_permitted(query['result_id'], actor,
                        [f['support_id'] for f in facts], include_synthetic, connection) else 'answer_support_changed_before_dispatch')
            except EvidenceError as error:
                code = str(error)
                outcome = {'status': 'meter_failure' if code in {'synthetic_service_bound_violated', 'provider_service_bound_or_meter_violated'} else 'blocked', 'reason': code}
            except Exception:
                outcome = {'status': 'transport_uncertain', 'reason': 'model_transport_outcome_unknown'}
        with self.db.connect() as connection:
            # Lock all actual inputs, including unselected evidence that influenced
            # relevance, across publication. New KB publications never replace them.
            if outcome['status'] == 'succeeded' and not self._inputs_permitted(
                    query['result_id'], actor, [f['support_id'] for f in facts], include_synthetic, connection):
                outcome = {**outcome, 'status': 'stale', 'reason': 'answer_support_changed', 'support_ids': []}
            connection.execute('UPDATE knowledge_answers SET status=%s,reason=%s,limitation=%s,configuration=%s,usage=%s,selected_support_ids=%s,finished_at=now() WHERE id=%s',
                (outcome['status'], outcome.get('reason'), outcome.get('limitation'), Jsonb(config), Jsonb(outcome.get('usage')),
                 outcome.get('support_ids', []), answer_id))
        return self.read(answer_id, actor, include_synthetic=include_synthetic)

    def _inputs_permitted(self, query_id, actor, input_ids, include_synthetic, connection):
        query = self.queries.read(query_id, actor, include_synthetic=include_synthetic, connection=connection)
        statuses = self.queries.statuses(query_id, actor, include_synthetic=include_synthetic, connection=connection)
        facts, _ = support_facts(query)
        return self._permitted(statuses) and set(input_ids) <= {f['support_id'] for f in facts}

    @staticmethod
    def _permitted(statuses):
        return all(s['can_process'] and s['can_display'] and s['current'] for s in statuses.values())

    def read(self, answer_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict:
        """Reopen immutable model/support context, withholding dependent selection on policy loss.

        Source values/dates always come from the exact query's current public read.
        Requiring every input to remain permitted prevents unselected withdrawn text
        from surviving indirectly in a generated selection. No new search or I/O.
        """
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM knowledge_answers WHERE id=%s AND workspace_id=%s', (answer_id, self.workspace_id)).fetchone()
            require(row is not None, 'knowledge_answer_not_found')
            require(not row['include_synthetic'] or include_synthetic, 'synthetic_evidence_excluded')
            query_id = str(row['query_result_id'])
            query = self.queries.read(query_id, actor, include_synthetic=include_synthetic, connection=connection)
            statuses = self.queries.statuses(query_id, actor, include_synthetic=include_synthetic, connection=connection)
            facts, _ = support_facts(query)
            by_id = {f['support_id']: f for f in facts}
            input_ids = [str(i) for i in row['input_support_ids']]
            selected = [str(i) for i in row['selected_support_ids']]
            usable = row['status'] == 'succeeded' and self._permitted(statuses) and all(i in by_id for i in input_ids)
            missing = sorted({u for m in query['members'] for u in m['unknowns']})
            limits = [*LIMITS, *query['unknowns']]
            if row['input_truncated']:
                limits.append('model_input_fact_limit_reached')
            if any(m['freshness']['state'] == 'stale' for m in query['members']):
                limits.append('stale_source_capture')
            if (usable or row['status'] == 'empty') and row['limitation'] in {'missing_information', 'ambiguous_question'}:
                limits.append(row['limitation'])
            if not usable and row['status'] == 'succeeded':
                limits.append('answer_input_support_unavailable_or_superseded')
            # Selected IDs encode a source-derived judgment; withhold that judgment
            # whenever any actual input loses policy, retaining only input lineage.
            return {'answer_id': answer_id, 'question': row['question'], 'request_id': row['request_id'],
                'requested_by': {'actor_id': row['requested_by'], 'kind': 'human'},
                'generated_by': {'actor_id': 'knowledge-answer-model', 'kind': 'automation'},
                'answer_basis': 'model_selected_exact_published_findings', 'status': row['status'], 'reason': row['reason'],
                'usable': usable, 'limitation': row['limitation'] if usable or row['status'] == 'empty' else None,
                'configuration': row['configuration'], 'operation_id': str(row['operation_id']) if row['operation_id'] else None,
                'usage': row['usage'], 'knowledge_query': query, 'input_support_ids': input_ids,
                'selected_support_ids': selected if usable else [], 'findings': [by_id[i] for i in selected] if usable else [],
                'missing_information': missing, 'limits': sorted(set(limits)),
                'recorded_at': row['recorded_at'].isoformat(), 'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None}
