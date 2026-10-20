"""Per-task PostgreSQL session ownership for bounded worker execution."""

from collections.abc import Callable
from contextlib import AbstractContextManager, contextmanager
import uuid

from psycopg import InterfaceError, OperationalError
from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext


def execution_lock_name(workspace_id: str, task_id: str) -> str:
    """Identify ownership of one normalized task UUID within its workspace."""
    return f'acquisition-execution:{workspace_id}:{task_id}'


def execution_is_running(connection, row) -> bool:
    """Observe the exact session lock, including after an ungraceful disconnect."""
    if row['execution_backend_pid'] is None:
        return False
    return connection.execute(
        "WITH key AS (SELECT hashtextextended(%s,0) AS id) "
        "SELECT EXISTS(SELECT 1 FROM pg_locks,key WHERE locktype='advisory' AND granted "
        "AND pid=%s AND objsubid=1 AND classid=((key.id >> 32) & 4294967295)::oid "
        "AND objid=(key.id & 4294967295)::oid) AS running",
        (execution_lock_name(row['workspace_id'], str(row['id'])), row['execution_backend_pid']),
    ).fetchone()['running']


class TaskExecution(AbstractContextManager):
    """Hold one task's execution session until return, interruption or disconnect.

    A competing worker returns without waiting. Session death releases ownership;
    a merely paused process continues owning its task, without blocking others.
    """

    def __init__(self, db: Database, workspace_id: str, task_id: str, actor: ActorContext, *,
                 before_commit: Callable[[str], None] | None = None):
        self.db, self.workspace_id, self.task_id, self.actor = db, workspace_id, str(uuid.UUID(task_id)), actor
        self._connection = None
        self.before_commit = before_commit
        self.acquired = self.terminal = False
        self.execution_id = str(uuid.uuid4())

    def __enter__(self):
        self.actor.require_workspace(self.workspace_id)
        if self.actor.kind != 'automation':
            raise EvidenceError('task_worker_authority_required')
        self._connection = self.db.connect()
        try:
            self._connection.commit()
            self._connection.autocommit = True
            self.acquired = self._connection.execute('SELECT pg_try_advisory_lock(hashtextextended(%s,0)) AS acquired',
                                                    (execution_lock_name(self.workspace_id, self.task_id),)).fetchone()['acquired']
            if self.acquired:
                with self._connection.transaction():
                    row = self._connection.execute('SELECT * FROM acquisition_tasks WHERE id=%s AND workspace_id=%s FOR UPDATE',
                                                  (self.task_id, self.workspace_id)).fetchone()
                    if row is None:
                        raise EvidenceError('acquisition_task_not_found')
                    self.terminal = row['outcome'] is not None
                    if not self.terminal:
                        self._connection.execute('UPDATE acquisition_tasks SET execution_id=%s,execution_backend_pid=pg_backend_pid(),execution_actor=%s WHERE id=%s',
                                                (self.execution_id, Jsonb({'actor_id': self.actor.actor_id, 'kind': self.actor.kind}), self.task_id))
            return self
        except BaseException:
            self._connection.close()
            raise

    @contextmanager
    def transaction(self, phase: str):
        """Yield the ownership connection; loss rolls back the actual owner effects.

        No collector I/O belongs in this scope. The trusted before-commit observer
        can interrupt a transaction for controlled fault testing. It must not call
        back into task execution while this transaction holds its task row.
        """
        if not self.acquired or self.terminal:
            raise TaskExecutionLost('task_execution_lost')
        try:
            with self._connection.transaction():
                row = self._connection.execute('SELECT execution_id,outcome FROM acquisition_tasks WHERE id=%s AND workspace_id=%s FOR UPDATE',
                                               (self.task_id, self.workspace_id)).fetchone()
                if row is None or str(row['execution_id']) != self.execution_id or row['outcome'] is not None:
                    raise TaskExecutionLost('task_execution_lost')
                yield self._connection
                if self.before_commit:
                    self.before_commit(phase)
                # psycopg's transaction context may silently skip COMMIT after
                # an explicit local close. Report loss at this effect boundary
                # so callers also clean any uncommitted retained payload file.
                if self._connection.closed:
                    raise TaskExecutionLost('task_execution_lost')
        except (InterfaceError, OperationalError) as error:
            if self._connection.closed or self._connection.broken:
                raise TaskExecutionLost('task_execution_lost') from error
            raise

    def disconnect(self) -> None:
        """Close this ownership session, aborting its transaction and allowing handoff.

        This trusted operational/fault-injection port does not cancel an external
        operation already in flight. Its late response cannot commit locally.
        """
        if self._connection:
            self._connection.close()

    def __exit__(self, *exc):
        self.disconnect()


class TaskExecutionLost(RuntimeError):
    """The worker's ownership connection is gone; its local effects cannot commit."""
