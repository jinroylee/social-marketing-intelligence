from __future__ import annotations

import json
import pytest

from smi_campaigns import CampaignStore
from smi_tasks import TaskAuthority
from smi_ingestion.evidence_sets import ActorContext
from smi_knowledge import Catalog, KnowledgeQueries, KnowledgeStore, QueryScope
from test_campaigns import BRIEF, CATALOG_PATH

HUMAN = ActorContext('local', 'task-marketer', 'human')
WORKER = ActorContext('local', 'offline-task-worker', 'automation')


def setup_task(stack, tmp_path, *, payload=None, items=None, policy=None, legacy_schema=False):
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
    tasks = AcquisitionTasks(db, route=OfflineRoute(manifest), authority=TaskAuthority.for_human(HUMAN.actor_id))
    if legacy_schema:
        from pathlib import Path
        with db.connect() as connection:
            connection.execute((Path(__file__).with_name("fixtures") / "acquisition-v1.sql").read_text())
    else:
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
    tasks = AcquisitionTasks(tasks.db, route=tasks.route, authority=TaskAuthority(
        campaign_humans=frozenset({HUMAN.actor_id}), campaign_automations=frozenset({WORKER.actor_id})))
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
        AcquisitionTasks(tasks.db, 'foreign', route=tasks.route, authority=TaskAuthority.for_human(foreign.actor_id)).submit_campaign(
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
        AcquisitionTasks(tasks.db, route=OfflineRoute(manifest), authority=TaskAuthority.for_human(HUMAN.actor_id)).submit_campaign(
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
        assert 'Origin: &quot;campaign&quot;' in queued
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


def test_fixed_limits_publish_valid_subset_with_explicit_incomplete_input(stack, tmp_path):
    from smi_ingestion.contracts import RunLimits
    from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path, items=[
        {'path': 'account.json', 'reference': 'synthetic://account/first'},
        {'path': 'account.json', 'reference': 'synthetic://account/second'},
    ])
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(1, 1, 1, 1000)), authority=tasks.authority)
    accepted = submit(tasks, campaign)
    limited = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert limited['outcome'] == 'partial_update'
    assert limited['failure'] == {'phase': 'collection', 'code': 'record_limit_reached'}
    assert limited['limits'] == {'max_requests': 1, 'max_pages': 1, 'max_records': 1, 'max_bytes': 1000}
    assert limited['coverage']['collected_observations'] == 1
    assert limited['coverage']['ingested_observations'] == 1
    assert limited['coverage']['published_members'] == 1
    assert limited['coverage']['remaining_inputs'] == 1
    assert len(limited['publication_ids']) == 1
    assert len(KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='limited', include_synthetic=True)['members']) == 1


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


def test_campaign_basis_remains_current_until_dependent_transaction_commits(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from dataclasses import replace
    from threading import Event
    import pytest
    from smi_ingestion.evidence import EvidenceError

    tasks, campaign, _, _ = setup_task(stack, tmp_path)
    campaigns = CampaignStore(tasks.db)
    attempted = Event()

    def revise():
        attempted.set()
        return campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Successor question'), HUMAN,
                                      expected_version=1, request_id='successor')

    with ThreadPoolExecutor(max_workers=1) as pool:
        with tasks.db.connect() as connection:
            campaigns.require_current_brief(campaign['campaign_id'], campaign['brief_id'], HUMAN,
                                            expected_version=1, connection=connection)
            future = pool.submit(revise)
            assert attempted.wait(5)
            with pytest.raises(TimeoutError):
                future.result(timeout=0.1)
        assert future.result(timeout=5)['brief_version'] == 2
    with tasks.db.connect() as connection:
        with pytest.raises(EvidenceError, match='brief_version_conflict'):
            campaigns.require_current_brief(campaign['campaign_id'], campaign['brief_id'], HUMAN,
                                            expected_version=1, connection=connection)
    assert tasks.list(HUMAN) == []


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
    denied = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest), authority=TaskAuthority.for_human(HUMAN.actor_id))
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
    later_tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest), authority=TaskAuthority.for_human(HUMAN.actor_id))
    later = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(later_tasks, campaign, request_id='new-capture')['task_id'], WORKER)
    assert later['outcome'] == 'usable_update'
    assert later['coverage']['unchanged_members'] == 0
    assert later['publication_ids'] != renewed['publication_ids']


