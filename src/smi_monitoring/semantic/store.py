"""Durable no-reissue claims with exact full-input policy and metered Responses I/O."""

import uuid
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_campaigns.responses import ResponsesRoute, ResponsesTransport, execute_request
from smi_costs import UsageAccounting
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_monitoring.contracts import require
from smi_monitoring.recent import RecentMonitoring
from smi_monitoring.recent.route import fingerprint, instant

from .method import ControversyThreshold, LIMITS, METHOD_VERSION, context, eligible, method_document, request_document, significant, validate


class SemanticAlerts:
    """Assess one exact window for possible quality controversy, without research authority.

    Trusted configuration selects thresholds and the installed shared model route.
    A committed claim owns at most one call; every retry reopens its first outcome.
    Source-free lineage outlives permanently purged source-dependent judgments.
    """

    def __init__(self, recent: RecentMonitoring, *, threshold: ControversyThreshold | None = None,
                 model_route: ResponsesRoute | None = None, model_transport: ResponsesTransport | None = None,
                 model_credential: str | None = None, clock: Callable[[], datetime] | None = None):
        self.recent, self.db, self.workspace_id = recent, recent.db, recent.workspace_id
        self.threshold = threshold
        self.model_route, self.model_transport, self.model_credential = model_route, model_transport, model_credential
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def migrate(self) -> None:
        """Install local semantic claims/alerts after recent evidence and shared costs."""
        self.recent.migrate()
        UsageAccounting(self.db, self.workspace_id).migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _inputs(self, connection, window_id, actor):
        # This public read checks all three permissions and keeps the recent owner's
        # workspace policy lock through the caller's local commit, including admission.
        window = self.recent.read_window_in_transaction(connection, window_id, actor, purpose='display')
        return window, context(window)

    def _current(self, connection, window_id, actor, digest):
        window, inputs = self._inputs(connection, window_id, actor)
        return 'source_support_unavailable' not in eligible(window) and fingerprint(inputs) == digest

    def detect(self, window_id: str, actor: ActorContext, *, request_id: str) -> dict:
        """Claim one configured assessment, admit one call and finalize against all inputs.

        Complete windows contain at most 20 retained captures. Missing baseline is
        explicit: this method assesses possible mixed positions, never semantic shift.
        Invalid output may consume usage but cannot create an alert or grant authority.
        No PostgreSQL transaction spans the model I/O.
        """
        self.recent.require_operator(actor)
        require(self.threshold is not None, 'controversy_threshold_unconfigured')
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200 and '\x00' not in request_id, 'invalid_semantic_request')
        try:
            window_id = str(uuid.UUID(window_id))
        except (TypeError, ValueError, AttributeError):
            raise EvidenceError('invalid_monitoring_window_id') from None
        method = method_document(self.threshold)
        config = asdict(self.model_route) if self.model_route is not None else {}
        key = fingerprint({'window': window_id, 'method': method, 'configuration': config})
        request_digest = fingerprint({'assessment': key, 'actor': actor.actor_id, 'kind': actor.kind})
        with self.db.connect() as connection:
            window, inputs = self._inputs(connection, window_id, actor)
            prior = connection.execute('SELECT * FROM monitoring_semantic_requests WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if prior:
                require(prior['request_digest'] == request_digest, 'semantic_request_conflict')
                return self._read(connection, prior['assessment_id'], actor)
            row = connection.execute('SELECT id FROM monitoring_semantic_assessments WHERE workspace_id=%s AND assessment_digest=%s', (self.workspace_id, key)).fetchone()
            fresh = row is None
            assessment_id = uuid.uuid4() if fresh else row['id']
            if fresh:
                count = connection.execute('SELECT count(*) AS n FROM monitoring_semantic_assessments WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
                require(count < 5000, 'monitoring_semantic_assessment_limit')
                connection.execute('INSERT INTO monitoring_semantic_assessments(id,workspace_id,window_id,assessment_digest,method,configuration,input_observation_ids,input_digest,status,outcome,limitations,recorded_by,actor_kind,recorded_at) '
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'in_progress','not_assessable',%s,%s,%s,%s)",
                    (assessment_id, self.workspace_id, window_id, key, Jsonb(method), Jsonb(config),
                     [o['observation_id'] for o in inputs['observations']], fingerprint(inputs), Jsonb(eligible(window)), actor.actor_id, actor.kind, instant(self.clock().isoformat())))
            count = connection.execute('SELECT count(*) AS n FROM monitoring_semantic_requests WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
            require(count < 20000, 'monitoring_semantic_request_limit')
            connection.execute('INSERT INTO monitoring_semantic_requests(workspace_id,request_id,request_digest,assessment_id) VALUES (%s,%s,%s,%s)',
                (self.workspace_id, request_id, request_digest, assessment_id))
            if not fresh:
                return self._read(connection, assessment_id, actor)
        limitations = eligible(window)
        outcome = {'status': 'not_assessable', 'reason': limitations[0] if limitations else None}
        if not limitations:
            try:
                require(self.model_route is not None and self.model_transport is not None, 'model_route_unavailable')
                require(isinstance(self.model_credential, str) and bool(self.model_credential.strip()), 'model_credential_unavailable')
                config = self.model_route.document()
                require(getattr(self.model_transport, 'execution_mode', 'simulated') == self.model_route.execution_mode, 'model_transport_classification_mismatch')
                if self.model_route.execution_mode == 'provider':
                    require(getattr(self.model_transport, 'enabled', False) is True, 'model_live_disabled')
                request = request_document(self.model_route, inputs)
                require(len(request['input'][0]['content'][0]['text'].encode('utf-8')) <= 131072, 'semantic_context_bound_exceeded')
                with self.db.connect() as connection:
                    connection.execute('UPDATE monitoring_semantic_assessments SET configuration=%s WHERE id=%s', (Jsonb(config), assessment_id))
                def attach(operation_id):
                    with self.db.connect() as connection:
                        connection.execute('UPDATE monitoring_semantic_assessments SET operation_id=%s WHERE id=%s', (operation_id, assessment_id))
                outcome = execute_request(self.model_route, self.model_transport, self.model_credential,
                    UsageAccounting(self.db, self.workspace_id), actor, operation_request='semantic:' + str(assessment_id),
                    method_version=METHOD_VERSION, request=request, validate=lambda response: validate(response, inputs), attach_operation=attach,
                    dispatch_guard=lambda connection: None if self._current(connection, window_id, actor, fingerprint(inputs)) else 'semantic_support_changed_before_dispatch')
            except EvidenceError as error:
                outcome = {'status': 'meter_failure' if str(error) in {'synthetic_service_bound_violated', 'provider_service_bound_or_meter_violated'} else 'blocked', 'reason': str(error)}
            except Exception:
                outcome = {'status': 'transport_uncertain', 'reason': 'model_transport_outcome_unknown'}
        with self.db.connect() as connection:
            current = self._current(connection, window_id, actor, fingerprint(inputs))
            row = connection.execute('SELECT support_purged FROM monitoring_semantic_assessments WHERE id=%s FOR UPDATE', (assessment_id,)).fetchone()
            if outcome['status'] == 'succeeded' and (not current or row['support_purged']):
                outcome = {**outcome, 'status': 'stale', 'reason': 'semantic_input_support_changed', 'judgments': []}
            judgments = outcome.get('judgments', [])
            finding = ('possible_controversy' if significant(judgments, inputs, method['configuration']) else 'no_signal') if outcome['status'] == 'succeeded' else 'not_assessable'
            connection.execute('UPDATE monitoring_semantic_assessments SET status=%s,outcome=%s,reason=%s,configuration=%s,usage=%s,judgments=%s,support_purged=%s,finished_at=%s WHERE id=%s',
                (outcome['status'], finding, outcome.get('reason'), Jsonb(config), Jsonb(outcome.get('usage')), Jsonb(judgments),
                 row['support_purged'] or not current, instant(self.clock().isoformat()), assessment_id))
            if finding == 'possible_controversy':
                connection.execute('INSERT INTO monitoring_semantic_alerts(id,assessment_id,notification_id,created_at) VALUES (%s,%s,%s,%s)',
                    (uuid.uuid4(), assessment_id, uuid.uuid4(), instant(self.clock().isoformat())))
        return self.read_assessment(str(assessment_id), actor)

    def _read(self, connection, assessment_id, actor):
        row = connection.execute('SELECT a.*,l.id AS alert_id,l.notification_id FROM monitoring_semantic_assessments a LEFT JOIN monitoring_semantic_alerts l ON l.assessment_id=a.id WHERE a.id=%s AND a.workspace_id=%s', (assessment_id, self.workspace_id)).fetchone()
        require(row is not None, 'monitoring_semantic_assessment_not_found')
        window, inputs = self._inputs(connection, row['window_id'], actor)
        row = connection.execute('SELECT a.*,l.id AS alert_id,l.notification_id FROM monitoring_semantic_assessments a LEFT JOIN monitoring_semantic_alerts l ON l.assessment_id=a.id WHERE a.id=%s AND a.workspace_id=%s FOR UPDATE OF a', (assessment_id, self.workspace_id)).fetchone()
        current = 'source_support_unavailable' not in eligible(window) and fingerprint(inputs) == row['input_digest']
        purged = row['support_purged'] or not current
        if purged:
            connection.execute("UPDATE monitoring_semantic_assessments SET judgments='[]',support_purged=TRUE WHERE id=%s", (row['id'],))
        usable = row['status'] == 'succeeded' and not purged
        by_id = {o['observation_id']: o for o in inputs['observations']}
        judgments = [{**j, 'native_id': by_id[j['observation_id']]['native_id'],
            'excerpt': by_id[j['observation_id']]['text'][j['start']:j['end']] if j['start'] is not None else None}
            for j in row['judgments']] if usable else []
        # A display grant cannot reveal source values when processing is denied.
        if not all(window['current_permissions'].values()):
            window = {**window, 'observations': [{**o, 'body': None} for o in window['observations']]}
        return {'assessment_id': str(row['id']), 'alert_id': str(row['alert_id']) if row['alert_id'] else None,
            'notification_id': str(row['notification_id']) if row['notification_id'] else None,
            'status': row['status'], 'outcome': row['outcome'], 'reason': row['reason'], 'usable': usable,
            'current_support': 'available' if current else 'unavailable', 'support_purged': purged,
            'judgments': judgments, 'input_observation_ids': [str(i) for i in row['input_observation_ids']],
            'input_digest': row['input_digest'], 'method': row['method'], 'configuration': row['configuration'],
            'comparison': {'baseline_window_id': None, 'change_status': 'not_assessed'},
            'limitations': sorted(set(LIMITS + row['limitations'] + (['semantic_input_support_unavailable'] if purged else []))),
            'window': window, 'recorded_by': row['recorded_by'], 'actor_kind': row['actor_kind'],
            'generated_by': {'actor_id': 'monitoring-quality-model', 'kind': 'automation'},
            'operation_id': str(row['operation_id']) if row['operation_id'] else None, 'usage': row['usage'],
            'recorded_at': row['recorded_at'].isoformat(), 'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None}

    def read_assessment(self, assessment_id: str, actor: ActorContext) -> dict:
        """Reopen exact historical inputs; any lost input permanently purges judgments."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            return self._read(connection, assessment_id, actor)

    def read_alert(self, alert_id: str, actor: ActorContext) -> dict:
        """Reopen one retained semantic alert through all actual input dependencies."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT a.id FROM monitoring_semantic_assessments a JOIN monitoring_semantic_alerts l ON l.assessment_id=a.id WHERE l.id=%s AND a.workspace_id=%s', (alert_id, self.workspace_id)).fetchone()
            require(row is not None, 'monitoring_semantic_alert_not_found')
            return self._read(connection, row['id'], actor)

    def history(self, actor: ActorContext) -> list[dict]:
        """List latest 100 exact claims including no-call, invalid and uncertain outcomes."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute('SELECT id FROM monitoring_semantic_assessments WHERE workspace_id=%s ORDER BY recorded_at DESC,id DESC LIMIT 100', (self.workspace_id,)).fetchall()
            return [self._read(connection, row['id'], actor) for row in rows]

    def notifications(self, actor: ActorContext) -> list[dict]:
        """Compose latest 100 local semantic notifications without copied source wording."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            if connection.execute("SELECT to_regclass('monitoring_semantic_alerts') AS relation").fetchone()['relation'] is None:
                return []
            rows = connection.execute('SELECT a.id FROM monitoring_semantic_assessments a JOIN monitoring_semantic_alerts l ON l.assessment_id=a.id WHERE a.workspace_id=%s ORDER BY l.created_at DESC,l.id DESC LIMIT 100', (self.workspace_id,)).fetchall()
            result = []
            for row in rows:
                assessment = self._read(connection, row['id'], actor)
                result.append({'notification_id': assessment['notification_id'], 'alert_id': assessment['alert_id'],
                    'kind': 'semantic', 'created_at': assessment['recorded_at'], 'href': '/monitoring/semantic-alerts/' + assessment['alert_id'],
                    'message': ('Provisional automated possible quality-controversy signal in the supplied X sample. No verified controversy or change-over-time claim.'
                        if assessment['usable'] else 'Retained semantic X alert. Current derived finding unavailable; original input support was lost.'),
                    'current_support': assessment['current_support']})
            return result
