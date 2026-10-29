"""Final synthetic billing and explicit meter recovery through public boundaries."""

import pytest

from smi_costs import SyntheticOperationAdapter, SyntheticResult, UsageAccounting
from smi_ingestion.evidence import EvidenceError
from test_cost_admission import ceiling
from test_costs import accounting, MEASURED
from test_tasks import HUMAN, WORKER, setup_task


RECONCILED = '2026-11-04T12:00:00Z'


def final_usage(costs, oid, *, reconciliation_id='final-1', measurement_id='bill-1', units='1',
                settle_admission=True, commitment_ids=(), uncertainty_ids=(), outcome='succeeded', actor=HUMAN, **changes):
    return costs.reconcile_usage(oid, actor, **(dict(
        reconciliation_id=reconciliation_id, measurement_id=measurement_id, units=units,
        rate_version='synthetic-v1', measured_at=MEASURED, provenance='simulated-final-meter-v1',
        reconciled_at=RECONCILED, evidence_id='simulated-final-report-1', outcome=outcome,
        settle_admission=settle_admission, commitment_ids=commitment_ids, uncertainty_ids=uncertainty_ids) | changes))


def lost_call(costs, request_id='lost'):
    calls = []

    def transport(bound):
        calls.append(bound)
        raise ConnectionError('simulated_response_loss')

    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='2')
    with pytest.raises(ConnectionError):
        adapter.execute(WORKER, request_id=request_id, method='fake-v1', call=transport)
    oid = costs.list(HUMAN)[0]['operation_id']
    return adapter, oid, calls


def test_late_final_usage_settles_only_its_reservation_and_replay_never_reissues(stack, tmp_path):
    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    adapter, oid, calls = lost_call(costs)
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.25'
    assert final_usage(costs, oid)['status'] == 'recorded'
    restarted = UsageAccounting(tasks.db)
    restarted.migrate()
    assert final_usage(restarted, oid)['status'] == 'duplicate'
    view = restarted.read(oid, HUMAN)
    assert view['actuals']['amount'] == '0.125'
    assert view['allowance']['outstanding_amount'] == '0'
    assert view['allowance']['available_amount'] == '0.125'
    assert len(view['entries']) == len(view['reconciliations']) == 1
    assert view['reconciliations'][0]['evidence_id'] == 'simulated-final-report-1'
    assert view['reconciliations'][0]['operator']['actor_id'] == HUMAN.actor_id
    assert adapter.execute(WORKER, request_id='lost', method='fake-v1', call=calls.append)['reason'] == 'cost_operation_already_executed'
    assert calls == ['2']


def test_final_report_resolves_named_declarations_and_unknown_without_erasing_or_recounting(stack, tmp_path):
    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '1')
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='declared', method='fake-v1')['operation_id']
    for mid, value in (('part-a', '0.5'), ('part-b', '0.25')):
        costs.record_commitment(oid, WORKER, measurement_id=mid, amount=value, currency='USD',
                                measured_at=MEASURED, provenance='simulated-declaration')
    costs.record_uncertainty(oid, WORKER, measurement_id='unknown-a', state='unknown', measured_at=MEASURED,
                             provenance='simulated-pending', reason='billing_delayed')
    costs.record_usage(oid, WORKER, measurement_id='bill-1', units='2', rate_version='synthetic-v1',
                       measured_at=MEASURED, provenance='simulated-final-meter-v1')
    final_usage(costs, oid, units='2', settle_admission=False, commitment_ids=('part-a',), uncertainty_ids=('unknown-a',))
    view = costs.read(oid, HUMAN)
    assert view['actuals']['amount'] == '0.25'
    assert view['commitments']['amount'] == '0.25'
    assert view['allowance']['outstanding_amount'] == '0.25'
    assert len(view['entries']) == 4
    assert view['entries'][-1]['recorder']['actor_id'] == WORKER.actor_id
    assert view['coverage']['unknown_cost'] is True
    assert view['unresolved']['commitment_ids'] == ['part-b']
    assert view['unresolved']['uncertainty_ids'] == []
    with pytest.raises(EvidenceError, match='cost_reconciliation_conflict'):
        final_usage(costs, oid, reconciliation_id='same-bill-again', units='2', settle_admission=False, commitment_ids=('part-b',))
    with pytest.raises(EvidenceError, match='cost_reconciliation_target_not_outstanding'):
        final_usage(costs, oid, reconciliation_id='conflicting-final', measurement_id='different-bill', units='3',
                    settle_admission=False, commitment_ids=('part-a',))
    assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.25'
    final_usage(costs, oid, reconciliation_id='final-b', measurement_id='bill-b', units='1', settle_admission=False,
                commitment_ids=('part-b',), evidence_id='simulated-final-report-b')
    assert costs.read(oid, HUMAN)['coverage'] == {'status': 'synthetic_measured', 'unknown_cost': False}
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.375'
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0'


