from __future__ import annotations

import json

from smi_campaigns import CampaignStore
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import Catalog, KnowledgeQueries, KnowledgeStore, QueryScope
from test_campaigns import BRIEF, CATALOG_PATH

HUMAN = ActorContext('local', 'task-marketer', 'human')
WORKER = ActorContext('local', 'offline-task-worker', 'automation')


def setup_task(stack, tmp_path, *, payload=None, items=None, policy=None):
    from smi_tasks import AcquisitionTasks, OfflineRoute

    db, evidence, _, _ = stack
    knowledge = KnowledgeStore(db)
    knowledge.migrate()
    knowledge.register_catalog(Catalog.load(CATALOG_PATH), HUMAN)
    campaigns = CampaignStore(db)
    campaigns.migrate()
    campaign = campaigns.start(BRIEF, HUMAN, request_id='campaign')
    (tmp_path / 'account.json').write_text(json.dumps(payload if payload is not None else {
        'account': {'id': 'offline-account', 'handle': 'test-account'},
    }))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({
        'adapter': 'fixture-json', 'provider_id': 'offline-synthetic', 'format_version': 'v1',
        'synthetic': True, 'captured_at': '2026-10-01T00:00:00Z',
        'policy': policy or {'context_id': 'offline', 'can_process': True, 'can_retain': True, 'can_display': True},
        'items': items if items is not None else [{'path': 'account.json', 'reference': 'synthetic://account/offline-account'}],
    }))
    tasks = AcquisitionTasks(db, route=OfflineRoute(manifest))
    tasks.migrate()
    return tasks, campaign, evidence, manifest


def submit(tasks, campaign, *, request_id='task', purpose='Fill campaign account coverage', actor=HUMAN):
    return tasks.submit_campaign(campaign['campaign_id'], actor, request_id=request_id,
                                 brief_id=campaign['brief_id'], purpose=purpose)


def test_campaign_task_acknowledges_before_collection_then_publishes_exact_support_after_restart(stack, tmp_path):
    from smi_tasks import AcquisitionTasks, OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    accepted = submit(tasks, campaign)
    queued = AcquisitionTasks(tasks.db).read(accepted['task_id'], HUMAN)
    assert queued['status'] == 'queued'
    assert queued['outcome'] is None
    assert queued['attempts'] == []
    assert queued['origin'] == 'campaign'
    assert queued['initiator'] == {'actor_id': 'task-marketer', 'kind': 'human'}
    assert queued['scope']['campaign_id'] == campaign['campaign_id']
    assert queued['scope']['brief_id'] == campaign['brief_id']
    assert queued['scope']['brief_version'] == 1
    assert queued['scope_version'] == 'campaign-offline-v1'
    assert queued['limits']['max_records'] == 10
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='before', include_synthetic=True)['members'] == []
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert completed['status'] == 'completed'
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage']['published_members'] == 1
    assert completed['coverage']['collected_observations'] == 1
    assert completed['coverage']['ingested_observations'] == 1
    assert len(completed['attempts']) == 1
    assert completed['attempts'][0]['producer'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert completed['attempts'][0]['run_id']
    assert len(completed['publication_ids']) == 1
    result = KnowledgeQueries(tasks.db).search(QueryScope(text='test-account'), HUMAN, request_id='after', include_synthetic=True)
    assert result['members'][0]['run_id'] == completed['attempts'][0]['run_id']
    assert result['manifest'][0]['publication_id'] == completed['publication_ids'][0]
    assert result['manifest'][0]['publication_producer']['actor_id'] == WORKER.actor_id
    assert AcquisitionTasks(tasks.db).read(accepted['task_id'], HUMAN) == completed
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER) == completed


