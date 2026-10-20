"""Synthetic accounting through public operations and local cost detail."""

from smi_tasks import OfflineTaskWorker
from test_tasks import HUMAN, WORKER, setup_task, submit


START = '2026-10-01T00:00:00+00:00'
END = '2026-11-01T00:00:00+00:00'
MEASURED = '2026-10-20T12:00:00+00:00'


def accounting(tasks):
    from smi_costs import CostScope, UsageAccounting

    costs = UsageAccounting(tasks.db, task_attribution=tasks.resolve_cost_attribution)
    costs.migrate()
    costs.configure_scope(CostScope('fixture-oct', 'synthetic-local', 'fixture-meter', 'metered', 'USD', START, END,
                                    unit='fixture-unit', rate_version='synthetic-v1', unit_rate='0.125'), HUMAN)
    return costs


def test_operator_reopens_exact_synthetic_task_usage_with_auditable_rate(stack, tmp_path):
    from smi_costs import UsageAccounting

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    costs = accounting(tasks)
    operation = costs.begin_operation('fixture-oct', WORKER, request_id='task-meter', method='fixture-read-v1',
                                      task_id=completed['task_id'], attempt_id=completed['attempts'][0]['attempt_id'])
    saved = costs.record_usage(operation['operation_id'], WORKER, measurement_id='meter-event-1', units='3',
                              rate_version='synthetic-v1', measured_at=MEASURED, provenance='synthetic-counter-v1')
    assert saved['status'] == 'recorded'
    reopened = UsageAccounting(tasks.db).read(operation['operation_id'], HUMAN)
    assert reopened['scope']['classification'] == 'metered'
    assert reopened['scope']['currency'] == 'USD'
    assert reopened['scope']['provider'] == 'synthetic-local'
    assert reopened['scope']['service'] == 'fixture-meter'
    assert reopened['scope']['period_start'] == START
    assert reopened['scope']['period_end'] == END
    assert reopened['task_id'] == completed['task_id']
    assert reopened['attempt_id'] == completed['attempts'][0]['attempt_id']
    assert reopened['actor'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert reopened['method'] == 'fixture-read-v1'
    assert reopened['actuals'] == {'amount': '0.375', 'synthetic': True, 'commercial_charge': False}
    assert reopened['entries'][0]['units'] == '3'
    assert reopened['entries'][0]['unit_rate'] == '0.125'
    assert reopened['entries'][0]['rate_version'] == 'synthetic-v1'
    assert reopened['entries'][0]['provenance'] == 'synthetic-counter-v1'
    assert reopened['entries'][0]['measured_at'] == MEASURED
    assert reopened['enforced_monetary_control'] is False


def test_forecasts_commitments_and_unknown_meter_failures_remain_separate(stack, tmp_path):
    import pytest
    from smi_costs import CostScope
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    operation = costs.begin_operation('fixture-oct', WORKER, request_id='model-no-task', method='synthetic-model-v1')
    oid = operation['operation_id']
    assert operation['task_id'] is None and operation['attempt_id'] is None
    assert operation['actuals']['amount'] is None
    assert operation['coverage']['unknown_cost'] is True
    costs.record_forecast(oid, HUMAN, measurement_id='forecast-1', amount='2.5', currency='USD',
                          measured_at=MEASURED, provenance='operator-estimate-v1', assumptions='Ten synthetic requests assumed')
    costs.record_commitment(oid, WORKER, measurement_id='pending-1', amount='1', currency='USD',
                            measured_at=MEASURED, provenance='simulated-pending-v1')
    costs.record_uncertainty(oid, WORKER, measurement_id='failure-1', state='meter_failure',
                             measured_at=MEASURED, provenance='synthetic-meter-v1', reason='counter_unavailable')
    view = costs.read(oid, HUMAN)
    assert view['forecasts']['amount'] == '2.5'
    assert view['commitments']['amount'] == '1'
    assert view['actuals']['amount'] is None
    assert view['coverage'] == {'status': 'meter_failure', 'unknown_cost': True}
    assert view['scope']['classification'] == 'metered'
    costs.record_usage(oid, WORKER, measurement_id='late-bill', units='3', rate_version='synthetic-v1',
                       measured_at=MEASURED, provenance='synthetic-meter-v1')
    assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.375'
    assert costs.read(oid, HUMAN)['coverage']['unknown_cost'] is True
    costs.configure_scope(CostScope('forecast-oct', 'unmetered-local', 'model-forecast', 'forecast_only', 'KRW', START, END), HUMAN)
    forecast = costs.begin_operation('forecast-oct', WORKER, request_id='forecast-model', method='model-estimate-v1')
    costs.record_forecast(forecast['operation_id'], HUMAN, measurement_id='forecast-2', amount='1000', currency='KRW',
                          measured_at=MEASURED, provenance='operator-v1', assumptions='Unknown commercial billing coverage')
    costs.record_uncertainty(forecast['operation_id'], WORKER, measurement_id='unknown-1', state='unknown',
                             measured_at=MEASURED, provenance='operator-v1', reason='unmeterable_scope')
    read = costs.read(forecast['operation_id'], HUMAN)
    assert read['coverage'] == {'status': 'unknown', 'unknown_cost': True}
    assert read['enforced_monetary_control'] is False
    assert read['actuals']['amount'] is None
    assert read['forecasts']['amount'] == '1000'
    with pytest.raises(EvidenceError, match='cost_scope_not_metered'):
        costs.record_usage(forecast['operation_id'], WORKER, measurement_id='forged-meter', units='1',
                           rate_version='synthetic-v1', measured_at=MEASURED, provenance='synthetic-v1')


def test_concurrent_measurements_and_model_operation_retries_reconcile_once(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import pytest
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    def begin(_):
        return costs.begin_operation('fixture-oct', WORKER, request_id='model-retry', method='synthetic-model-v1')
    with ThreadPoolExecutor(max_workers=4) as pool:
        operations = list(pool.map(begin, range(4)))
    oid = operations[0]['operation_id']
    assert {o['operation_id'] for o in operations} == {oid}
    def measure(_):
        return costs.record_usage(oid.upper(), WORKER, measurement_id='retry-event', units='0.3',
                                  rate_version='synthetic-v1', measured_at=MEASURED, provenance='synthetic-model-meter-v1')
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(measure, range(4)))
    assert sorted(r['status'] for r in records) == ['duplicate', 'duplicate', 'duplicate', 'recorded']
    assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.0375'
    with pytest.raises(EvidenceError, match='cost_measurement_conflict'):
        costs.record_usage(oid, WORKER, measurement_id='retry-event', units='0.4', rate_version='synthetic-v1',
                           measured_at=MEASURED, provenance='synthetic-model-meter-v1')
    other = costs.begin_operation('fixture-oct', WORKER, request_id='model-other', method='synthetic-model-v1')
    with pytest.raises(EvidenceError, match='cost_measurement_conflict'):
        costs.record_usage(other['operation_id'], WORKER, measurement_id='retry-event', units='0.3', rate_version='synthetic-v1',
                           measured_at=MEASURED, provenance='synthetic-model-meter-v1')
    with pytest.raises(EvidenceError, match='cost_operation_conflict'):
        costs.begin_operation('fixture-oct', HUMAN, request_id='model-retry', method='synthetic-model-v1')
    assert len(costs.read(oid, HUMAN)['entries']) == 1
    assert costs.read(other['operation_id'], HUMAN)['actuals']['amount'] is None


def test_task_attribution_rejects_missing_foreign_or_mismatched_attempt_through_task_owner(stack, tmp_path):
    import uuid
    import pytest
    from smi_costs import UsageAccounting
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_tasks import AcquisitionTasks

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    first = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    second = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign, request_id='second')['task_id'], WORKER)
    costs = accounting(tasks)
    for task_id, attempt_id in ((str(uuid.uuid4()), first['attempts'][0]['attempt_id']),
                                (first['task_id'], str(uuid.uuid4())),
                                (first['task_id'], second['attempts'][0]['attempt_id'])):
        with pytest.raises(EvidenceError, match='not_found'):
            costs.begin_operation('fixture-oct', WORKER, request_id='bad-task', method='fixture-v1',
                                  task_id=task_id, attempt_id=attempt_id)
    foreign_actor = ActorContext('foreign', 'operator', 'human')
    foreign_tasks = AcquisitionTasks(tasks.db, 'foreign')
    foreign_costs = UsageAccounting(tasks.db, 'foreign', task_attribution=foreign_tasks.resolve_cost_attribution)
    with pytest.raises(EvidenceError, match='acquisition_task_not_found'):
        foreign_costs.begin_operation('fixture-oct', foreign_actor, request_id='foreign-task', method='fixture-v1',
                                      task_id=first['task_id'], attempt_id=first['attempts'][0]['attempt_id'])
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        costs.begin_operation('fixture-oct', foreign_actor, request_id='foreign-actor', method='fixture-v1')
    operation = costs.begin_operation('fixture-oct', WORKER, request_id='valid', method='fixture-v1')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        costs.read(operation['operation_id'], foreign_actor)
    with pytest.raises(EvidenceError, match='cost_operation_not_found'):
        foreign_costs.read(operation['operation_id'], foreign_actor)
    with pytest.raises(EvidenceError, match='cost_task_resolver_unconfigured'):
        UsageAccounting(tasks.db).begin_operation('fixture-oct', WORKER, request_id='unresolved', method='fixture-v1',
                                                  task_id=first['task_id'], attempt_id=first['attempts'][0]['attempt_id'])