def test_campaign_origin_requires_operator_authority_not_an_automation_actor_label(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import AcquisitionTasks

    tasks, campaign, _, _ = setup_task(stack, tmp_path)
    with pytest.raises(EvidenceError, match='campaign_task_authority_required'):
        submit(tasks, campaign, actor=WORKER)
    unconfigured = AcquisitionTasks(tasks.db, route=tasks.route)
    with pytest.raises(EvidenceError, match='campaign_task_authority_required'):
        submit(unconfigured, campaign)
    assistant = ActorContext('local', 'assistant', 'automation')
    configured = AcquisitionTasks(tasks.db, route=tasks.route, authority=TaskAuthority(
        campaign_automations=frozenset({'campaign-coverage-service'})))
    with pytest.raises(EvidenceError, match='campaign_task_authority_required'):
        submit(configured, campaign, actor=assistant)
    campaign_worker = ActorContext('local', 'campaign-coverage-service', 'automation')
    accepted = submit(configured, campaign, actor=campaign_worker)
    assert configured.read(accepted['task_id'], HUMAN)['initiator'] == {
        'actor_id': 'campaign-coverage-service', 'kind': 'automation'}
    assert len(tasks.list(HUMAN)) == 1


def test_saved_proposal_exact_human_approval_submits_one_durable_offline_task(stack, tmp_path):
    from smi_tasks import AcquisitionTasks, EnrichmentProposal, OfflineTaskWorker

    tasks, _, evidence, _ = setup_task(stack, tmp_path)
    assistant = ActorContext('local', 'knowledge-assistant', 'automation')
    proposal = tasks.save_proposal(EnrichmentProposal(
        purpose='Fill missing independent creator evidence', intent='expansion',
        subject_ids=('creator:outside-schedule',), search_queries=('unregistered creator topic',)),
        assistant, request_id='proposal')
    assert tasks.list(HUMAN) == []
    reopened = AcquisitionTasks(tasks.db).read_proposal(proposal['proposal_id'], HUMAN)
    assert reopened['workspace_id'] == 'local'
    assert reopened['proposer'] == {'actor_id': 'knowledge-assistant', 'kind': 'automation'}
    assert reopened['scope']['intent'] == 'expansion'
    assert reopened['scope']['purpose'] == 'Fill missing independent creator evidence'
    assert reopened['scope']['subject_ids'] == ['creator:outside-schedule']
    assert reopened['scope']['search_queries'] == ['unregistered creator topic']
    assert reopened['approval'] is None
    approval = tasks.approve_proposal(proposal['proposal_id'], HUMAN,
        scope_digest=reopened['scope_digest'], request_id='human-approval')
    accepted = tasks.submit_approved(proposal['proposal_id'], assistant, approval_id=approval['approval_id'],
        scope_digest=reopened['scope_digest'], request_id='submit-approved')
    queued = AcquisitionTasks(tasks.db).read(accepted['task_id'], HUMAN)
    assert queued['origin'] == 'assistant'
    assert queued['scope'] == reopened['scope']
    assert queued['initiator'] == {'actor_id': 'knowledge-assistant', 'kind': 'automation'}
    assert queued['proposal_approval']['approver'] == {'actor_id': 'task-marketer', 'kind': 'human'}
    assert queued['proposal_approval']['proposal_id'] == proposal['proposal_id']
    assert queued['proposal_approval']['scope_digest'] == reopened['scope_digest']
    assert AcquisitionTasks(tasks.db).read_proposal(proposal['proposal_id'], HUMAN)['approval']['task_id'] == accepted['task_id']
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(accepted['task_id'], WORKER)
    assert completed['outcome'] == 'usable_update'
    assert completed['limits']['max_records'] == 10


def test_proposal_approval_rejects_missing_changed_foreign_and_unconfigured_human_authority(stack, tmp_path):
    from dataclasses import replace
    import uuid
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import AcquisitionTasks, EnrichmentProposal

    tasks, _, _, manifest = setup_task(stack, tmp_path)
    scope = EnrichmentProposal('Refresh known account evidence', 'refresh', ('account:known',))
    saved = tasks.save_proposal(scope, WORKER, request_id='scope')
    proposal_id = saved['proposal_id']
    digest = tasks.read_proposal(proposal_id, HUMAN)['scope_digest']
    assert tasks.save_proposal(scope, WORKER, request_id='scope') == {'status': 'duplicate', 'proposal_id': proposal_id}
    with pytest.raises(EvidenceError, match='proposal_request_conflict'):
        tasks.save_proposal(replace(scope, subject_ids=('account:known', 'account:other')), WORKER, request_id='scope')
    for actor in (WORKER, ActorContext('local', WORKER.actor_id, 'human'), ActorContext('local', 'unconfigured-human', 'human')):
        with pytest.raises(EvidenceError, match='proposal_human_approval_required'):
            tasks.approve_proposal(proposal_id, actor, scope_digest=digest, request_id='forged')
    with pytest.raises(EvidenceError, match='proposal_human_approval_required'):
        AcquisitionTasks(tasks.db).approve_proposal(proposal_id, HUMAN, scope_digest=digest, request_id='unconfigured')
    with pytest.raises(EvidenceError, match='proposal_scope_conflict'):
        tasks.approve_proposal(proposal_id, HUMAN, scope_digest='changed', request_id='changed')
    with pytest.raises(EvidenceError, match='proposal_approval_required'):
        tasks.submit_approved(proposal_id, WORKER, approval_id=str(uuid.uuid4()), scope_digest=digest, request_id='missing')
    approval = tasks.approve_proposal(proposal_id, HUMAN, scope_digest=digest, request_id='approval')
    broader = tasks.save_proposal(replace(scope, search_queries=('broader topic',)), WORKER, request_id='broader')
    for other_id, other_digest in ((proposal_id, 'changed'), (broader['proposal_id'], digest)):
        with pytest.raises(EvidenceError, match='proposal_scope_conflict'):
            tasks.submit_approved(other_id, WORKER, approval_id=approval['approval_id'], scope_digest=other_digest, request_id='changed')
    foreign = ActorContext('foreign', 'human', 'human')
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        tasks.approve_proposal(proposal_id, foreign, scope_digest=digest, request_id='foreign')
    with pytest.raises(EvidenceError, match='enrichment_proposal_not_found'):
        AcquisitionTasks(tasks.db, 'foreign').read_proposal(proposal_id, foreign)
    with pytest.raises(EvidenceError, match='proposal_approval_required'):
        AcquisitionTasks(tasks.db, 'foreign').submit_approved(proposal_id, foreign, approval_id=approval['approval_id'], scope_digest=digest, request_id='foreign')
    manifest.write_text(manifest.read_text() + '\n')
    with pytest.raises(EvidenceError, match='proposal_input_changed'):
        tasks.submit_approved(proposal_id, WORKER, approval_id=approval['approval_id'], scope_digest=digest, request_id='changed-input')
    assert tasks.list(HUMAN) == []
    assert tasks.read_proposal(proposal_id, HUMAN)['approval']['task_id'] is None


def test_concurrent_approval_and_submission_retries_cannot_mint_another_task(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import AcquisitionTasks, EnrichmentProposal

    tasks, _, _, _ = setup_task(stack, tmp_path)
    saved = tasks.save_proposal(EnrichmentProposal('Fill subject gaps', 'fill', search_queries=('new topic',)), WORKER, request_id='proposal')
    proposal_id = saved['proposal_id']
    digest = tasks.read_proposal(proposal_id, HUMAN)['scope_digest']
    with ThreadPoolExecutor(max_workers=2) as pool:
        approvals = list(pool.map(lambda _: tasks.approve_proposal(proposal_id, HUMAN, scope_digest=digest, request_id='approval'), range(2)))
    assert approvals[0]['approval_id'] == approvals[1]['approval_id']
    with ThreadPoolExecutor(max_workers=2) as pool:
        submissions = list(pool.map(lambda i: tasks.submit_approved(proposal_id, WORKER, approval_id=approvals[0]['approval_id'],
            scope_digest=digest, request_id='submit'), range(2)))
    assert submissions[0]['task_id'] == submissions[1]['task_id']
    assert sorted(s['status'] for s in submissions) == ['accepted', 'duplicate']
    assert len(tasks.list(HUMAN)) == 1
    assert AcquisitionTasks(tasks.db).submit_approved(proposal_id, WORKER, approval_id=approvals[0]['approval_id'],
        scope_digest=digest, request_id='submit')['task_id'] == submissions[0]['task_id']
    with pytest.raises(EvidenceError, match='approval_request_conflict'):
        tasks.approve_proposal(proposal_id, HUMAN, scope_digest=digest, request_id='alternate-approval')
    with pytest.raises(EvidenceError, match='task_request_conflict'):
        tasks.submit_approved(proposal_id, WORKER, approval_id=approvals[0]['approval_id'], scope_digest=digest, request_id='alternate-submission')
    with pytest.raises(EvidenceError, match='task_request_conflict'):
        tasks.submit_approved(proposal_id, HUMAN, approval_id=approvals[0]['approval_id'], scope_digest=digest, request_id='other-initiator')


def test_local_supplied_proposal_requires_exact_review_and_reopens_approval_after_restart(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running

    tasks, _, _, _ = setup_task(stack, tmp_path)
    with running(ReviewApp(tasks.db, actor_id='configured-approver', offline_route=tasks.route)) as url:
        status, _, page = request(url, path='/proposals/new')
        assert status == 200
        supplied = form(page, '/proposals')
        supplied.update(purpose=['<script>Fill missing knowledge</script>'], intent=['expansion'],
                        subject_ids=['account:outside-schedule'], search_queries=['new unregistered topic'])
        assert request(url, 'POST', '/proposals', {**supplied, 'origin': 'campaign'})[0] == 422
        status, headers, _ = request(url, 'POST', '/proposals', supplied)
        assert status == 303
        proposal_path = headers['Location']
        status, _, review = request(url, path=proposal_path)
        assert status == 200
        for expected in ('local', 'expansion', 'account:outside-schedule', 'new unregistered topic', '&lt;script&gt;Fill missing knowledge&lt;/script&gt;'):
            assert expected in review
        assert '<script>Fill missing knowledge</script>' not in review
        assert tasks.list(HUMAN) == []
        approval_action = proposal_path + '/approve'
        approval = form(review, approval_action)
        assert request(url, 'POST', approval_action, approval)[0] == 422
        approval['reviewed'] = ['yes']
        for forged in ({'origin': 'campaign'}, {'origin': 'schedule'}, {'actor_kind': 'human'}, {'actor_id': 'someone'}, {'approved': 'yes'}, {'purpose': 'Broader'}, {'search_queries': 'anything'}):
            assert request(url, 'POST', approval_action, {**approval, **forged})[0] == 422
        assert request(url, 'POST', approval_action, {**approval, 'scope_digest': 'changed'})[0] == 409
        assert request(url, 'POST', approval_action, {**approval, 'csrf': 'forged'})[0] == 422
        assert request(url, 'POST', approval_action, approval, headers={'Origin': 'http://foreign.invalid'})[0] == 403
        status, headers, _ = request(url, 'POST', approval_action, approval)
        assert status == 303
        task_path = headers['Location']
        assert request(url, 'POST', approval_action, approval)[1]['Location'] == task_path
    with running(ReviewApp(tasks.db)) as url:
        status, _, reopened = request(url, path=proposal_path)
        assert status == 200
        assert 'configured-approver' in reopened
        assert task_path in reopened
        status, _, task_page = request(url, path=task_path)
        assert status == 200
        assert 'configured-approver' in task_page
        assert proposal_path in task_page
        assert 'new unregistered topic' in task_page
        assert request(url, path='/proposals')[0] == 200


def test_proposal_validation_preserves_editable_escaped_scope_and_retry_identity(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running

    tasks, _, _, _ = setup_task(stack, tmp_path)
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route)) as url:
        supplied = form(request(url, path='/proposals/new')[2], '/proposals')
        supplied.update(purpose=['Fill <missing> knowledge'], intent=['expansion'],
                        subject_ids=['\n'.join(f'account:{n}' for n in range(31))], search_queries=['a & b'])
        status, _, page = request(url, 'POST', '/proposals', supplied)
        assert status == 422
        retry = form(page, '/proposals')
        for field in ('request_id', 'purpose', 'intent', 'subject_ids', 'search_queries'):
            assert retry[field] == supplied[field]
        assert 'Fill &lt;missing&gt; knowledge' in page
        assert 'Fill <missing> knowledge' not in page
        assert tasks.list_proposals(HUMAN) == []
        retry['subject_ids'] = ['account:one']
        assert request(url, 'POST', '/proposals', retry)[0] == 303
        retry['search_queries'] = ['Changed <search> scope']
        status, _, page = request(url, 'POST', '/proposals', retry)
        assert status == 409
        conflict = form(page, '/proposals')
        assert conflict['request_id'] == retry['request_id']
        assert conflict['search_queries'] == retry['search_queries']
        assert len(tasks.list_proposals(HUMAN)) == 1


def test_campaign_task_errors_preserve_edits_and_identity_with_server_owned_basis(stack, tmp_path):
    from dataclasses import replace
    import uuid
    from smi_review import ReviewApp
    from test_review import form, request, running

    tasks, campaign, _, _ = setup_task(stack, tmp_path)
    path = f"/campaigns/{campaign['campaign_id']}/tasks"
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route)) as url:
        supplied = form(request(url, path=path + '/new')[2], path)
        supplied['purpose'] = ['<missing>' + 'x' * 1000]
        status, _, page = request(url, 'POST', path, supplied)
        assert status == 422
        retry = form(page, path)
        assert retry['purpose'] == supplied['purpose']
        assert retry['request_id'] == supplied['request_id']
        assert '<missing>' not in page
        assert tasks.list(HUMAN) == []

        retry['purpose'] = ['Keep my <research> question']
        CampaignStore(tasks.db).revise_brief(campaign['campaign_id'], replace(BRIEF, objective='New question'), HUMAN,
                                           expected_version=1, request_id='revised')
        status, _, page = request(url, 'POST', path, retry)
        assert status == 409
        stale = form(page, path)
        assert stale['brief_id'] == [campaign['brief_id']]
        assert stale['purpose'] == retry['purpose']
        assert stale['request_id'] == retry['request_id']
        assert 'brief version 1' in page

        forged_id = str(uuid.uuid4())
        status, _, page = request(url, 'POST', path, {**retry, 'brief_id': forged_id, 'origin': 'schedule', 'actor_id': 'forged'})
        assert status == 422
        safe = form(page, path)
        current = CampaignStore(tasks.db).read_campaign(campaign['campaign_id'], HUMAN)['briefs'][-1]
        assert safe['brief_id'] == [current['id']]
        assert not {'origin', 'actor_id'} & safe.keys()
        assert forged_id not in page
        assert request(url, 'POST', path, safe, headers={'Origin': 'http://foreign.invalid'})[0] == 403
        status, headers, _ = request(url, 'POST', path, safe)
        assert status == 303
        safe['purpose'] = ['Changed <purpose>']
        status, _, page = request(url, 'POST', path, safe)
        assert status == 409
        conflict = form(page, path)
        assert conflict['purpose'] == safe['purpose']
        assert conflict['request_id'] == safe['request_id']
        assert len(tasks.list(HUMAN)) == 1
        assert request(url, path=headers['Location'])[0] == 200


