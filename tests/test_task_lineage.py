"""Task-to-publication lineage through public owners and local HTTP."""

import pytest

from smi_tasks import OfflineTaskWorker, TaskLineage
from test_tasks import HUMAN, WORKER, setup_task, submit


def test_trace_distinguishes_acceptance_from_usable_publication_and_exact_methods(stack, tmp_path):
    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    queued = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert queued['stages']['queue'] == 'accepted'
    assert queued['stages']['source'] == 'not_started'
    assert queued['stages']['publication'] == 'not_started'
    assert queued['attempts'] == []
    assert queued['costs']['coverage'] == 'unknown'
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    manifest.unlink()
    (tmp_path / 'account.json').unlink()
    trace = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert trace['task_id'] == task_id
    assert trace['authority']['campaign_id'] == campaign['campaign_id']
    assert trace['authority']['brief_id'] == campaign['brief_id']
    assert trace['authority']['initiator'] == {'actor_id': HUMAN.actor_id, 'kind': 'human'}
    assert trace['stages'] == {'queue': 'accepted', 'source': 'completed', 'ingestion': 'completed',
                              'publication': 'published', 'completion': 'usable_update'}
    attempt = trace['attempts'][0]
    assert attempt['attempt_id'] == completed['attempts'][0]['attempt_id']
    assert attempt['run']['run_id'] == completed['attempts'][0]['run_id']
    observation = attempt['run']['observations'][0]
    derivation = observation['derivations'][0]
    assert observation['status'] == 'applied'
    assert derivation['mapper_key'] == 'fixture-json:v1'
    assert derivation['policy_version'] == 'canonical-v1'
    assert observation['captured_at'] == '2026-10-01T00:00:00+00:00'
    publication = trace['publications'][0]
    assert publication['publication_id'] == completed['publication_ids'][0]
    assert publication['method_version'] == 'ingested-support-publication-v1'
    assert publication['support'][0]['observation_id'] == observation['observation_id']
    assert publication['support'][0]['derivation_id'] == derivation['derivation_id']
    assert publication['current_support']['available_members'] == 1
    assert publication['published_at']
    assert trace['historical_coverage']['published_members'] == 1
    assert trace['costs']['operations'] == []


