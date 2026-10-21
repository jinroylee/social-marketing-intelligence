"""Fenced task execution composed from public ingestion/publication operations."""

from collections.abc import Callable
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import uuid
from typing import Any

from psycopg.types.json import Jsonb

from smi_costs import UsageAccounting, SyntheticOperationAdapter, SyntheticResult
from smi_ingestion.adapters.json_fixture import JsonFixtureMapper
from smi_ingestion.adapters.keyword_fixture import ROUTE, KeywordFixtureCollector, KeywordFixtureMapper, validate_keyword_scope
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
from .contracts import OfflineRoute, execution_configuration_digest
from .execution import TaskExecution


class _ObserverFailure(Exception):
    def __init__(self, cause: Exception):
        self.cause = cause


class _CostDispatchBlocked(RuntimeError):
    def __init__(self, result):
        self.result = result


class _ControlledCollector:
    """Composition of exact task authority, execution fencing and one-use cost control."""

    def __init__(self, collector, accounting, control, attempt, execution):
        self.collector, self.accounting, self.control = collector, accounting, control
        self.attempt, self.execution = attempt, execution

    def collect(self, manifest, checkpoint, limits):
        # One invocation may make at most one synthetic request, including waits.
        # The persisted checkpoint identifies that dispatch across worker recovery.
        identity = hashlib.sha256(json.dumps(checkpoint, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        adapter = SyntheticOperationAdapter(self.accounting, self.control['scope_id'], max_units=self.control['max_units'])

        def call(bound):
            batch = self.collector.collect(manifest, checkpoint, RunLimits(1, limits.max_pages, limits.max_records, limits.max_bytes))
            requests = sum(item.request_attempts for item in batch.items) if batch.items else batch.request_attempts
            return SyntheticResult(batch, requests)

        result = adapter.execute(self.execution.actor, request_id=f'task:{self.execution.task_id}:{identity}', method='fixture-dispatch-v1' if manifest['adapter'] == 'fixture-json' else 'keyword-dispatch-v1', call=call,
                                 task_id=self.execution.task_id, attempt_id=str(self.attempt['id']), transaction=self.execution.transaction,
                                 operation_actor=ActorContext(self.accounting.workspace_id, self.attempt['producer_id'], self.attempt['producer_kind']))
        if result['status'] != 'executed':
            raise _CostDispatchBlocked(result)
        return result['value']


class OfflineTaskWorker:
    """Execute/resume one admitted task using only the configured synthetic offline capabilities.

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
        self.collector = collector
        self.costs = UsageAccounting(db, workspace_id, task_attribution=self.tasks.resolve_cost_attribution)

    def _notify(self, execution, *, phase=None, publication_id=None):
        if self.on_progress:
            view = self.tasks.read(execution.task_id, execution.actor)
            if phase:
                view['progress'] = {'phase': phase, 'publication_id': publication_id}
            try:
                self.on_progress(view)
            except Exception as error:
                raise _ObserverFailure(error) from error

    def _checkpoint(self, execution, attempt_id, phase, coverage, *, observation_id=None,
                    support=None, failure_phase=None, failure_code=None, waiting=None):
        progress = {'phase': phase}
        if observation_id:
            progress['observation_id'] = observation_id
        status = 'publishing' if phase == 'publication_prepared' else 'waiting' if waiting else 'ingesting'
        if waiting:
            progress.update(waiting)
        with execution.transaction('checkpoint') as connection:
            connection.execute('UPDATE acquisition_tasks SET status=%s,progress=%s,coverage=%s,failure_phase=%s,failure_code=%s WHERE id=%s',
                               (status, Jsonb(progress), Jsonb(coverage), failure_phase, failure_code, execution.task_id))
            phases = connection.execute('SELECT phases FROM acquisition_attempts WHERE id=%s', (attempt_id,)).fetchone()['phases']
            connection.execute('UPDATE acquisition_attempts SET phases=%s WHERE id=%s', (Jsonb((phases + [phase])[-100:]), attempt_id))
            if support is not None:
                connection.execute('UPDATE acquisition_attempts SET publication_support=%s WHERE id=%s', (Jsonb([asdict(s) for s in support]), attempt_id))
        self._notify(execution)

    def _finish(self, execution, attempt_id, coverage, *, outcome, failure_phase=None, failure_code=None):
        with execution.transaction('completion') as connection:
            connection.execute("UPDATE acquisition_tasks SET status=%s,outcome=%s,progress=%s,coverage=%s,failure_phase=%s,failure_code=%s,finished_at=now() WHERE id=%s",
                               ('failed' if outcome == 'failure' else 'completed', outcome, Jsonb({'phase': 'completed'}), Jsonb(coverage), failure_phase, failure_code, execution.task_id))
            phases = connection.execute('SELECT phases FROM acquisition_attempts WHERE id=%s', (attempt_id,)).fetchone()['phases']
            connection.execute('UPDATE acquisition_attempts SET finished_at=now(),phases=%s WHERE id=%s', (Jsonb((phases + ['completed'])[-100:]), attempt_id))
            connection.execute('INSERT INTO task_completion_events(task_id,created_at) SELECT id,finished_at FROM acquisition_tasks WHERE id=%s ON CONFLICT (task_id) DO NOTHING', (execution.task_id,))
        self._notify(execution)

    @staticmethod
    def _coverage(report, requested_inputs, discovery=False):
        coverage = {'collected_observations': report['observations'], 'ingested_observations': report['applied'],
                'published_members': 0, 'quarantined_observations': report['quarantined'],
                'requested_inputs': requested_inputs,
                'remaining_inputs': max(0, requested_inputs - report['observations']) + report['quarantined'] + report['pending'],
                'input_coverage': report['coverage'], 'scope': 'bounded_requested_input', 'market_coverage': 'unknown',
                'requests_used': report['requests_used'], 'bytes_used': report['bytes_used'], 'issues': report['issues'],
                'unresolved': report['unresolved'], 'missing_fields': report['missing_fields']}
        if discovery:
            coverage.update(scope='bounded_query_discovery',
                            remaining_inputs=report['quarantined'] + report['pending'] + int(report['coverage'] != 'complete_for_requested_input'),
                            latest_captured_at=report['latest_captured_at'],
                            unassessable_records=sum(issue['code'] == 'discovery_selection_unassessable' for issue in report['issues']))
        return coverage

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
                result = self._run_one(execution)
        except _ObserverFailure as error:
            raise error.cause
        # Waiting/recoverable reads must observe the released ownership session.
        return self.tasks.read(task_id, actor) if result['outcome'] is None else result

    def _run_one(self, execution):
        task_id, actor = execution.task_id, execution.actor
        with execution.transaction('attempt') as connection:
            row = connection.execute('SELECT * FROM acquisition_tasks WHERE id=%s AND workspace_id=%s FOR UPDATE', (task_id, self.workspace_id)).fetchone()
            if row['outcome'] is not None:
                return self.tasks.read(task_id, actor)
            if row['origin'] not in {'campaign', 'assistant'} or row['scope']['route'] not in {'fixture-json', ROUTE}:
                raise EvidenceError('unsupported_task_origin_or_route')
            if row['status'] == 'queued':
                run_id = self.evidence.start_run(Path(row['manifest_path']), row['manifest_hash'], row['scope']['route'], RunLimits(**row['limits']), connection=connection, workspace_id=self.workspace_id)
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
        discovery = row['scope']['route'] == ROUTE
        requested_inputs = 1 if discovery else len(row['scope']['references'])
        phase = 'collection'
        coverage = row['coverage'] or {'collected_observations': 0, 'ingested_observations': 0, 'published_members': 0,
                                       'requested_inputs': requested_inputs, 'remaining_inputs': requested_inputs,
                                       'scope': 'bounded_query_discovery' if discovery else 'bounded_requested_input', 'market_coverage': 'unknown'}
        failed_phase, code = row['failure_phase'], row['failure_code']
        try:
            OfflineRoute(Path(row['manifest_path']), row['scope']['route_version'], RunLimits(**row['limits'])).validate()
            if discovery:
                scope = dict(row['scope'])
                digest = scope.pop('execution_digest', None)
                if digest != execution_configuration_digest(scope, row['limits'], row['manifest_path']):
                    raise EvidenceError('task_configuration_changed')
                validate_keyword_scope(scope['discovery'])
                base_collector = self.collector or KeywordFixtureCollector(scope['discovery'], scope['route_version'])
                mapper = KeywordFixtureMapper()
            else:
                base_collector, mapper = self.collector or LocalFileCollector('fixture-json'), JsonFixtureMapper()
            registry = AdapterRegistry()
            control = self.costs.route_control(row['scope']['route'], actor)
            collector = _ControlledCollector(base_collector, self.costs, control, attempt, execution) if control else base_collector
            registry.register(row['scope']['route'], collector, mapper)
            runner = IngestionRunner(self.evidence, CanonicalWriter(self.db), registry)
            publications = KnowledgePublications(self.db, self.workspace_id)
            phase = 'publication'
            with execution.transaction('publication_recovery') as connection:
                published = self.tasks.read_committed_publication(task_id, actor, connection=connection)
            if not published:
                if attempt['publication_support'] is None:
                    phase = 'collection'
                    with Path(row['manifest_path']).open('rb') as source:
                        raw = source.read(1_048_577)
                    if hashlib.sha256(raw).hexdigest() != row['manifest_hash']:
                        raise EvidenceError('input_changed')
                    _, _, manifest = OfflineRoute(Path(row['manifest_path']), row['scope']['route_version'], RunLimits(**row['limits'])).snapshot()
                    if manifest['adapter'] != row['scope']['route']:
                        raise EvidenceError('unsupported_task_route')

                    def committed(commit_phase, observation_id):
                        counts = self._coverage(runner.inspect(run_id), requested_inputs, discovery)
                        self._checkpoint(execution, attempt_id, commit_phase, counts, observation_id=observation_id)

                    report = runner.resume(run_id, on_commit=committed, transaction=execution.transaction)
                    phase = 'ingestion'
                    coverage = self._coverage(report, requested_inputs, discovery)
                    if report['waiting']:
                        self._checkpoint(execution, attempt_id, 'waiting', coverage, waiting=report['waiting'])
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
                    self._checkpoint(execution, attempt_id, 'publication_prepared', coverage, support=support,
                                     failure_phase=failed_phase, failure_code=code)
                else:
                    phase = 'publication'
                    support = tuple(SupportReference(s['observation_id'], s['derivation_id'], tuple(s['assertion_ids']), tuple(s['metric_ids'])) for s in attempt['publication_support'])
                if not support:
                    self._finish(execution, attempt_id, coverage, outcome='failure' if code else 'no_usable_update', failure_phase=failed_phase, failure_code=code)
                    return self.tasks.read(task_id, actor)
                with execution.transaction('publication') as connection:
                    published = publications.publish(support, actor, request_id=f'task:{task_id}', include_synthetic=True, connection=connection)
                    if published['status'] != 'published':
                        raise EvidenceError('publication_request_conflict')
                    # This task-owned receipt shares the actual publication commit;
                    # a public caller choosing the request text cannot create it.
                    connection.execute('INSERT INTO acquisition_task_publications(task_id,publication_id) VALUES (%s,%s)',
                                       (task_id, published['publication_id']))
                self._notify(execution, phase='publication_committed', publication_id=published['publication_id'])
                coverage['published_members'] = len(support)
            else:
                coverage['published_members'] = published['coverage']['members']
            coverage['unpublished_members'] = 0
            self._finish(execution, attempt_id, coverage, outcome='partial_update' if code else 'usable_update',
                         failure_phase=failed_phase, failure_code=code)
        except _CostDispatchBlocked as blocked:
            result = blocked.result
            coverage = self._coverage(runner.inspect(run_id), requested_inputs, discovery)
            self._checkpoint(execution, attempt_id, 'waiting', coverage,
                             waiting={'reason': result['reason'], 'operation_id': result['operation_id'],
                                      'resumable': result['status'] == 'refused', 'allowance': result['allowance']})
        except (EvidenceError, OSError, ValueError, KeyError, TypeError) as error:
            code = error.code if isinstance(error, EvidenceError) else 'offline_input_unavailable'
            self._finish(execution, attempt_id, coverage, outcome='failure', failure_phase=phase, failure_code=code)
        return self.tasks.read(task_id, actor)
