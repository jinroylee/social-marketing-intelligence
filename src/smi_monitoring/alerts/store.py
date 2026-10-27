"""Source-free alert lineage; current windows supply every displayed source value."""

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from psycopg.types.json import Jsonb

from smi_monitoring.contracts import require
from smi_monitoring.recent import RecentMonitoring
from smi_monitoring.recent.route import fingerprint, instant


@dataclass(frozen=True)
class VolumeThreshold:
    """Operator-selected sample signal thresholds, not a statistical significance test."""

    minimum_baseline_posts: int
    minimum_increase_posts: int
    minimum_ratio: int

    def __post_init__(self):
        for value in asdict(self).values():
            require(type(value) is int and 1 <= value <= 100, 'invalid_volume_threshold')
        require(self.minimum_ratio >= 2, 'invalid_volume_threshold')


def _evaluate(baseline, detection, configuration):
    limitations = []
    if baseline is None:
        limitations.append('baseline_missing')
    else:
        if {o['native_id'] for o in baseline['observations']} & {o['native_id'] for o in detection['observations']}:
            limitations.append('native_publication_incomparable')
        if baseline['topic_key'] != detection['topic_key']:
            limitations.append('topic_incomparable')
        bs, be = instant(baseline['window_start']), instant(baseline['window_end'])
        ds, de = instant(detection['window_start']), instant(detection['window_end'])
        if be - bs != de - ds or be > ds:
            limitations.append('windows_incomparable')
        for field in ('query', 'cadence_minutes', 'max_records', 'source_policy_id'):
            if baseline['configuration'][field] != detection['configuration'][field]:
                limitations.append(field + '_incomparable')
        for field in ('route', 'version', 'synthetic', 'sampling', 'max_records'):
            if field not in baseline['acquisition'] or field not in detection['acquisition']:
                limitations.append(field + '_unrecorded')
            elif baseline['acquisition'][field] != detection['acquisition'][field]:
                limitations.append(field + '_incomparable')
    for window in (baseline, detection):
        if window is None:
            continue
        if window['coverage']['collection_status'] != 'complete':
            limitations.append('collection_incomplete')
        if not window['support_permitted'] or any(o['body'] is None for o in window['observations']):
            limitations.append('source_support_unavailable')
    if limitations:
        return 'not_assessable', sorted(set(limitations)), None
    before = len({o['native_id'] for o in baseline['observations']})
    after = len({o['native_id'] for o in detection['observations']})
    if before < configuration['minimum_baseline_posts']:
        return 'not_assessable', ['baseline_below_minimum'], None
    comparison = {'baseline_posts': before, 'detection_posts': after,
                  'increase_posts': after - before, 'ratio': after / before}
    significant = (after - before >= configuration['minimum_increase_posts']
                   and after >= before * configuration['minimum_ratio'])
    return 'significant_change' if significant else 'no_change', [], comparison


