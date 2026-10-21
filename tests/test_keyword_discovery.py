"""Bounded offline query discovery through approved tasks and public KB readers."""

import hashlib
import json

import pytest

from smi_tasks import AcquisitionTasks, EnrichmentProposal, OfflineRoute, OfflineTaskWorker
from smi_knowledge import KnowledgePublications, KnowledgeQueries, QueryScope
from test_tasks import HUMAN, WORKER, setup_task


def record(native_id, *, caption='Daily sunscreen review', subjects=('product:sunscreen',), published='2026-10-03T00:00:00Z'):
    return {'account': {'id': 'creator-1'},
            'video': {'id': native_id, 'author_id': 'creator-1', 'caption': caption, 'published_at': published},
            'subjects': list(subjects), 'captured_at': '2026-10-04T12:00:00Z',
            'reference': f'synthetic://video/{native_id}'}


def discovery_setup(stack, tmp_path, records=None, *, limits=None, policy=None):
    tasks, _, evidence, manifest = setup_task(stack, tmp_path, policy=policy)
    response = tmp_path / 'discovery-response.json'
    response.write_text(json.dumps({'records': records if records is not None else [record('post-1')]}))
    document = json.loads(manifest.read_text())
    document.update(adapter='offline-keyword-json', response_path=response.name,
                    response_sha256=hashlib.sha256(response.read_bytes()).hexdigest())
    document.pop('items')
    manifest.write_text(json.dumps(document))
    route = OfflineRoute(manifest, **({'limits': limits} if limits else {}))
    return AcquisitionTasks(tasks.db, route=route, authority=tasks.authority), evidence, response


def proposal(**changes):
    return EnrichmentProposal(**{'purpose': 'Find sunscreen evidence', 'intent': 'expansion',
        'subject_ids': ('product:sunscreen',), 'search_queries': ('sunscreen review',),
        'published_from': '2026-10-01T00:00:00Z', 'published_before': '2026-10-10T00:00:00Z', **changes})


def approved_task(tasks, scope=None, *, request_id='discovery'):
    saved = tasks.save_proposal(scope or proposal(), WORKER, request_id=request_id)
    view = tasks.read_proposal(saved['proposal_id'], HUMAN)
    approval = tasks.approve_proposal(saved['proposal_id'], HUMAN, scope_digest=view['scope_digest'], request_id=request_id)
    return tasks.submit_approved(saved['proposal_id'], WORKER, approval_id=approval['approval_id'],
        scope_digest=view['scope_digest'], request_id=request_id)['task_id']


def test_approved_query_filters_actual_subject_text_and_time_then_publishes_exact_lineage(stack, tmp_path):
    tasks, evidence, _ = discovery_setup(stack, tmp_path, [record('selected'),
        record('wrong-query', caption='Foundation tutorial'),
        record('wrong-subject', subjects=('product:foundation',)),
        record('before-window', published='2026-09-30T23:59:59Z'),
        record('end-excluded', published='2026-10-10T00:00:00Z')])
    task_id = approved_task(tasks)
    queued = tasks.read(task_id, HUMAN)
    assert queued['scope']['route'] == 'offline-keyword-json'
    assert queued['attempts'] == []
    assert queued['proposal_approval']['approver']['actor_id'] == HUMAN.actor_id
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['published_members'] == 1
    assert completed['coverage']['requests_used'] == 1
    assert completed['coverage']['scope'] == 'bounded_query_discovery'
    assert completed['coverage']['market_coverage'] == 'unknown'
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='discovered', include_synthetic=True)
    assert len(result['members']) == 1
    member = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)['members'][0]
    assert member['captured_at'] == '2026-10-04T12:00:00+00:00'
    assert member['run_id'] == completed['attempts'][0]['run_id']
    assert member['adapter'] == 'offline-keyword-json'
    assert member['coverage']['discovery']['query'] == 'sunscreen review'
    assert member['coverage']['discovery']['subject_ids'] == ['product:sunscreen']
    assert member['coverage']['discovery']['selection_position'] == 1
    assert member['coverage']['discovery']['priority'] == 'source_response_order'
    assert member['coverage']['discovery']['method'] == 'literal-caption-subject-time-v1'
    assert {a['namespace'] for a in member['assertions']} == {'offline-keyword:public'}
    assert {a['native_id'] for a in member['assertions']} == {'creator-1', 'selected'}
    assert {'field': 'handle', 'state': 'not_returned', 'count': 1} in completed['coverage']['missing_fields']
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == completed