def test_invalid_or_nonfinite_money_rate_currency_period_and_missing_configuration_fail(stack, tmp_path):
    from dataclasses import replace
    import pytest
    from smi_costs import CostScope
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    original = CostScope('fixture-oct', 'synthetic-local', 'fixture-meter', 'metered', 'USD', START, END,
                         unit='fixture-unit', rate_version='synthetic-v1', unit_rate='0.125')
    for change in ({'currency': 'usd'}, {'currency': 'US1'}, {'period_end': START}, {'period_start': '2026-10-01'},
                   {'classification': 'automatic'}, {'rate_version': ''}, {'unit_rate': '-0.1'}, {'unit_rate': 'NaN'},
                   {'unit_rate': 'Infinity'}, {'unit_rate': '0.0000000000001'}, {'unit_rate': 0.1}):
        with pytest.raises(EvidenceError, match='invalid_cost_'):
            costs.configure_scope(replace(original, **change), HUMAN)
    with pytest.raises(EvidenceError, match='cost_scope_conflict'):
        costs.configure_scope(replace(original, rate_version='synthetic-v2', unit_rate='0.25'), HUMAN)
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        costs.configure_scope(original, WORKER)
    with pytest.raises(EvidenceError, match='cost_scope_not_found'):
        costs.begin_operation('unconfigured', WORKER, request_id='missing', method='fixture-v1')
    operation = costs.begin_operation('fixture-oct', WORKER, request_id='invalid-measurement', method='fixture-v1')
    oid = operation['operation_id']
    for invalid in ('NaN', 'sNaN', 'Infinity', '-Infinity', '-1', '1e19', '1e-13', 'invalid', 0.1, True):
        with pytest.raises(EvidenceError, match='invalid_cost_decimal'):
            costs.record_usage(oid, WORKER, measurement_id='invalid', units=invalid, rate_version='synthetic-v1',
                               measured_at=MEASURED, provenance='synthetic-v1')
    for field, invalid, code in (('rate_version', 'v2', 'cost_rate_version_mismatch'),
                                ('measured_at', END, 'cost_measurement_outside_period'),
                                ('measured_at', '2026-10-20T00:00:00', 'invalid_cost_time')):
        args = {'measurement_id': 'invalid', 'units': '1', 'rate_version': 'synthetic-v1', 'measured_at': MEASURED, 'provenance': 'synthetic-v1'}
        args[field] = invalid
        with pytest.raises(EvidenceError, match=code):
            costs.record_usage(oid, WORKER, **args)
    with pytest.raises(EvidenceError, match='cost_currency_mismatch'):
        costs.record_forecast(oid, HUMAN, measurement_id='currency', amount='1', currency='KRW', measured_at=MEASURED,
                              provenance='operator-v1', assumptions='Explicit mismatch')
    assert costs.read(oid, HUMAN)['entries'] == []