def recover(costs, oid, *, recovery_id='health-1', failure_ids=(), **changes):
    return costs.recover_meter(oid, HUMAN, **(dict(recovery_id=recovery_id, failure_ids=failure_ids,
        recovered_at='2026-11-05T12:00:00Z', provenance='simulated-health-check-v1', evidence_id='health-report-1') | changes))


def test_failed_meter_requires_final_accounting_and_attributed_recovery_even_over_ceiling(stack, tmp_path):
    from datetime import datetime, timedelta

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    calls = []
    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1')

    def broken(bound):
        calls.append(bound)
        return SyntheticResult(None, '8')

    with pytest.raises(EvidenceError, match='synthetic_service_bound_violated'):
        adapter.execute(WORKER, request_id='broken', method='v1', call=broken)
    oid = costs.list(HUMAN)[0]['operation_id']
    failure = costs.read(oid, HUMAN)['entries'][0]
    failure_id = failure['measurement_id']
    # This entry is generated at dispatch time, unlike the historical reports in
    # the other cases. Pin later attestations once so exact retries stay exact.
    failure_at = datetime.fromisoformat(failure['measured_at'])
    reconciled_at = (failure_at + timedelta(seconds=1)).isoformat()
    recovered_at = (failure_at + timedelta(seconds=2)).isoformat()
    with pytest.raises(EvidenceError, match='cost_meter_failure_unreconciled'):
        recover(costs, oid, failure_ids=(failure_id,), recovered_at=recovered_at)
    final_usage(costs, oid, units='8', uncertainty_ids=(failure_id,), outcome='failed', reconciled_at=reconciled_at)
    view = costs.read(oid, HUMAN)
    assert view['actuals']['amount'] == '1'
    assert view['allowance']['outstanding_amount'] == '0'
    assert view['allowance']['over_ceiling_amount'] == '0.75'
    assert view['coverage']['status'] == 'meter_failure'
    assert view['limits']['billing_state'] == 'final_measurement_recorded'
    assert view['limits']['bound_status'] == 'violated'
    assert adapter.execute(WORKER, request_id='blocked', method='v1', call=broken)['reason'] == 'cost_coverage_unavailable'
    all_failures = tuple(view['unresolved']['meter_failure_ids'])
    assert recover(costs, oid, failure_ids=all_failures, recovered_at=recovered_at)['status'] == 'recorded'
    reopened = UsageAccounting(tasks.db)
    assert recover(reopened, oid, failure_ids=all_failures, recovered_at=recovered_at)['status'] == 'duplicate'
    assert reopened.read(oid, HUMAN)['coverage']['unknown_cost'] is False
    assert adapter.execute(WORKER, request_id='still-exhausted', method='v1', call=broken)['reason'] == 'cost_allowance_exhausted'
    ceiling(costs, '2')
    assert adapter.execute(WORKER, request_id='broken', method='v1', call=broken)['reason'] == 'cost_operation_already_executed'
    assert adapter.execute(WORKER, request_id='recovered', method='v1', call=lambda bound: SyntheticResult(None, '1'))['status'] == 'executed'
    assert calls == ['1']
    costs.record_uncertainty(oid, WORKER, measurement_id='new-failure', state='meter_failure', measured_at=MEASURED,
                             provenance='simulated-meter', reason='counter_unavailable_again')
    assert costs.allowance('fixture-oct', HUMAN)['blocked_reason'] == 'cost_coverage_unavailable'
    assert len(costs.read(oid, HUMAN)['meter_recoveries']) == 1