def test_http_lineage_reopens_real_cost_attribution_and_governed_support_without_files(stack, tmp_path):
    import json
    from smi_costs import CostScope
    from smi_review import ReviewApp
    from test_costs import accounting, START, END, MEASURED
    from test_review import request, running

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('fixture-json', 'fixture-oct', HUMAN, max_units=1)
    costs.configure_ceiling('fixture-oct', HUMAN, amount='20', currency='USD', period_start=START, period_end=END)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    task_id = completed['task_id']
    attempt_id = completed['attempts'][0]['attempt_id']
    operation = costs.list(HUMAN, task_id=task_id)[0]
    oid = operation['operation_id']
    costs.record_forecast(oid, HUMAN, measurement_id='estimate', amount='2.5', currency='USD',
                         measured_at=MEASURED, provenance='operator-estimate-v1', assumptions='Bounded future work')
    costs.record_commitment(oid, HUMAN, measurement_id='pending', amount='1', currency='USD',
                           measured_at=MEASURED, provenance='pending-report-v1')
    costs.record_uncertainty(oid, HUMAN, measurement_id='unknown', state='unknown', measured_at=MEASURED,
                            provenance='missing-report-v1', reason='unresolved_liability')
    costs.configure_scope(CostScope('future', 'unmetered-local', 'model-forecast', 'forecast_only', 'KRW', START, END), HUMAN)
    forecast = costs.begin_operation('future', WORKER, request_id='future', method='estimate-v1', task_id=task_id, attempt_id=attempt_id)
    costs.record_forecast(forecast['operation_id'], HUMAN, measurement_id='future-estimate', amount='1000', currency='KRW',
                         measured_at=MEASURED, provenance='operator-v1', assumptions='Unknown commercial billing')
    trace = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    by_id = {op['operation_id']: op for op in trace['costs']['operations']}
    assert by_id[oid]['task_id'] == task_id
    assert by_id[oid]['attempt_id'] == attempt_id
    assert by_id[oid]['actuals']['amount'] == '0.125'
    assert by_id[oid]['forecasts']['amount'] == '2.5'
    assert by_id[oid]['commitments']['amount'] == '1'
    assert by_id[oid]['coverage']['unknown_cost'] is True
    assert by_id[oid]['unresolved']['uncertainty_ids'] == ['unknown']
    assert by_id[oid]['limits']['billing_lag_bound'] is None
    assert by_id[forecast['operation_id']]['enforced_monetary_control'] is False
    assert by_id[forecast['operation_id']]['actuals']['amount'] is None
    assert by_id[forecast['operation_id']]['forecasts']['amount'] == '1000'
    assert by_id[oid]['entries'][0]['provenance'] == 'bounded-synthetic-adapter-v1'
    manifest.unlink()
    (tmp_path / 'account.json').unlink()
    path = f'/tasks/{task_id}/lineage'
    with running(ReviewApp(tasks.db)) as url:
        assert path in request(url, path=f'/tasks/{task_id}')[2]
        status, _, hidden = request(url, path=path)
        assert status == 200
        assert 'synthetic_evidence_excluded' in hidden
        status, _, page = request(url, path=path + '?include_synthetic=yes')
        assert status == 200
        for text in ('Queue acceptance: accepted', 'Source collection: completed', 'Ingestion: completed',
                     'Publication: published', 'Historical completion: usable_update', task_id, attempt_id,
                     completed['attempts'][0]['run_id'], completed['publication_ids'][0], oid, '0.125',
                     '2.5', '1000', 'pending-report-v1', 'missing-report-v1', 'No enforced monetary ceiling',
                     'No zero-overshoot guarantee', 'Billing lag bound: Unknown'):
            assert text in page
        assert 'test-account' not in page
        assert str(tmp_path) not in page
        assert 'checkpoint' not in page
        assert request(url, path=path + '?actor_id=forged')[0] == 422
    observation_id = trace['publications'][0]['support'][0]['observation_id']
    evidence.revoke(observation_id)
    reopened = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert reopened['outcome'] == 'usable_update'
    assert reopened['historical_coverage']['published_members'] == 1
    assert reopened['publications'][0]['current_support'] == {'available_members': 0, 'unavailable_members': 1}
    assert reopened['publications'][0]['href'] is None
    with running(ReviewApp(tasks.db)) as url:
        status, _, denied = request(url, path=path + '?include_synthetic=yes')
        assert status == 200
        assert 'Currently permitted members: 0' in denied
        assert f'href="/knowledge/publications/{completed["publication_ids"][0]}' not in denied
        assert 'test-account' not in denied
    assert 'test-account' not in json.dumps(reopened)