def test_cost_detail_http_reopens_separate_synthetic_amounts_and_escapes_metadata(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    costs = accounting(tasks)
    operation = costs.begin_operation('fixture-oct', WORKER, request_id='http-cost', method='synthetic-v1',
                                      task_id=completed['task_id'], attempt_id=completed['attempts'][0]['attempt_id'])
    oid = operation['operation_id']
    costs.record_usage(oid, WORKER, measurement_id='http-event', units='3', rate_version='synthetic-v1',
                       measured_at=MEASURED, provenance='synthetic-v1')
    costs.record_forecast(oid, HUMAN, measurement_id='http-forecast', amount='2', currency='USD', measured_at=MEASURED,
                          provenance='operator-v1', assumptions='<script>assumption</script>')
    for _ in range(2):
        with running(ReviewApp(tasks.db)) as url:
            status, _, page = request(url, path=f'/costs/{oid}')
            assert status == 200
            assert 'Synthetic measured amount: 0.375 USD' in page
            assert 'Forecasts: 2 USD' in page
            assert 'Outstanding commitments: Unknown' in page
            assert 'No commercial charge' in page
            assert 'No enforced monetary ceiling' in page
            assert '&lt;script&gt;assumption&lt;/script&gt;' in page
            assert '<script>assumption</script>' not in page
            assert f'/tasks/{completed["task_id"]}' in page
            status, _, page = request(url, path='/costs')
            assert status == 200 and f'/costs/{oid}' in page
            status, _, page = request(url, path=f'/tasks/{completed["task_id"]}/costs')
            assert status == 200 and f'/costs/{oid}' in page
            assert request(url, path=f'/tasks/{completed["task_id"]}')[0] == 200
    publication_id = completed['publication_ids'][0]
    from smi_knowledge import KnowledgePublications
    publication = KnowledgePublications(tasks.db).read(publication_id, HUMAN, include_synthetic=True)
    evidence.revoke(publication['members'][0]['observation_id'])
    assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.375'
    with running(ReviewApp(tasks.db, workspace_id='foreign')) as url:
        assert request(url, path=f'/costs/{oid}')[0] == 404
        assert request(url, path=f'/tasks/{completed["task_id"]}/costs')[0] == 404
        assert f'/costs/{oid}' not in request(url, path='/costs')[2]


def test_exact_decimal_totals_survive_low_ambient_precision_and_explicit_zero(stack, tmp_path):
    from decimal import localcontext
    import pytest
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='exact', method='synthetic-model-v1')['operation_id']
    with localcontext() as context:
        context.prec = 2
        for mid, units in (('first', '0.1'), ('second', '0.2')):
            costs.record_usage(oid, WORKER, measurement_id=mid, units=units, rate_version='synthetic-v1',
                               measured_at=MEASURED, provenance='synthetic-v1')
        assert costs.read(oid, HUMAN)['actuals']['amount'] == '0.0375'
        context.Emax = 2
        context.Emin = -2
        costs.record_usage(oid, WORKER, measurement_id='large-exact', units='1000000000000000000',
                           rate_version='synthetic-v1', measured_at=MEASURED, provenance='synthetic-v1')
        assert costs.read(oid, HUMAN)['actuals']['amount'] == '125000000000000000.0375'
    zero = costs.begin_operation('fixture-oct', WORKER, request_id='zero', method='synthetic-model-v1')['operation_id']
    costs.record_usage(zero, WORKER, measurement_id='zero-event', units='-0', rate_version='synthetic-v1',
                       measured_at=MEASURED, provenance='synthetic-v1')
    assert costs.read(zero, HUMAN)['actuals']['amount'] == '0'
    assert costs.read(zero, HUMAN)['coverage']['unknown_cost'] is False
    for value in ('0e999999999', 'NaN', '-1', 'Infinity', 0.1):
        for record in (costs.record_forecast, costs.record_commitment):
            extra = {'assumptions': 'Synthetic estimate'} if record == costs.record_forecast else {}
            with pytest.raises(EvidenceError, match='invalid_cost_decimal'):
                record(oid, HUMAN, measurement_id='invalid-estimate', amount=value, currency='USD',
                       measured_at=MEASURED, provenance='operator-v1', **extra)


