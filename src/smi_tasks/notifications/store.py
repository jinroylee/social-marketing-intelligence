"""Completion identities retain no source text; owners supply current support."""

from typing import Any

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgePublications

from ..store import AcquisitionTasks


class CompletionInbox:
    """Reopen the newest 100 logical task completions in one trusted workspace."""

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db, self.workspace_id = db, workspace_id

    def reconcile(self, actor: ActorContext) -> dict[str, int]:
        """Idempotently backfill terminal tasks in this workspace after an upgrade."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            created = connection.execute(
                'INSERT INTO task_completion_events(task_id,created_at) '
                'SELECT id,coalesce(finished_at,submitted_at) FROM acquisition_tasks '
                'WHERE workspace_id=%s AND outcome IS NOT NULL ORDER BY id '
                'ON CONFLICT (task_id) DO NOTHING RETURNING id', (self.workspace_id,),
            ).fetchall()
        return {'created_events': len(created)}

    def list(self, actor: ActorContext) -> list[dict[str, Any]]:
        """Return source-free messages with links checked against current policy."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            rows = connection.execute(
                'SELECT e.* FROM task_completion_events e JOIN acquisition_tasks t ON t.id=e.task_id '
                'WHERE t.workspace_id=%s ORDER BY e.created_at DESC,e.id DESC LIMIT 100',
                (self.workspace_id,),
            ).fetchall()
        return [self._view(row, actor) for row in rows]

    def read(self, event_id: str, actor: ActorContext) -> dict[str, Any]:
        """Reopen one completion; foreign-workspace identities are unavailable."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute(
                'SELECT e.* FROM task_completion_events e JOIN acquisition_tasks t ON t.id=e.task_id '
                'WHERE e.id=%s AND t.workspace_id=%s', (event_id, self.workspace_id),
            ).fetchone()
        if row is None:
            raise EvidenceError('completion_event_not_found')
        return self._view(row, actor)

    def read_task(self, task_id: str, actor: ActorContext) -> dict[str, Any] | None:
        """Read one task's logical completion even beyond the newest-100 inbox window."""
        actor.require_workspace(self.workspace_id)
        AcquisitionTasks(self.db, self.workspace_id).read(task_id, actor)
        with self.db.connect() as connection:
            row = connection.execute('SELECT e.* FROM task_completion_events e JOIN acquisition_tasks t ON t.id=e.task_id WHERE t.id=%s AND t.workspace_id=%s',
                                     (task_id, self.workspace_id)).fetchone()
        return self._view(row, actor) if row else None

    def _view(self, row, actor):
        task = AcquisitionTasks(self.db, self.workspace_id).read(str(row['task_id']), actor)
        publications = []
        available = unavailable = 0
        for publication_id in task['publication_ids']:
            publication = KnowledgePublications(self.db, self.workspace_id).read(publication_id, actor, purpose='display', include_synthetic=True)
            count = sum(m['availability'] == 'available' and m['support_status'] == 'current' for m in publication['members'])
            denied = len(publication['members']) - count
            available += count
            unavailable += denied
            publications.append({'publication_id': publication_id,
                                 'href': f'/knowledge/publications/{publication_id}?include_synthetic=yes' if count else None,
                                 'available_members': count, 'unavailable_members': denied})
        label = {'usable_update': 'Usable update completed.', 'partial_update': 'Partial update completed.',
                 'no_usable_update': 'No usable update.', 'failure': 'Task failed.'}[task['outcome']]
        coverage = task['coverage']
        publication_message = (f'Published members: {coverage["published_members"]}; currently available: {available}.'
                               if coverage.get('published_members') else 'No new publication.')
        message = f'{label} {publication_message} Remaining inputs: {coverage.get("remaining_inputs", "unknown")}.'
        if task['failure']:
            message += f' Failure: {task["failure"]["phase"]} / {task["failure"]["code"]}.'
        if unavailable:
            message += f' Support unavailable: {unavailable} member(s).'
        campaign = None
        if task['origin'] == 'campaign' and task['scope_version'] == 'campaign-coverage-discovery-v1':
            can_regenerate = task['outcome'] in {'usable_update', 'partial_update'} and available > 0
            campaign = {'campaign_id': task['scope']['campaign_id'], 'shortlist_id': task['scope']['shortlist_id'],
                        'regeneration_href': f"/inbox/{row['id']}/regenerate" if can_regenerate else None,
                        'reason': None if can_regenerate else 'published_support_unavailable' if available == 0 and task['publication_ids'] else 'no_new_usable_evidence'}
        return {'event_id': str(row['id']), 'task_id': task['task_id'], 'task_href': f'/tasks/{task["task_id"]}',
                'created_at': row['created_at'].isoformat(), 'outcome': task['outcome'], 'message': message,
                'coverage': coverage, 'failure': task['failure'], 'publications': publications, 'campaign_discovery': campaign,
                'current_coverage': {'available_members': available, 'unavailable_members': unavailable}}
