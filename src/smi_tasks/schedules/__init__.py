"""Versioned registered keyword authority and bounded daily task composition."""

from collections.abc import Callable
from datetime import datetime, time, timedelta, timezone
import uuid
import hashlib
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from psycopg.types.json import Jsonb

from .allowance import ScheduledPostAllowance

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

if TYPE_CHECKING:
    from smi_tasks import AcquisitionTasks


def migrate(db: Database) -> None:
    """Install schedule-owned configuration and occurrence history after task tables."""
    with db.connect() as connection:
        connection.execute(Path(__file__).with_name('schema.sql').read_text())


def require_occurrence(workspace_id: str, occurrence_id: str, actor: ActorContext, *, connection) -> dict[str, Any]:
    """Reopen schedule-owned authority on the admission transaction; caller text grants none."""
    actor.require_workspace(workspace_id)
    row = connection.execute('SELECT * FROM keyword_schedule_occurrences WHERE id=%s AND workspace_id=%s FOR UPDATE',
                             (occurrence_id, workspace_id)).fetchone()
    if row is None:
        raise EvidenceError('schedule_occurrence_not_found')
    if row['initiator_id'] != actor.actor_id or row['initiator_kind'] != actor.kind:
        raise EvidenceError('schedule_occurrence_actor_conflict')
    if row['status'] == 'refused':
        raise EvidenceError('schedule_occurrence_refused')
    return row['context']


