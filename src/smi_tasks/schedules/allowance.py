"""Atomic scheduled new-post admission; canonical effects share the caller transaction."""

from contextlib import nullcontext
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from smi_ingestion.contracts import ExternalKey, NormalizedBatch
from smi_ingestion.db import Database
from smi_ingestion.evidence_sets import ActorContext

from smi_ingestion.evidence import EvidenceError


class ScheduledPostAllowance:
    """Coordinate workspace/day consumption without owning canonical source tables.

    CanonicalWriter supplies validated normalized keys and the identities it has
    locked as already known. A refusal returns False before any canonical writes.
    Only successfully committed new-post effects consume allowance.
    """

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db, self.workspace_id = db, workspace_id

    @staticmethod
    def configure_day(connection, workspace_id: str, day: date, document: dict[str, Any], version: int) -> None:
        """Pin a day's bounds and update its cap without resetting admissions."""
        zone = ZoneInfo(document['timezone'])
        connection.execute(
            'INSERT INTO scheduled_post_days(workspace_id,accounting_day,accounting_timezone,day_start,day_end,allowance_version,allowance_limit) '
            'VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(workspace_id,accounting_day) DO UPDATE '
            'SET allowance_version=EXCLUDED.allowance_version,allowance_limit=EXCLUDED.allowance_limit '
            'WHERE scheduled_post_days.allowance_version <= EXCLUDED.allowance_version',
            (workspace_id, day, document['timezone'], datetime.combine(day, time(), zone).astimezone(timezone.utc),
             datetime.combine(day + timedelta(days=1), time(), zone).astimezone(timezone.utc), version, document['daily_allowance']))

    def admit(self, occurrence_id: str, observation_id: str, batch: NormalizedBatch, known: frozenset[ExternalKey], synthetic: bool, *, connection) -> bool:
        """Admit one mapped post on the fenced canonical transaction, or record exclusion.

        Current process permission and normalization are checked by ingestion
        before this operation. Retries reopen the committed observation disposition.
        """
        occurrence = connection.execute('SELECT * FROM keyword_schedule_occurrences WHERE id=%s AND workspace_id=%s',
                                        (occurrence_id, self.workspace_id)).fetchone()
        if occurrence is None or occurrence['status'] != 'submitted':
            raise EvidenceError('schedule_occurrence_not_found')
        day = connection.execute('SELECT * FROM scheduled_post_days WHERE workspace_id=%s AND accounting_day=%s FOR UPDATE',
                                 (self.workspace_id, occurrence['accounting_day'])).fetchone()
        if day is None:
            # Upgrade an already queued occurrence without rewriting old authority.
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('keyword-schedule:' + self.workspace_id,))
            context = occurrence['context']
            configuration = connection.execute('SELECT * FROM keyword_schedule_configurations WHERE workspace_id=%s AND recorded_at < %s ORDER BY version DESC LIMIT 1',
                                               (self.workspace_id, context['day_end'])).fetchone()
            self.configure_day(connection, self.workspace_id, occurrence['accounting_day'], configuration['document'], configuration['version'])
            day = connection.execute('SELECT * FROM scheduled_post_days WHERE workspace_id=%s AND accounting_day=%s FOR UPDATE',
                                     (self.workspace_id, occurrence['accounting_day'])).fetchone()
        previous = connection.execute('SELECT disposition FROM scheduled_post_admissions WHERE observation_id=%s', (observation_id,)).fetchone()
        if previous:
            return previous['disposition'] not in {'limit_excluded_posts', 'ineligible_posts'}
        keys = {*batch.entities, *(f.subject for f in batch.fields), *(m.subject for m in batch.metrics)}
        posts = {k for k in keys if k.kind == 'content'}
        post = next(iter(posts)) if len(posts) == 1 else None
        identity = (post.platform, post.namespace, post.native_id) if post else (None, None, None)
        prior = connection.execute('SELECT disposition FROM scheduled_post_admissions WHERE workspace_id=%s AND accounting_day=%s '
                                   'AND platform=%s AND namespace=%s AND native_id=%s AND synthetic=%s '
                                   "AND disposition IN ('new_posts','known_refreshes','deduplicated_posts') LIMIT 1",
                                   (self.workspace_id, occurrence['accounting_day'], *identity, synthetic)).fetchone() if post else None
        used = connection.execute("SELECT count(*) AS n FROM scheduled_post_admissions WHERE workspace_id=%s AND accounting_day=%s AND disposition='new_posts'",
                                  (self.workspace_id, occurrence['accounting_day'])).fetchone()['n']
        if post is None:
            disposition = 'ineligible_posts'
        elif prior:
            disposition = 'deduplicated_posts'
        elif post in known:
            disposition = 'known_refreshes'
        elif used >= day['allowance_limit']:
            disposition = 'limit_excluded_posts'
        else:
            disposition = 'new_posts'
        connection.execute('INSERT INTO scheduled_post_admissions(observation_id,occurrence_id,workspace_id,accounting_day,platform,namespace,native_id,synthetic,disposition) '
                           'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (observation_id, occurrence_id, self.workspace_id, occurrence['accounting_day'], *identity, synthetic, disposition))
        return disposition not in {'limit_excluded_posts', 'ineligible_posts'}

    def read(self, day: date | str, actor: ActorContext, *, occurrence_id: str | None = None, connection=None) -> dict[str, Any] | None:
        """Read shared consumption, projecting an unconsumed day without admitting work.

        With no day row, its admission foreign key guarantees zero usage. Read
        the applicable configuration and fixed bounds without creating a row.
        """
        actor.require_workspace(self.workspace_id)
        own_connection = connection is None
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            if own_connection:
                connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            row = connection.execute('SELECT * FROM scheduled_post_days WHERE workspace_id=%s AND accounting_day=%s', (self.workspace_id, day)).fetchone()
            if row is None:
                schedule = connection.execute('SELECT accounting_timezone FROM keyword_schedules WHERE workspace_id=%s', (self.workspace_id,)).fetchone()
                if schedule is None:
                    return None
                accounting_day = date.fromisoformat(day) if isinstance(day, str) else day
                zone = ZoneInfo(schedule['accounting_timezone'])
                start = datetime.combine(accounting_day, time(), zone).astimezone(timezone.utc)
                end = datetime.combine(accounting_day + timedelta(days=1), time(), zone).astimezone(timezone.utc)
                configuration = connection.execute('SELECT version,document FROM keyword_schedule_configurations WHERE workspace_id=%s AND recorded_at < %s ORDER BY version DESC LIMIT 1',
                                                   (self.workspace_id, end)).fetchone()
                if configuration is None:
                    return None
                row = {'accounting_day': accounting_day, 'accounting_timezone': schedule['accounting_timezone'],
                       'day_start': start, 'day_end': end, 'allowance_limit': configuration['document']['daily_allowance'],
                       'allowance_version': configuration['version']}
            rows = connection.execute('SELECT disposition,count(*) AS n FROM scheduled_post_admissions WHERE workspace_id=%s AND accounting_day=%s GROUP BY disposition',
                                      (self.workspace_id, day)).fetchall()
            counts = {r['disposition']: r['n'] for r in rows}
            result = {'accounting_day': row['accounting_day'].isoformat(), 'accounting_timezone': row['accounting_timezone'],
                      'day_start': row['day_start'].isoformat(), 'day_end': row['day_end'].isoformat(),
                      'limit': row['allowance_limit'], 'allowance_version': row['allowance_version'], 'used': counts.get('new_posts', 0),
                      'remaining': max(0, row['allowance_limit'] - counts.get('new_posts', 0)), 'enforcement': 'atomic_unique_new_posts',
                      'counts': {name: counts.get(name, 0) for name in self.dispositions}}
            if occurrence_id:
                rows = connection.execute('SELECT disposition,count(*) AS n FROM scheduled_post_admissions WHERE occurrence_id=%s AND workspace_id=%s GROUP BY disposition',
                                          (occurrence_id, self.workspace_id)).fetchall()
                own = {r['disposition']: r['n'] for r in rows}
                result['occurrence_counts'] = {name: own.get(name, 0) for name in self.dispositions}
            return result

    dispositions = ('new_posts', 'known_refreshes', 'deduplicated_posts', 'limit_excluded_posts', 'ineligible_posts')