def test_http_reviews_explicit_query_window_before_approval_then_reopens_published_discovery(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running

    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route)) as url:
        status, _, page = request(url, path='/proposals/new')
        assert status == 200
        assert 'Bounded offline keyword discovery' in page
        supplied = form(page, '/proposals')
        assert 'published_from' in supplied and 'published_before' in supplied
        supplied.update(purpose=['Find sunscreen evidence'], intent=['expansion'], subject_ids=['product:sunscreen'],
                        search_queries=['sunscreen review'], published_from=['2026-10-01T00:00:00Z'],
                        published_before=['2026-10-10T00:00:00Z'])
        assert request(url, 'POST', '/proposals', {**supplied, 'route': ['brightdata-tiktok']})[0] == 422
        assert tasks.list_proposals(HUMAN) == []
        status, headers, _ = request(url, 'POST', '/proposals', supplied)
        assert status == 303
        path = headers['Location']
        review = request(url, path=path)[2]
        assert 'literal-caption-subject-time-v1' in review
        assert '2026-10-10T00:00:00Z' in review
        assert 'does not perform query discovery' not in review
        action = path + '/approve'
        approval = form(review, action)
        assert request(url, 'POST', action, approval)[0] == 422
        assert tasks.list(HUMAN) == []
        approval['reviewed'] = ['yes']
        status, headers, _ = request(url, 'POST', action, approval)
        assert status == 303
        task_path = headers['Location']
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_path.split('/')[-1], WORKER)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id)) as url:
        detail = request(url, path=task_path)[2]
        assert 'usable_update' in detail and 'bounded_query_discovery' in detail
        assert path in detail
        publication_path = f'/knowledge/publications/{completed["publication_ids"][0]}?include_synthetic=yes'
        assert publication_path in detail
        published = request(url, path=publication_path)[2]
        assert 'Daily sunscreen review' in published
        assert '2026-10-04' in published


def test_discovery_dispatches_share_configured_cost_admission_with_existing_route(stack, tmp_path):
    from test_costs import accounting
    from test_cost_admission import ceiling

    tasks, evidence, _ = discovery_setup(stack, tmp_path, [record('first'), record('second')])
    costs = accounting(tasks)
    costs.configure_route('offline-keyword-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    task_id = approved_task(tasks)
    waiting = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert waiting['outcome'] is None
    assert waiting['progress']['reason'] == 'cost_allowance_exhausted'
    assert waiting['coverage']['collected_observations'] == 1
    assert waiting['coverage']['requests_used'] == 1
    assert waiting['publication_ids'] == []
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.125'
    assert len(costs.list(HUMAN, task_id=task_id)) == 2
    ceiling(costs, '0.250')
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['published_members'] == 2
    assert completed['coverage']['requests_used'] == 2
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0.25'
    assert 'Daily sunscreen review' not in json.dumps(costs.list(HUMAN, task_id=task_id))


def test_unassessable_source_selection_is_partial_failure_instead_of_valid_empty_coverage(stack, tmp_path):
    malformed = record('bad-date', published='unknown')
    tasks, evidence, _ = discovery_setup(stack, tmp_path, [record('valid'), malformed])
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(approved_task(tasks), WORKER)
    assert completed['outcome'] == 'partial_update'
    assert completed['failure'] == {'phase': 'ingestion', 'code': 'discovery_selection_unassessable'}
    assert completed['coverage']['quarantined_observations'] == 1
    assert completed['coverage']['unassessable_records'] == 1
    assert completed['coverage']['remaining_inputs'] == 1
    assert completed['coverage']['published_members'] == 1
    assert 'bad-date' not in json.dumps(completed)
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='valid-only', include_synthetic=True)
    assert len(result['members']) == 1