def test_concurrent_conflicting_retry_is_visible_and_preserves_original_measurement(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from smi_ingestion.evidence import EvidenceError

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    oid = costs.begin_operation('fixture-oct', WORKER, request_id='conflict', method='synthetic-v1')['operation_id']
    def record(units):
        try:
            return costs.record_usage(oid, WORKER, measurement_id='racing-identity', units=units, rate_version='synthetic-v1',
                                      measured_at=MEASURED, provenance='synthetic-v1')['status']
        except EvidenceError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(record, ('1', '2')))
    assert sorted(statuses) == ['cost_measurement_conflict', 'recorded']
    view = costs.read(oid, HUMAN)
    assert len(view['entries']) == 1
    assert view['actuals']['amount'] in {'0.125', '0.25'}
    for record, mid, extra in ((costs.record_forecast, 'forecast-retry', {'assumptions': 'Fixed synthetic estimate'}),
                               (costs.record_commitment, 'commitment-retry', {})):
        args = {'measurement_id': mid, 'amount': '1.25', 'currency': 'USD', 'measured_at': MEASURED,
                'provenance': 'operator-v1', **extra}
        assert record(oid, HUMAN, **args)['status'] == 'recorded'
        assert record(oid, HUMAN, **args)['status'] == 'duplicate'
    assert costs.read(oid, HUMAN)['forecasts']['amount'] == '1.25'
    assert costs.read(oid, HUMAN)['commitments']['amount'] == '1.25'


