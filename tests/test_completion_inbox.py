"""Durable completion delivery through public worker/inbox and HTTP operations."""

import pytest

from smi_tasks import OfflineTaskWorker
from test_tasks import HUMAN, WORKER, setup_task, submit


def test_completion_is_visible_after_committed_outcome_and_lost_acknowledgment(stack, tmp_path):
    from smi_tasks import CompletionInbox

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    assert CompletionInbox(tasks.db).list(HUMAN) == []

    def interrupt(task):
        if task['outcome'] is not None:
            raise RuntimeError('lost completion acknowledgment')

    with pytest.raises(RuntimeError, match='lost completion acknowledgment'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    completed = tasks.read(task_id, HUMAN)
    assert completed['outcome'] == 'usable_update'
    inbox = CompletionInbox(tasks.db)
    events = inbox.list(HUMAN)
    assert len(events) == 1
    event = inbox.read(events[0]['event_id'], HUMAN)
    assert event == events[0]
    assert event['outcome'] == 'usable_update'
    assert event['task_href'] == f'/tasks/{task_id}'
    assert event['coverage']['published_members'] == 1
    assert event['current_coverage'] == {'available_members': 1, 'unavailable_members': 0}
    assert event['publications'][0]['href'] == f"/knowledge/publications/{completed['publication_ids'][0]}?include_synthetic=yes"
    assert event['message'] == 'Usable update completed. Published members: 1; currently available: 1. Remaining inputs: 0.'
    OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert CompletionInbox(tasks.db).list(HUMAN) == events


def test_inbox_links_survive_http_restart_and_withdrawn_support_is_unavailable(stack, tmp_path):
    from smi_knowledge import KnowledgePublications
    from smi_review import ReviewApp
    from smi_tasks import CompletionInbox
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, payload={
        'account': {'id': 'secret-account', 'handle': '<script>restricted-source-wording</script>'},
    })
    task_id = submit(tasks, campaign, purpose='Untrusted <script>purpose</script>')['task_id']
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    event = CompletionInbox(tasks.db).list(HUMAN)[0]
    event_path = f"/inbox/{event['event_id']}"
    publication_path = event['publications'][0]['href']
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path='/inbox')
        assert status == 200
        assert event_path in page
        assert 'Requested inputs: 1' in page
        assert 'Collected: 1' in page
        assert 'Ingested: 1' in page
        assert 'Market coverage is unknown.' in page
        assert 'restricted-source-wording' not in page
        assert 'Untrusted' not in page
        assert request(url, path=event_path)[0] == 200
        assert request(url, path=event['task_href'])[0] == 200
        assert request(url, path=publication_path)[0] == 200
    publication = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)
    evidence.revoke(publication['members'][0]['observation_id'])
    current = CompletionInbox(tasks.db).read(event['event_id'], HUMAN)
    assert current['event_id'] == event['event_id']
    assert current['outcome'] == 'usable_update'
    assert current['coverage']['published_members'] == 1
    assert current['current_coverage'] == {'available_members': 0, 'unavailable_members': 1}
    assert current['publications'][0]['href'] is None
    with running(ReviewApp(tasks.db)) as url:
        for path in ('/inbox', event_path):
            status, _, page = request(url, path=path)
            assert status == 200
            assert 'currently available: 0' in page
            assert 'Support unavailable: 1' in page
            assert publication_path not in page
            assert 'restricted-source-wording' not in page
            assert event['task_href'] in page


def test_operator_can_reopen_and_reconcile_inbox_in_separate_processes(stack, tmp_path):
    import json

    from smi_tasks import CompletionInbox
    from test_cli import _cli

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    listed = _cli(tasks.db, evidence.root, 'list-inbox')
    assert listed.returncode == 0, listed.stdout + listed.stderr
    event = json.loads(listed.stdout)[0]
    assert event['task_id'] == task_id
    reopened = _cli(tasks.db, evidence.root, 'inspect-completion', event['event_id'])
    assert reopened.returncode == 0, reopened.stdout + reopened.stderr
    assert json.loads(reopened.stdout) == event
    reconciled = _cli(tasks.db, evidence.root, 'reconcile-completions')
    assert reconciled.returncode == 0, reconciled.stdout + reconciled.stderr
    assert json.loads(reconciled.stdout) == {'created_events': 0}
    assert CompletionInbox(tasks.db).list(HUMAN) == [event]
    foreign = _cli(tasks.db, evidence.root, 'list-inbox', '--workspace-id', 'foreign')
    assert foreign.returncode == 0, foreign.stdout + foreign.stderr
    assert json.loads(foreign.stdout) == []