class QuantitativeAlerts:
    """Assess bounded frozen windows and atomically retain one alert/notification.

    All source reads go through RecentMonitoring; its policy lock remains held
    through local assessment/alert commit. No acquisition, model or campaign path
    is available here. Detection requires a threshold; saved reads need none.
    """

    def __init__(self, recent: RecentMonitoring, *, threshold: VolumeThreshold | None = None, clock=None):
        self.recent, self.db, self.workspace_id = recent, recent.db, recent.workspace_id
        self.threshold = threshold
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def migrate(self):
        """Add retained assessment/request/alert identities after the recent schema."""
        self.recent.migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def _windows(self, connection, row, actor, purpose):
        return {name: self.recent.read_window_in_transaction(connection, row[name + '_window_id'], actor, purpose=purpose)
                if row[name + '_window_id'] else None for name in ('baseline', 'detection')}

    def detect(self, detection_window_id, baseline_window_id, actor, *, request_id):
        """Save a configured comparison; identical requests and pairs reopen history.

        Missing baseline is a durable limitation. Changed inputs/configuration or
        actor under the same request conflict. New requests for a saved pair retain
        its first decision, including any original limitation.
        """
        self.recent.require_operator(actor)
        require(self.threshold is not None, 'volume_threshold_unconfigured')
        require(isinstance(request_id, str) and 1 <= len(request_id) <= 200, 'invalid_detection_request')
        try:
            detection_window_id = str(uuid.UUID(detection_window_id))
            baseline_window_id = str(uuid.UUID(baseline_window_id)) if baseline_window_id is not None else None
        except (ValueError, TypeError, AttributeError):
            require(False, 'invalid_monitoring_window_id')
        method = {'name': 'distinct_native_post_volume', 'version': 'distinct-post-volume-v1',
                  'metric': 'Distinct native X posts published within the scoped window; repeated captures count once.',
                  'configuration': asdict(self.threshold), 'significance': 'configured_threshold_signal',
                  'uncertainty': 'Synthetic fixture sample only; not independent statistical proof or complete market coverage.'}
        pair = fingerprint({'detection': detection_window_id, 'baseline': baseline_window_id, 'method': method})
        request_digest = fingerprint({'pair': pair, 'actor': actor.actor_id, 'kind': actor.kind})
        with self.db.connect() as connection:
            # The public window read acquires the recent owner's workspace policy lock.
            windows = self._windows(connection, {'detection_window_id': detection_window_id,
                'baseline_window_id': baseline_window_id}, actor, 'process')
            previous = connection.execute('SELECT * FROM monitoring_detection_requests WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if previous:
                require(previous['request_digest'] == request_digest, 'detection_request_conflict')
                return self._read(connection, previous['assessment_id'], actor)
            row = connection.execute('SELECT id FROM monitoring_volume_assessments WHERE workspace_id=%s AND pair_digest=%s', (self.workspace_id, pair)).fetchone()
            if row:
                assessment_id = row['id']
            else:
                count = connection.execute('SELECT count(*) AS n FROM monitoring_volume_assessments WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
                require(count < 5000, 'monitoring_assessment_limit')
                assessment_id = uuid.uuid4()
                outcome, limitations, _ = _evaluate(windows['baseline'], windows['detection'], method['configuration'])
                now = instant(self.clock().isoformat())
                connection.execute('INSERT INTO monitoring_volume_assessments(id,workspace_id,detection_window_id,baseline_window_id,pair_digest,method,outcome,limitations,recorded_by,actor_kind,recorded_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (assessment_id, self.workspace_id, detection_window_id, baseline_window_id, pair, Jsonb(method), outcome, Jsonb(limitations), actor.actor_id, actor.kind, now))
                if outcome == 'significant_change':
                    connection.execute('INSERT INTO monitoring_alerts(id,assessment_id,notification_id,created_at) VALUES (%s,%s,%s,%s)', (uuid.uuid4(), assessment_id, uuid.uuid4(), now))
            count = connection.execute('SELECT count(*) AS n FROM monitoring_detection_requests WHERE workspace_id=%s', (self.workspace_id,)).fetchone()['n']
            require(count < 20000, 'monitoring_detection_request_limit')
            connection.execute('INSERT INTO monitoring_detection_requests(workspace_id,request_id,request_digest,assessment_id) VALUES (%s,%s,%s,%s)', (self.workspace_id, request_id, request_digest, assessment_id))
            return self._read(connection, assessment_id, actor)

    def _read(self, connection, assessment_id, actor):
        row = connection.execute('SELECT a.*,l.id AS alert_id,l.notification_id FROM monitoring_volume_assessments a LEFT JOIN monitoring_alerts l ON l.assessment_id=a.id WHERE a.id=%s AND a.workspace_id=%s', (assessment_id, self.workspace_id)).fetchone()
        require(row is not None, 'monitoring_assessment_not_found')
        windows = self._windows(connection, row, actor, 'display')
        processing = self._windows(connection, row, actor, 'process')
        _, limitations, comparison = _evaluate(windows['baseline'], windows['detection'], row['method']['configuration'])
        _, process_limits, _ = _evaluate(processing['baseline'], processing['detection'], row['method']['configuration'])
        unavailable = 'source_support_unavailable' in limitations or 'source_support_unavailable' in process_limits
        if unavailable or row['outcome'] == 'not_assessable':
            comparison = None
        return {'assessment_id': str(row['id']), 'alert_id': str(row['alert_id']) if row['alert_id'] else None,
                'notification_id': str(row['notification_id']) if row['notification_id'] else None,
                'outcome': row['outcome'], 'current_support': 'unavailable' if unavailable else 'available',
                'limitations': sorted(set(row['limitations'] + limitations + process_limits)), 'comparison': comparison,
                'method': row['method'], 'windows': windows, 'recorded_by': row['recorded_by'],
                'actor_kind': row['actor_kind'], 'recorded_at': row['recorded_at'].isoformat()}

    def read_assessment(self, assessment_id, actor):
        """Reopen exact original assessment and current permitted window evidence."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            return self._read(connection, assessment_id, actor)

    def read_alert(self, alert_id, actor):
        """Reopen retained alert support; never substitute newer source captures."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT a.id FROM monitoring_volume_assessments a JOIN monitoring_alerts l ON l.assessment_id=a.id WHERE l.id=%s AND a.workspace_id=%s', (alert_id, self.workspace_id)).fetchone()
            require(row is not None, 'monitoring_alert_not_found')
            return self._read(connection, row['id'], actor)

    def history(self, actor):
        """List latest 100 assessments including explicit non-alert limitations."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute('SELECT id FROM monitoring_volume_assessments WHERE workspace_id=%s ORDER BY recorded_at DESC,id DESC LIMIT 100', (self.workspace_id,)).fetchall()
            return [self._read(connection, r['id'], actor) for r in rows]

    def notifications(self, actor):
        """Read latest 100 local notifications; an uninstalled optional owner is empty."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            if connection.execute("SELECT to_regclass('monitoring_alerts') AS relation").fetchone()['relation'] is None:
                return []
            rows = connection.execute('SELECT a.id FROM monitoring_volume_assessments a JOIN monitoring_alerts l ON l.assessment_id=a.id WHERE a.workspace_id=%s ORDER BY l.created_at DESC,l.id DESC LIMIT 100', (self.workspace_id,)).fetchall()
            result = []
            for row in rows:
                assessment = self._read(connection, row['id'], actor)
                comparison = assessment['comparison']
                message = (f'Synthetic sample volume threshold crossed: {comparison["baseline_posts"]} → {comparison["detection_posts"]} distinct X posts. Market coverage is unknown.'
                           if comparison else 'Retained X volume alert. Current support unavailable; no current quantitative claim.')
                result.append({'notification_id': assessment['notification_id'], 'alert_id': assessment['alert_id'],
                    'created_at': assessment['recorded_at'], 'href': '/monitoring/alerts/' + assessment['alert_id'],
                    'message': message, 'current_support': assessment['current_support']})
            return result