def test_approval_errors_reopen_exact_scope_and_original_action_after_submission_failure(stack, tmp_path):
    from smi_review import ReviewApp
    from smi_tasks import EnrichmentProposal
    from test_review import form, request, running

    tasks, _, _, manifest = setup_task(stack, tmp_path)
    saved = tasks.save_proposal(EnrichmentProposal('Fill <account> gaps', 'fill', ('account:one',)), WORKER, request_id='proposal')
    proposal = tasks.read_proposal(saved['proposal_id'], HUMAN)
    path = f"/proposals/{saved['proposal_id']}/approve"
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id, offline_route=tasks.route)) as url:
        approval = form(request(url, path=path.removesuffix('/approve'))[2], path)
        status, _, page = request(url, 'POST', path, approval)
        assert status == 422
        retry = form(page, path)
        assert retry['request_id'] == approval['request_id']
        assert 'reviewed' not in retry

        retry['reviewed'] = ['yes']
        status, _, page = request(url, 'POST', path, {**retry, 'scope_digest': '<forged>', 'actor_id': 'forged'})
        assert status == 422
        trusted = form(page, path)
        assert trusted['scope_digest'] == [proposal['scope_digest']]
        assert trusted['request_id'] == retry['request_id']
        assert trusted['reviewed'] == ['yes']
        assert 'actor_id' not in trusted
        assert '&lt;forged&gt;' not in page
        status, _, page = request(url, 'POST', path, {**trusted, 'scope_digest': 'wrong-digest'})
        assert status == 409
        assert form(page, path)['scope_digest'] == [proposal['scope_digest']]

        original_manifest = manifest.read_text()
        manifest.write_text(original_manifest + '\n')
        status, _, page = request(url, 'POST', path, trusted)
        assert status == 422
        durable = tasks.read_proposal(saved['proposal_id'], HUMAN)['approval']
        assert durable['request_id'] == trusted['request_id'][0]
        retry = form(page, path)
        assert retry['request_id'] == [durable['request_id']]
        assert retry['scope_digest'] == [proposal['scope_digest']]
        assert tasks.list(HUMAN) == []

        status, _, page = request(url, 'POST', path, {**retry, 'request_id': 'another-action'})
        assert status == 409
        retry = form(page, path)
        assert retry['request_id'] == [durable['request_id']]
        manifest.write_text(original_manifest)
        assert request(url, 'POST', path, {**retry, 'csrf': 'forged'})[0] == 422
        status, headers, _ = request(url, 'POST', path, retry)
        assert status == 303
        assert request(url, 'POST', path, retry)[1]['Location'] == headers['Location']