def test_identical_retry_is_one_task_and_scope_or_actor_reuse_conflicts_before_work(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import AcquisitionTasks

    tasks, campaign, _, manifest = setup_task(stack, tmp_path)
    with ThreadPoolExecutor(max_workers=2) as executor:
        accepted = list(executor.map(lambda _: submit(tasks, campaign), range(2)))
    assert accepted[0]['task_id'] == accepted[1]['task_id']
    assert sorted(r['status'] for r in accepted) == ['accepted', 'duplicate']
    for kwargs in ({'purpose': 'Broader research'}, {'actor': WORKER}):
        with pytest.raises(EvidenceError, match='task_request_conflict'):
            submit(tasks, campaign, **kwargs)
    foreign = ActorContext('foreign', 'reader', 'human')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        submit(tasks, campaign, actor=foreign)
    with pytest.raises(EvidenceError, match='acquisition_task_not_found'):
        AcquisitionTasks(tasks.db, 'foreign').read(accepted[0]['task_id'], foreign)
    with pytest.raises(EvidenceError, match='campaign_not_found'):
        AcquisitionTasks(tasks.db, 'foreign', route=tasks.route).submit_campaign(
            campaign['campaign_id'], foreign, brief_id=campaign['brief_id'], purpose='Foreign', request_id='foreign')
    manifest.write_text(manifest.read_text() + '\n')
    with pytest.raises(EvidenceError, match='task_request_conflict'):
        submit(tasks, campaign)
    queued = tasks.read(accepted[0]['task_id'], HUMAN)
    assert queued['status'] == 'queued'
    assert queued['attempts'] == []


def test_changed_manifest_and_live_route_cannot_dispatch_live_work(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    accepted = submit(tasks, campaign)
    body = json.loads(manifest.read_text())
    body['adapter'] = 'tiktok-web'
    body['items'] = [{'reference': 'https://www.tiktok.com/@live'}]
    manifest.write_text(json.dumps(body))
    with pytest.raises(EvidenceError, match='unsupported_task_route'):
        AcquisitionTasks(tasks.db, route=OfflineRoute(manifest)).submit_campaign(
            campaign['campaign_id'], HUMAN, brief_id=campaign['brief_id'], purpose='Live', request_id='live')
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'collection', 'code': 'input_changed'}
    assert failed['coverage']['collected_observations'] == 0
    assert failed['publication_ids'] == []


def test_fetch_success_with_mapping_failure_never_claims_a_usable_kb_update(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, payload={'account': {'id': 17}})
    accepted = submit(tasks, campaign)
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'ingestion', 'code': 'normalization_failed'}
    assert failed['coverage']['collected_observations'] == 1
    assert failed['coverage']['ingested_observations'] == 0
    assert failed['coverage']['published_members'] == 0
    assert failed['publication_ids'] == []
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='failed', include_synthetic=True)['members'] == []


def test_empty_or_identity_free_inputs_finish_without_a_fictitious_update(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, items=[])
    accepted = submit(tasks, campaign)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert completed['outcome'] == 'no_usable_update'
    assert completed['coverage']['collected_observations'] == 0
    assert completed['coverage']['market_coverage'] == 'unknown'
    assert completed['publication_ids'] == []


def test_another_task_over_unchanged_published_capture_reports_no_new_usable_update(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    first = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    second = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign, request_id='same-capture')['task_id'], WORKER)
    assert first['outcome'] == 'usable_update'
    assert second['outcome'] == 'no_usable_update'
    assert second['coverage']['unchanged_members'] == 1
    assert second['coverage']['published_members'] == 0
    assert second['publication_ids'] == []
    assert second['attempts'][0]['run_id'] != first['attempts'][0]['run_id']
    current = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='only-first', include_synthetic=True)
    assert len(current['members']) == 1
    assert current['members'][0]['run_id'] == first['attempts'][0]['run_id']


def test_local_form_establishes_authority_and_reopens_task_publication_after_restart(stack, tmp_path):
    import re
    from smi_review import ReviewApp
    from smi_tasks import OfflineTaskWorker
    from test_review import request, running

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    form_path = f"/campaigns/{campaign['campaign_id']}/tasks/new"
    with running(ReviewApp(tasks.db, actor_id='configured-marketer', offline_route=tasks.route)) as url:
        status, _, page = request(url, path=form_path)
        assert status == 200
        csrf = re.search(r'name="csrf" value="([^"]+)"', page)[1]
        form = {'csrf': csrf, 'request_id': 'browser-task', 'brief_id': campaign['brief_id'], 'purpose': '<script>Research account coverage</script>'}
        for forged in ({'origin': 'schedule'}, {'actor_kind': 'human'}, {'actor_id': 'approved-user'}, {'approved': 'yes'}, {'route': 'tiktok-web'}):
            assert request(url, 'POST', f"/campaigns/{campaign['campaign_id']}/tasks", {**form, **forged})[0] == 422
        assert request(url, 'POST', f"/campaigns/{campaign['campaign_id']}/tasks", {**form, 'csrf': 'forged'})[0] == 422
        status, headers, _ = request(url, 'POST', f"/campaigns/{campaign['campaign_id']}/tasks", form)
        assert status == 303
        task_path = headers['Location']
        status, _, queued = request(url, path=task_path)
        assert status == 200
        assert 'queued' in queued
        assert 'configured-marketer' in queued
        assert 'schedule' not in queued
        assert '&lt;script&gt;Research account coverage&lt;/script&gt;' in queued
        assert '<script>Research account coverage</script>' not in queued
    task_id = task_path.rsplit('/', 1)[1]
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    with running(ReviewApp(tasks.db)) as url:
        status, _, detail = request(url, path=task_path)
        assert status == 200
        assert 'usable_update' in detail
        assert completed['attempts'][0]['run_id'] in detail
        assert completed['publication_ids'][0] in detail
        assert 'configured-marketer' in detail
        publication_path = f"/knowledge/publications/{completed['publication_ids'][0]}?include_synthetic=yes"
        assert publication_path in detail
        status, _, publication = request(url, path=publication_path)
        assert status == 200
        assert 'test-account' in publication
        assert request(url, path='/tasks')[0] == 200