@pytest.mark.parametrize('returned_units', ['1', '2'])
def test_final_report_racing_original_response_never_records_a_second_charge(stack, tmp_path, returned_units):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.5')
    adapter = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='2')
    entered, release = Event(), Event()
    calls = []

    def transport(bound):
        calls.append(bound)
        entered.set()
        assert release.wait(10)
        return SyntheticResult('late-response', returned_units)

    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(adapter.execute, WORKER, request_id='racing-report', method='v1', call=transport)
        try:
            assert entered.wait(5)
            oid = costs.list(HUMAN)[0]['operation_id']
            final_usage(costs, oid)
        finally:
            release.set()
        if returned_units == '1':
            assert pending.result(5)['status'] == 'executed'
        else:
            with pytest.raises(EvidenceError, match='cost_measurement_conflict'):
                pending.result(5)
    view = costs.read(oid, HUMAN)
    assert view['actuals']['amount'] == '0.125'
    assert len(view['entries']) == 1
    assert calls == ['2']


def test_confirmed_uncharged_failure_releases_exact_bound_but_cannot_restart_same_task_call(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker, TaskExecutionLost
    from smi_review import ReviewApp
    from test_review import running, request
    from test_tasks import submit

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    task_id = submit(tasks, campaign)['task_id']
    calls, executions = [], []

    class LostService:
        def collect(self, *args):
            calls.append('attempted')
            executions[0].disconnect()
            raise TaskExecutionLost('simulated_lost_session')

    with pytest.raises(TaskExecutionLost):
        OfflineTaskWorker(tasks.db, evidence.root, collector=LostService(), on_execution=executions.append).run_one(task_id, WORKER)
    oid = costs.list(HUMAN, task_id=task_id)[0]['operation_id']
    final_usage(costs, oid, units='0', outcome='failed', evidence_id='simulated-confirmed-not-billed')
    view = costs.read(oid, HUMAN)
    assert view['actuals']['amount'] == '0'
    assert view['allowance']['available_amount'] == '0.125'
    assert view['limits']['known_charge_bound'] == '0.125'
    assert view['limits']['billing_state'] == 'final_measurement_recorded'
    assert view['limits']['zero_overshoot_guaranteed'] is False
    assert view['limits']['billing_lag_bound'] is None
    resumed = OfflineTaskWorker(tasks.db, evidence.root, collector=LostService()).run_one(task_id, WORKER)
    assert resumed['status'] == 'waiting' and resumed['outcome'] is None
    assert resumed['progress']['reason'] == 'cost_operation_already_executed'
    assert calls == ['attempted']
    with running(ReviewApp(tasks.db)) as url:
        for path in (f'/costs/{oid}', f'/tasks/{task_id}'):
            status, _, page = request(url, path=path)
            assert status == 200
            assert 'final_measurement_recorded' in page
            assert 'Known charge bound: 0.125 USD' in page
            assert 'Billing lag bound: Unknown. Unresolved charges have no automatic expiry.' in page
            assert 'No zero-overshoot guarantee for delayed or unbounded charges.' in page
        page = request(url, path=f'/costs/{oid}')[2]
        assert 'simulated-confirmed-not-billed' in page
        assert 'Synthetic measured amount: 0 USD' in page


def test_concurrent_reconciliation_and_admission_use_one_authoritative_scope_frontier(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    _, oid, old_calls = lost_call(costs)
    barrier, calls = Barrier(3), []

    def resolve():
        barrier.wait(5)
        return final_usage(UsageAccounting(tasks.db), oid)

    def admit():
        barrier.wait(5)
        return SyntheticOperationAdapter(UsageAccounting(tasks.db), 'fixture-oct', max_units='1').execute(
            WORKER, request_id='competitor', method='v1', call=lambda bound: (calls.append(bound), SyntheticResult(None, '1'))[1])

    with ThreadPoolExecutor(max_workers=3) as executor:
        a, b, new = executor.submit(resolve), executor.submit(resolve), executor.submit(admit)
        assert sorted([a.result(10)['status'], b.result(10)['status']]) == ['duplicate', 'recorded']
        assert new.result(10)['status'] in {'executed', 'refused'}
    retry = SyntheticOperationAdapter(costs, 'fixture-oct', max_units='1').execute(
        WORKER, request_id='competitor', method='v1', call=lambda bound: (calls.append(bound), SyntheticResult(None, '1'))[1])
    assert retry['status'] in {'executed', 'paused'}
    assert old_calls == ['2'] and calls == ['1']
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.25'
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0'
    assert costs.allowance('fixture-oct', HUMAN)['available_amount'] == '0'


def test_competing_conflicting_final_reports_preserve_only_the_winner(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    _, oid, calls = lost_call(costs)
    barrier = Barrier(2)

    def resolve(units):
        barrier.wait(5)
        try:
            final_usage(UsageAccounting(tasks.db), oid, reconciliation_id=f'final-{units}', measurement_id=f'bill-{units}', units=units)
            return 'recorded'
        except EvidenceError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(resolve, ['1', '2'])) == ['cost_reconciliation_target_not_outstanding', 'recorded']
    view = costs.read(oid, HUMAN)
    assert len(view['entries']) == len(view['reconciliations']) == 1
    assert view['actuals']['amount'] in {'0.125', '0.25'}
    assert view['allowance']['outstanding_amount'] == '0'
    assert calls == ['2']


def test_final_reconciliation_requires_exact_operator_evidence_targets_and_original_rate_period(stack, tmp_path):
    from test_costs import END

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    _, oid, _ = lost_call(costs)
    cases = [({'outcome': 'ambiguous'}, 'invalid_cost_final_outcome'),
             ({'evidence_id': ''}, 'invalid_cost_evidence_id'),
             ({'settle_admission': False}, 'invalid_cost_reconciliation_targets'),
             ({'settle_admission': 'true'}, 'invalid_cost_reconciliation_targets'),
             ({'units': 'NaN'}, 'invalid_cost_decimal'),
             ({'rate_version': 'new-rate'}, 'cost_rate_version_mismatch'),
             ({'measured_at': END}, 'cost_measurement_outside_period'),
             ({'reconciled_at': '2026-10-19T12:00:00Z'}, 'invalid_cost_reconciliation_time'),
             ({'commitment_ids': ('absent',)}, 'invalid_cost_reconciliation_targets')]
    for changes, error in cases:
        with pytest.raises(EvidenceError, match=error):
            final_usage(costs, oid, **changes)
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        final_usage(costs, oid, actor=WORKER)
    assert costs.read(oid, HUMAN)['actuals']['amount'] is None
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.25'
    final_usage(costs, oid)
    with pytest.raises(EvidenceError, match='cost_measurement_conflict'):
        final_usage(costs, oid, units='2')
    with pytest.raises(EvidenceError, match='cost_reconciliation_conflict'):
        final_usage(costs, oid, evidence_id='different-evidence')
    assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.125'


def test_final_evidence_cannot_predate_the_uncertainty_it_claims_to_resolve(stack, tmp_path):
    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='later-unknown', method='v1')['operation_id']
    costs.record_uncertainty(oid, WORKER, measurement_id='later-unknown', state='unknown',
                             measured_at='2026-10-22T12:00:00Z', provenance='simulated-meter', reason='pending')
    with pytest.raises(EvidenceError, match='invalid_cost_reconciliation_time'):
        final_usage(costs, oid, settle_admission=False, uncertainty_ids=('later-unknown',),
                    reconciled_at='2026-10-20T13:00:00Z')
    assert costs.read(oid, HUMAN)['actuals']['amount'] is None
    assert costs.read(oid, HUMAN)['coverage']['unknown_cost'] is True


def _reconcile_process(dsn, schema, oid, results):
    from smi_ingestion.db import Database
    costs = UsageAccounting(Database(dsn, schema))
    costs.migrate()
    results.put(final_usage(costs, oid))


def test_final_billing_replay_survives_separate_process_restarts(stack, tmp_path):
    import multiprocessing

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    _, oid, calls = lost_call(costs)
    ctx = multiprocessing.get_context('spawn')
    results = ctx.Queue()
    for expected in ('recorded', 'duplicate'):
        process = ctx.Process(target=_reconcile_process, args=(tasks.db.dsn, tasks.db.schema, oid, results))
        try:
            process.start()
            assert results.get(timeout=15)['status'] == expected
            process.join(10)
            assert process.exitcode == 0
        finally:
            if process.is_alive():
                process.terminate()
                process.join(5)
    assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.125'
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0'
    assert calls == ['2']


def test_meter_recovery_rejects_wrong_targets_conflicts_and_untrusted_or_early_attestation(stack, tmp_path):
    from smi_ingestion.evidence_sets import ActorContext

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='failed-health', method='v1')['operation_id']
    costs.record_uncertainty(oid, WORKER, measurement_id='failed-health', state='meter_failure', measured_at=MEASURED,
                             provenance='simulated-meter', reason='counter_unavailable')
    final_usage(costs, oid, settle_admission=False, uncertainty_ids=('failed-health',))
    for failures, error in (((), 'invalid_cost_recovery_targets'), (('absent',), 'invalid_cost_recovery_targets'),
                             (('bill-1',), 'invalid_cost_recovery_targets')):
        with pytest.raises(EvidenceError, match=error):
            recover(costs, oid, failure_ids=failures)
    with pytest.raises(EvidenceError, match='invalid_cost_recovery_time'):
        recover(costs, oid, failure_ids=('failed-health',), recovered_at='2026-11-03T00:00:00Z')
    for actor in (WORKER, ActorContext('foreign', 'operator', 'human')):
        with pytest.raises(EvidenceError, match='workspace_access_denied'):
            costs.recover_meter(oid, actor, recovery_id='health', failure_ids=('failed-health',),
                                recovered_at='2026-11-05T12:00:00Z', provenance='simulated-health', evidence_id='health')
    assert costs.allowance('fixture-oct', HUMAN)['blocked_reason'] == 'cost_control_missing'
    ceiling(costs, '1')
    assert costs.allowance('fixture-oct', HUMAN)['blocked_reason'] == 'cost_coverage_unavailable'
    recover(costs, oid, failure_ids=('failed-health',))
    with pytest.raises(EvidenceError, match='cost_meter_recovery_conflict'):
        recover(costs, oid, failure_ids=('failed-health',), evidence_id='different-health-report')
    with pytest.raises(EvidenceError, match='cost_meter_failure_already_recovered'):
        recover(costs, oid, recovery_id='second', failure_ids=('failed-health',))
    assert costs.allowance('fixture-oct', HUMAN)['blocked_reason'] is None
    assert len(costs.read(oid, HUMAN)['meter_recoveries']) == 1


def test_late_report_that_disproves_dispatch_bound_itself_blocks_meter_until_recovery(stack, tmp_path):
    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    ceiling(costs, '0.25')
    adapter, oid, calls = lost_call(costs)
    final_usage(costs, oid, units='4')
    view = costs.read(oid, HUMAN)
    assert view['actuals']['amount'] == '0.5'
    assert view['allowance']['outstanding_amount'] == '0'
    assert view['limits']['bound_status'] == 'violated'
    assert view['limits']['billing_state'] == 'final_measurement_recorded'
    assert view['coverage']['status'] == 'meter_failure'
    failures = view['unresolved']['meter_failure_ids']
    assert len(failures) == 1
    ceiling(costs, '2')
    assert adapter.execute(WORKER, request_id='blocked-late-bound', method='fake-v1', call=calls.append)['reason'] == 'cost_coverage_unavailable'
    assert final_usage(costs, oid, units='4')['status'] == 'duplicate'
    recover(costs, oid, failure_ids=tuple(failures))
    assert costs.allowance('fixture-oct', HUMAN)['blocked_reason'] is None
    assert calls == ['2']