def test_operator_saves_reviews_approves_and_submits_exact_proposal_in_separate_processes(stack, tmp_path):
    from test_cli import _cli

    tasks, _, evidence, manifest = setup_task(stack, tmp_path)
    proposal_file = tmp_path / 'supplied-proposal.json'
    proposal_file.write_text(json.dumps({'purpose': 'Refresh specific account evidence', 'intent': 'refresh',
                                        'subject_ids': ['account:known'], 'search_queries': []}))
    saved = _cli(tasks.db, evidence.root, 'save-proposal', str(proposal_file), '--request-id', 'cli-proposal',
                 '--offline-manifest', str(manifest), '--actor', 'supplied-assistant')
    assert saved.returncode == 0, saved.stdout + saved.stderr
    proposal_id = json.loads(saved.stdout)['proposal_id']
    inspected = _cli(tasks.db, evidence.root, 'inspect-proposal', proposal_id)
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    digest = json.loads(inspected.stdout)['scope_digest']
    missing_action = _cli(tasks.db, evidence.root, 'approve-proposal', proposal_id, '--scope-digest', digest,
                          '--request-id', 'cli-approval', '--actor', 'cli-human')
    assert missing_action.returncode != 0
    assert tasks.read_proposal(proposal_id, HUMAN)['approval'] is None
    approved = _cli(tasks.db, evidence.root, 'approve-proposal', proposal_id, '--scope-digest', digest,
                    '--request-id', 'cli-approval', '--actor', 'cli-human', '--approve-exact-scope')
    assert approved.returncode == 0, approved.stdout + approved.stderr
    approval_id = json.loads(approved.stdout)['approval_id']
    submitted = _cli(tasks.db, evidence.root, 'submit-approved-task', proposal_id, '--approval-id', approval_id,
                     '--scope-digest', digest, '--request-id', 'cli-submission', '--actor', 'supplied-assistant')
    assert submitted.returncode == 0, submitted.stdout + submitted.stderr
    task_id = json.loads(submitted.stdout)['task_id']
    executed = _cli(tasks.db, evidence.root, 'run-offline-task', task_id)
    assert executed.returncode == 0, executed.stdout + executed.stderr
    task = json.loads(executed.stdout)
    assert task['outcome'] == 'usable_update'
    assert task['proposal_approval']['approver']['actor_id'] == 'cli-human'
    assert task['initiator'] == {'actor_id': 'supplied-assistant', 'kind': 'automation'}
    assert task['scope']['intent'] == 'refresh'
    proposal_file.write_text(json.dumps({'purpose': 'Do anything', 'intent': 'expansion',
                                        'search_queries': ['everything'], 'approved': True, 'origin': 'campaign'}))
    forged = _cli(tasks.db, evidence.root, 'save-proposal', str(proposal_file), '--request-id', 'forged',
                  '--offline-manifest', str(manifest))
    assert forged.returncode != 0
    assert len(tasks.list_proposals(HUMAN)) == 1