class ScheduledDiscovery:
    """Configure and tick one local daily keyword schedule; collection stays in the worker.

    The task owner is injected so schedule SQL remains here and task admission is
    composed through its public interface. The clock is trusted operator wiring.
    """

    def __init__(self, tasks: 'AcquisitionTasks', *, clock: Callable[[], datetime] | None = None):
        self.tasks = tasks
        self.db, self.workspace_id = tasks.db, tasks.workspace_id
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def migrate(self) -> None:
        """Install only schedule-owned tables; task migrations must already be installed."""
        migrate(self.db)

    def _now(self) -> datetime:
        now = self.clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise EvidenceError('invalid_schedule_clock')
        return now.astimezone(timezone.utc)

    @staticmethod
    def _validate(document: dict[str, Any]) -> dict[str, Any]:
        if (not isinstance(document, dict) or set(document) != {'timezone', 'daily_at', 'lookback_days', 'daily_allowance', 'keywords'}
                or not isinstance(document['timezone'], str)
                or not isinstance(document['daily_at'], str) or re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', document['daily_at']) is None
                or type(document['lookback_days']) is not int or not 1 <= document['lookback_days'] <= 30
                or type(document['daily_allowance']) is not int or not 1 <= document['daily_allowance'] <= 100_000
                or not isinstance(document['keywords'], list) or len(document['keywords']) > 10):
            raise EvidenceError('invalid_keyword_schedule')
        try:
            ZoneInfo(document['timezone'])
        except (ZoneInfoNotFoundError, ValueError):
            raise EvidenceError('invalid_keyword_schedule_timezone') from None
        keys, queries = set(), set()
        for keyword in document['keywords']:
            if (not isinstance(keyword, dict) or set(keyword) != {'key', 'query', 'subject_ids'}
                    or not isinstance(keyword['key'], str) or re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', keyword['key']) is None
                    or keyword['key'] in keys
                    or not isinstance(keyword['query'], str) or not keyword['query'].strip() or len(keyword['query']) > 500
                    or keyword['query'].strip().casefold() in queries
                    or not isinstance(keyword['subject_ids'], list) or not 1 <= len(keyword['subject_ids']) <= 30
                    or any(not isinstance(s, str) or not s.strip() or len(s) > 500 for s in keyword['subject_ids'])
                    or len(set(keyword['subject_ids'])) != len(keyword['subject_ids'])):
                raise EvidenceError('invalid_keyword_schedule')
            keys.add(keyword['key'])
            queries.add(keyword['query'].strip().casefold())
        return json.loads(json.dumps(document))

    def configure(self, document: dict[str, Any], actor: ActorContext, *, expected_version: int) -> dict[str, Any]:
        """Save a successor configuration under operator authority, retaining every old version.

        The accounting timezone is fixed by the first configuration. Stable keyword
        keys and day identities survive query edits, removal and later re-registration.
        """
        actor.require_workspace(self.workspace_id)
        self.tasks.authority.require_schedule_operator(actor)
        document = self._validate(document)
        if type(expected_version) is not int or expected_version < 0:
            raise EvidenceError('schedule_configuration_conflict')
        digest = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('keyword-schedule:' + self.workspace_id,))
            connection.execute('INSERT INTO keyword_schedules(workspace_id,accounting_timezone) VALUES (%s,%s) ON CONFLICT DO NOTHING',
                               (self.workspace_id, document['timezone']))
            schedule = connection.execute('SELECT * FROM keyword_schedules WHERE workspace_id=%s FOR UPDATE', (self.workspace_id,)).fetchone()
            if schedule['current_version'] != expected_version:
                raise EvidenceError('schedule_configuration_conflict')
            if schedule['accounting_timezone'] != document['timezone']:
                raise EvidenceError('schedule_accounting_timezone_fixed')
            now = self._now()
            if schedule['last_tick_at'] and now < schedule['last_tick_at']:
                raise EvidenceError('schedule_clock_regressed')
            version = expected_version + 1
            connection.execute('INSERT INTO keyword_schedule_configurations(workspace_id,version,document,digest,operator_id,recorded_at) VALUES (%s,%s,%s,%s,%s,%s)',
                               (self.workspace_id, version, Jsonb(document), digest, actor.actor_id, now))
            connection.execute('UPDATE keyword_schedules SET current_version=%s WHERE workspace_id=%s', (version, self.workspace_id))
            ScheduledPostAllowance.configure_day(connection, self.workspace_id, now.astimezone(ZoneInfo(document['timezone'])).date(), document, version)
        return self.read(actor)

    def read(self, actor: ActorContext) -> dict[str, Any]:
        """Read current settings, immutable versions and the latest 100 occurrence dispositions."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            schedule = connection.execute('SELECT * FROM keyword_schedules WHERE workspace_id=%s', (self.workspace_id,)).fetchone()
            configurations = connection.execute('SELECT * FROM keyword_schedule_configurations WHERE workspace_id=%s ORDER BY version', (self.workspace_id,)).fetchall()
            occurrences = connection.execute('SELECT * FROM keyword_schedule_occurrences WHERE workspace_id=%s ORDER BY accounting_day DESC,keyword_key LIMIT 100', (self.workspace_id,)).fetchall()
            daily_allowance = ScheduledPostAllowance(self.db, self.workspace_id).read(
                self._now().astimezone(ZoneInfo(schedule['accounting_timezone'])).date(), actor, connection=connection) if schedule else None
        versions = [{'version': c['version'], 'document': c['document'], 'digest': c['digest'],
                     'operator_id': c['operator_id'], 'recorded_at': c['recorded_at'].isoformat()} for c in configurations]
        return {'workspace_id': self.workspace_id, 'version': schedule['current_version'] if schedule else 0,
                'document': versions[-1]['document'] if versions else None,
                'accounting_timezone': schedule['accounting_timezone'] if schedule else None,
                'last_tick_at': schedule['last_tick_at'].isoformat() if schedule and schedule['last_tick_at'] else None,
                'cadence': 'daily-local-v1', 'live_activation': False, 'allowance_enforcement': 'atomic_unique_new_posts', 'daily_allowance': daily_allowance,
                'catch_up': 'current_day_only', 'configurations': versions,
                'occurrences': [self._occurrence(row, actor) for row in occurrences]}

    def read_occurrence(self, occurrence_id: str, actor: ActorContext) -> dict[str, Any]:
        """Reopen an exact historical occurrence beyond the bounded recent list."""
        actor.require_workspace(self.workspace_id)
        occurrence_id = str(uuid.UUID(occurrence_id))
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM keyword_schedule_occurrences WHERE id=%s AND workspace_id=%s',
                                     (occurrence_id, self.workspace_id)).fetchone()
        if row is None:
            raise EvidenceError('schedule_occurrence_not_found')
        return self._occurrence(row, actor)

    def _occurrence(self, row, actor):
        task_id = str(row['task_id']) if row['task_id'] else None
        return {'occurrence_id': str(row['id']), 'configuration_version': row['configuration_version'],
                'keyword_key': row['keyword_key'], 'accounting_day': row['accounting_day'].isoformat(),
                'context': row['context'], 'status': row['status'], 'reason': row['reason'],
                'initiator': {'actor_id': row['initiator_id'], 'kind': row['initiator_kind']},
                'recorded_at': row['recorded_at'].isoformat(), 'task_id': task_id,
                'task': self.tasks.read(task_id, actor) if task_id else None}

    def tick(self, actor: ActorContext) -> dict[str, Any]:
        """Acknowledge at most ten current-day occurrences atomically, without collection.

        Earlier unticked days are never replayed. Refused occurrences keep their
        disposition for that day; edits and restarts cannot retry them as new work.
        """
        actor.require_workspace(self.workspace_id)
        self.tasks.authority.require_schedule_tick(actor)
        created = []
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('keyword-schedule:' + self.workspace_id,))
            schedule = connection.execute('SELECT * FROM keyword_schedules WHERE workspace_id=%s FOR UPDATE', (self.workspace_id,)).fetchone()
            if schedule is None:
                raise EvidenceError('keyword_schedule_unconfigured')
            configuration = connection.execute('SELECT * FROM keyword_schedule_configurations WHERE workspace_id=%s AND version=%s',
                                               (self.workspace_id, schedule['current_version'])).fetchone()
            now = self._now()
            if now < configuration['recorded_at'] or (schedule['last_tick_at'] and now < schedule['last_tick_at']):
                raise EvidenceError('schedule_clock_regressed')
            document = configuration['document']
            zone = ZoneInfo(schedule['accounting_timezone'])
            day = now.astimezone(zone).date()
            ScheduledPostAllowance.configure_day(connection, self.workspace_id, day, document, configuration['version'])
            # fold=0 chooses the earlier overlap; UTC roundtrip shifts a gap forward.
            due_local = datetime.combine(day, time.fromisoformat(document['daily_at']), zone)
            due = due_local.astimezone(timezone.utc)
            missed = max(0, (day - schedule['last_tick_at'].astimezone(zone).date()).days - 1) if schedule['last_tick_at'] else 0
            connection.execute('UPDATE keyword_schedules SET last_tick_at=%s WHERE workspace_id=%s', (now, self.workspace_id))
            if now >= due:
                for keyword in document['keywords']:
                    prior = connection.execute('SELECT id FROM keyword_schedule_occurrences WHERE workspace_id=%s AND accounting_day=%s AND keyword_key=%s',
                                               (self.workspace_id, day, keyword['key'])).fetchone()
                    if prior:
                        continue
                    occurrence_id = str(uuid.uuid4())
                    context = {'occurrence_id': occurrence_id, 'configuration_version': configuration['version'],
                               'configuration_digest': configuration['digest'], 'keyword_key': keyword['key'], 'keyword': keyword,
                               'cadence': 'daily-local-v1', 'daily_at': document['daily_at'], 'accounting_day': day.isoformat(),
                               'accounting_timezone': schedule['accounting_timezone'], 'day_boundary': 'local-midnight-v1',
                               'day_start': datetime.combine(day, time(), zone).astimezone(timezone.utc).isoformat(),
                               'day_end': datetime.combine(day + timedelta(days=1), time(), zone).astimezone(timezone.utc).isoformat(),
                               'due_at': due.isoformat(), 'published_from': (due_local - timedelta(days=document['lookback_days'])).astimezone(timezone.utc).isoformat(),
                               'published_before': due.isoformat(), 'daily_allowance': document['daily_allowance'],
                               'allowance_version': configuration['version'], 'allowance_enforcement': 'atomic_unique_new_posts'}
                    connection.execute('INSERT INTO keyword_schedule_occurrences(id,workspace_id,configuration_version,keyword_key,accounting_day,context,initiator_id,initiator_kind,status,recorded_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                       (occurrence_id, self.workspace_id, configuration['version'], keyword['key'], day, Jsonb(context), actor.actor_id, actor.kind, 'pending', now))
                    status, reason, task_id = 'submitted', None, None
                    try:
                        admission = self.tasks.submit_scheduled(occurrence_id, actor, connection=connection)
                        task_id = admission['task_id']
                    except EvidenceError as error:
                        status, reason = 'refused', error.code
                    connection.execute('UPDATE keyword_schedule_occurrences SET status=%s,reason=%s,task_id=%s WHERE id=%s',
                                       (status, reason, task_id, occurrence_id))
                    created.append(occurrence_id)
        view = self.read(actor)
        return {'created_occurrences': [self.read_occurrence(occurrence_id, actor) for occurrence_id in created],
                'missed_days_not_replayed': missed, 'schedule': view}