def test_empty_and_unchanged_queries_do_not_invent_new_publication_benefit(stack, tmp_path):
    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    first = OfflineTaskWorker(tasks.db, evidence.root).run_one(approved_task(tasks), WORKER)
    unchanged = OfflineTaskWorker(tasks.db, evidence.root).run_one(
        approved_task(tasks, proposal(search_queries=('SUNSCREEN',)), request_id='different-query'), WORKER)
    assert unchanged['outcome'] == 'no_usable_update'
    assert unchanged['coverage']['unchanged_members'] == 1
    assert unchanged['coverage']['published_members'] == 0
    assert unchanged['publication_ids'] == []
    assert len(KnowledgePublications(tasks.db).list(HUMAN, include_synthetic=True)) == 1
    empty = OfflineTaskWorker(tasks.db, evidence.root).run_one(
        approved_task(tasks, proposal(search_queries=('not present',)), request_id='empty-query'), WORKER)
    assert empty['outcome'] == 'no_usable_update'
    assert empty['coverage']['requests_used'] == 1
    assert empty['coverage']['collected_observations'] == 0
    assert empty['coverage']['remaining_inputs'] == 0
    assert empty['coverage']['market_coverage'] == 'unknown'
    assert empty['publication_ids'] == []
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='no-duplicate', include_synthetic=True)
    assert len(result['members']) == 1
    assert result['manifest'][0]['publication_id'] == first['publication_ids'][0]


@pytest.mark.parametrize(('bounds', 'code'), [((1, 3, 3), 'request_limit_reached'),
    ((3, 1, 3), 'record_limit_reached'), ((3, 3, 1), 'record_limit_reached')])
def test_record_and_request_bounds_publish_only_the_bounded_subset(stack, tmp_path, bounds, code):
    from smi_ingestion.contracts import RunLimits

    tasks, evidence, _ = discovery_setup(stack, tmp_path, [record('first'), record('second')],
                                         limits=RunLimits(*bounds, 10000))
    task_id = approved_task(tasks)
    bounded = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert bounded['outcome'] == 'partial_update'
    assert bounded['failure'] == {'phase': 'collection', 'code': code}
    assert bounded['coverage']['requests_used'] == 1
    assert bounded['coverage']['collected_observations'] == 1
    assert bounded['coverage']['remaining_inputs'] == 1
    member = KnowledgePublications(tasks.db).read(bounded['publication_ids'][0], HUMAN, include_synthetic=True)['members'][0]
    assert member['coverage']['discovery']['matching_records'] == 2
    assert {a['native_id'] for a in member['assertions']} == {'creator-1', 'first'}
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == bounded


def test_unknown_capture_stays_unknown_and_withdrawal_hides_current_support(stack, tmp_path):
    source = record('unknown-capture')
    source.pop('captured_at')
    tasks, evidence, _ = discovery_setup(stack, tmp_path, [source])
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(approved_task(tasks), WORKER)
    publication = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)
    member = publication['members'][0]
    assert member['captured_at'] is None
    assert completed['coverage']['latest_captured_at'] is None
    assert member['ingested_at'] is not None
    evidence.revoke(member['observation_id'])
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='withdrawn', include_synthetic=True)['members'] == []
    hidden = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)['members'][0]
    assert hidden['availability'] == 'unavailable'
    assert 'assertions' not in hidden and 'coverage' not in hidden
    assert 'Daily sunscreen review' not in json.dumps(tasks.read(completed['task_id'], HUMAN))