def test_campaign_only_database_upgrades_without_changing_existing_task_basis(stack, tmp_path):
    from smi_tasks import EnrichmentProposal, OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, legacy_schema=True)
    existing = submit(tasks, campaign)
    tasks.migrate()
    tasks.migrate()
    reopened = tasks.read(existing['task_id'], HUMAN)
    assert reopened['origin'] == 'campaign'
    assert reopened['scope']['brief_id'] == campaign['brief_id']
    assert reopened['initiator'] == {'actor_id': 'task-marketer', 'kind': 'human'}
    assert reopened['proposal_approval'] is None
    assert reopened['status'] == 'queued'
    assert submit(tasks, campaign)['task_id'] == existing['task_id']
    proposal = tasks.save_proposal(EnrichmentProposal('Fill new gaps', 'fill', ('account:new',)), WORKER, request_id='new-proposal')
    view = tasks.read_proposal(proposal['proposal_id'], HUMAN)
    approved = tasks.approve_proposal(proposal['proposal_id'], HUMAN, scope_digest=view['scope_digest'], request_id='approval')
    assistant_task = tasks.submit_approved(proposal['proposal_id'], WORKER, approval_id=approved['approval_id'],
        scope_digest=view['scope_digest'], request_id='assistant-task')
    assert tasks.read(assistant_task['task_id'], HUMAN)['origin'] == 'assistant'
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(existing['task_id'], WORKER)['outcome'] == 'usable_update'


def test_approval_only_restart_reuses_original_human_action_to_finish_submission(stack, tmp_path):
    from smi_review import ReviewApp
    from smi_tasks import EnrichmentProposal
    from test_review import form, request, running

    tasks, _, _, _ = setup_task(stack, tmp_path)
    saved = tasks.save_proposal(EnrichmentProposal('Fill account gaps', 'fill', ('account:one',)), WORKER, request_id='proposal')
    proposal_id = saved['proposal_id']
    scope = tasks.read_proposal(proposal_id, HUMAN)
    approved = tasks.approve_proposal(proposal_id, HUMAN, scope_digest=scope['scope_digest'], request_id='original-human-action')
    assert tasks.list(HUMAN) == []
    with running(ReviewApp(tasks.db, actor_id=HUMAN.actor_id)) as url:
        path = f'/proposals/{proposal_id}'
        status, _, page = request(url, path=path)
        assert status == 200
        retry = form(page, path + '/approve')
        assert retry['request_id'] == ['original-human-action']
        retry['reviewed'] = ['yes']
        status, headers, _ = request(url, 'POST', path + '/approve', retry)
        assert status == 303
        assert request(url, 'POST', path + '/approve', retry)[1]['Location'] == headers['Location']
    reopened = tasks.read_proposal(proposal_id, HUMAN)
    assert reopened['approval']['approval_id'] == approved['approval_id']
    assert reopened['approval']['approver'] == {'actor_id': 'task-marketer', 'kind': 'human'}
    assert len(tasks.list(HUMAN)) == 1