def test_http_exposes_forecast_only_and_meter_failure_without_zero_or_control_claim(stack, tmp_path):
    from smi_costs import CostScope
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, _, _, _ = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_scope(CostScope('forecast', 'local-unmetered', 'forecast-model', 'forecast_only', 'USD', START, END), HUMAN)
    forecast = costs.begin_operation('forecast', WORKER, request_id='forecast-view', method='model-v1')
    costs.record_forecast(forecast['operation_id'], HUMAN, measurement_id='forecast-view', amount='5', currency='USD',
                          measured_at=MEASURED, provenance='operator-v1', assumptions='Unmeterable usage; sample estimate only')
    failure = costs.begin_operation('fixture-oct', WORKER, request_id='failure-view', method='synthetic-v1')
    costs.record_uncertainty(failure['operation_id'], WORKER, measurement_id='meter-failed', state='meter_failure',
                             measured_at=MEASURED, provenance='synthetic-v1', reason='meter_offline')
    with running(ReviewApp(tasks.db)) as url:
        for operation, word in ((forecast, 'forecast_only'), (failure, 'meter_failure')):
            status, _, page = request(url, path=f'/costs/{operation["operation_id"]}')
            assert status == 200
            assert word in page
            assert 'Synthetic measured amount: Unknown' in page
            assert 'Unknown cost: True' in page
            assert 'No enforced monetary ceiling' in page
        assert 'Forecasts: 5 USD' in request(url, path=f'/costs/{forecast["operation_id"]}')[2]


def test_cli_and_repeated_migrations_preserve_independent_model_accounting(stack):
    from smi_costs import CostScope, UsageAccounting
    from test_cli import _cli

    db, evidence, _, _ = stack
    result = _cli(db, evidence.root, 'migrate')
    assert result.returncode == 0, result.stdout + result.stderr
    costs = UsageAccounting(db)
    costs.configure_scope(CostScope('independent-model', 'synthetic-local', 'model-meter', 'metered', 'USD', START, END,
                                    unit='synthetic-token', rate_version='simulation-v1', unit_rate='0.0001'), HUMAN)
    oid = costs.begin_operation('independent-model', WORKER, request_id='independent-retry', method='synthetic-model-v1')['operation_id']
    costs.record_usage(oid, WORKER, measurement_id='independent-meter', units='2500', rate_version='simulation-v1',
                       measured_at=MEASURED, provenance='synthetic-token-counter-v1')
    before = costs.read(oid, HUMAN)
    costs.migrate()
    result = _cli(db, evidence.root, 'migrate')
    assert result.returncode == 0, result.stdout + result.stderr
    assert UsageAccounting(db).read(oid, HUMAN) == before
    assert before['actuals']['amount'] == '0.25'
    assert costs.begin_operation('independent-model', WORKER, request_id='independent-retry', method='synthetic-model-v1') == before
    assert len(costs.list(HUMAN)) == 1
