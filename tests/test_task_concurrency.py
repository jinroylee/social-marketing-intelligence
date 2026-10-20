"""Competing public workers with real PostgreSQL and simulated source I/O."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock

import pytest

from smi_ingestion.adapters.local import LocalFileCollector
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import KnowledgeQueries, QueryScope
from smi_tasks import OfflineTaskWorker
from test_tasks import HUMAN, WORKER, setup_task, submit


@pytest.mark.parametrize('identity', ['canonical', 'uppercase', 'compact'])
def test_competing_workers_dispatch_once_while_another_task_progresses(stack, tmp_path, identity):
    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    independent_id = submit(tasks, campaign, request_id='independent')['task_id']
    entered, release = Event(), Event()
    calls, lock = [], Lock()

    class BlockedSource:
        def collect(self, *args):
            with lock:
                calls.append('acquire')
                assert len(calls) == 1, 'a competing worker dispatched the same task'
            entered.set()
            assert release.wait(10)
            return LocalFileCollector('fixture-json').collect(*args)

    with ThreadPoolExecutor(max_workers=3) as executor:
        first = executor.submit(OfflineTaskWorker(tasks.db, evidence.root, collector=BlockedSource()).run_one, task_id, WORKER)
        try:
            assert entered.wait(5)
            competing_id = task_id.upper() if identity == 'uppercase' else task_id.replace('-', '') if identity == 'compact' else task_id
            second = executor.submit(OfflineTaskWorker(tasks.db, evidence.root, collector=BlockedSource()).run_one,
                                     competing_id, ActorContext('local', 'competitor', 'automation'))
            competing = second.result(timeout=5)
            assert competing['outcome'] is None
            assert competing['execution']['state'] == 'running'
            assert len(competing['attempts']) == 1
            independent = executor.submit(OfflineTaskWorker(tasks.db, evidence.root).run_one, independent_id, WORKER).result(timeout=5)
            assert independent['outcome'] == 'usable_update'
        finally:
            release.set()
        completed = first.result(timeout=5)
    assert calls == ['acquire']
    assert completed['outcome'] == 'no_usable_update'
    assert completed['execution']['state'] == 'completed'
    assert len(completed['attempts']) == 1
    assert completed['attempts'][0]['resumed_by'] == []
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='concurrent', include_synthetic=True)
    assert len(result['members']) == 1
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == completed


def test_disconnected_worker_cannot_save_late_source_results_over_successor(stack, tmp_path):
    from dataclasses import replace
    from smi_tasks import TaskExecutionLost

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    entered, release = Event(), Event()
    executions = []

    class LateSource:
        def collect(self, *args):
            batch = LocalFileCollector('fixture-json').collect(*args)
            entered.set()
            assert release.wait(10)
            draft = replace(batch.items[0], payload=b'{"account":{"id":"stale","handle":"stale-worker"}}')
            return replace(batch, items=(draft,))

    worker = OfflineTaskWorker(tasks.db, evidence.root, collector=LateSource(), on_execution=executions.append)
    with ThreadPoolExecutor(max_workers=2) as executor:
        stale = executor.submit(worker.run_one, task_id, WORKER)
        try:
            assert entered.wait(5)
            original = tasks.read(task_id, HUMAN)
            executions[0].disconnect()
            assert tasks.read(task_id, HUMAN)['execution']['state'] == 'recoverable'
            successor = executor.submit(OfflineTaskWorker(tasks.db, evidence.root).run_one,
                                        task_id, ActorContext('local', 'successor', 'automation')).result(timeout=5)
            assert successor['outcome'] == 'usable_update'
        finally:
            release.set()
        with pytest.raises(TaskExecutionLost):
            stale.result(timeout=5)
    assert tasks.read(task_id, HUMAN) == successor
    assert successor['attempts'][0]['run_id'] == original['attempts'][0]['run_id']
    assert successor['coverage']['collected_observations'] == 1
    assert successor['coverage']['requests_used'] == 1
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='fenced', include_synthetic=True)
    assert len(result['members']) == 1
    assert KnowledgeQueries(tasks.db).search(QueryScope(text='stale-worker'), HUMAN, request_id='no-stale', include_synthetic=True)['members'] == []


@pytest.mark.parametrize('phase', ['evidence', 'canonical', 'publication', 'completion'])
def test_session_loss_before_owner_commit_rolls_back_effect_and_allows_handoff(stack, tmp_path, phase):
    from smi_tasks import TaskExecutionLost

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    entered, release = Event(), Event()
    executions = []

    def before_commit(committing):
        if committing == phase:
            entered.set()
            assert release.wait(10)

    with ThreadPoolExecutor(max_workers=2) as executor:
        stale = executor.submit(OfflineTaskWorker(tasks.db, evidence.root, on_execution=executions.append,
                                                 before_commit=before_commit).run_one, task_id, WORKER)
        try:
            assert entered.wait(5)
            interrupted = tasks.read(task_id, HUMAN)
            assert interrupted['outcome'] is None
            executions[0].disconnect()
            successor = executor.submit(OfflineTaskWorker(tasks.db, evidence.root).run_one,
                                        task_id, ActorContext('local', 'successor', 'automation')).result(timeout=5)
            assert successor['outcome'] == 'usable_update'
        finally:
            release.set()
        with pytest.raises(TaskExecutionLost):
            stale.result(timeout=5)
    assert tasks.read(task_id, HUMAN) == successor
    assert len(successor['attempts']) == 1
    assert successor['attempts'][0]['attempt_id'] == interrupted['attempts'][0]['attempt_id']
    assert successor['attempts'][0]['run_id'] == interrupted['attempts'][0]['run_id']
    assert successor['coverage']['collected_observations'] == 1
    assert successor['coverage']['ingested_observations'] == 1
    assert successor['coverage']['requests_used'] == 1
    assert len(successor['publication_ids']) == 1
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='commit-fence', include_synthetic=True)
    assert len(result['manifest']) == 1
    producer = WORKER.actor_id if phase == 'completion' else 'successor'
    assert result['manifest'][0]['publication_producer']['actor_id'] == producer
    assert len(list(evidence.root.glob('*.bin'))) == 1


def test_repeated_safe_wait_handoffs_keep_bounded_history_and_exact_attempt(stack, tmp_path):
    from smi_ingestion.contracts import CollectedBatch, RunLimits
    from smi_tasks import AcquisitionTasks, OfflineRoute

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(max_requests=100)), authority=tasks.authority)
    task_id = submit(tasks, campaign)['task_id']

    class PendingSource:
        def collect(self, manifest, checkpoint, limits):
            return CollectedBatch((), {'opaque_operation': 'secret-provider-handle', 'poll': checkpoint.get('poll', 0) + 1},
                                  False, waiting='provider_pending', request_attempts=1)

    first = OfflineTaskWorker(tasks.db, evidence.root, collector=PendingSource()).run_one(task_id, WORKER)
    for number in range(25):
        result = OfflineTaskWorker(tasks.db, evidence.root, collector=PendingSource()).run_one(
            task_id, ActorContext('local', f'recovery-{number}', 'automation'))
    assert result['execution']['state'] == 'waiting'
    assert len(result['attempts']) == 1
    attempt = result['attempts'][0]
    assert attempt['attempt_id'] == first['attempts'][0]['attempt_id']
    assert attempt['recovery_count'] == 25
    assert len(attempt['resumed_by']) == 20
    assert attempt['resumed_by'][0]['actor_id'] == 'recovery-5'
    assert attempt['resumed_by'][-1]['actor_id'] == 'recovery-24'
    assert result['coverage']['requests_used'] == 26
    assert 'secret-provider-handle' not in str(result)


@pytest.mark.parametrize('phase', ['evidence_committed', 'publication_committed'])
def test_process_death_releases_claim_and_preserves_exact_committed_frontier(stack, tmp_path, phase):
    import json
    import select
    import subprocess
    import sys
    from test_cli import _cli

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    code = '''
import json, sys, time
from pathlib import Path
from smi_ingestion.db import Database
from smi_ingestion.evidence_sets import ActorContext
from smi_tasks import OfflineTaskWorker
def progress(task):
    if task['progress']['phase'] == sys.argv[5]:
        print(json.dumps(task), flush=True)
        time.sleep(30)
OfflineTaskWorker(Database(sys.argv[1], sys.argv[2]), Path(sys.argv[3]), on_progress=progress).run_one(
    sys.argv[4], ActorContext('local', 'original-process', 'automation'))
'''
    process = subprocess.Popen([sys.executable, '-c', code, tasks.db.dsn, tasks.db.schema, str(evidence.root), task_id, phase],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([process.stdout], [], [], 5)[0], 'worker did not reach committed frontier'
        original = json.loads(process.stdout.readline())
        competing = _cli(tasks.db, evidence.root, 'run-offline-task', task_id, '--worker-id', 'competing-process')
        assert competing.returncode == 0, competing.stdout + competing.stderr
        assert json.loads(competing.stdout)['execution']['state'] == 'running'
        assert json.loads(competing.stdout)['attempts'][0]['resumed_by'] == []
        process.kill()
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()
    assert tasks.read(task_id, HUMAN)['execution']['state'] == 'recoverable'
    (tmp_path / 'account.json').unlink()
    if phase == 'publication_committed':
        manifest.unlink()
    resumed = _cli(tasks.db, evidence.root, 'run-offline-task', task_id, '--worker-id', 'recovery-process')
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    completed = json.loads(resumed.stdout)
    assert completed['outcome'] == 'usable_update'
    assert completed['attempts'][0]['attempt_id'] == original['attempts'][0]['attempt_id']
    assert completed['attempts'][0]['run_id'] == original['attempts'][0]['run_id']
    assert completed['attempts'][0]['producer'] == {'actor_id': 'original-process', 'kind': 'automation'}
    assert completed['attempts'][0]['recovery_count'] == 1
    assert completed['coverage']['collected_observations'] == 1
    assert completed['coverage']['requests_used'] == 1
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='process-handoff', include_synthetic=True)
    assert len(result['manifest']) == 1
    expected_producer = 'original-process' if phase == 'publication_committed' else 'recovery-process'
    assert result['manifest'][0]['publication_producer']['actor_id'] == expected_producer


def test_local_task_detail_displays_recoverable_execution_state(stack, tmp_path):
    from smi_review.app import ReviewApp

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']

    def interrupt(task):
        if task['progress']['phase'] == 'evidence_committed':
            raise RuntimeError('interrupted')

    with pytest.raises(RuntimeError, match='interrupted'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    response = ReviewApp(tasks.db).handle('GET', f'/tasks/{task_id}')
    assert response.status == 200
    body = response.body.decode()
    assert 'Execution' in body
    assert 'recoverable' in body
    assert 'offline-task-worker' in body


def test_before_commit_observer_interrupts_without_turning_rollback_into_task_failure(stack, tmp_path):
    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']

    def interrupt(phase):
        if phase == 'publication':
            raise ValueError('controlled interruption')

    with pytest.raises(ValueError, match='controlled interruption'):
        OfflineTaskWorker(tasks.db, evidence.root, before_commit=interrupt).run_one(task_id, WORKER)
    recoverable = tasks.read(task_id, HUMAN)
    assert recoverable['outcome'] is None
    assert recoverable['execution']['state'] == 'recoverable'
    assert recoverable['publication_ids'] == []
    assert recoverable['attempts'][0]['publication_support']
    manifest.unlink()
    (tmp_path / 'account.json').unlink()
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['requests_used'] == 1


def test_worker_losing_session_between_records_cannot_dispatch_more_source_io(stack, tmp_path):
    from smi_tasks import TaskExecutionLost

    items = [{'path': 'account.json', 'reference': f'synthetic://account/{number}'} for number in range(2)]
    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, items=items)
    task_id = submit(tasks, campaign)['task_id']
    entered, release = Event(), Event()
    executions, calls = [], []

    class OneSourceCall:
        def collect(self, *args):
            calls.append('source')
            assert len(calls) == 1, 'stale worker dispatched another source call'
            return LocalFileCollector('fixture-json').collect(*args)

    def after_commit(task):
        if task['progress']['phase'] == 'canonical_committed':
            entered.set()
            assert release.wait(10)

    with ThreadPoolExecutor(max_workers=2) as executor:
        stale = executor.submit(OfflineTaskWorker(tasks.db, evidence.root, collector=OneSourceCall(),
                                                 on_execution=executions.append, on_progress=after_commit).run_one, task_id, WORKER)
        try:
            assert entered.wait(5)
            executions[0].disconnect()
            completed = executor.submit(OfflineTaskWorker(tasks.db, evidence.root).run_one,
                                        task_id, ActorContext('local', 'successor', 'automation')).result(timeout=5)
        finally:
            release.set()
        with pytest.raises(TaskExecutionLost):
            stale.result(timeout=5)
    assert calls == ['source']
    assert completed['coverage']['collected_observations'] == 2
    assert completed['coverage']['requests_used'] == 2
    assert tasks.read(task_id, HUMAN) == completed


def test_distinct_tasks_can_prepare_same_capture_without_a_workspace_execution_lock(stack, tmp_path):
    from smi_knowledge import KnowledgePublications

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_ids = [submit(tasks, campaign, request_id=f'task-{number}')['task_id'] for number in range(2)]
    prepared = Barrier(2)

    def await_other_task(task):
        if task['progress']['phase'] == 'publication_prepared':
            prepared.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(OfflineTaskWorker(tasks.db, evidence.root, on_progress=await_other_task).run_one,
                                   task_id, WORKER) for task_id in task_ids]
        results = [future.result(timeout=10) for future in futures]
    assert all(result['outcome'] == 'usable_update' for result in results)
    assert len({result['attempts'][0]['run_id'] for result in results}) == 2
    publication_ids = {result['publication_ids'][0] for result in results}
    assert len(publication_ids) == 2
    for task_id, result in zip(task_ids, results):
        assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == result
    assert {publication['publication_id'] for publication in KnowledgePublications(tasks.db).list(HUMAN, include_synthetic=True)} == publication_ids
