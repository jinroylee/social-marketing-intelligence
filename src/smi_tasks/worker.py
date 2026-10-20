"""Fenced task execution composed from public ingestion/publication operations."""

from collections.abc import Callable
from dataclasses import asdict
import hashlib
from pathlib import Path
import uuid
from typing import Any

from psycopg.types.json import Jsonb

from smi_ingestion.adapters.json_fixture import JsonFixtureMapper
from smi_ingestion.adapters.local import LocalFileCollector
from smi_ingestion.adapters.registry import AdapterRegistry
from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import Collector, RunLimits
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError, EvidenceStore
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.runner import IngestionRunner
from smi_ingestion.support import IngestedEvidence, SupportReference
from smi_knowledge import KnowledgePublications

from .store import AcquisitionTasks
from .execution import TaskExecution


class _ObserverFailure(Exception):
    def __init__(self, cause: Exception):
        self.cause = cause


class OfflineTaskWorker:
    """Execute/resume one admitted task using only the synthetic fixture route.

    ``on_progress`` observes source-free task snapshots after owner commits. Its
    exceptions propagate, leaving committed work recoverable. Publication commit
    notification precedes task acknowledgment. One task owns a PostgreSQL session;
    all owner mutations use its connection, so session loss fences late results.
    ``on_execution`` exposes a trusted disconnect handle. ``before_commit`` is a
    trusted source-free interruption/diagnostic port inside owner transactions.
    """

    def __init__(self, db: Database, evidence_root: Path, workspace_id: str = 'local', *,
                 collector: Collector | None = None, on_progress: Callable[[dict[str, Any]], None] | None = None,
                 on_execution: Callable[[TaskExecution], None] | None = None,
                 before_commit: Callable[[str], None] | None = None):
        self.db, self.workspace_id = db, workspace_id
        self.tasks = AcquisitionTasks(db, workspace_id)
        self.evidence = EvidenceStore(db, evidence_root)
        self.on_progress = on_progress
        self.on_execution, self.before_commit = on_execution, before_commit
        registry = AdapterRegistry()
        registry.register('fixture-json', collector or LocalFileCollector('fixture-json'), JsonFixtureMapper())
        self.runner = IngestionRunner(self.evidence, CanonicalWriter(db), registry)

    def _notify(self, task_id, actor, *, phase=None, publication_id=None):
        if self.on_progress:
            view = self.tasks.read(task_id, actor)
            if phase:
                view['progress'] = {'phase': phase, 'publication_id': publication_id}
            try:
                self.on_progress(view)
            except Exception as error:
                raise _ObserverFailure(error) from error

    def _checkpoint(self, task_id, attempt_id, phase, coverage, actor, execution, *, observation_id=None,
                    support=None, failure_phase=None, failure_code=None, waiting=None):
        progress = {'phase': phase}
        if observation_id:
            progress['observation_id'] = observation_id
        status = 'publishing' if phase == 'publication_prepared' else 'waiting' if waiting else 'ingesting'
        if waiting:
            progress.update(waiting)
        with execution.transaction('checkpoint') as connection:
            connection.execute('UPDATE acquisition_tasks SET status=%s,progress=%s,coverage=%s,failure_phase=%s,failure_code=%s WHERE id=%s',
                               (status, Jsonb(progress), Jsonb(coverage), failure_phase, failure_code, task_id))
            phases = connection.execute('SELECT phases FROM acquisition_attempts WHERE id=%s', (attempt_id,)).fetchone()['phases']
            connection.execute('UPDATE acquisition_attempts SET phases=%s WHERE id=%s', (Jsonb((phases + [phase])[-100:]), attempt_id))
            if support is not None:
                connection.execute('UPDATE acquisition_attempts SET publication_support=%s WHERE id=%s', (Jsonb([asdict(s) for s in support]), attempt_id))
        self._notify(task_id, actor)

    def _finish(self, task_id, attempt_id, coverage, actor, execution, *, outcome, failure_phase=None, failure_code=None, publication_id=None):
        with execution.transaction('completion') as connection:
            connection.execute("UPDATE acquisition_tasks SET status=%s,outcome=%s,progress=%s,coverage=%s,failure_phase=%s,failure_code=%s,finished_at=now() WHERE id=%s",
                               ('failed' if outcome == 'failure' else 'completed', outcome, Jsonb({'phase': 'completed'}), Jsonb(coverage), failure_phase, failure_code, task_id))
            phases = connection.execute('SELECT phases FROM acquisition_attempts WHERE id=%s', (attempt_id,)).fetchone()['phases']
            connection.execute('UPDATE acquisition_attempts SET finished_at=now(),phases=%s WHERE id=%s', (Jsonb((phases + ['completed'])[-100:]), attempt_id))
            if publication_id:
                connection.execute('INSERT INTO acquisition_task_publications(task_id,publication_id) VALUES (%s,%s) ON CONFLICT DO NOTHING', (task_id, publication_id))
        self._notify(task_id, actor)

    @staticmethod
    def _coverage(report, requested_inputs):
        return {'collected_observations': report['observations'], 'ingested_observations': report['applied'],
                'published_members': 0, 'quarantined_observations': report['quarantined'],
                'requested_inputs': requested_inputs,
                'remaining_inputs': max(0, requested_inputs - report['observations']) + report['quarantined'] + report['pending'],
                'input_coverage': report['coverage'], 'scope': 'bounded_requested_input', 'market_coverage': 'unknown',
                'requests_used': report['requests_used'], 'bytes_used': report['bytes_used'], 'issues': report['issues'],
                'unresolved': report['unresolved'], 'missing_fields': report['missing_fields']}

    def run_one(self, task_id: str, actor: ActorContext) -> dict[str, Any]:
        """Resume the same attempt/run/support, or reopen a terminal outcome.

        Admission authority and scope remain those saved on the task. Recovery
        records its actual actor and never grants a new attempt or broader scope.
        """
        actor.require_workspace(self.workspace_id)
        if actor.kind != 'automation':
            raise EvidenceError('task_worker_authority_required')
        task_id = str(uuid.UUID(task_id))

        def before_commit(phase):
            if self.before_commit:
                try:
                    self.before_commit(phase)
                except Exception as error:
                    raise _ObserverFailure(error) from error

        try:
            with TaskExecution(self.db, self.workspace_id, task_id, actor, before_commit=before_commit) as execution:
                if not execution.acquired or execution.terminal:
                    return self.tasks.read(task_id, actor)
                if self.on_execution:
                    self.on_execution(execution)
                result = self._run_one(task_id, actor, execution)
        except _ObserverFailure as error:
            raise error.cause
        # Waiting/recoverable reads must observe the released ownership session.
        return self.tasks.read(task_id, actor) if result['outcome'] is None else result

    def _run_one(self, task_id, actor, execution):
        with execution.transaction('attempt') as connection:
            row = connection.execute('SELECT * FROM acquisition_tasks WHERE id=%s AND workspace_id=%s FOR UPDATE', (task_id, self.workspace_id)).fetchone()
            if row['outcome'] is not None:
                return self.tasks.read(task_id, actor)
            if row['origin'] not in {'campaign', 'assistant'} or row['scope']['route'] != 'fixture-json':
                raise EvidenceError('unsupported_task_origin_or_route')
            if row['status'] == 'queued':
                run_id = self.evidence.start_run(Path(row['manifest_path']), row['manifest_hash'], 'fixture-json', RunLimits(**row['limits']), connection=connection, workspace_id=self.workspace_id)
                attempt_id = str(uuid.uuid4())
                attempt = connection.execute('INSERT INTO acquisition_attempts(id,task_id,number,run_id,producer_id,producer_kind) VALUES (%s,%s,1,%s,%s,%s) RETURNING *',
                                             (attempt_id, task_id, run_id, actor.actor_id, actor.kind)).fetchone()
                connection.execute("UPDATE acquisition_tasks SET status='collecting',progress=%s WHERE id=%s", (Jsonb({'phase': 'collecting'}), task_id))
            else:
                attempt = connection.execute('SELECT * FROM acquisition_attempts WHERE task_id=%s ORDER BY number DESC LIMIT 1', (task_id,)).fetchone()
                if attempt is None:
                    raise EvidenceError('task_execution_incomplete')
                attempt_id, run_id = str(attempt['id']), str(attempt['run_id'])
                resumed_by = (attempt['resumed_by'] + [{'actor_id': actor.actor_id, 'kind': actor.kind}])[-20:]
                connection.execute('UPDATE acquisition_attempts SET resumed_by=%s,recovery_count=recovery_count+1 WHERE id=%s',
                                   (Jsonb(resumed_by), attempt_id))
        phase = 'collection'
        coverage = row['coverage'] or {'collected_observations': 0, 'ingested_observations': 0, 'published_members': 0,
                                       'scope': 'bounded_requested_input', 'market_coverage': 'unknown'}
        failed_phase, code = row['failure_phase'], row['failure_code']
        try:
            publications = KnowledgePublications(self.db, self.workspace_id)
            published = publications.find_request(f'task:{task_id}', actor, include_synthetic=True)
            if not published:
                if attempt['publication_support'] is None:
                    with Path(row['manifest_path']).open('rb') as source:
                        raw = source.read(1_048_577)
                    if hashlib.sha256(raw).hexdigest() != row['manifest_hash']:
                        raise EvidenceError('input_changed')

                    def committed(commit_phase, observation_id):
                        counts = self._coverage(self.runner.inspect(run_id), len(row['scope']['references']))
                        self._checkpoint(task_id, attempt_id, commit_phase, counts, actor, execution, observation_id=observation_id)

                    report = self.runner.resume(run_id, on_commit=committed, transaction=execution.transaction)
                    phase = 'ingestion'
                    coverage = self._coverage(report, len(row['scope']['references']))
                    if report['waiting']:
                        self._checkpoint(task_id, attempt_id, 'waiting', coverage, actor, execution, waiting=report['waiting'])
                        return self.tasks.read(task_id, actor)
                    failed_phase = code = None
                    if report['issues'] or report['status'] != 'completed':
                        code = report['issues'][0]['code'] if report['issues'] else 'incomplete_input'
                        failed_phase = 'ingestion' if report['quarantined'] or code == 'processing_not_permitted' else 'collection'
                    support = IngestedEvidence(self.db, self.workspace_id).select_run(run_id, actor, include_synthetic=True)
                    phase = 'publication'
                    with execution.transaction('selection') as connection:
                        new_support = publications.unpublished(support, actor, include_synthetic=True, connection=connection)
                    coverage.update(eligible_members=len(support), unchanged_members=len(support) - len(new_support),
                                    ineligible_observations=report['applied'] - len(support), unpublished_members=len(new_support))
                    support = new_support
                    self._checkpoint(task_id, attempt_id, 'publication_prepared', coverage, actor, execution, support=support,
                                     failure_phase=failed_phase, failure_code=code)
                else:
                    phase = 'publication'
                    support = tuple(SupportReference(s['observation_id'], s['derivation_id'], tuple(s['assertion_ids']), tuple(s['metric_ids'])) for s in attempt['publication_support'])
                if not support:
                    self._finish(task_id, attempt_id, coverage, actor, execution, outcome='failure' if code else 'no_usable_update', failure_phase=failed_phase, failure_code=code)
                    return self.tasks.read(task_id, actor)
                with execution.transaction('publication') as connection:
                    published = publications.publish(support, actor, request_id=f'task:{task_id}', include_synthetic=True, connection=connection)
                self._notify(task_id, actor, phase='publication_committed', publication_id=published['publication_id'])
                coverage['published_members'] = len(support)
            else:
                coverage['published_members'] = published['coverage']['members']
            coverage['unpublished_members'] = 0
            self._finish(task_id, attempt_id, coverage, actor, execution, outcome='partial_update' if code else 'usable_update',
                         failure_phase=failed_phase, failure_code=code, publication_id=published['publication_id'])
        except (EvidenceError, OSError, ValueError, KeyError, TypeError) as error:
            code = error.code if isinstance(error, EvidenceError) else 'offline_input_unavailable'
            self._finish(task_id, attempt_id, coverage, actor, execution, outcome='failure', failure_phase=phase, failure_code=code)
        return self.tasks.read(task_id, actor)