@pytest.mark.parametrize(('mode', 'outcome', 'message', 'published', 'remaining'), [
    ('usable', 'usable_update', 'Usable update completed. Published members: 1; currently available: 1. Remaining inputs: 0.', 1, 0),
    ('partial', 'partial_update', 'Partial update completed. Published members: 1; currently available: 1. Remaining inputs: 1. Failure: ingestion / normalization_failed.', 1, 1),
    ('empty', 'no_usable_update', 'No usable update. No new publication. Remaining inputs: 0.', 0, 0),
    ('failed', 'failure', 'Task failed. No new publication. Remaining inputs: 1. Failure: ingestion / normalization_failed.', 0, 1),
])
def test_completion_messages_distinguish_actual_terminal_outcomes(stack, tmp_path, mode, outcome, message, published, remaining):
    import json

    from smi_tasks import CompletionInbox

    options = {'items': []} if mode == 'empty' else {'payload': {'account': {'id': 17}}} if mode == 'failed' else {}
    if mode == 'partial':
        (tmp_path / 'invalid.json').write_text(json.dumps({'account': {'id': 17}}))
        options['items'] = [{'path': 'account.json', 'reference': 'synthetic://valid'},
                            {'path': 'invalid.json', 'reference': 'synthetic://invalid'}]
    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, **options)
    task_id = submit(tasks, campaign)['task_id']
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    event = CompletionInbox(tasks.db).list(HUMAN)[0]
    assert event['outcome'] == outcome == completed['outcome']
    assert event['message'] == message
    assert event['coverage']['published_members'] == published
    assert event['coverage']['remaining_inputs'] == remaining
    assert [p['publication_id'] for p in event['publications']] == completed['publication_ids']
    assert event['failure'] == completed['failure']


def test_completion_transaction_fences_event_and_outcome_together_under_concurrent_handoff(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from smi_tasks import CompletionInbox, TaskExecutionLost

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    entered, release = Event(), Event()
    executions = []

    def before_commit(phase):
        if phase == 'completion':
            entered.set()
            assert release.wait(10)

    worker = OfflineTaskWorker(tasks.db, evidence.root, on_execution=executions.append, before_commit=before_commit)
    with ThreadPoolExecutor(max_workers=3) as executor:
        stale = executor.submit(worker.run_one, task_id, WORKER)
        try:
            assert entered.wait(5)
            assert tasks.read(task_id, HUMAN)['outcome'] is None
            assert CompletionInbox(tasks.db).list(HUMAN) == []
            executions[0].disconnect()
            recovered = executor.submit(OfflineTaskWorker(tasks.db, evidence.root).run_one, task_id, WORKER).result(timeout=5)
            assert recovered['outcome'] == 'usable_update'
        finally:
            release.set()
        with pytest.raises(TaskExecutionLost):
            stale.result(timeout=5)
    inbox = CompletionInbox(tasks.db)
    original = inbox.list(HUMAN)
    assert len(original) == 1
    with ThreadPoolExecutor(max_workers=4) as executor:
        deliveries = list(executor.map(lambda _: OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER), range(4)))
        reconciliations = list(executor.map(lambda _: CompletionInbox(tasks.db).reconcile(HUMAN), range(4)))
    assert all(task == recovered for task in deliveries)
    assert reconciliations == [{'created_events': 0}] * 4
    assert CompletionInbox(tasks.db).list(HUMAN) == original


