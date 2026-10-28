"""Atomic selected-source ingestion and publication with durable exact receipts."""

import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_ingestion.adapters.registry import AdapterRegistry
from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import ObservationDraft, RunLimits, SourceReference
from smi_ingestion.evidence import policy_from_json
from smi_ingestion.dependencies import SourceDependencies
from smi_ingestion.runner import IngestionRunner
from smi_ingestion.support import IngestedEvidence
from smi_knowledge import KnowledgePublications
from smi_monitoring.contracts import require
from smi_monitoring.recent.route import fingerprint, instant

from .mapper import ExistingCaptureOnly, RecentXMapper


class MonitoringPromotion:
    """Promote at most twenty explicitly selected captures without acquisition."""

    def __init__(self, recent, evidence):
        self.recent, self.evidence = recent, evidence
        self.db, self.workspace_id = recent.db, recent.workspace_id
        self.publications = KnowledgePublications(self.db, self.workspace_id)

    def migrate(self):
        """Install normal ingestion/publication prerequisites and source-free receipts."""
        self.db.migrate()
        self.recent.migrate()
        self.publications.migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def promote(self, window_id, observation_ids, actor, *, request_id):
        """Commit permitted selected captures and exact outcomes in one local transaction."""
        self.recent.require_operator(actor)
        require(isinstance(request_id, str) and 1 <= len(request_id.strip()) <= 200, 'invalid_promotion_request')
        require(isinstance(observation_ids, tuple) and 1 <= len(observation_ids) <= 20 and all(isinstance(i, str) for i in observation_ids) and len(set(observation_ids)) == len(observation_ids), 'invalid_promotion_selection')
        try:
            require(all(str(uuid.UUID(i)) == i for i in (window_id, *observation_ids)), 'invalid_promotion_selection')
        except (ValueError, TypeError, AttributeError):
            require(False, 'invalid_promotion_selection')
        hashed = fingerprint({'window_id': window_id, 'observation_ids': observation_ids, 'actor': actor.actor_id, 'kind': actor.kind})
        with self.db.connect() as connection:
            self.publications.lock_current(actor, connection=connection)
            window = self.recent.read_window_in_transaction(connection, window_id, actor, purpose='process')
            prior = connection.execute('SELECT * FROM monitoring_promotions WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior:
                require(prior['request_digest'] == hashed, 'promotion_request_conflict')
                return self._result(prior)
            count = connection.execute('SELECT count(*) AS n FROM monitoring_promotions WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
            require(count < 5000, 'monitoring_promotion_limit')
            records = {o['observation_id']: o for o in window['observations']}
            items = []
            for identity in observation_ids:
                record = records.get(identity)
                item = {'monitoring_observation_id': identity}
                if record is None:
                    items.append({**item, 'state': 'not_in_window'})
                    continue
                previous = connection.execute('SELECT * FROM monitoring_promoted_captures WHERE workspace_id=%s AND monitoring_observation_id=%s', (self.workspace_id, identity)).fetchone()
                if previous:
                    published = self.publications.read(str(previous['publication_id']), actor, purpose='process', include_synthetic=True, connection=connection)
                    usable = record['body'] is not None and window['support_permitted'] and all(m['availability'] == 'available' and m['support_status'] == 'current' for m in published['members'])
                    items.append({**item, 'state': 'publication_reused' if usable else 'publication_unavailable', **{k: str(previous[k]) for k in ('run_id', 'observation_id', 'publication_id')}})
                    continue
                if record['body'] is None or not window['support_permitted']:
                    items.append({**item, 'state': 'source_unavailable'})
                    continue
                items.append({**item, **self._publish(connection, window, record, actor)})
            successes = sum(i['state'] in {'published', 'publication_reused'} for i in items)
            outcome = 'published' if successes == len(items) else 'partial' if successes else 'unavailable'
            row = connection.execute('INSERT INTO monitoring_promotions(id,workspace_id,request_id,request_digest,window_id,recorded_by,outcome,items) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
                                     (uuid.uuid4(), self.workspace_id, request_id, hashed, window_id, actor.actor_id, outcome, Jsonb(items))).fetchone()
            return self._result(row)

    def _publish(self, connection, window, record, actor):
        payload = json.dumps(record, sort_keys=True).encode()
        policy_document = self.recent.read_source_policy_in_transaction(connection, record['policy_context_id'], actor)
        policy_document['expires_at'] = min(instant(record['retain_until']), instant(policy_document['expires_at']) if policy_document['expires_at'] else instant(record['retain_until'])).isoformat()
        run_id = self.evidence.start_run(Path('monitoring-selection'), fingerprint({'origin': record['observation_id']}), 'monitoring-x', RunLimits(max_requests=1, max_records=1), connection=connection, workspace_id=self.workspace_id)
        draft = ObservationDraft(record['observation_id'], 'monitoring-x', record['acquisition']['route'], 'retained-recent-x-v1',
            SourceReference(record['source_reference'], 'x', 'content', record['native_id']), payload, 'application/json',
            instant(record['captured_at']) if record['captured_at'] else None, None,
            policy_from_json(policy_document), record['acquisition']['synthetic'],
            {'monitoring_origin': {'window_id': window['window_id'], 'observation_id': record['observation_id'], 'topic_revision_id': window['topic_revision_id']},
             'original_acquisition': record['acquisition'], 'original_imported_at': record['imported_at'],
             'published_at': record['published_at'], 'metric_measured_at': record['metric_measured_at'], 'retain_until': record['retain_until'],
             'metric_definitions': record['metric_definitions'], 'unavailable_fields': ['author_account', 'creator', 'product_association'], 'market_coverage': 'unknown'}, request_attempts=0)
        observation = self.evidence.save(run_id, 0, draft, {'index': 1}, complete=True, connection=connection, retain_payload=False)
        SourceDependencies().bind(connection, observation.id, owner_id='recent-x:' + self.workspace_id, origin_id=record['observation_id'], native_id=record['native_id'], policy_context_id=record['policy_context_id'], retain_until=instant(record['retain_until']))
        registry = AdapterRegistry()
        registry.register('monitoring-x', ExistingCaptureOnly(), RecentXMapper())
        runner = IngestionRunner(self.evidence, CanonicalWriter(self.db), registry)
        applied = runner.map_observation(observation, payload, connection=connection)
        self.evidence.finish(run_id, 'completed' if applied else 'partial', connection=connection)
        if not applied:
            return {'state': 'quarantined', 'run_id': run_id, 'observation_id': observation.id}
        support = IngestedEvidence(self.db, self.workspace_id).select_run(run_id, actor, include_synthetic=True, connection=connection)
        publication = self.publications.publish(support, actor, request_id='monitoring-capture:' + record['observation_id'], include_synthetic=True, connection=connection)
        connection.execute('INSERT INTO monitoring_promoted_captures(workspace_id,monitoring_observation_id,run_id,observation_id,publication_id) VALUES (%s,%s,%s,%s,%s)',
                           (self.workspace_id, record['observation_id'], run_id, observation.id, publication['publication_id']))
        return {'state': 'published', 'run_id': run_id, 'observation_id': observation.id, 'publication_id': publication['publication_id']}

    def _result(self, row):
        return {'promotion_id': str(row['id']), 'window_id': str(row['window_id']), 'status': row['outcome'], 'items': row['items'],
                'recorded_by': row['recorded_by'], 'recorded_at': row['recorded_at'].isoformat()}

    def read(self, promotion_id, actor):
        """Reopen source-free original selection/results without acquisition or new effects."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM monitoring_promotions WHERE id=%s AND workspace_id=%s', (promotion_id, self.workspace_id)).fetchone()
            require(row is not None, 'monitoring_promotion_not_found')
            return self._result(row)
