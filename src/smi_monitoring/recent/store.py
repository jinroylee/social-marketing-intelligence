"""Durable topic revisions, logical collection windows and governed recent copies."""

import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.dependencies import SourceDependencies
from smi_ingestion.evidence import policy_from_json
from smi_monitoring.contracts import require

from .route import METRICS, OfflineXRoute, capture_fingerprint, capture_identity, fingerprint, instant, validate_records


MAX_TOPICS = 50
MAX_WINDOWS = 1000
MAX_OBSERVATIONS = 20000
MAX_TOPIC_REVISIONS = 100
MAX_POLICIES = 50
MAX_WITHDRAWALS = 20000


class RecentMonitoring:
    """Own recent evidence and current-policy composition for dependent local reads."""

    def __init__(self, db, workspace_id='local', *, route: OfflineXRoute | None = None,
                 operators: frozenset[str] = frozenset(), clock=None):
        self.db, self.workspace_id, self.route = db, workspace_id, route
        self.operators = operators
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def migrate(self):
        """Install independently of knowledge/snapshot schemas; preserve existing tables."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _now(self):
        return instant(self.clock().isoformat())

    def require_operator(self, actor):
        """Require the trusted human operator for bounded monitoring mutations."""
        actor.require_workspace(self.workspace_id)
        require(actor.kind == 'human' and actor.actor_id in self.operators, 'monitoring_operator_required')

    def _lock(self, connection):
        connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('recent-x:' + self.workspace_id,))

    def set_policy(self, document, actor: ActorContext, *, expected_version: int):
        """Set current source permission explicitly; retained copies reconcile synchronously."""
        self.require_operator(actor)
        require(type(expected_version) is int and expected_version >= 0, 'invalid_recent_x_version')
        require(isinstance(document, dict) and set(document) == {'context_id', 'can_process', 'can_display', 'can_retain', 'expires_at', 'revoked'}, 'invalid_recent_x_policy')
        require(isinstance(document['context_id'], str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', document['context_id']), 'invalid_recent_x_policy')
        require(all(type(document[k]) is bool for k in ('can_process', 'can_display', 'can_retain', 'revoked')), 'invalid_recent_x_policy')
        policy = dict(document)
        if policy['expires_at'] is not None:
            policy['expires_at'] = instant(policy['expires_at']).isoformat()
        with self.db.connect() as connection:
            self._lock(connection)
            self._reconcile(connection)
            row = connection.execute('SELECT * FROM monitoring_source_policies WHERE workspace_id=%s AND context_id=%s', (self.workspace_id, policy['context_id'])).fetchone()
            version = row['version'] if row else 0
            if row is None:
                count = connection.execute('SELECT count(*) AS n FROM monitoring_source_policies WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
                require(count < MAX_POLICIES, 'recent_x_policy_limit')
            require(version == expected_version, 'recent_x_policy_version_conflict')
            connection.execute('INSERT INTO monitoring_source_policies(workspace_id,context_id,version,document,recorded_by,recorded_at) VALUES (%s,%s,%s,%s,%s,%s) '
                               'ON CONFLICT (workspace_id,context_id) DO UPDATE SET version=EXCLUDED.version,document=EXCLUDED.document,recorded_by=EXCLUDED.recorded_by,recorded_at=EXCLUDED.recorded_at',
                               (self.workspace_id, policy['context_id'], version + 1, Jsonb(policy), actor.actor_id, self._now()))
            SourceDependencies().update_policy(connection, 'recent-x:' + self.workspace_id, policy_from_json(policy), now=self._now())
            self._reconcile(connection)
        return {'context_id': policy['context_id'], 'version': version + 1}

    def withdraw(self, native_id, actor):
        """Permanently withdraw a native X post, including future fixture captures."""
        self.require_operator(actor)
        require(isinstance(native_id, str) and re.fullmatch(r'[0-9]{1,24}', native_id), 'invalid_recent_x_native_id')
        with self.db.connect() as connection:
            self._lock(connection)
            known = connection.execute('SELECT 1 FROM monitoring_x_withdrawals WHERE workspace_id=%s AND native_id=%s', (self.workspace_id, native_id)).fetchone()
            count = connection.execute('SELECT count(*) AS n FROM monitoring_x_withdrawals WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
            require(known or count < MAX_WITHDRAWALS, 'recent_x_withdrawal_limit')
            connection.execute('INSERT INTO monitoring_x_withdrawals(workspace_id,native_id,withdrawn_by,withdrawn_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING', (self.workspace_id, native_id, actor.actor_id, self._now()))
            connection.execute("UPDATE recent_x_observations SET body=NULL,purged_reason='source_withdrawn' WHERE workspace_id=%s AND native_id=%s", (self.workspace_id, native_id))
            SourceDependencies().withdraw(connection, 'recent-x:' + self.workspace_id, native_id)
        return {'native_id': native_id, 'status': 'withdrawn'}

    def _topic(self, connection, key):
        row = connection.execute('SELECT * FROM monitoring_topics WHERE workspace_id=%s AND topic_key=%s', (self.workspace_id, key)).fetchone()
        require(row is not None, 'monitoring_topic_not_found')
        return row

    def configure(self, key, settings, actor: ActorContext, *, expected_version: int, request_id: str):
        """Save one operator topic revision; stable topic/end identity outlives edits."""
        self.require_operator(actor)
        require(isinstance(key, str) and re.fullmatch(r'[a-z0-9_-]{1,80}', key), 'invalid_monitoring_topic_key')
        require(type(expected_version) is int and expected_version >= 0, 'invalid_recent_x_version')
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200, 'invalid_recent_x_request')
        require(isinstance(settings, dict) and set(settings) == {'query', 'cadence_minutes', 'window_minutes', 'max_records', 'retention_hours', 'source_policy_id'}, 'invalid_monitoring_topic')
        require(isinstance(settings['query'], str) and 1 <= len(settings['query'].strip()) <= 200 and '\x00' not in settings['query'], 'invalid_monitoring_topic_query')
        for field, low, high in (('cadence_minutes', 1, 1440), ('window_minutes', 1, 10080), ('max_records', 1, 100), ('retention_hours', 1, 720)):
            require(type(settings[field]) is int and low <= settings[field] <= high, 'invalid_monitoring_topic_' + field)
        require(isinstance(settings['source_policy_id'], str), 'invalid_recent_x_policy')
        hashed = fingerprint({'settings': settings, 'expected_version': expected_version})
        with self.db.connect() as connection:
            self._lock(connection)
            row = connection.execute('SELECT * FROM monitoring_topics WHERE workspace_id=%s AND topic_key=%s', (self.workspace_id, key)).fetchone()
            if row:
                previous = connection.execute('SELECT * FROM monitoring_topic_revisions WHERE topic_id=%s AND request_id=%s', (row['id'], request_id)).fetchone()
                if previous:
                    require(previous['request_digest'] == hashed and previous['recorded_by'] == actor.actor_id, 'monitoring_topic_request_conflict')
                    return {'topic_key': key, 'version': previous['version'], 'status': 'duplicate'}
            version = row['version'] if row else 0
            require(version == expected_version, 'monitoring_topic_version_conflict')
            require(version < MAX_TOPIC_REVISIONS, 'monitoring_topic_revision_limit')
            require(connection.execute('SELECT 1 FROM monitoring_source_policies WHERE workspace_id=%s AND context_id=%s', (self.workspace_id, settings['source_policy_id'])).fetchone(), 'monitoring_source_policy_not_found')
            if row is None:
                count = connection.execute('SELECT count(*) AS n FROM monitoring_topics WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
                require(count < MAX_TOPICS, 'monitoring_topic_limit')
                topic_id = uuid.uuid4()
                connection.execute('INSERT INTO monitoring_topics(id,workspace_id,topic_key,version) VALUES (%s,%s,%s,1)', (topic_id, self.workspace_id, key))
            else:
                topic_id = row['id']
                connection.execute('UPDATE monitoring_topics SET version=%s WHERE id=%s', (version + 1, topic_id))
            connection.execute('INSERT INTO monitoring_topic_revisions(id,topic_id,version,document,request_id,request_digest,recorded_by,recorded_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                               (uuid.uuid4(), topic_id, version + 1, Jsonb(settings), request_id, hashed, actor.actor_id, self._now()))
        return {'topic_key': key, 'version': version + 1, 'status': 'configured'}

    def _policy(self, connection, context):
        row = connection.execute('SELECT * FROM monitoring_source_policies WHERE workspace_id=%s AND context_id=%s', (self.workspace_id, context)).fetchone()
        require(row is not None, 'monitoring_source_policy_not_found')
        return row['document']

    def read_source_policy_in_transaction(self, connection, context_id, actor):
        """Return current original source policy while retaining the workspace lock."""
        actor.require_workspace(self.workspace_id)
        self._lock(connection)
        return dict(self._policy(connection, context_id))

    def _allowed(self, policy, purpose):
        return (not policy['revoked'] and (policy['expires_at'] is None or instant(policy['expires_at']) > self._now())
                and policy['can_' + purpose])

    def _reconcile(self, connection):
        SourceDependencies().reconcile(connection, owner_id='recent-x:' + self.workspace_id, now=self._now())
        connection.execute("UPDATE recent_x_observations SET body=NULL,purged_reason='retention_expired' WHERE workspace_id=%s AND body IS NOT NULL AND retain_until<=%s", (self.workspace_id, self._now()))
        policies = connection.execute('SELECT document FROM monitoring_source_policies WHERE workspace_id=%s', (self.workspace_id,)).fetchall()
        for row in policies:
            policy = row['document']
            if not self._allowed(policy, 'retain'):
                connection.execute("UPDATE recent_x_observations SET body=NULL,purged_reason='source_retention_unavailable' WHERE workspace_id=%s AND policy_context_id=%s AND body IS NOT NULL", (self.workspace_id, policy['context_id']))

    def list_topics(self, actor):
        """List at most fifty configured topic keys, independent of scheduled keywords."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute('SELECT topic_key,version FROM monitoring_topics WHERE workspace_id=%s ORDER BY topic_key', (self.workspace_id,)).fetchall()
        return rows

    def read_topic(self, key, actor):
        """Reopen configuration history and the latest one hundred source-free windows."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            self._lock(connection)
            self._reconcile(connection)
            row = self._topic(connection, key)
            revisions = connection.execute('SELECT * FROM monitoring_topic_revisions WHERE topic_id=%s ORDER BY version', (row['id'],)).fetchall()
            windows = connection.execute('SELECT id,window_start,window_end FROM monitoring_windows WHERE topic_id=%s ORDER BY window_end DESC LIMIT 100', (row['id'],)).fetchall()
            policy = self._policy(connection, revisions[-1]['document']['source_policy_id'])
        return {'topic_key': key, 'version': row['version'], 'revisions': [{**r, 'id': str(r['id']), 'topic_id': str(r['topic_id']), 'recorded_at': r['recorded_at'].isoformat()} for r in revisions],
                'source_policy': policy, 'windows': [{**w, 'id': str(w['id']), 'window_start': w['window_start'].isoformat(), 'window_end': w['window_end'].isoformat()} for w in windows]}

    def prepare_collection_in_transaction(self, connection, key, window_end, actor, *, for_activation=False, max_new_records=0):
        """Pin one explicit logical window while retaining current policy through commit.

        Trusted collectors authorize their dispatcher separately. No network I/O may
        occur in this transaction; call again immediately before dispatch and save.
        """
        actor.require_workspace(self.workspace_id)
        require(type(max_new_records) is int and 0 <= max_new_records <= 100, 'invalid_recent_x_capacity')
        end = instant(window_end)
        self._lock(connection)
        self._reconcile(connection)
        topic = self._topic(connection, key)
        prior = connection.execute('SELECT id FROM monitoring_windows WHERE topic_id=%s AND window_end=%s', (topic['id'], end)).fetchone()
        revision = connection.execute('SELECT * FROM monitoring_topic_revisions WHERE topic_id=%s AND version=%s', (topic['id'], topic['version'])).fetchone()
        settings = revision['document']
        policy = self._policy(connection, settings['source_policy_id'])
        allowed = self._allowed(policy, 'process') and self._allowed(policy, 'retain')
        now = self._now()
        require(prior or now - timedelta(days=7) <= end <= now + (timedelta(minutes=settings['cadence_minutes']) if for_activation else timedelta(0)) and int(end.timestamp()) % (settings['cadence_minutes'] * 60) == 0 and end.microsecond == 0, 'invalid_recent_x_window')
        count = connection.execute('SELECT count(*) AS n FROM monitoring_windows WHERE topic_id=%s', (topic['id'],)).fetchone()['n']
        require(prior or count < MAX_WINDOWS, 'recent_x_window_limit')
        if not prior and max_new_records:
            observations = connection.execute('SELECT count(*) AS n FROM recent_x_observations WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
            require(observations + min(settings['max_records'], max_new_records) <= MAX_OBSERVATIONS, 'recent_x_observation_limit')
        policy_version = connection.execute('SELECT version FROM monitoring_source_policies WHERE workspace_id=%s AND context_id=%s', (self.workspace_id, settings['source_policy_id'])).fetchone()['version']
        return {'topic_id': str(topic['id']), 'revision_id': str(revision['id']), 'version': topic['version'], 'settings': settings,
                'window_start': (end - timedelta(minutes=settings['window_minutes'])).isoformat(), 'window_end': end.isoformat(),
                'permitted': allowed, 'policy_version': policy_version, 'existing_window_id': str(prior['id']) if prior else None}

    def poll(self, key, window_end, actor):
        """Collect one bounded local fixture; retries reopen the original logical window."""
        self.require_operator(actor)
        with self.db.connect() as connection:
            prepared = self.prepare_collection_in_transaction(connection, key, window_end, actor)
            if prepared['existing_window_id']:
                return {'status': 'duplicate', 'window_id': prepared['existing_window_id']}
            require(self.route is not None, 'recent_x_route_unavailable')
            require(prepared['permitted'], 'recent_x_collection_not_permitted')
            records, acquisition = self.route.collect()
            acquisition.update(sampling={'method': 'literal-query-capture-order-v1', 'record_schema': 'offline-x-record-v1',
                                         'file_record_limit': 200, 'file_byte_limit': 262144})
            return self.save_collection_in_transaction(connection, key, window_end, actor, revision_id=prepared['revision_id'], records=records, acquisition=acquisition)

    def save_collection_in_transaction(self, connection, key, window_end, actor, *, revision_id, records, acquisition):
        """Save a trusted bounded response under original revision and current permissions.

        The caller owns commit/rollback and uses the prepare port before external
        dispatch. Acquisition metadata is trusted server input, never HTTP form data.
        No external I/O occurs here; a stale revision or policy denies all new copies.
        """
        prepared = self.prepare_collection_in_transaction(connection, key, window_end, actor)
        if prepared['existing_window_id']:
            return {'status': 'duplicate', 'window_id': prepared['existing_window_id']}
        require(prepared['revision_id'] == revision_id, 'monitoring_topic_version_conflict')
        require(prepared['permitted'], 'recent_x_collection_not_permitted')
        records = validate_records(records)
        end, start, now = instant(prepared['window_end']), instant(prepared['window_start']), self._now()
        settings = prepared['settings']
        topic, revision = {'id': prepared['topic_id']}, {'id': revision_id}
        acquisition = {**acquisition, 'policy_context_id': settings['source_policy_id'], 'policy_version': prepared['policy_version'], 'max_records': settings['max_records']}
        for record in records:
            capture = instant(record['captured_at']) if record['captured_at'] else None
            publication = instant(record['published_at']) if record['published_at'] else None
            measurement = instant(record['metric_measured_at']) if record['metric_measured_at'] else None
            require(capture is None or capture <= now and (publication is None or publication <= capture), 'invalid_recent_x_source_time')
            require(measurement is None or measurement <= now and (capture is None or measurement <= capture), 'invalid_recent_x_source_time')
        selected, unassessable, withdrawn = [], 0, 0
        withdrawn_ids = {r['native_id'] for r in connection.execute('SELECT native_id FROM monitoring_x_withdrawals WHERE workspace_id=%s', (self.workspace_id,)).fetchall()}
        for record in records:
            if record['native_id'] in withdrawn_ids:
                withdrawn += 1
            elif record['published_at'] is None or record['text'] is None:
                unassessable += 1
            elif start <= instant(record['published_at']) < end and settings['query'].strip().casefold() in record['text'].casefold():
                selected.append(record)
        unique = {}
        for record in selected:
            source_key = capture_identity(record, acquisition.get('response_id'))
            prior_record = unique.get(source_key)
            require(prior_record is None or capture_fingerprint(prior_record) == capture_fingerprint(record), 'recent_x_capture_conflict')
            unique.setdefault(source_key, record)
        duplicates = len(selected) - len(unique)
        selected = sorted(unique.values(), key=lambda r: (r['native_id'], capture_identity(r, acquisition.get('response_id'))))
        truncated = len(selected) > settings['max_records']
        selected = selected[:settings['max_records']]
        incomplete = withdrawn > 0 or unassessable > 0 or truncated or any(r['captured_at'] is None for r in selected)
        status = acquisition['declared_coverage']
        if status == 'complete' and incomplete:
            status = 'partial'
        coverage = {'collection_status': status, 'market_coverage': 'unknown', 'scanned_records': len(records), 'unassessable_records': unassessable,
                    'duplicate_records': duplicates, 'withdrawn_records': withdrawn, 'record_limit_reached': truncated, 'selected_records': len(selected), 'query': settings['query'],
                    'field_coverage': 'not_assessable' if not selected else 'partial' if any(r['captured_at'] is None or r['metric_measured_at'] is None or set(r['metrics']) != set(METRICS) for r in selected) else 'complete',
                    'publication_from': start.isoformat(), 'publication_before': end.isoformat(), 'baseline': None,
                    'limits': 'Only the supplied synthetic fixture; no complete market or trend claim.' if acquisition['synthetic'] else 'One bounded recent-search page; pagination is not followed. Market coverage is unknown.'}
        window_id = uuid.uuid4()
        connection.execute('INSERT INTO monitoring_windows(id,topic_id,revision_id,window_start,window_end,coverage,acquisition,collected_by,imported_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (window_id, topic['id'], revision['id'], start, end, Jsonb(coverage), Jsonb(acquisition), actor.actor_id, now))
        for record in selected:
            original = connection.execute('SELECT * FROM recent_x_observations WHERE workspace_id=%s AND capture_key=%s', (self.workspace_id, capture_identity(record, acquisition.get('response_id')))).fetchone()
            hashed = capture_fingerprint(record)
            retain_until = min(now, instant(record['captured_at'])) + timedelta(hours=settings['retention_hours']) if record['captured_at'] else now + timedelta(hours=settings['retention_hours'])
            if original:
                require(original['capture_digest'] == hashed and original['policy_context_id'] == settings['source_policy_id'], 'recent_x_capture_conflict')
                observation_id = original['id']
                connection.execute('UPDATE recent_x_observations SET retain_until=LEAST(retain_until,%s) WHERE id=%s', (retain_until, observation_id))
                SourceDependencies().shorten(connection, 'recent-x:' + self.workspace_id, str(observation_id), retain_until, now=now)
            else:
                count = connection.execute('SELECT count(*) AS n FROM recent_x_observations WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
                require(count < MAX_OBSERVATIONS, 'recent_x_observation_limit')
                observation_id = uuid.uuid4()
                body = {'text': record['text'], 'metrics': record['metrics']}
                connection.execute('INSERT INTO recent_x_observations(id,workspace_id,capture_id,native_id,source_reference,capture_key,capture_digest,acquisition,missing_fields,policy_context_id,captured_at,published_at,metric_measured_at,imported_at,retain_until,body) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (observation_id, self.workspace_id, record['capture_id'], record['native_id'], 'https://x.com/i/status/' + record['native_id'], capture_identity(record, acquisition.get('response_id')), hashed, Jsonb(acquisition), Jsonb([k for k in ('captured_at', 'published_at', 'metric_measured_at') if record[k] is None] + [k for k in METRICS if k not in record['metrics']]), settings['source_policy_id'], record['captured_at'], record['published_at'], record['metric_measured_at'], now, retain_until, Jsonb(body)))
            connection.execute('INSERT INTO monitoring_window_members(window_id,observation_id) VALUES (%s,%s) ON CONFLICT DO NOTHING', (window_id, observation_id))
        self._reconcile(connection)
        return {'status': 'collected', 'window_id': str(window_id)}

    def _observation(self, connection, row, purpose):
        policy = self._policy(connection, row['policy_context_id'])
        available = row['body'] is not None and self._allowed(policy, purpose) and self._allowed(policy, 'retain')
        return {'observation_id': str(row['id']), 'capture_id': row['capture_id'], 'native_id': row['native_id'], 'source_reference': row['source_reference'],
                **{k: row[k].isoformat() if row[k] else None for k in ('captured_at', 'published_at', 'metric_measured_at', 'imported_at', 'retain_until')},
                'policy_context_id': row['policy_context_id'], 'body': row['body'] if available else None,
                'state': 'available' if available else row['purged_reason'] or 'permission_denied',
                'missing_fields': row['missing_fields'], 'metric_definitions': dict(METRICS), 'acquisition': row['acquisition']}

    def read_observation(self, observation_id, actor, *, purpose='display'):
        """Reopen a single retained capture under current process/display/retention policy."""
        actor.require_workspace(self.workspace_id)
        require(purpose in {'display', 'process'}, 'invalid_evidence_purpose')
        with self.db.connect() as connection:
            self._lock(connection)
            self._reconcile(connection)
            row = connection.execute('SELECT * FROM recent_x_observations WHERE id=%s AND workspace_id=%s', (observation_id, self.workspace_id)).fetchone()
            require(row is not None, 'recent_x_observation_not_found')
            return self._observation(connection, row, purpose)

    def read_window(self, window_id, actor, *, purpose='display'):
        """Read original membership under current policy, never replacement evidence."""
        with self.db.connect() as connection:
            return self.read_window_in_transaction(connection, window_id, actor, purpose=purpose)

    def read_window_in_transaction(self, connection, window_id, actor, *, purpose='display'):
        """Hold current policy stable through a caller's local PostgreSQL commit.

        The caller supplies a connection from this database and owns commit/rollback.
        The workspace lock and reconciliation remain owned here. Perform no external
        I/O while holding this transaction; use this for atomic dependent local saves.
        """
        actor.require_workspace(self.workspace_id)
        require(purpose in {'display', 'process'}, 'invalid_evidence_purpose')
        self._lock(connection)
        self._reconcile(connection)
        row = connection.execute('SELECT w.*,t.topic_key,r.document AS configuration FROM monitoring_windows w JOIN monitoring_topics t ON t.id=w.topic_id JOIN monitoring_topic_revisions r ON r.id=w.revision_id WHERE w.id=%s AND t.workspace_id=%s', (window_id, self.workspace_id)).fetchone()
        require(row is not None, 'monitoring_window_not_found')
        rows = connection.execute('SELECT o.* FROM recent_x_observations o JOIN monitoring_window_members m ON m.observation_id=o.id WHERE m.window_id=%s ORDER BY o.native_id,o.capture_id LIMIT 100', (window_id,)).fetchall()
        observations = [self._observation(connection, r, purpose) for r in rows]
        policy = self._policy(connection, row['configuration']['source_policy_id'])
        permissions = {use: self._allowed(policy, use) for use in ('process', 'display', 'retain')}
        return {'current_permissions': permissions, 'support_permitted': permissions[purpose] and permissions['retain'], 'window_id': str(row['id']), 'topic_key': row['topic_key'], 'topic_revision_id': str(row['revision_id']), 'configuration': row['configuration'],
                'window_start': row['window_start'].isoformat(), 'window_end': row['window_end'].isoformat(),
                'coverage': row['coverage'], 'acquisition': row['acquisition'], 'collected_by': row['collected_by'], 'imported_at': row['imported_at'].isoformat(), 'observations': observations}

    def timeline(self, key, actor, *, limit=50, offset=0, purpose='display'):
        """Return bounded distinct source captures; repeated membership is not new freshness."""
        actor.require_workspace(self.workspace_id)
        require(type(limit) is int and 1 <= limit <= 100 and type(offset) is int and 0 <= offset <= MAX_OBSERVATIONS, 'invalid_recent_x_page')
        require(purpose in {'display', 'process'}, 'invalid_evidence_purpose')
        with self.db.connect() as connection:
            self._lock(connection)
            self._reconcile(connection)
            topic = self._topic(connection, key)
            rows = connection.execute('SELECT o.* FROM recent_x_observations o WHERE o.workspace_id=%s AND EXISTS (SELECT 1 FROM monitoring_window_members m JOIN monitoring_windows w ON w.id=m.window_id WHERE m.observation_id=o.id AND w.topic_id=%s) ORDER BY o.captured_at DESC NULLS LAST,o.id LIMIT %s OFFSET %s', (self.workspace_id, topic['id'], limit + 1, offset)).fetchall()
            observations = [self._observation(connection, r, purpose) for r in rows[:limit]]
        return {'topic_key': key, 'observations': observations, 'has_more': len(rows) > limit, 'limit': limit, 'offset': offset}