def test_partial_ingestion_and_publication_failure_have_distinct_historical_paths(stack, tmp_path):
    import json
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, items=[
        {'path': 'account.json', 'reference': 'synthetic://valid'},
        {'path': 'bad.json', 'reference': 'synthetic://invalid'},
    ])
    (tmp_path / 'bad.json').write_text(json.dumps({'account': {'id': 17}}))
    task_id = submit(tasks, campaign)['task_id']
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    trace = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert result['outcome'] == 'partial_update'
    assert trace['stages'] == {'queue': 'accepted', 'source': 'completed', 'ingestion': 'partial',
                              'publication': 'published', 'completion': 'partial_update'}
    assert trace['failure'] == {'phase': 'ingestion', 'code': 'normalization_failed'}
    observations = trace['attempts'][0]['run']['observations']
    assert [o['status'] for o in observations] == ['applied', 'quarantined']
    assert observations[1]['derivations'] == []
    assert trace['publications'][0]['support'][0]['observation_id'] == observations[0]['observation_id']
    assert trace['historical_coverage']['remaining_inputs'] == 1
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path=f'/tasks/{task_id}/lineage?include_synthetic=yes')
        assert status == 200
        assert 'Ingestion: partial' in page
        assert 'normalization_failed' in page
        assert 'quarantined' in page
    # A new capture is not an unchanged publication; current process denial at
    # the real publication boundary must retain ingestion without usable output.
    (tmp_path / 'account.json').write_text(json.dumps({'account': {'id': 'second', 'handle': 'second'}}))
    next_id = submit(tasks, campaign, request_id='publication-failure')['task_id']

    def deny_prepared(progress):
        if progress['progress']['phase'] == 'publication_prepared':
            evidence.revoke(progress['attempts'][0]['publication_support'][0]['observation_id'])

    failed = OfflineTaskWorker(tasks.db, evidence.root, on_progress=deny_prepared).run_one(next_id, WORKER)
    trace = TaskLineage(tasks.db).read(next_id, HUMAN, include_synthetic=True)
    assert failed['failure'] == {'phase': 'publication', 'code': 'publication_support_unavailable'}
    assert trace['stages'] == {'queue': 'accepted', 'source': 'completed', 'ingestion': 'partial',
                              'publication': 'failed', 'completion': 'failure'}
    assert trace['publications'] == []
    assert trace['historical_coverage']['published_members'] == 0
    assert trace['attempts'][0]['prepared_support'][0]['observation_id']
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path=f'/tasks/{next_id}/lineage?include_synthetic=yes')
        assert status == 200
        assert 'Publication: failed' in page
        assert 'Historical completion: failure' in page
        assert 'publication_support_unavailable' in page


def test_restart_preserves_committed_publication_original_attempt_and_recovery_actor(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence_sets import ActorContext
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']

    def stop_after_publication(progress):
        if progress['progress']['phase'] == 'publication_committed':
            raise RuntimeError('simulated process stop')

    with pytest.raises(RuntimeError, match='simulated process stop'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=stop_after_publication).run_one(task_id, WORKER)
    interrupted = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert interrupted['stages']['publication'] == 'published'
    assert interrupted['stages']['completion'] == 'pending'
    assert interrupted['execution']['state'] == 'recoverable'
    successor = ActorContext('local', 'successor-worker', 'automation')
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, successor)
    trace = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert len(trace['attempts']) == 1
    assert trace['attempts'][0]['attempt_id'] == interrupted['attempts'][0]['attempt_id']
    assert trace['attempts'][0]['run']['run_id'] == interrupted['attempts'][0]['run']['run_id']
    assert trace['attempts'][0]['run']['observations'] == interrupted['attempts'][0]['run']['observations']
    assert trace['attempts'][0]['recovery_count'] == 1
    assert trace['attempts'][0]['resumed_by'] == [{'actor_id': successor.actor_id, 'kind': 'automation'}]
    assert trace['attempts'][0]['producer'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert trace['publications'] == interrupted['publications']
    assert trace['publications'][0]['publication_id'] == completed['publication_ids'][0]
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path=f'/tasks/{task_id}/lineage?include_synthetic=yes')
        assert status == 200
        assert 'successor-worker' in page
        assert 'Recovery count: 1' in page
        assert 'Historical completion: usable_update' in page


