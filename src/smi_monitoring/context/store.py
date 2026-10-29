"""Compose governed alert and KB readers without copying source-derived facts."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from psycopg.types.json import Jsonb

from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope
from smi_monitoring.alerts import QuantitativeAlerts
from smi_monitoring.contracts import require
from smi_monitoring.recent import RecentMonitoring
from smi_monitoring.recent.route import fingerprint
from smi_monitoring.semantic import SemanticAlerts


UNCERTAINTY = ('Literal topic matching provides possible context only. Co-occurrence establishes neither causation '
               'nor entity equivalence. No complete market coverage, verified controversy, semantic relevance or change explanation is established.')


class AlertInvestigations:
    """Save one bounded existing-KB selection beside either retained alert method.

    Only public local readers are composed. No model, acquisition, task, campaign
    or topic-mutation dependency is accepted. Source locks last through commits.
    """

    method_version = 'literal-alert-context-v1'

    def __init__(self, recent: RecentMonitoring):
        self.db, self.workspace_id = recent.db, recent.workspace_id
        self.quantitative = QuantitativeAlerts(recent)
        self.semantic = SemanticAlerts(recent)
        self.queries = KnowledgeQueries(self.db, self.workspace_id)
        self.publications = KnowledgePublications(self.db, self.workspace_id)

    def migrate(self) -> None:
        """Install the source-free context manifest after the owning reader schemas."""
        self.quantitative.migrate()
        self.semantic.migrate()
        self.queries.migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _alert(self, connection, kind, alert_id, actor):
        require(kind in {'quantitative', 'semantic'}, 'invalid_alert_kind')
        reader = self.quantitative if kind == 'quantitative' else self.semantic
        return reader.read_alert(alert_id, actor, connection=connection)

    def investigate(self, kind: Literal['quantitative', 'semantic'], alert_id: str, actor: ActorContext, *, request_id: str, include_synthetic: bool = False) -> dict:
        """Pin a literal query over at most 100 publications and 20 context members.

        The query uses the alert's frozen detection-topic wording across existing
        KB platforms; it does not infer entity identity. Changed request inputs or
        producer conflict. New requests may select newer committed publications.
        """
        actor.require_workspace(self.workspace_id)
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200, 'invalid_alert_investigation_request')
        require(type(include_synthetic) is bool, 'invalid_synthetic_selection')
        try:
            alert_id = str(uuid.UUID(alert_id))
        except (TypeError, ValueError, AttributeError):
            require(False, 'invalid_monitoring_alert_id')
        digest = fingerprint({'kind': kind, 'alert': alert_id, 'actor': actor.actor_id,
            'actor_kind': actor.kind, 'synthetic': include_synthetic, 'method': self.method_version})
        with self.db.connect() as connection:
            # Search and promotion both compose the frontier before recent policy;
            # acquiring it after the alert read would invert promotion's order.
            self.publications.lock_current(actor, connection=connection)
            alert = self._alert(connection, kind, alert_id, actor)
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'alert-context:{self.workspace_id}',))
            row = connection.execute('SELECT * FROM monitoring_alert_investigations WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if row:
                require(row['request_digest'] == digest, 'alert_investigation_request_conflict')
                return self._read(connection, row, actor, include_synthetic)
            require(alert['current_support'] == 'available' and alert.get('usable', True), 'alert_context_support_unavailable')
            count = connection.execute('SELECT count(*) AS n FROM monitoring_alert_investigations WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
            require(count < 5000, 'alert_investigation_limit')
            windows = list(alert['windows'].values()) if kind == 'quantitative' else [alert['window']]
            window = alert['windows']['detection'] if kind == 'quantitative' else alert['window']
            dependencies = [{'window_id': w['window_id'], 'observation_ids': [o['observation_id'] for o in w['observations']]} for w in windows if w]
            investigation_id = str(uuid.uuid4())
            query = self.queries.search(QueryScope(text=window['configuration']['query'], limit=20), actor,
                request_id='alert-context:' + investigation_id, purpose='display', include_synthetic=include_synthetic, connection=connection)
            connection.execute('INSERT INTO monitoring_alert_investigations(id,workspace_id,request_id,request_digest,alert_kind,alert_id,query_result_id,recent_dependencies,method_version,include_synthetic,recorded_by,actor_kind,recorded_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (investigation_id, self.workspace_id, request_id, digest, kind, alert_id, query['result_id'], Jsonb(dependencies), self.method_version, include_synthetic, actor.actor_id, actor.kind, datetime.now(timezone.utc)))
            row = connection.execute('SELECT * FROM monitoring_alert_investigations WHERE id=%s', (investigation_id,)).fetchone()
            return self._read(connection, row, actor, include_synthetic)

    def _read(self, connection, row, actor, include_synthetic):
        require(not row['include_synthetic'] or include_synthetic, 'synthetic_evidence_excluded')
        alert = self._alert(connection, row['alert_kind'], str(row['alert_id']), actor)
        # Recent's workspace lock precedes this row lock on both new and saved reads.
        row = connection.execute('SELECT * FROM monitoring_alert_investigations WHERE id=%s FOR UPDATE', (row['id'],)).fetchone()
        query = self.queries.read(str(row['query_result_id']), actor, include_synthetic=include_synthetic, connection=connection)
        statuses = self.queries.statuses(query['result_id'], actor, include_synthetic=include_synthetic, connection=connection)
        permitted = {key: all(status.get(p, False) for p in ('can_process', 'can_display', 'can_retain', 'current')) for key, status in statuses.items()}
        required_claims = {identity for member in query['manifest'] for identity in member['interpretation_ids']}
        supported_claims = {claim['id'] for claim in query['interpretations'] if claim['state'] == 'supported'}
        usable = (alert['current_support'] == 'available' and alert.get('usable', True)
                  and all(permitted.values()) and required_claims <= supported_claims)
        withheld = row['explanation_withheld'] or not usable
        if withheld:
            connection.execute('UPDATE monitoring_alert_investigations SET explanation_withheld=TRUE WHERE id=%s', (row['id'],))
        query = {**query, 'members': [m if permitted[m['observation_id']] else {
            **{key: m[key] for key in ('observation_id', 'publication_id', 'derivation_id', 'assertion_ids', 'metric_ids')}, 'availability': 'unavailable',
            'support_status': m['support_status'], 'freshness': {'state': 'unknown'}, 'unknowns': ['context_support_unavailable']}
            for m in query['members']], 'interpretations': [c for c in query['interpretations'] if permitted[c['observation_id']]]}
        selected = len(query['manifest'])
        explanation = None if withheld else {'basis': 'bounded_literal_context_juxtaposition',
            'selected_context_members': selected, 'alert_outcome': alert['outcome'],
            'finding': ('Existing permitted KB support matches the frozen topic wording; inspect its independent source dates and claims below.'
                        if selected else 'No matching permitted published KB context was selected. The knowledge gap remains unresolved.'),
            'uncertainty': UNCERTAINTY}
        return {'investigation_id': str(row['id']), 'alert_kind': row['alert_kind'], 'alert_id': str(row['alert_id']),
            'recent_evidence': alert, 'recent_dependencies': row['recent_dependencies'], 'knowledge_context': query,
            'explanation': explanation, 'explanation_withheld': withheld,
            'gaps': ['existing_kb_context_missing'] if not selected else [], 'uncertainty': UNCERTAINTY,
            'method_version': row['method_version'], 'recorded_by': row['recorded_by'], 'actor_kind': row['actor_kind'],
            'recorded_at': row['recorded_at'].isoformat()}

    def read(self, investigation_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict:
        """Reopen exact dependencies; observed policy loss permanently withholds explanation."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM monitoring_alert_investigations WHERE id=%s AND workspace_id=%s', (investigation_id, self.workspace_id)).fetchone()
            require(row is not None, 'alert_investigation_not_found')
            return self._read(connection, row, actor, include_synthetic)