def test_discovery_restart_reuses_exact_source_support_after_response_file_disappears(stack, tmp_path):
    import pytest

    tasks, evidence, response = discovery_setup(stack, tmp_path)
    task_id = approved_task(tasks)

    def interrupt(progress):
        if progress['progress']['phase'] == 'evidence_committed':
            raise RuntimeError('simulated source response interruption')

    with pytest.raises(RuntimeError, match='simulated source response interruption'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    interrupted = tasks.read(task_id, HUMAN)
    response.unlink()
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['attempts'][0]['attempt_id'] == interrupted['attempts'][0]['attempt_id']
    assert completed['attempts'][0]['run_id'] == interrupted['attempts'][0]['run_id']
    assert completed['coverage']['requests_used'] == 1
    member = KnowledgePublications(tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)['members'][0]
    assert member['observation_id'] == interrupted['progress']['observation_id']
    assert member['coverage']['discovery']['query'] == 'sunscreen review'


def test_unavailable_scope_authority_and_changed_configuration_cannot_dispatch(stack, tmp_path):
    import pytest
    from smi_ingestion.contracts import RunLimits
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext

    tasks, campaign, _, _ = setup_task(stack, tmp_path)
    assert tasks.route.capability() == {'route': 'fixture-json', 'query_discovery': False,
        'method': 'supplied-reference-fixture-v1', 'unavailable_reason': 'keyword_discovery_unavailable_supplied_reference_route'}
    with pytest.raises(EvidenceError, match='keyword_discovery_unavailable_supplied_reference_route'):
        tasks.save_proposal(proposal(), WORKER, request_id='unavailable')
    assert tasks.list_proposals(HUMAN) == []
    tasks, evidence, response = discovery_setup(stack, tmp_path)
    for index, invalid in enumerate(({'published_from': None}, {'published_before': '2026-10-01T00:00:00Z'},
            {'published_before': '2028-10-10T00:00:00Z'}, {'published_from': '2026-10-01'},
            {'search_queries': ('one', 'two')}, {'subject_ids': ()})):
        with pytest.raises(EvidenceError, match='invalid_keyword_discovery_scope'):
            tasks.save_proposal(proposal(**invalid), WORKER, request_id=f'invalid-{index}')
    bad_route = OfflineRoute(tasks.route.manifest_path, limits=RunLimits(True, 1, 1, 1000))
    with pytest.raises(EvidenceError, match='invalid_task_limits'):
        AcquisitionTasks(tasks.db, route=bad_route).save_proposal(proposal(), WORKER, request_id='invalid-limit')
    with pytest.raises(EvidenceError, match='campaign_task_authority_required'):
        tasks.submit_campaign(campaign['campaign_id'], WORKER, brief_id=campaign['brief_id'], purpose='discover', request_id='forged')
    with pytest.raises(EvidenceError, match='keyword_discovery_requires_explicit_proposal_scope'):
        tasks.submit_campaign(campaign['campaign_id'], HUMAN, brief_id=campaign['brief_id'], purpose='query in prose', request_id='implicit')
    saved = tasks.save_proposal(proposal(), WORKER, request_id='unapproved')
    view = tasks.read_proposal(saved['proposal_id'], HUMAN)
    with pytest.raises(EvidenceError, match='proposal_human_approval_required'):
        tasks.approve_proposal(saved['proposal_id'], ActorContext('local', 'unconfigured-human', 'human'),
                               scope_digest=view['scope_digest'], request_id='forged-human')
    assert tasks.list(HUMAN) == []
    task_id = approved_task(tasks)
    response.write_text(json.dumps({'records': [record('replaced')]}))
    changed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert changed['outcome'] == 'failure'
    assert changed['failure'] == {'phase': 'collection', 'code': 'discovery_response_changed'}
    assert changed['coverage']['collected_observations'] == 0
    assert changed['publication_ids'] == []


def test_entirely_unassessable_or_process_denied_response_never_publishes(stack, tmp_path):
    tasks, evidence, _ = discovery_setup(stack, tmp_path, [record('bad-date', published='unknown')])
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(approved_task(tasks), WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'ingestion', 'code': 'discovery_selection_unassessable'}
    assert failed['coverage']['published_members'] == 0
    assert failed['coverage']['unassessable_records'] == 1
    assert failed['publication_ids'] == []
    tasks, evidence, _ = discovery_setup(stack, tmp_path,
        policy={'context_id': 'denied', 'can_process': False, 'can_retain': False, 'can_display': False})
    denied = OfflineTaskWorker(tasks.db, evidence.root).run_one(approved_task(tasks, request_id='denied'), WORKER)
    assert denied['outcome'] == 'failure'
    assert denied['failure'] == {'phase': 'ingestion', 'code': 'processing_not_permitted'}
    assert denied['coverage']['collected_observations'] == 0
    assert denied['publication_ids'] == []
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='none', include_synthetic=True)['members'] == []