def test_fake_source_error_and_pending_handle_never_escape_into_lineage(stack, tmp_path):
    import json
    from smi_ingestion.contracts import CollectedBatch
    from smi_ingestion.evidence import EvidenceError
    from smi_review import ReviewApp
    from test_review import request, running

    secret = 'provider-credential-and-unrestricted-payload'

    class BrokenSource:
        def collect(self, manifest, checkpoint, limits):
            raise EvidenceError(secret)

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    failed = OfflineTaskWorker(tasks.db, evidence.root, collector=BrokenSource()).run_one(submit(tasks, campaign)['task_id'], WORKER)
    trace = TaskLineage(tasks.db).read(failed['task_id'], HUMAN, include_synthetic=True)
    assert trace['stages']['source'] == 'failed'
    assert trace['stages']['publication'] == 'not_reached'
    assert trace['failure'] == {'phase': 'collection', 'code': 'unclassified_failure'}
    assert trace['attempts'][0]['run']['issue_count'] == 1
    assert secret not in json.dumps(trace)

    class PendingSource:
        def collect(self, manifest, checkpoint, limits):
            return CollectedBatch((), {'provider_handle': secret}, False, waiting='provider_pending', request_attempts=1)

    waiting = OfflineTaskWorker(tasks.db, evidence.root, collector=PendingSource()).run_one(submit(tasks, campaign, request_id='pending')['task_id'], WORKER)
    pending = TaskLineage(tasks.db).read(waiting['task_id'], HUMAN)
    assert pending['stages']['source'] == 'waiting'
    assert pending['stages']['completion'] == 'pending'
    assert pending['attempts'][0]['run']['waiting'] == {'code': 'provider_pending', 'resumable': True}
    assert secret not in json.dumps(pending)
    with running(ReviewApp(tasks.db)) as url:
        for task_id in (failed['task_id'], waiting['task_id']):
            status, _, page = request(url, path=f'/tasks/{task_id}/lineage?include_synthetic=yes')
            assert status == 200
            assert secret not in page
            assert 'provider_handle' not in page
            assert str(tmp_path) not in page


def test_unchanged_and_empty_tasks_report_no_new_update_without_prior_receipt_transfer(stack, tmp_path):
    import json

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    first = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    repeated = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign, request_id='unchanged')['task_id'], WORKER)
    trace = TaskLineage(tasks.db).read(repeated['task_id'], HUMAN, include_synthetic=True)
    assert trace['stages'] == {'queue': 'accepted', 'source': 'completed', 'ingestion': 'completed',
                              'publication': 'no_update', 'completion': 'no_usable_update'}
    assert trace['historical_coverage']['unchanged_members'] == 1
    assert trace['publications'] == []
    assert first['publication_ids'][0] not in json.dumps(trace)
    body = json.loads(manifest.read_text())
    body['items'] = []
    manifest.write_text(json.dumps(body))
    empty = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign, request_id='empty')['task_id'], WORKER)
    trace = TaskLineage(tasks.db).read(empty['task_id'], HUMAN, include_synthetic=True)
    assert trace['stages']['publication'] == 'no_update'
    assert trace['attempts'][0]['run']['observations'] == []
    assert trace['historical_coverage']['collected_observations'] == 0
    assert trace['market_coverage'] == 'unknown'


def test_source_provenance_distinguishes_partial_collection_from_ingestion(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, items=[
        {'path': 'account.json', 'reference': 'synthetic://first'},
        {'path': 'missing.json', 'reference': 'synthetic://missing'},
    ])
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    trace = TaskLineage(tasks.db).read(result['task_id'], HUMAN, include_synthetic=True)
    assert trace['stages'] == {'queue': 'accepted', 'source': 'partial', 'ingestion': 'completed',
                              'publication': 'published', 'completion': 'partial_update'}
    assert trace['failure'] == {'phase': 'collection', 'code': 'source_unavailable'}
    observation = trace['attempts'][0]['run']['observations'][0]
    assert observation['source'] == {'adapter': 'fixture-json', 'provider': 'offline-synthetic', 'format_version': 'v1'}
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path=f'/tasks/{result["task_id"]}/lineage?include_synthetic=yes')
        assert status == 200
        assert 'Source collection: partial' in page
        assert 'offline-synthetic' in page


