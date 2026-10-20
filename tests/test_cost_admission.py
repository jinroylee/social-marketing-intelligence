"""Shared synthetic monetary allowance through public operations and workers."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

import pytest

from smi_tasks import OfflineTaskWorker
from test_costs import accounting, START, END
from test_tasks import HUMAN, WORKER, setup_task, submit


def ceiling(costs, value):
    return costs.configure_ceiling('fixture-oct', HUMAN, amount=value, currency='USD',
                                   period_start=START, period_end=END)


def test_exact_allowance_is_spent_once_and_exhaustion_prevents_transport(stack, tmp_path):
    from smi_costs import SyntheticOperationAdapter, SyntheticResult

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.125')
    calls = []

    def transport(bound):
        calls.append(bound)
        return SyntheticResult('synthetic-result', '1')

    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')
    first = adapter.execute(WORKER, request_id='first', method='fake-v1', call=transport)
    assert first['status'] == 'executed'
    assert first['value'] == 'synthetic-result'
    assert first['allowance']['actual_amount'] == '0.125'
    assert first['allowance']['outstanding_amount'] == '0'
    duplicate = adapter.execute(WORKER, request_id='first', method='fake-v1', call=transport)
    assert duplicate['status'] == 'paused'
    assert duplicate['reason'] == 'cost_operation_already_executed'
    refused = adapter.execute(WORKER, request_id='second', method='fake-v1', call=transport)
    assert refused['status'] == 'refused'
    assert refused['reason'] == 'cost_allowance_exhausted'
    assert calls == ['1']
    assert costs.read(first['operation_id'], HUMAN)['actuals']['amount'] == '0.125'


def test_competing_operations_share_outstanding_reservation_before_either_response(stack, tmp_path):
    from smi_costs import SyntheticOperationAdapter, SyntheticResult

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.125')
    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')
    entered, release = Event(), Event()
    calls, lock = [], Lock()

    def transport(bound):
        with lock:
            calls.append(bound)
        entered.set()
        assert release.wait(10)
        return SyntheticResult(None, '1')

    with ThreadPoolExecutor(max_workers=3) as executor:
        first = executor.submit(adapter.execute, WORKER, request_id='first', method='fake-v1', call=transport)
        try:
            assert entered.wait(5)
            assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.125'
            results = list(executor.map(lambda request: adapter.execute(WORKER, request_id=request, method='fake-v1', call=transport),
                                        ['first', 'competitor']))
            assert [r['status'] for r in results] == ['paused', 'refused']
            assert calls == ['1']
        finally:
            release.set()
        assert first.result(5)['status'] == 'executed'
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.125'
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0'


def test_admission_exposes_controls_and_includes_older_actual_and_declared_commitments(stack, tmp_path):
    from smi_costs import SyntheticOperationAdapter, SyntheticResult
    from test_costs import MEASURED

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')
    calls = []

    def transport(bound):
        calls.append(bound)
        return SyntheticResult(None, '1')

    assert adapter.execute(WORKER, request_id='missing', method='v1', call=transport)['reason'] == 'cost_control_missing'
    costs.configure_ceiling('fixture-oct', HUMAN, amount='1', currency='USD', period_start=START, period_end=END, paused=True)
    assert adapter.execute(WORKER, request_id='paused', method='v1', call=transport)['reason'] == 'cost_scope_paused'
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='old', method='v1')['operation_id']
    costs.record_usage(oid, WORKER, measurement_id='prior-usage', units='2', rate_version='synthetic-v1', measured_at=MEASURED, provenance='fake-counter')
    costs.record_commitment(oid, WORKER, measurement_id='legacy-declaration', amount='0.625', currency='USD', measured_at=MEASURED, provenance='fake-declaration')
    for i in range(101):
        costs.begin_operation('fixture-oct', WORKER, request_id=f'new-{i}', method='v1')
    assert oid not in [o['operation_id'] for o in costs.list(HUMAN)]
    ceiling(costs, '1')
    exact = adapter.execute(WORKER, request_id='exact', method='v1', call=transport)
    assert exact['status'] == 'executed'
    assert exact['allowance']['actual_amount'] == '0.375'
    assert exact['allowance']['outstanding_amount'] == '0.625'
    assert adapter.execute(WORKER, request_id='exhausted', method='v1', call=transport)['reason'] == 'cost_allowance_exhausted'
    assert calls == ['1']


def test_meter_failure_blocks_new_dispatch_even_after_late_usage_and_ceiling_increase(stack, tmp_path):
    from smi_costs import SyntheticOperationAdapter
    from test_costs import MEASURED

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='uncertain', method='v1')['operation_id']
    costs.record_uncertainty(oid, WORKER, measurement_id='unknown', state='meter_failure', measured_at=MEASURED,
                             provenance='fake-meter', reason='meter_unavailable')
    costs.record_usage(oid, WORKER, measurement_id='late', units='1', rate_version='synthetic-v1', measured_at=MEASURED, provenance='late-meter')
    ceiling(costs, '100')
    calls = []
    result = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1').execute(
        WORKER, request_id='blocked', method='v1', call=lambda bound: calls.append(bound))
    assert result['reason'] == 'cost_coverage_unavailable'
    assert calls == []


def test_campaign_and_approved_assistant_workers_share_guard_and_http_reason(stack, tmp_path):
    from smi_costs import UsageAccounting
    from smi_ingestion.adapters.local import LocalFileCollector
    from smi_review import ReviewApp
    from smi_tasks import EnrichmentProposal
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    campaign_id = submit(tasks, campaign)['task_id']
    proposal = tasks.save_proposal(EnrichmentProposal('Fill exact account', 'fill', subject_ids=('account-1',)), WORKER, request_id='proposal')
    reviewed = tasks.read_proposal(proposal['proposal_id'], HUMAN)
    approval = tasks.approve_proposal(proposal['proposal_id'], HUMAN, scope_digest=reviewed['scope_digest'], request_id='approval')
    assistant_id = tasks.submit_approved(proposal['proposal_id'], WORKER, approval_id=approval['approval_id'],
                                         scope_digest=reviewed['scope_digest'], request_id='assistant')['task_id']
    calls = []

    class FakeService:
        def collect(self, *args):
            calls.append('chargeable')
            return LocalFileCollector('fixture-json').collect(*args)

    completed = OfflineTaskWorker(tasks.db, evidence.root, collector=FakeService()).run_one(campaign_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    refused = OfflineTaskWorker(tasks.db, evidence.root, collector=FakeService()).run_one(assistant_id, WORKER)
    assert refused['outcome'] is None
    assert refused['status'] == 'waiting'
    assert refused['progress']['reason'] == 'cost_allowance_exhausted'
    assert refused['progress']['resumable'] is True
    assert calls == ['chargeable']
    assert OfflineTaskWorker(tasks.db, evidence.root, collector=FakeService()).run_one(assistant_id, WORKER)['status'] == 'waiting'
    assert calls == ['chargeable']
    operations = UsageAccounting(tasks.db).list(HUMAN, task_id=campaign_id)
    assert len(operations) == 1
    assert operations[0]['attempt_id'] == completed['attempts'][0]['attempt_id']
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path=f'/tasks/{assistant_id}')
        assert status == 200 and 'cost_allowance_exhausted' in page
        status, _, page = request(url, path=f'/costs/{operations[0]["operation_id"]}')
        assert status == 200 and 'Enforced synthetic monetary ceiling' in page
        assert '0.125 USD' in page


def test_lost_worker_response_retains_commitment_and_successor_never_reissues(stack, tmp_path):
    import pytest
    from smi_tasks import TaskExecutionLost
    from smi_ingestion.adapters.local import LocalFileCollector

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    task_id = submit(tasks, campaign)['task_id']
    entered, release = Event(), Event()
    executions, calls = [], []

    class LateService:
        def collect(self, *args):
            calls.append('chargeable')
            entered.set()
            assert release.wait(10)
            return LocalFileCollector('fixture-json').collect(*args)

    with ThreadPoolExecutor(max_workers=2) as executor:
        stale = executor.submit(OfflineTaskWorker(tasks.db, evidence.root, collector=LateService(), on_execution=executions.append).run_one,
                                task_id, WORKER)
        try:
            assert entered.wait(5)
            executions[0].disconnect()
            successor = executor.submit(OfflineTaskWorker(tasks.db, evidence.root, collector=LateService()).run_one, task_id, WORKER).result(5)
            assert successor['status'] == 'waiting'
            assert successor['progress']['reason'] == 'cost_operation_in_flight_or_uncertain'
            assert successor['progress']['resumable'] is False
            assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.125'
        finally:
            release.set()
        with pytest.raises(TaskExecutionLost):
            stale.result(5)
    assert calls == ['chargeable']
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0'
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.125'
    assert OfflineTaskWorker(tasks.db, evidence.root, collector=LateService()).run_one(task_id, WORKER)['status'] == 'waiting'
    assert calls == ['chargeable']


def test_forecast_worker_stops_at_independent_request_record_and_byte_bounds(stack, tmp_path):
    from smi_costs import CostScope
    from smi_tasks import AcquisitionTasks, OfflineRoute
    from smi_ingestion.contracts import RunLimits, CollectedBatch
    from smi_ingestion.adapters.local import LocalFileCollector

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_scope(CostScope('forecast', 'synthetic-local', 'forecast-fixture', 'forecast_only', 'USD', START, END), HUMAN)
    costs.configure_route('fixture-json', 'forecast', HUMAN, max_units='1')
    calls = []

    class PendingService:
        def collect(self, manifest, checkpoint, limits):
            calls.append(limits.max_requests)
            return CollectedBatch((), {'poll': 1}, False, waiting='provider_pending', request_attempts=1)

    bounded = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(max_requests=1)), authority=tasks.authority)
    task_id = submit(bounded, campaign)['task_id']
    assert OfflineTaskWorker(tasks.db, evidence.root, collector=PendingService()).run_one(task_id, WORKER)['status'] == 'waiting'
    result = OfflineTaskWorker(tasks.db, evidence.root, collector=PendingService()).run_one(task_id, WORKER)
    assert result['outcome'] == 'failure'
    assert result['failure']['code'] == 'request_limit_reached'
    assert calls == [1]
    operation = costs.list(HUMAN, task_id=task_id)[0]
    assert operation['actuals']['amount'] is None
    assert operation['enforced_monetary_control'] is False

    class FixtureService:
        def collect(self, *args):
            calls.append('fixture')
            return LocalFileCollector('fixture-json').collect(*args)

    import json
    body = json.loads(manifest.read_text())
    body['items'] *= 2
    manifest.write_text(json.dumps(body))
    bounded = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(max_records=1)), authority=tasks.authority)
    result = OfflineTaskWorker(tasks.db, evidence.root, collector=FixtureService()).run_one(submit(bounded, campaign, request_id='record')['task_id'], WORKER)
    assert result['failure']['code'] == 'record_limit_reached'
    assert result['coverage']['collected_observations'] == 1
    bounded = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(max_bytes=1)), authority=tasks.authority)
    result = OfflineTaskWorker(tasks.db, evidence.root, collector=FixtureService()).run_one(submit(bounded, campaign, request_id='byte')['task_id'], WORKER)
    assert result['failure']['code'] == 'byte_limit_reached'
    assert result['coverage']['collected_observations'] == 0
    assert calls == [1, 'fixture', 'fixture']


def _worker_process(dsn, schema, root, task_id, entered, release, calls, results):
    """Real separate worker process with a counted bounded external-service fake."""
    from pathlib import Path
    from smi_ingestion.db import Database
    from smi_ingestion.adapters.local import LocalFileCollector

    class Service:
        def collect(self, *args):
            calls.put('chargeable')
            entered.set()
            if not release.wait(15):
                raise RuntimeError('fake_service_timeout')
            return LocalFileCollector('fixture-json').collect(*args)

    result = OfflineTaskWorker(Database(dsn, schema), Path(root), collector=Service()).run_one(task_id, WORKER)
    results.put(result)


def test_distinct_worker_processes_compete_for_one_scope_before_external_call(stack, tmp_path):
    import multiprocessing
    import queue

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    ids = [submit(tasks, campaign, request_id=f'process-{i}')['task_id'] for i in range(2)]
    ctx = multiprocessing.get_context('spawn')
    entered, release = ctx.Event(), ctx.Event()
    calls, results = ctx.Queue(), ctx.Queue()
    processes = [ctx.Process(target=_worker_process, args=(tasks.db.dsn, tasks.db.schema, str(evidence.root), task_id,
                                                          entered, release, calls, results)) for task_id in ids]
    try:
        processes[0].start()
        assert entered.wait(10)
        processes[1].start()
        refused = results.get(timeout=10)
        assert refused['task_id'] == ids[1]
        assert refused['progress']['reason'] == 'cost_allowance_exhausted'
        assert refused['outcome'] is None
        assert calls.get(timeout=5) == 'chargeable'
        with pytest.raises(queue.Empty):
            calls.get(timeout=0.1)
        release.set()
        assert results.get(timeout=10)['outcome'] == 'usable_update'
    finally:
        release.set()
        for process in processes:
            if process.pid:
                process.join(10)
                if process.is_alive():
                    process.terminate()
                    process.join(5)
    assert [p.exitcode for p in processes] == [0, 0]
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.125'
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0'


def test_missing_control_then_pause_and_resume_preserves_task_authority(stack, tmp_path):
    from smi_ingestion.adapters.local import LocalFileCollector

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units='1')
    task_id = submit(tasks, campaign)['task_id']
    calls = []

    class Service:
        def collect(self, *args):
            calls.append('chargeable')
            return LocalFileCollector('fixture-json').collect(*args)

    worker = OfflineTaskWorker(tasks.db, evidence.root, collector=Service())
    missing = worker.run_one(task_id, WORKER)
    assert missing['progress']['reason'] == 'cost_control_missing'
    costs.configure_ceiling('fixture-oct', HUMAN, amount='0.125', currency='USD', period_start=START, period_end=END, paused=True)
    assert worker.run_one(task_id, WORKER)['progress']['reason'] == 'cost_scope_paused'
    assert calls == []
    ceiling(costs, '0.125')
    finished = worker.run_one(task_id, WORKER)
    assert finished['outcome'] == 'usable_update'
    assert finished['scope'] == missing['scope']
    assert finished['initiator'] == missing['initiator']
    assert finished['attempts'][0]['attempt_id'] == missing['attempts'][0]['attempt_id']
    assert calls == ['chargeable']


def test_lost_settlement_and_post_settlement_evidence_loss_never_repeat_a_charge(stack, tmp_path):
    import pytest
    from smi_tasks import TaskExecutionLost
    from smi_ingestion.adapters.local import LocalFileCollector

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '1')
    calls = []

    class Service:
        def collect(self, *args):
            calls.append('chargeable')
            return LocalFileCollector('fixture-json').collect(*args)

    for phase in ('cost_dispatch', 'cost_settlement', 'evidence'):
        task_id = submit(tasks, campaign, request_id=phase)['task_id']
        executions = []

        def before_commit(current):
            if current == phase:
                executions[0].disconnect()

        with pytest.raises(TaskExecutionLost):
            OfflineTaskWorker(tasks.db, evidence.root, collector=Service(), on_execution=executions.append,
                              before_commit=before_commit).run_one(task_id, WORKER)
        after_loss = len(calls)
        successor = OfflineTaskWorker(tasks.db, evidence.root, collector=Service()).run_one(task_id, WORKER)
        if phase == 'cost_dispatch':
            assert len(calls) == after_loss + 1
            assert successor['outcome'] == 'usable_update'
        else:
            assert len(calls) == after_loss
            assert successor['status'] == 'waiting'
            assert successor['progress']['reason'] == ('cost_operation_in_flight_or_uncertain' if phase == 'cost_settlement'
                                                       else 'cost_operation_already_executed')
    allowance = costs.allowance('fixture-oct', HUMAN)
    assert calls == ['chargeable', 'chargeable', 'chargeable']
    assert allowance['actual_amount'] == '0.25'
    assert allowance['outstanding_amount'] == '0.125'


def test_control_configuration_requires_human_exact_currency_period_and_finite_amount(stack, tmp_path):
    import pytest
    from smi_costs import CostScope, SyntheticOperationAdapter
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        costs.configure_ceiling('fixture-oct', WORKER, amount='1', currency='USD', period_start=START, period_end=END)
    for change in ({'currency': 'KRW'}, {'period_start': '2026-10-02T00:00:00Z'}, {'period_end': '2026-11-02T00:00:00Z'}):
        with pytest.raises(EvidenceError, match='cost_ceiling_scope_mismatch'):
            costs.configure_ceiling('fixture-oct', HUMAN, **({'amount': '1', 'currency': 'USD', 'period_start': START, 'period_end': END} | change))
    for value in ('NaN', 'Infinity', '-1', 0.1, True, '0.0000000000001'):
        with pytest.raises(EvidenceError, match='invalid_cost_decimal'):
            ceiling(costs, value)
    assert costs.allowance('fixture-oct', HUMAN)['ceiling_amount'] is None
    costs.configure_scope(CostScope('past', 'synthetic-local', 'past-meter', 'metered', 'USD',
                                    '2000-01-01T00:00:00Z', '2000-02-01T00:00:00Z',
                                    unit='request', unit_rate='1', rate_version='v1'), HUMAN)
    calls = []
    result = SyntheticOperationAdapter(costs, 'past', max_units='1').execute(WORKER, request_id='past', method='v1', call=calls.append)
    assert result['reason'] == 'cost_accounting_period_inactive'
    assert calls == []


def test_concurrent_independent_ledger_writes_reduce_allowance_while_transport_is_in_flight(stack, tmp_path):
    from threading import Barrier
    from smi_costs import SyntheticOperationAdapter, SyntheticResult
    from test_costs import MEASURED

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.5')
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='independent-ledger', method='counter-v1')['operation_id']
    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')
    entered, release = Event(), Event()
    writes = Barrier(2)
    calls = []

    def transport(bound):
        calls.append(bound)
        entered.set()
        assert release.wait(10)
        return SyntheticResult(None, '1')

    def actual():
        writes.wait(5)
        return costs.record_usage(oid, WORKER, measurement_id='concurrent-actual', units='2', rate_version='synthetic-v1',
                                  measured_at=MEASURED, provenance='independent-counter')

    def commitment():
        writes.wait(5)
        return costs.record_commitment(oid, WORKER, measurement_id='concurrent-declaration', amount='0.125', currency='USD',
                                       measured_at=MEASURED, provenance='independent-declaration')

    with ThreadPoolExecutor(max_workers=3) as executor:
        first = executor.submit(adapter.execute, WORKER, request_id='in-flight', method='v1', call=transport)
        try:
            assert entered.wait(5)
            actual_write, commitment_write = executor.submit(actual), executor.submit(commitment)
            assert actual_write.result(5)['status'] == 'recorded'
            assert commitment_write.result(5)['status'] == 'recorded'
            assert costs.allowance('fixture-oct', HUMAN)['available_amount'] == '0'
            refused = adapter.execute(WORKER, request_id='no-stale-total', method='v1', call=transport)
            assert refused['reason'] == 'cost_allowance_exhausted'
            assert calls == ['1']
        finally:
            release.set()
        assert first.result(5)['status'] == 'executed'
    final = costs.allowance('fixture-oct', HUMAN)
    assert final['actual_amount'] == '0.375'
    assert final['outstanding_amount'] == '0.125'
    assert final['available_amount'] == '0'


def test_bounded_settlement_releases_only_unused_reservation_once(stack, tmp_path):
    from smi_costs import SyntheticOperationAdapter, SyntheticResult
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    calls = []

    def transport(bound):
        calls.append(bound)
        return SyntheticResult(None, '1')

    wide = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='2')
    narrow = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')
    settled = wide.execute(WORKER, request_id='wide', method='v1', call=transport)
    assert settled['allowance']['actual_amount'] == '0.125'
    assert settled['allowance']['outstanding_amount'] == '0'
    assert settled['allowance']['available_amount'] == '0.125'
    assert wide.execute(WORKER, request_id='wide', method='v1', call=transport)['reason'] == 'cost_operation_already_executed'
    with pytest.raises(EvidenceError, match='cost_admission_conflict'):
        narrow.execute(WORKER, request_id='wide', method='v1', call=transport)
    assert narrow.execute(WORKER, request_id='narrow', method='v1', call=transport)['status'] == 'executed'
    assert narrow.execute(WORKER, request_id='exhausted', method='v1', call=transport)['reason'] == 'cost_allowance_exhausted'
    assert calls == ['2', '1']
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.25'
    assert costs.allowance('fixture-oct', HUMAN)['available_amount'] == '0'


def test_broken_synthetic_meter_contract_blocks_further_scope_dispatch(stack, tmp_path):
    from smi_costs import SyntheticOperationAdapter, SyntheticResult
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '1')
    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')
    calls = []

    def broken(bound):
        calls.append(bound)
        return SyntheticResult(None, '2')

    with pytest.raises(EvidenceError, match='synthetic_service_bound_violated'):
        adapter.execute(WORKER, request_id='broken', method='v1', call=broken)
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.125'
    assert costs.allowance('fixture-oct', HUMAN)['blocked_reason'] == 'cost_coverage_unavailable'
    result = adapter.execute(WORKER, request_id='next', method='v1', call=broken)
    assert result['reason'] == 'cost_coverage_unavailable'
    assert calls == ['1']
