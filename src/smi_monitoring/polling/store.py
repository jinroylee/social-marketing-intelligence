"""Durable topic authority and one-use periodic source attempts."""

from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
import uuid

import psycopg
from psycopg.types.json import Jsonb


from smi_costs import UsageAccounting, DeferredProviderOperationAdapter, DeferredProviderResult
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_monitoring.contracts import require
from smi_monitoring.recent.route import fingerprint, instant

from .route import LiveXConfig, XRecentRoute, ROUTE, BOUNDS, XCollectionError

CONFIGURATION = {'route': ROUTE, 'version': 'x-recent-search-v1', 'bounds': BOUNDS, 'query_mode': 'literal-phrase'}


class RecentPolling:
    """Run at most one due topic/window per invocation with no paid-call reissue.

    The trusted caller supplies allowed worker identities and runtime gates. Invoke
    periodically from an operator-controlled process; no daemon or environment key
    confers activation. Source response bodies live only in recent evidence.
    """

    def __init__(self, recent, *, config=None, workers=frozenset(), monotonic=None, transaction_observer=None):
        self.recent, self.db, self.workspace_id = recent, recent.db, recent.workspace_id
        self.config, self.workers = config or LiveXConfig(), workers
        self.route = XRecentRoute(self.config, **({'monotonic': monotonic} if monotonic else {}))
        self.transaction_observer = transaction_observer
        self.costs = UsageAccounting(self.db, self.workspace_id)

    def migrate(self):
        """Install recent/cost prerequisites and additive source-free polling records."""
        self.recent.migrate()
        self.costs.migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _now(self):
        return instant(self.recent.clock().isoformat())

    def activate(self, key, actor, *, expected_topic_version, first_window_end, request_id):
        """Record one exact operator activation; process enablement grants no topic authority."""
        self.recent.require_operator(actor)
        require(type(expected_topic_version) is int and expected_topic_version > 0, 'invalid_recent_x_version')
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200, 'invalid_recent_x_request')
        end = instant(first_window_end)
        hashed = fingerprint({'key': key, 'version': expected_topic_version, 'end': end.isoformat(), 'actor': actor.actor_id})
        with self.db.connect() as connection:
            previous = connection.execute('SELECT * FROM monitoring_poll_activations WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if previous:
                require(previous['request_digest'] == hashed, 'monitoring_poll_activation_conflict')
                return {'activation_id': str(previous['id']), 'status': 'duplicate'}
            prepared = self.recent.prepare_collection_in_transaction(connection, key, first_window_end, actor, for_activation=True)
            previous = connection.execute('SELECT * FROM monitoring_poll_activations WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if previous:
                require(previous['request_digest'] == hashed, 'monitoring_poll_activation_conflict')
                return {'activation_id': str(previous['id']), 'status': 'duplicate'}
            require(prepared['version'] == expected_topic_version, 'monitoring_topic_version_conflict')
            require(prepared['permitted'], 'recent_x_collection_not_permitted')
            self.route.validate(prepared, self._now(), activation=True)
            active = connection.execute('SELECT 1 FROM monitoring_poll_activations WHERE workspace_id=%s AND topic_key=%s AND enabled', (self.workspace_id, key)).fetchone()
            require(not active, 'monitoring_poll_already_active')
            count = connection.execute('SELECT count(*) AS n FROM monitoring_poll_activations WHERE workspace_id=%s AND topic_key=%s', (self.workspace_id, key)).fetchone()['n']
            require(count < 100, 'monitoring_poll_activation_limit')
            identity = uuid.uuid4()
            connection.execute('INSERT INTO monitoring_poll_activations(id,workspace_id,topic_key,topic_revision_id,topic_version,configuration,request_id,request_digest,next_window_end,activated_by,activated_at,enabled) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true)',
                (identity, self.workspace_id, key, prepared['revision_id'], expected_topic_version, Jsonb(CONFIGURATION), request_id, hashed, end, actor.actor_id, self._now()))
        return {'activation_id': str(identity), 'status': 'activated'}

    def deactivate(self, key, actor):
        """Stop future dispatch; an already admitted call keeps its accounting identity."""
        self.recent.require_operator(actor)
        # Acquire recent policy/authority lock first, matching dispatch lock order.
        with self.db.connect() as connection:
            configuration = self.recent.read_topic(key, actor)
            self.recent.read_source_policy_in_transaction(connection, configuration['revisions'][-1]['document']['source_policy_id'], actor)
            connection.execute('UPDATE monitoring_poll_activations SET enabled=false WHERE workspace_id=%s AND topic_key=%s AND enabled', (self.workspace_id, key))
        return {'topic_key': key, 'status': 'deactivated'}

    def read(self, key, actor):
        """Reopen bounded source-free activation/attempt lineage without runtime credentials."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            if connection.execute("SELECT to_regclass('monitoring_poll_activations') AS table_name").fetchone()['table_name'] is None:
                return {'topic_key': key, 'activations': [], 'occurrences': []}
            activations = connection.execute('SELECT * FROM monitoring_poll_activations WHERE workspace_id=%s AND topic_key=%s ORDER BY activated_at DESC,id LIMIT 100', (self.workspace_id, key)).fetchall()
            occurrences = connection.execute('SELECT * FROM monitoring_poll_occurrences WHERE workspace_id=%s AND topic_key=%s ORDER BY window_end DESC LIMIT 100', (self.workspace_id, key)).fetchall()
        def document(row):
            return {k: v.isoformat() if hasattr(v, 'isoformat') else str(v) if isinstance(v, uuid.UUID) else v for k, v in row.items() if k != 'request_digest'}
        return {'topic_key': key, 'activations': [document(a) for a in activations], 'occurrences': [document(o) for o in occurrences]}

    def run_due(self, actor):
        """Attempt one due interval; concurrent workers return busy and losses never reissue.

        A session advisory lock grants one dispatcher per topic and is released on
        disconnect. The committed dispatched state fences restarts after I/O loss.
        Admission and recent save use short transactions; HTTP has none open.
        """
        actor.require_workspace(self.workspace_id)
        require(actor.kind == 'automation' and actor.actor_id in self.workers, 'monitoring_poll_worker_required')
        with self.db.connect() as connection:
            candidates = connection.execute('SELECT * FROM monitoring_poll_activations WHERE workspace_id=%s AND enabled AND next_window_end<=%s ORDER BY checked_at NULLS FIRST,next_window_end,topic_key LIMIT 50', (self.workspace_id, self._now() - timedelta(seconds=30))).fetchall()
        if not candidates:
            return {'status': 'not_due'}
        with self.db.connect() as ownership:
            # Session locks, unlike transaction locks, outlive the admission commit.
            ownership.commit()
            ownership.autocommit = True
            for activation in candidates:
                lock = 'recent-poll:' + self.workspace_id + ':' + activation['topic_key']
                granted = ownership.execute('SELECT pg_try_advisory_lock(hashtext(%s)) AS granted', (lock,)).fetchone()['granted']
                if granted:
                    try:
                        try:
                            return self._run(activation, actor, ownership)
                        except psycopg.Error:
                            return {'status': 'ownership_lost', 'reason': 'monitoring_poll_session_lost'}
                    finally:
                        if not ownership.closed:
                            try:
                                ownership.execute('SELECT pg_advisory_unlock(hashtext(%s))', (lock,))
                            except psycopg.Error:
                                pass
        return {'status': 'busy'}

    def _run(self, activation, actor, ownership):
        key, end = activation['topic_key'], activation['next_window_end'].isoformat()
        with ownership.transaction():
            connection = ownership
            connection.execute('UPDATE monitoring_poll_activations SET checked_at=clock_timestamp() WHERE id=%s', (activation['id'],))
            previous = connection.execute('SELECT * FROM monitoring_poll_occurrences WHERE workspace_id=%s AND topic_key=%s AND window_end=%s', (self.workspace_id, key, end)).fetchone()
        if previous:
            previous = {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in previous.items()}
        if previous and previous['state'] in {'dispatched', 'uncertain', 'collected', 'discarded'}:
            if previous['state'] == 'dispatched':
                return self._finish(previous['id'], 'uncertain', 'live_x_response_unavailable', previous['operation_id'], ownership=ownership)
            return self._result(previous)
        if activation['configuration'] != CONFIGURATION:
            return {'status': 'waiting', 'reason': 'monitoring_poll_reactivation_required', 'topic_key': key}
        reason = self.config.unavailable_reason()
        if reason:
            return {'status': 'waiting', 'reason': reason, 'topic_key': key}
        control = self.costs.route_control(ROUTE, actor)
        if not control:
            return {'status': 'waiting', 'reason': 'live_x_cost_configuration_required', 'topic_key': key}
        try:
            with ownership.transaction():
                connection = ownership
                prepared = self.recent.prepare_collection_in_transaction(connection, key, end, actor, max_new_records=10)
                self.route.validate(prepared, self._now())
                require(prepared['revision_id'] == str(activation['topic_revision_id']), 'monitoring_poll_reactivation_required')
                require(prepared['permitted'], 'recent_x_collection_not_permitted')
                current = connection.execute('SELECT * FROM monitoring_poll_activations WHERE id=%s FOR UPDATE', (activation['id'],)).fetchone()
                require(current['enabled'] and current['next_window_end'].isoformat() == end, 'monitoring_poll_authority_changed')
                if prepared['existing_window_id']:
                    connection.execute('UPDATE monitoring_poll_activations SET next_window_end=%s WHERE id=%s', (instant(end) + timedelta(minutes=prepared['settings']['cadence_minutes']), activation['id']))
                    return {'status': 'duplicate', 'window_id': prepared['existing_window_id']}
                count = connection.execute('SELECT count(*) AS n FROM monitoring_poll_occurrences WHERE workspace_id=%s AND topic_key=%s', (self.workspace_id, key)).fetchone()['n']
                require(previous or count < 1000, 'monitoring_poll_occurrence_limit')
                identity = uuid.UUID(previous['id']) if previous else uuid.uuid4()
                occurrence = connection.execute("INSERT INTO monitoring_poll_occurrences(id,activation_id,workspace_id,topic_key,window_end,topic_revision_id,state,acquisition,initiated_by,actor_kind,recorded_at) VALUES (%s,%s,%s,%s,%s,%s,'prepared','{}',%s,%s,%s) ON CONFLICT (workspace_id,topic_key,window_end) DO UPDATE SET id=monitoring_poll_occurrences.id RETURNING *",
                    (identity, activation['id'], self.workspace_id, key, end, prepared['revision_id'], actor.actor_id, actor.kind, self._now())).fetchone()
                identity = occurrence['id']
                previous = occurrence
        except EvidenceError as error:
            return {'status': 'waiting', 'reason': str(error), 'topic_key': key}
        if self.transaction_observer:
            self.transaction_observer('prepared', ownership)
        operation_actor = ActorContext(self.workspace_id, previous['initiated_by'], previous['actor_kind']) if previous else actor
        operation = self.costs.begin_operation(control['scope_id'], operation_actor, request_id='recent-x:' + str(identity), method='x-recent-search-http-v1')
        oid = operation['operation_id']

        @contextmanager
        def transaction(stage):
            with ownership.transaction():
                if self.transaction_observer:
                    self.transaction_observer(stage, ownership)
                yield ownership

        def guard(connection):
            try:
                current = self.recent.prepare_collection_in_transaction(connection, key, end, actor, max_new_records=10)
                reason = ('monitoring_poll_reactivation_required' if current['revision_id'] != prepared['revision_id']
                          else 'recent_x_collection_not_permitted' if not current['permitted'] else None)
                activation_now = connection.execute('SELECT * FROM monitoring_poll_activations WHERE id=%s FOR UPDATE', (activation['id'],)).fetchone()
                if not activation_now['enabled']:
                    reason = 'monitoring_poll_authority_changed'
                self.route.validate(current, self._now())
            except EvidenceError as error:
                reason = str(error)
            if reason is None:
                now = self._now()
                connection.execute('INSERT INTO monitoring_source_cooldowns(route,next_allowed_at) VALUES (%s,%s) ON CONFLICT DO NOTHING', (ROUTE, now))
                quota = connection.execute('SELECT next_allowed_at FROM monitoring_source_cooldowns WHERE route=%s FOR UPDATE', (ROUTE,)).fetchone()
                if now < quota['next_allowed_at']:
                    reason = 'live_x_source_cooldown'
                else:
                    connection.execute('UPDATE monitoring_source_cooldowns SET next_allowed_at=%s WHERE route=%s', (now + timedelta(seconds=2), ROUTE))
            connection.execute('UPDATE monitoring_poll_occurrences SET state=%s,reason=%s,operation_id=%s,dispatched_by=%s,acquisition=%s WHERE id=%s',
                ('waiting' if reason else 'dispatched', reason, oid, actor.actor_id, Jsonb({'route': ROUTE, 'bounds': dict(BOUNDS), 'requests': None, 'bytes_read': None}), identity))
            return reason

        def collect(bound):
            records, acquisition = self.route.collect(prepared, str(identity), self._now())
            acquisition['retrieved_at'] = self._now().isoformat()
            return DeferredProviderResult((records, acquisition))

        adapter = DeferredProviderOperationAdapter(self.costs, control['scope_id'], max_units=control['max_units'])
        try:
            result = adapter.execute(actor, request_id='recent-x:' + str(identity), method='x-recent-search-http-v1', call=collect, operation_actor=operation_actor, dispatch_guard=guard, transaction=transaction)
        except XCollectionError as error:
            return self._finish(identity, 'uncertain', str(error), oid, receipt=error.receipt, ownership=ownership)
        if result['status'] != 'executed':
            return self._finish(identity, 'waiting' if result['status'] == 'refused' else 'uncertain', result['reason'], oid, ownership=ownership)
        records, acquisition = result['value']
        try:
            with ownership.transaction():
                connection = ownership
                self.recent.prepare_collection_in_transaction(connection, key, end, actor, max_new_records=10)
                self._apply_cooldown(connection, acquisition)
                active = connection.execute('SELECT enabled FROM monitoring_poll_activations WHERE id=%s FOR UPDATE', (activation['id'],)).fetchone()
                require(active['enabled'], 'monitoring_poll_authority_changed')
                require(self._now() - instant(acquisition['retrieved_at']) <= timedelta(seconds=20), 'live_x_save_deadline')
                saved = self.recent.save_collection_in_transaction(connection, key, end, actor, revision_id=prepared['revision_id'], records=records, acquisition={**acquisition, 'operation_id': oid})
                connection.execute("UPDATE monitoring_poll_occurrences SET state='collected',reason=NULL,operation_id=%s,window_id=%s,acquisition=%s WHERE id=%s", (oid, saved['window_id'], Jsonb(acquisition), identity))
                connection.execute('UPDATE monitoring_poll_activations SET next_window_end=%s WHERE id=%s', (instant(end) + timedelta(minutes=prepared['settings']['cadence_minutes']), activation['id']))
        except EvidenceError as error:
            return self._finish(identity, 'discarded', str(error), oid, receipt=acquisition, ownership=ownership)
        return {'status': 'collected', 'window_id': saved['window_id'], 'operation_id': oid, 'occurrence_id': str(identity)}

    def _finish(self, identity, state, reason, oid, *, receipt=None, ownership):
        with ownership.transaction():
            connection = ownership
            self._apply_cooldown(connection, receipt or {})
            connection.execute('UPDATE monitoring_poll_occurrences SET state=%s,reason=%s,operation_id=%s,acquisition=COALESCE(%s,acquisition) WHERE id=%s', (state, reason, oid, Jsonb(receipt) if receipt is not None else None, identity))
        return {'status': state, 'reason': reason, 'operation_id': oid, 'occurrence_id': str(identity)}

    def _apply_cooldown(self, connection, receipt):
        delay = receipt.get('cooldown_seconds', 0)
        if delay:
            connection.execute('UPDATE monitoring_source_cooldowns SET next_allowed_at=GREATEST(next_allowed_at,%s) WHERE route=%s', (self._now() + timedelta(seconds=delay), ROUTE))

    def _result(self, row):
        return {'status': row['state'], 'reason': row['reason'], 'operation_id': row['operation_id'], 'window_id': row['window_id'], 'occurrence_id': row['id']}