def test_workspace_and_explicit_visibility_are_checked_at_public_lineage_ports(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_ingestion.support import IngestedEvidence
    from smi_review import ReviewApp
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    task_id, run_id = result['task_id'], result['attempts'][0]['run_id']
    foreign = ActorContext('foreign', 'reader', 'human')
    for reader, record_id in ((TaskLineage(tasks.db), task_id), (IngestedEvidence(tasks.db), run_id)):
        operation = reader.read if isinstance(reader, TaskLineage) else reader.run_lineage
        with pytest.raises(EvidenceError, match='workspace_access_denied'):
            operation(record_id, foreign)
        for forged in ('yes', 1, None):
            with pytest.raises(EvidenceError, match='invalid_synthetic_visibility'):
                operation(record_id, HUMAN, include_synthetic=forged)
    with pytest.raises(EvidenceError, match='acquisition_task_not_found'):
        TaskLineage(tasks.db, 'foreign').read(task_id, foreign)
    with pytest.raises(EvidenceError, match='ingestion_run_not_found'):
        IngestedEvidence(tasks.db, 'foreign').run_lineage(run_id, foreign)
    hidden = TaskLineage(tasks.db).read(task_id, HUMAN)
    assert hidden['publications'][0]['availability'] == 'synthetic_evidence_excluded'
    assert hidden['attempts'][0]['run']['observations'][0]['captured_at'] is None
    assert hidden['publications'][0]['href'] is None
    with running(ReviewApp(tasks.db, workspace_id='foreign')) as url:
        assert request(url, path=f'/tasks/{task_id}/lineage?include_synthetic=yes')[0] == 404


@pytest.mark.parametrize("denied", ["can_display", "can_retain"])
def test_process_display_and_retention_jointly_govern_current_lineage_support(stack, tmp_path, denied):
    import json
    from smi_review import ReviewApp
    from test_review import request, running

    # Retention permission can be absent at acquisition: normalization uses the
    # transient response and publication is historical, not ongoing retention.
    policy = {'context_id': 'ephemeral', 'can_process': True, 'can_display': True, 'can_retain': True, denied: False}
    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, policy=policy)
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    assert result['outcome'] == 'usable_update'
    trace = TaskLineage(tasks.db).read(result['task_id'], HUMAN, include_synthetic=True)
    assert trace['publications'][0]['current_support']['available_members'] == 0
    assert trace['publications'][0]['href'] is None
    observation = trace['attempts'][0]['run']['observations'][0]
    assert observation['availability'] == 'unavailable'
    assert observation['captured_at'] is None
    assert 'test-account' not in json.dumps(trace)
    with running(ReviewApp(tasks.db)) as url:
        status, _, page = request(url, path=f'/tasks/{result["task_id"]}/lineage?include_synthetic=yes')
        assert status == 200
        assert 'Currently permitted members: 0' in page
        assert 'test-account' not in page


def test_expiry_withholds_current_navigation_without_changing_historical_completion(stack, tmp_path, monkeypatch):
    from datetime import datetime, timezone

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, policy={
        'context_id': 'expiring', 'can_process': True, 'can_display': True, 'can_retain': True,
        'expires_at': '2099-01-01T00:00:00+00:00'})
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    assert TaskLineage(tasks.db).read(result['task_id'], HUMAN, include_synthetic=True)['publications'][0]['href']

    class AfterExpiry(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2100, 1, 1, tzinfo=timezone.utc)

    monkeypatch.setattr('smi_ingestion.evidence.datetime', AfterExpiry)
    trace = TaskLineage(tasks.db).read(result['task_id'], HUMAN, include_synthetic=True)
    assert trace['outcome'] == 'usable_update'
    assert trace['historical_coverage']['published_members'] == 1
    assert trace['publications'][0]['href'] is None
    assert trace['attempts'][0]['run']['observations'][0]['captured_at'] is None