def test_worker_recovers_committed_evidence_without_refetching_or_replacing_attempt(stack, tmp_path):
    import pytest
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']

    def interrupt(progress):
        if progress['progress']['phase'] == 'evidence_committed':
            raise RuntimeError('simulated process interruption')

    with pytest.raises(RuntimeError, match='simulated process interruption'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    interrupted = tasks.read(task_id, HUMAN)
    assert interrupted['status'] == 'ingesting'
    assert interrupted['outcome'] is None
    assert interrupted['coverage']['collected_observations'] == 1
    assert interrupted['coverage']['ingested_observations'] == 0
    assert interrupted['progress']['observation_id']
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='interrupted', include_synthetic=True)['members'] == []
    (tmp_path / 'account.json').unlink()
    recovered = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, ActorContext('local', 'recovery-worker', 'automation'))
    assert recovered['outcome'] == 'usable_update'
    assert len(recovered['attempts']) == 1
    assert recovered['attempts'][0]['attempt_id'] == interrupted['attempts'][0]['attempt_id']
    assert recovered['attempts'][0]['run_id'] == interrupted['attempts'][0]['run_id']
    assert recovered['attempts'][0]['producer'] == interrupted['attempts'][0]['producer']
    assert recovered['attempts'][0]['resumed_by'] == [{'actor_id': 'recovery-worker', 'kind': 'automation'}]
    assert recovered['coverage']['requests_used'] == 1
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='recovered', include_synthetic=True)
    assert result['members'][0]['observation_id'] == interrupted['progress']['observation_id']
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == recovered


def test_mixed_mapping_failure_publishes_only_valid_support_and_reports_remainder(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, items=[
        {'path': 'invalid.json', 'reference': 'synthetic://invalid'},
        {'path': 'account.json', 'reference': 'synthetic://valid'},
    ])
    (tmp_path / 'invalid.json').write_text(json.dumps({'account': {'id': 17}}))
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(submit(tasks, campaign)['task_id'], WORKER)
    assert completed['outcome'] == 'partial_update'
    assert completed['failure'] == {'phase': 'ingestion', 'code': 'normalization_failed'}
    assert completed['coverage']['collected_observations'] == 2
    assert completed['coverage']['ingested_observations'] == 1
    assert completed['coverage']['quarantined_observations'] == 1
    assert completed['coverage']['published_members'] == 1
    assert completed['coverage']['remaining_inputs'] == 1
    assert len(completed['publication_ids']) == 1
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='valid-subset', include_synthetic=True)
    assert len(result['members']) == 1
    assert result['members'][0]['run_id'] == completed['attempts'][0]['run_id']
    assert result['members'][0]['observation_id'] != completed['coverage']['issues'][0]['observation_id']


def test_worker_recovers_canonical_and_publication_commits_with_exact_support(stack, tmp_path):
    import pytest
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    phases = ['canonical_committed', 'publication_prepared', 'publication_committed', 'completed']
    for phase in phases:
        (tmp_path / 'account.json').write_text(json.dumps({'account': {'id': 'offline-account', 'handle': 'test-account'}}))
        # A distinct capture is a valid new update, independent of the prior task.
        manifest = tasks.route.manifest_path
        document = json.loads(manifest.read_text())
        document['captured_at'] = f'2026-10-0{phases.index(phase) + 2}T00:00:00Z'
        manifest.write_text(json.dumps(document))
        task_id = submit(tasks, campaign, request_id=phase)['task_id']

        def interrupt(progress):
            if progress['progress']['phase'] == phase:
                raise RuntimeError('simulated process interruption')

        with pytest.raises(RuntimeError, match='simulated process interruption'):
            OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
        interrupted = tasks.read(task_id, HUMAN)
        run_id = interrupted['attempts'][0]['run_id']
        support = IngestedEvidence(tasks.db).select_run(run_id, HUMAN, include_synthetic=True)
        assert len(support) == 1
        (tmp_path / 'account.json').unlink()
        recovery_actor = ActorContext('local', 'different-recovery-worker', 'automation')
        recovered = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, recovery_actor)
        assert recovered['outcome'] == 'usable_update'
        assert recovered['attempts'][0]['attempt_id'] == interrupted['attempts'][0]['attempt_id']
        assert recovered['attempts'][0]['run_id'] == run_id
        assert recovered['coverage']['requests_used'] == 1
        assert recovered['coverage']['published_members'] == 1
        assert IngestedEvidence(tasks.db).select_run(run_id, HUMAN, include_synthetic=True) == support
        publication = KnowledgePublications(tasks.db).read(recovered['publication_ids'][0], HUMAN, include_synthetic=True)
        assert publication['members'][0]['observation_id'] == support[0].observation_id
        expected_producer = recovery_actor if phase in {'canonical_committed', 'publication_prepared'} else WORKER
        assert publication['producer']['actor_id'] == expected_producer.actor_id
        assert len(KnowledgePublications(tasks.db).list(HUMAN, include_synthetic=True)) == phases.index(phase) + 1
        assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == recovered


