"""Source-owned lifecycle inheritance for already acquired dependent observations.

Parents push policy mutations through this port in their local transaction;
ingestion never queries parent schemas or calls back into a higher-level owner.
"""

from dataclasses import replace
from datetime import datetime, timezone

from psycopg.types.json import Jsonb

from .evidence import EvidenceError, _policy_json, policy_from_json


class SourceDependencies:
    """Mirror parent authority and permanently purge copied source values on loss."""

    @staticmethod
    def _installed(connection):
        return connection.execute("SELECT to_regclass('source_observation_dependencies') AS name").fetchone()['name'] is not None

    def bind(self, connection, observation_id, *, owner_id, origin_id, native_id, policy_context_id, retain_until):
        """Bind one transiently imported observation to an immutable parent origin.

        The caller must hold its parent's policy lock. No raw payload copy may be
        retained: this port owns only canonical copies and source-free lineage.
        """
        row = connection.execute('SELECT payload_path FROM source_observations WHERE id=%s FOR UPDATE', (observation_id,)).fetchone()
        if row is None or row['payload_path'] is not None:
            raise EvidenceError('invalid_dependent_observation')
        connection.execute('INSERT INTO source_observation_dependencies(observation_id,owner_id,origin_id,native_id,policy_context_id,retain_until) VALUES (%s,%s,%s,%s,%s,%s)',
                           (observation_id, owner_id, origin_id, native_id, policy_context_id, retain_until))

    def update_policy(self, connection, owner_id, policy, *, now):
        """Atomically mirror current parent permission; lost retention cannot recover."""
        if not self._installed(connection):
            return
        self.reconcile(connection, owner_id=owner_id, now=now)
        rows = connection.execute('SELECT o.id,d.retain_until,d.purged FROM source_observations o JOIN source_observation_dependencies d ON d.observation_id=o.id WHERE d.owner_id=%s AND d.policy_context_id=%s ORDER BY o.id FOR UPDATE OF o',
                                  (owner_id, policy.context_id)).fetchall()
        for row in rows:
            expiry = min(row['retain_until'], policy.expires_at) if policy.expires_at else row['retain_until']
            lost = row['purged'] or policy.revoked or not policy.can_retain or expiry <= now
            inherited = replace(policy, expires_at=expiry, revoked=policy.revoked or bool(lost))
            connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(_policy_json(inherited)), row['id']))
            if lost:
                self._purge(connection, row['id'])

    def withdraw(self, connection, owner_id, native_id):
        """Permanently deny every copied capture of the parent's native source post."""
        if not self._installed(connection):
            return
        rows = connection.execute('SELECT o.id FROM source_observations o JOIN source_observation_dependencies d ON d.observation_id=o.id WHERE d.owner_id=%s AND d.native_id=%s ORDER BY o.id FOR UPDATE OF o', (owner_id, native_id)).fetchall()
        for row in rows:
            self._purge(connection, row['id'])

    def shorten(self, connection, owner_id, origin_id, retain_until, *, now):
        """Shorten an existing parent capture deadline without creating a refresh."""
        if not self._installed(connection):
            return
        rows = connection.execute('SELECT o.id,o.policy,d.retain_until FROM source_observations o JOIN source_observation_dependencies d ON d.observation_id=o.id WHERE d.owner_id=%s AND d.origin_id=%s ORDER BY o.id FOR UPDATE OF o', (owner_id, origin_id)).fetchall()
        for row in rows:
            deadline = min(row['retain_until'], retain_until)
            policy = policy_from_json(row['policy'])
            expiry = min(deadline, policy.expires_at) if policy.expires_at else deadline
            connection.execute('UPDATE source_observation_dependencies SET retain_until=%s WHERE observation_id=%s', (deadline, row['id']))
            connection.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(_policy_json(replace(policy, expires_at=expiry))), row['id']))
            if expiry <= now:
                self._purge(connection, row['id'])

    def reconcile(self, connection, *, workspace_id=None, owner_id=None, now=None):
        """Purge expired inherited bodies on independent source/knowledge reads."""
        if not self._installed(connection):
            return
        if (workspace_id is None) == (owner_id is None):
            raise EvidenceError('dependency_scope_required')
        now = max(now, datetime.now(timezone.utc)) if now else datetime.now(timezone.utc)
        scope = 'r.workspace_id=%s' if workspace_id is not None else 'd.owner_id=%s'
        rows = connection.execute("SELECT o.id FROM source_observations o JOIN ingestion_runs r ON r.id=o.run_id JOIN source_observation_dependencies d ON d.observation_id=o.id WHERE " + scope + " AND NOT d.purged AND (d.retain_until<=%s OR (o.policy->>'expires_at')::timestamptz<=%s OR (o.policy->>'revoked')::boolean OR NOT (o.policy->>'can_retain')::boolean) ORDER BY o.id FOR UPDATE OF o", (workspace_id if workspace_id is not None else owner_id, now, now)).fetchall()
        for row in rows:
            self._purge(connection, row['id'])

    @staticmethod
    def _purge(connection, observation_id):
        connection.execute("UPDATE source_observations SET policy=jsonb_set(jsonb_set(policy,'{revoked}','true'),'{can_retain}','false'),payload_path=NULL WHERE id=%s", (observation_id,))
        connection.execute('UPDATE source_observation_dependencies SET purged=TRUE WHERE observation_id=%s', (observation_id,))
        connection.execute("UPDATE field_assertions SET value=NULL,state='removed',reason='parent_support_purged' WHERE derivation_id IN (SELECT id FROM derivations WHERE observation_id=%s)", (observation_id,))
        connection.execute('UPDATE metric_observations SET value=NULL,raw_display=NULL WHERE derivation_id IN (SELECT id FROM derivations WHERE observation_id=%s)', (observation_id,))