def test_operator_submits_executes_and_inspects_a_task_in_separate_processes(stack, tmp_path):
    from test_cli import _cli

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    accepted = _cli(tasks.db, evidence.root, 'submit-campaign-task', campaign['campaign_id'],
                    '--brief-id', campaign['brief_id'], '--purpose', 'CLI evidence coverage',
                    '--request-id', 'cli-task', '--offline-manifest', str(manifest), '--actor', 'cli-marketer')
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    task_id = json.loads(accepted.stdout)['task_id']
    queued = _cli(tasks.db, evidence.root, 'inspect-task', task_id)
    assert queued.returncode == 0, queued.stdout + queued.stderr
    assert json.loads(queued.stdout)['status'] == 'queued'
    executed = _cli(tasks.db, evidence.root, 'run-offline-task', task_id, '--worker-id', 'cli-offline-worker')
    assert executed.returncode == 0, executed.stdout + executed.stderr
    result = json.loads(executed.stdout)
    assert result['outcome'] == 'usable_update'
    assert result['initiator'] == {'actor_id': 'cli-marketer', 'kind': 'human'}
    assert result['attempts'][0]['producer'] == {'actor_id': 'cli-offline-worker', 'kind': 'automation'}
    reopened = _cli(tasks.db, evidence.root, 'inspect-task', task_id)
    assert reopened.returncode == 0, reopened.stdout + reopened.stderr
    assert json.loads(reopened.stdout) == result


def test_submission_does_not_fetch_missing_payload_and_worker_sanitizes_failure(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    (tmp_path / 'account.json').unlink()
    accepted = submit(tasks, campaign)
    assert tasks.read(accepted['task_id'], HUMAN)['status'] == 'queued'
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'collection', 'code': 'source_unavailable'}
    assert str(tmp_path) not in json.dumps(failed)
    assert failed['publication_ids'] == []


def test_fixed_limits_stop_worker_without_publishing_incomplete_input(stack, tmp_path):
    from smi_ingestion.contracts import RunLimits
    from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path, items=[
        {'path': 'account.json', 'reference': 'synthetic://account/first'},
        {'path': 'account.json', 'reference': 'synthetic://account/second'},
    ])
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(1, 1, 1, 1000)))
    accepted = submit(tasks, campaign)
    limited = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert limited['outcome'] == 'failure'
    assert limited['failure'] == {'phase': 'collection', 'code': 'record_limit_reached'}
    assert limited['limits'] == {'max_requests': 1, 'max_pages': 1, 'max_records': 1, 'max_bytes': 1000}
    assert limited['coverage']['collected_observations'] == 1
    assert limited['coverage']['ingested_observations'] == 1
    assert limited['coverage']['published_members'] == 0
    assert limited['publication_ids'] == []
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='limited', include_synthetic=True)['members'] == []


def test_current_campaign_basis_stale_brief_and_worker_authority_are_explicit(stack, tmp_path):
    from dataclasses import replace
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    accepted = submit(tasks, campaign)
    with pytest.raises(EvidenceError, match='task_worker_authority_required'):
        OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], HUMAN)
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], ActorContext('foreign', 'worker', 'automation'))
    CampaignStore(tasks.db).revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Changed campaign question'), HUMAN,
                                       expected_version=1, request_id='revised')
    assert submit(tasks, campaign)['task_id'] == accepted['task_id']
    with pytest.raises(EvidenceError, match='brief_version_conflict'):
        submit(tasks, campaign, request_id='new-against-stale')
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert completed['scope']['brief_id'] == campaign['brief_id']
    assert completed['scope']['brief_version'] == 1
    assert completed['outcome'] == 'usable_update'


def test_identity_free_and_process_denied_inputs_cannot_become_published_support(stack, tmp_path):
    from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path, payload={})
    empty = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    assert empty['outcome'] == 'no_usable_update'
    assert empty['coverage']['collected_observations'] == 1
    assert empty['coverage']['ingested_observations'] == 1
    assert empty['coverage']['published_members'] == 0
    body = json.loads(manifest.read_text())
    body['policy']['can_process'] = False
    manifest.write_text(json.dumps(body))
    denied = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest))
    failed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(denied, campaign, request_id='denied')['task_id'], WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'ingestion', 'code': 'processing_not_permitted'}
    assert failed['publication_ids'] == []


def test_unchanged_detection_uses_current_policy_and_separate_capture_versions(stack, tmp_path):
    from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    first = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='original', include_synthetic=True)
    evidence.revoke(result['members'][0]['observation_id'])
    renewed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign, request_id='new-permission')['task_id'], WORKER)
    assert renewed['outcome'] == 'usable_update'
    assert renewed['publication_ids'] != first['publication_ids']
    body = json.loads(manifest.read_text())
    body['captured_at'] = '2026-10-02T00:00:00Z'
    manifest.write_text(json.dumps(body))
    later_tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest))
    later = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(later_tasks, campaign, request_id='new-capture')['task_id'], WORKER)
    assert later['outcome'] == 'usable_update'
    assert later['coverage']['unchanged_members'] == 0
    assert later['publication_ids'] != renewed['publication_ids']