def test_pending_collection_resumes_saved_operation_and_ambiguous_operation_never_reissues(stack, tmp_path):
    from smi_ingestion.adapters.local import LocalFileCollector
    from smi_ingestion.contracts import CollectedBatch
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)

    class SimulatedAsyncFixture:
        def __init__(self, code):
            self.code, self.starts, self.resumes = code, 0, 0

        def collect(self, manifest, checkpoint, limits):
            if 'operation_id' not in checkpoint:
                self.starts += 1
                return CollectedBatch((), {'index': 0, 'operation_id': 'simulated-operation'}, False,
                                      waiting=self.code, request_attempts=1)
            self.resumes += 1
            return LocalFileCollector('fixture-json').collect(manifest, checkpoint, limits)

    provider = SimulatedAsyncFixture('provider_pending')
    task_id = submit(tasks, campaign)['task_id']
    waiting = OfflineTaskWorker(tasks.db, evidence.root, collector=provider).run_one(task_id, WORKER)
    assert waiting['status'] == 'waiting'
    assert waiting['outcome'] is None
    assert waiting['failure'] is None
    assert waiting['progress'] == {'phase': 'waiting', 'code': 'provider_pending', 'resumable': True}
    assert waiting['coverage']['requests_used'] == 1
    assert waiting['publication_ids'] == []
    assert tasks.read(task_id, HUMAN) == waiting
    from smi_review import ReviewApp
    from test_review import request, running
    with running(ReviewApp(tasks.db)) as url:
        status, _, detail = request(url, path=f'/tasks/{task_id}')
        assert status == 200
        assert 'provider_pending' in detail
        assert 'resumable' in detail
    resumed = OfflineTaskWorker(tasks.db, evidence.root, collector=provider).run_one(task_id, WORKER)
    assert resumed['outcome'] == 'usable_update'
    assert resumed['coverage']['requests_used'] == 2
    assert resumed['attempts'][0]['attempt_id'] == waiting['attempts'][0]['attempt_id']
    assert provider.starts == 1
    assert provider.resumes == 1

    ambiguous_provider = SimulatedAsyncFixture('provider_operation_ambiguous')
    ambiguous_id = submit(tasks, campaign, request_id='ambiguous')['task_id']
    ambiguous = OfflineTaskWorker(tasks.db, evidence.root, collector=ambiguous_provider).run_one(ambiguous_id, WORKER)
    assert ambiguous['progress'] == {'phase': 'waiting', 'code': 'provider_operation_ambiguous', 'resumable': False}
    again = OfflineTaskWorker(tasks.db, evidence.root, collector=ambiguous_provider).run_one(ambiguous_id, WORKER)
    assert again['status'] == 'waiting'
    assert again['outcome'] is None
    assert again['coverage']['requests_used'] == 1
    assert again['attempts'][0]['run_id'] == ambiguous['attempts'][0]['run_id']
    assert ambiguous_provider.starts == 1
    assert ambiguous_provider.resumes == 0


def test_withdrawal_at_publication_boundary_reports_unpublished_support_without_query_visibility(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']

    def withdraw(progress):
        if progress['progress']['phase'] == 'publication_prepared':
            evidence.revoke(progress['attempts'][0]['publication_support'][0]['observation_id'])

    failed = OfflineTaskWorker(tasks.db, evidence.root, on_progress=withdraw).run_one(task_id, WORKER)
    assert failed['outcome'] == 'failure'
    assert failed['failure'] == {'phase': 'publication', 'code': 'publication_support_unavailable'}
    assert failed['coverage']['ingested_observations'] == 1
    assert failed['coverage']['published_members'] == 0
    assert failed['coverage']['unpublished_members'] == 1
    assert failed['publication_ids'] == []
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='withdrawn-preparation', include_synthetic=True)['members'] == []


def test_waiting_operation_stops_at_persisted_request_bound_without_another_call(stack, tmp_path):
    from smi_ingestion.contracts import CollectedBatch, RunLimits
    from smi_tasks import AcquisitionTasks, OfflineRoute, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path)
    tasks = AcquisitionTasks(tasks.db, route=OfflineRoute(manifest, limits=RunLimits(1, 1, 1, 1000)), authority=tasks.authority)

    class PendingFixture:
        calls = 0

        def collect(self, manifest, checkpoint, limits):
            self.calls += 1
            return CollectedBatch((), {'operation_id': 'pending'}, False, waiting='provider_pending', request_attempts=1)

    provider = PendingFixture()
    task_id = submit(tasks, campaign)['task_id']
    waiting = OfflineTaskWorker(tasks.db, evidence.root, collector=provider).run_one(task_id, WORKER)
    assert waiting['status'] == 'waiting'
    exhausted = OfflineTaskWorker(tasks.db, evidence.root, collector=provider).run_one(task_id, WORKER)
    assert exhausted['outcome'] == 'failure'
    assert exhausted['failure'] == {'phase': 'collection', 'code': 'request_limit_reached'}
    assert exhausted['coverage']['requests_used'] == 1
    assert provider.calls == 1


def test_interrupted_partial_publication_reopens_committed_coverage_without_inputs(stack, tmp_path):
    import pytest
    from smi_tasks import OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path, items=[
        {'path': 'account.json', 'reference': 'synthetic://valid'},
        {'path': 'missing.json', 'reference': 'synthetic://failed'},
    ])
    task_id = submit(tasks, campaign)['task_id']

    def interrupt(progress):
        if progress['progress']['phase'] == 'publication_committed':
            raise OSError('simulated lost acknowledgment')

    with pytest.raises(OSError, match='simulated lost acknowledgment'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    committed = tasks.read(task_id, HUMAN)
    assert committed['outcome'] is None
    assert committed['progress']['phase'] == 'publication_committed'
    assert committed['coverage']['published_members'] == 1
    assert committed['coverage']['unpublished_members'] == 0
    assert committed['coverage']['remaining_inputs'] == 1
    assert committed['failure'] == {'phase': 'collection', 'code': 'source_unavailable'}
    assert len(committed['publication_ids']) == 1
    manifest.unlink()
    (tmp_path / 'account.json').unlink()
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, ActorContext('local', 'recovery', 'automation'))
    assert completed['outcome'] == 'partial_update'
    assert completed['failure'] == committed['failure']
    assert completed['publication_ids'] == committed['publication_ids']
    assert completed['coverage'] == committed['coverage']
    result = KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='committed-partial', include_synthetic=True)
    assert len(result['members']) == 1
    assert result['manifest'][0]['publication_producer']['actor_id'] == WORKER.actor_id