def test_upgrade_and_concurrent_reconciliation_backfill_old_outcomes_once(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_tasks import AcquisitionTasks, CompletionInbox

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    queued_id = submit(tasks, campaign, request_id='queued')['task_id']
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    # Restore the pre-inbox schema as upgrade input, without asserting on tables.
    with tasks.db.connect() as connection:
        connection.execute('DROP TABLE campaign_regeneration_requests')
        connection.execute('DROP TABLE task_completion_events')
    tasks.migrate()
    upgraded = CompletionInbox(tasks.db).list(HUMAN)
    assert len(upgraded) == 1
    assert upgraded[0]['task_id'] == task_id
    assert upgraded[0]['created_at'] == completed['finished_at']
    tasks.migrate()
    assert CompletionInbox(tasks.db).list(HUMAN) == upgraded
    assert AcquisitionTasks(tasks.db).read(task_id, HUMAN) == completed
    assert tasks.read(queued_id, HUMAN)['outcome'] is None
    # A legacy writer may still have committed an outcome after migration.
    with tasks.db.connect() as connection:
        connection.execute('DELETE FROM task_completion_events')
    with ThreadPoolExecutor(max_workers=4) as executor:
        reconciled = list(executor.map(lambda _: CompletionInbox(tasks.db).reconcile(HUMAN), range(4)))
    assert sorted(r['created_events'] for r in reconciled) == [0, 0, 0, 1]
    events = CompletionInbox(tasks.db).list(HUMAN)
    assert len(events) == 1
    assert events[0]['task_id'] == task_id
    assert tasks.read(task_id, HUMAN) == completed
    foreign = ActorContext('foreign', 'reader', 'human')
    assert CompletionInbox(tasks.db, 'foreign').list(foreign) == []
    assert CompletionInbox(tasks.db, 'foreign').reconcile(foreign) == {'created_events': 0}
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        CompletionInbox(tasks.db).list(foreign)
    with pytest.raises(EvidenceError, match='completion_event_not_found'):
        CompletionInbox(tasks.db, 'foreign').read(events[0]['event_id'], foreign)


def test_collection_failure_notification_reports_requested_remainder_without_source_wording(stack, tmp_path):
    from smi_tasks import CompletionInbox

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    manifest.write_text(manifest.read_text() + '\n')
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    event = CompletionInbox(tasks.db).list(HUMAN)[0]
    assert completed['outcome'] == event['outcome'] == 'failure'
    assert event['coverage']['requested_inputs'] == 1
    assert event['coverage']['remaining_inputs'] == 1
    assert event['message'] == 'Task failed. No new publication. Remaining inputs: 1. Failure: collection / input_changed.'


@pytest.mark.parametrize('boundary', ['before_commit', 'after_commit'])
def test_process_death_at_completion_boundary_preserves_one_deliverable_event(stack, tmp_path, boundary):
    import subprocess
    import sys

    from smi_tasks import CompletionInbox

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    code = '''
import os, sys
from pathlib import Path
from smi_ingestion.db import Database
from smi_ingestion.evidence_sets import ActorContext
from smi_tasks import OfflineTaskWorker
def before_commit(phase):
    if sys.argv[5] == 'before_commit' and phase == 'completion':
        os._exit(23)
def progress(task):
    if sys.argv[5] == 'after_commit' and task['outcome'] is not None:
        os._exit(23)
OfflineTaskWorker(Database(sys.argv[1], sys.argv[2]), Path(sys.argv[3]),
    before_commit=before_commit, on_progress=progress).run_one(
    sys.argv[4], ActorContext('local', 'crashed-completion-worker', 'automation'))
'''
    process = subprocess.run([sys.executable, '-c', code, tasks.db.dsn, tasks.db.schema, str(evidence.root), task_id, boundary],
                             capture_output=True, text=True, timeout=10, check=False)
    assert process.returncode == 23, process.stdout + process.stderr
    inbox = CompletionInbox(tasks.db)
    before = inbox.list(HUMAN)
    if boundary == 'before_commit':
        assert tasks.read(task_id, HUMAN)['outcome'] is None
        assert before == []
    else:
        assert tasks.read(task_id, HUMAN)['outcome'] == 'usable_update'
        assert len(before) == 1
    (tmp_path / 'account.json').unlink()
    manifest.unlink()
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    events = CompletionInbox(tasks.db).list(HUMAN)
    assert len(events) == 1
    assert events[0]['task_id'] == task_id
    assert events[0]['coverage']['published_members'] == 1
    assert events[0]['publications'][0]['publication_id'] == completed['publication_ids'][0]
    assert completed['attempts'][0]['producer']['actor_id'] == 'crashed-completion-worker'
    if boundary == 'after_commit':
        assert events == before


def test_inbox_obeys_display_denial_without_copying_restricted_source_support(stack, tmp_path):
    from smi_tasks import CompletionInbox

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, policy={
        'context_id': 'process-only', 'can_process': True, 'can_retain': True, 'can_display': False,
    }, payload={'account': {'id': 'process-only-id', 'handle': 'restricted-source-wording'}})
    task_id = submit(tasks, campaign)['task_id']
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    event = CompletionInbox(tasks.db).list(HUMAN)[0]
    assert event['outcome'] == completed['outcome'] == 'usable_update'
    assert event['coverage']['published_members'] == 1
    assert event['current_coverage'] == {'available_members': 0, 'unavailable_members': 1}
    assert event['publications'][0]['href'] is None
    assert 'restricted-source-wording' not in str(event)
    assert 'process-only-id' not in str(event)
    assert 'synthetic://' not in str(event)