def test_supersession_keeps_exact_published_derivation_separate_from_current_method(stack, tmp_path):
    from smi_ingestion.adapters.json_fixture import JsonFixtureMapper
    from smi_ingestion.canonical import CanonicalWriter

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    result = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    before = TaskLineage(tasks.db).read(result['task_id'], HUMAN, include_synthetic=True)
    pinned = before['publications'][0]['support'][0]
    observation, payload = evidence.load(pinned['observation_id'])
    CanonicalWriter(tasks.db).apply(observation.id, JsonFixtureMapper().normalize(observation, payload),
                                   'fixture-json:v1', policy_version='canonical-v2')
    trace = TaskLineage(tasks.db).read(result['task_id'], HUMAN, include_synthetic=True)
    assert trace['publications'][0]['support'][0]['derivation_id'] == pinned['derivation_id']
    assert trace['publications'][0]['support'][0]['support_status'] == 'superseded_review_required'
    assert trace['publications'][0]['href'] is None
    versions = {d['policy_version']: d for d in trace['attempts'][0]['run']['observations'][0]['derivations']}
    assert versions['canonical-v1']['derivation_id'] == pinned['derivation_id']
    assert versions['canonical-v1']['support_status'] == 'superseded_review_required'
    assert versions['canonical-v2']['support_status'] == 'current'
    assert trace['outcome'] == 'usable_update'


def test_exact_approved_proposal_authority_is_preserved_in_lineage(stack, tmp_path):
    from test_keyword_discovery import discovery_setup, approved_task

    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    task_id = approved_task(tasks)
    accepted = tasks.read(task_id, HUMAN)
    OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    trace = TaskLineage(tasks.db).read(task_id, HUMAN, include_synthetic=True)
    assert trace['authority']['origin'] == 'assistant'
    assert trace['authority']['approval'] == accepted['proposal_approval']
    assert trace['authority']['approval']['approver']['actor_id'] == HUMAN.actor_id
    assert trace['authority']['approval']['proposal_id']
    assert trace['authority']['approval']['scope_digest']
    assert trace['authority']['initiator'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert trace['stages']['completion'] == 'usable_update'


def test_recorded_schedule_authority_survives_successor_configuration(stack, tmp_path):
    from test_schedules import scheduled, config

    owner, tasks, evidence, _ = scheduled(stack, tmp_path)
    owner.configure(config(), HUMAN, expected_version=0)
    occurrence = owner.tick(WORKER)['created_occurrences'][0]
    owner.configure(config(daily_allowance=70), HUMAN, expected_version=1)
    OfflineTaskWorker(tasks.db, evidence.root).run_one(occurrence['task_id'], WORKER)
    trace = TaskLineage(tasks.db).read(occurrence['task_id'], HUMAN, include_synthetic=True)
    assert trace['authority']['origin'] == 'schedule'
    assert trace['authority']['schedule'] == {'occurrence_id': occurrence['occurrence_id'],
        'configuration_version': 1, 'keyword_key': 'sunscreen', 'accounting_day': '2026-10-04'}
    assert trace['authority']['initiator'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert trace['stages']['completion'] == 'usable_update'


def test_cost_attribution_window_reports_truncation_without_inventing_complete_or_zero_cost(stack, tmp_path):
    from smi_costs import CostScope
    from test_costs import accounting, START, END

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    costs = accounting(tasks)
    costs.configure_scope(CostScope('future', 'unmetered', 'forecast', 'forecast_only', 'USD', START, END), HUMAN)
    ids = []
    for number in range(101):
        operation = costs.begin_operation('future', WORKER, request_id=f'cost-{number}', method='estimate-v1',
                                          task_id=completed['task_id'], attempt_id=completed['attempts'][0]['attempt_id'])
        ids.append(operation['operation_id'])
    trace = TaskLineage(tasks.db).read(completed['task_id'], HUMAN)
    assert trace['costs']['limit'] == 100
    assert trace['costs']['truncated'] is True
    assert trace['costs']['coverage'] == 'recorded_attribution_only'
    assert len(trace['costs']['operations']) == 100
    assert ids[0] not in {o['operation_id'] for o in trace['costs']['operations']}
    assert all(o['actuals']['amount'] is None and o['coverage']['unknown_cost'] for o in trace['costs']['operations'])