def test_public_publication_request_text_cannot_authorize_an_empty_task_update(stack, tmp_path):
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from smi_tasks import OfflineTaskWorker
    from test_publications import ingest_account

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path, items=[])
    task_id = submit(tasks, campaign)['task_id']
    run_id, _ = ingest_account(stack, native_id='unrelated')
    publications = KnowledgePublications(tasks.db)
    unrelated = publications.publish(IngestedEvidence(tasks.db).select_run(run_id, HUMAN), WORKER,
                                     request_id=f'task:{task_id}', include_synthetic=True)
    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'failure'
    assert completed['failure'] == {'phase': 'publication', 'code': 'publication_request_conflict'}
    assert completed['coverage']['collected_observations'] == 0
    assert completed['coverage']['published_members'] == 0
    assert completed['publication_ids'] == []
    assert completed['attempts'][0]['publication_support'] is None
    assert publications.read(unrelated['publication_id'], HUMAN)['members'][0]['run_id'] == run_id
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == completed


@pytest.mark.parametrize('collision', ['unrelated_prepared', 'exact_prepared', 'exact_race'])
def test_public_publication_cannot_claim_prepared_task_support_without_worker_receipt(stack, tmp_path, collision):
    from smi_ingestion.support import IngestedEvidence, SupportReference
    from smi_knowledge import KnowledgePublications
    from smi_tasks import OfflineTaskWorker
    from test_publications import ingest_account

    tasks, campaign, evidence, _ = setup_task(stack, tmp_path)
    task_id = submit(tasks, campaign)['task_id']
    unrelated_run, _ = ingest_account(stack, native_id='unrelated')
    publications = KnowledgePublications(tasks.db)

    def collide(progress):
        if progress['progress']['phase'] != 'publication_prepared':
            return
        if collision == 'unrelated_prepared':
            support = IngestedEvidence(tasks.db).select_run(unrelated_run, HUMAN)
        else:
            support = tuple(SupportReference(s['observation_id'], s['derivation_id'], tuple(s['assertion_ids']), tuple(s['metric_ids']))
                            for s in progress['attempts'][0]['publication_support'])
        publications.publish(support, WORKER, request_id=f'task:{task_id}', include_synthetic=True)
        if collision != 'exact_race':
            raise RuntimeError('interrupted after unrelated public publication')

    if collision == 'exact_race':
        completed = OfflineTaskWorker(tasks.db, evidence.root, on_progress=collide).run_one(task_id, WORKER)
    else:
        with pytest.raises(RuntimeError, match='interrupted after unrelated public publication'):
            OfflineTaskWorker(tasks.db, evidence.root, on_progress=collide).run_one(task_id, WORKER)
        prepared = tasks.read(task_id, HUMAN)
        assert prepared['progress']['phase'] == 'publication_prepared'
        assert prepared['coverage']['published_members'] == 0
        assert prepared['publication_ids'] == []
        completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'failure'
    assert completed['failure'] == {'phase': 'publication', 'code': 'publication_request_conflict'}
    assert completed['coverage']['collected_observations'] == 1
    assert completed['coverage']['ingested_observations'] == 1
    assert completed['coverage']['published_members'] == 0
    assert completed['publication_ids'] == []
    assert len(publications.list(HUMAN, include_synthetic=True)) == 1


def test_lost_acknowledgment_recovers_receipted_publication_after_policy_withdrawal(stack, tmp_path):
    from smi_knowledge import KnowledgePublications
    from smi_tasks import CompletionInbox, OfflineTaskWorker

    tasks, campaign, evidence, manifest = setup_task(stack, tmp_path, payload={
        'account': {'id': 'private-account', 'handle': 'secret-source-wording'},
    })
    task_id = submit(tasks, campaign)['task_id']

    def interrupt(progress):
        if progress['progress']['phase'] == 'publication_committed':
            raise RuntimeError('lost task acknowledgment')

    with pytest.raises(RuntimeError, match='lost task acknowledgment'):
        OfflineTaskWorker(tasks.db, evidence.root, on_progress=interrupt).run_one(task_id, WORKER)
    committed = tasks.read(task_id, HUMAN)
    assert committed['progress']['phase'] == 'publication_committed'
    publication_id = committed['publication_ids'][0]
    original = KnowledgePublications(tasks.db).find_request(f'task:{task_id}', HUMAN, include_synthetic=True)
    evidence.revoke(original['support'][0]['observation_id'])
    manifest.unlink()
    (tmp_path / 'account.json').unlink()

    completed = OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, ActorContext('local', 'successor', 'automation'))
    assert completed['outcome'] == 'usable_update'
    assert completed['coverage'] == committed['coverage']
    assert completed['publication_ids'] == [publication_id]
    assert completed['attempts'][0]['producer'] == committed['attempts'][0]['producer']
    assert completed['attempts'][0]['publication_support'] == committed['attempts'][0]['publication_support']
    assert KnowledgePublications(tasks.db).find_request(f'task:{task_id}', HUMAN, include_synthetic=True) == original
    historical = KnowledgePublications(tasks.db).read(publication_id, HUMAN, include_synthetic=True)
    assert historical['producer'] == {'actor_id': WORKER.actor_id, 'kind': 'automation'}
    assert historical['current_coverage']['available_members'] == 0
    assert 'assertions' not in historical['members'][0]
    assert 'secret-source-wording' not in json.dumps(completed)
    assert KnowledgeQueries(tasks.db).search(QueryScope(), HUMAN, request_id='withdrawn', include_synthetic=True)['members'] == []
    event = CompletionInbox(tasks.db).list(HUMAN)[0]
    assert event['coverage']['published_members'] == 1
    assert event['current_coverage'] == {'available_members': 0, 'unavailable_members': 1}
    assert event['publications'][0]['href'] is None
    assert OfflineTaskWorker(tasks.db, evidence.root).run_one(task_id, WORKER) == completed