def test_lost_publication_acknowledgment_preserves_query_receipt_after_policy_withdrawal(stack, tmp_path):
    import pytest

    tasks, evidence, response = discovery_setup(stack, tmp_path)
    task_id = approved_task(tasks)

    def interrupt(progress):
        if progress['progress']['phase'] == 'publication_committed':
            raise RuntimeError('lost query publication acknowledgment')

    with pytest.raises(RuntimeError, match='lost query publication acknowledgment'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    committed = tasks.read(task_id, HUMAN)
    receipt = tasks.read_committed_publication(task_id, HUMAN)
    evidence.revoke(receipt['support'][0]['observation_id'])
    response.unlink()
    tasks.route.manifest_path.unlink()
    recovered = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert recovered['outcome'] == 'usable_update'
    assert recovered['publication_ids'] == committed['publication_ids']
    assert recovered['attempts'][0]['publication_support'] == committed['attempts'][0]['publication_support']
    assert recovered['coverage'] == committed['coverage']
    assert tasks.read_committed_publication(task_id, HUMAN) == receipt
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='withdrawn-recovery', include_synthetic=True)['members'] == []


def test_lost_meter_settlement_keeps_unknown_liability_and_never_reissues_discovery(stack, tmp_path):
    import pytest
    from test_costs import accounting
    from test_cost_admission import ceiling

    tasks, evidence, response = discovery_setup(stack, tmp_path)
    costs = accounting(tasks)
    costs.configure_route('offline-keyword-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.125')
    task_id = approved_task(tasks)

    def interrupt(phase):
        if phase == 'cost_settlement':
            raise RuntimeError('lost synthetic settlement')

    with pytest.raises(RuntimeError, match='lost synthetic settlement'):
        OfflineTaskWorker(tasks.db, evidence.root, before_commit=interrupt).run_one(task_id, WORKER)
    response.unlink()
    waiting = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert waiting['outcome'] is None
    assert waiting['progress']['reason'] == 'cost_operation_in_flight_or_uncertain'
    assert waiting['progress']['resumable'] is False
    assert waiting['coverage']['collected_observations'] == 0
    assert costs.allowance('fixture-oct', HUMAN)['outstanding_amount'] == '0.125'
    operation = costs.read(costs.list(HUMAN, task_id=task_id)[0]['operation_id'], HUMAN)
    assert operation['coverage'] == {'status': 'unknown', 'unknown_cost': True}
    assert operation['actuals']['amount'] is None
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)['progress']['reason'] == 'cost_operation_in_flight_or_uncertain'


@pytest.mark.parametrize(('fault', 'code'), [('scope', 'task_configuration_changed'), ('limits', 'invalid_task_limits')])
def test_worker_revalidates_immutable_discovery_configuration_before_source_dispatch(stack, tmp_path, fault, code):
    from psycopg.types.json import Jsonb

    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    task_id = approved_task(tasks)
    task = tasks.read(task_id, HUMAN)
    # Fault setup only: normal public operations expose no mutable task configuration.
    with tasks.db.connect() as connection:
        if fault == 'scope':
            scope = task['scope']
            scope['discovery']['query'] = 'broader query'
            connection.execute('UPDATE acquisition_tasks SET scope=%s WHERE id=%s', (Jsonb(scope), task_id))
        else:
            limits = task['limits']
            limits['max_records'] = 101
            connection.execute('UPDATE acquisition_tasks SET limits=%s WHERE id=%s', (Jsonb(limits), task_id))
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'collection', 'code': code}
    assert failed['coverage']['collected_observations'] == 0
    assert failed['publication_ids'] == []
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='fault-empty', include_synthetic=True)['members'] == []


def test_returned_byte_bound_stops_before_evidence_or_publication(stack, tmp_path):
    from smi_ingestion.contracts import RunLimits

    tasks, evidence, _ = discovery_setup(stack, tmp_path, limits=RunLimits(2, 2, 2, 20))
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(approved_task(tasks), WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'collection', 'code': 'byte_limit_reached'}
    assert failed['coverage']['bytes_used'] == 0
    assert failed['coverage']['collected_observations'] == 0
    assert failed['publication_ids'] == []
