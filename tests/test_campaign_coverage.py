"""Campaign coverage journeys through public application, shortlist and task readers."""

from smi_campaigns import CampaignStore
from test_campaigns import AUTOMATION
from test_keyword_discovery import discovery_setup
from test_publications import HUMAN


def journey(stack, tmp_path):
    from smi_tasks import CampaignRecommendations, TaskAuthority, AcquisitionTasks
    tasks, evidence, _ = discovery_setup(stack, tmp_path)
    store = CampaignStore(tasks.db)
    campaign = store.list_campaigns(HUMAN)[0]
    view = store.read_campaign(campaign['campaign_id'], HUMAN)
    campaign = {'campaign_id': view['campaign_id'], 'brief_id': view['briefs'][0]['id']}
    tasks = AcquisitionTasks(tasks.db, route=tasks.route,
        authority=TaskAuthority(campaign_automations=frozenset({AUTOMATION.actor_id})))
    return CampaignRecommendations(store, tasks), campaign, evidence


def recommend(app, campaign, **options):
    return app.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=0, request_id='recommend', **options)


def test_empty_supported_shortlist_is_saved_while_one_campaign_discovery_is_queued(stack, tmp_path):
    app, campaign, _ = journey(stack, tmp_path)
    result = recommend(app, campaign)
    shortlist = app.campaigns.read_shortlist(result['shortlist_id'], HUMAN)
    assert shortlist['selected'] == []
    coverage = shortlist['coverage_assessment']
    assert coverage['profile']['version'] == 'supported-campaign-coverage-v1'
    assert coverage['result']['sufficient'] is False
    assert coverage['result']['reasons'] == ['insufficient_quantity', 'insufficient_relevance', 'insufficient_freshness']
    assert coverage['inputs']['candidate_ids'] == []
    enrichment = app.read(result['shortlist_id'], HUMAN)['enrichment']
    assert enrichment['status'] == 'submitted'
    task = app.tasks.read(enrichment['task_id'], HUMAN)
    assert task['origin'] == 'campaign' and task['proposal_approval'] is None
    assert task['status'] == 'queued' and task['attempts'] == []
    assert task['scope']['shortlist_id'] == result['shortlist_id']
    assert task['scope']['discovery']['query'] == 'Hero Cushion'
    assert task['scope']['discovery']['subject_ids'] == ['product:aprilskin-hero-cushion']
    assert recommend(app, campaign)['shortlist_id'] == result['shortlist_id']
    assert len(app.tasks.list(HUMAN)) == 1


def test_http_returns_saved_empty_result_with_automatic_task_and_reopens_after_restart(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    app, campaign, _ = journey(stack, tmp_path)
    path = '/campaigns/' + campaign['campaign_id']
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id, offline_route=app.tasks.route)) as url:
        fields = form(request(url, path=path)[2], path + '/recommendations')
        for forged in ('origin', 'task_authority', 'approval', 'coverage_profile', 'route', 'query'):
            assert request(url, 'POST', path + '/recommendations', {**fields, forged: ['campaign']})[0] == 422
        status, headers, _ = request(url, 'POST', path + '/recommendations', fields)
        assert status == 303
        saved_path = headers['Location']
        page = request(url, path=saved_path)[2]
        assert 'Campaign coverage' in page and 'insufficient_quantity' in page
        assert 'Supported candidates' in page and '0 / 3 required' in page
        assert 'Candidates with supported literal relevance' in page
        assert 'Candidates with recent known captures' in page
        assert 'Exact coverage profile and input references' in page
        assert 'supported-campaign-coverage-v1' in page and 'No accounts selected' in page
        tasks = app.tasks.list(HUMAN)
        assert len(tasks) == 1
        assert '/tasks/' + tasks[0]['task_id'] in page
        task_page = request(url, path='/tasks/' + tasks[0]['task_id'])[2]
        assert 'queued' in task_page and 'Hero Cushion' in task_page
        assert request(url, 'POST', path + '/recommendations', fields)[1]['Location'] == saved_path
    with running(ReviewApp(app.tasks.db)) as url:
        assert '/tasks/' + tasks[0]['task_id'] in request(url, path=saved_path)[2]


def freeze_clock(monkeypatch, instant='2026-10-21T00:00:00+00:00'):
    from datetime import datetime
    import smi_campaigns.store as store_module
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(instant)
    monkeypatch.setattr(store_module, 'datetime', Clock)


def publish_captions(app, stack, tmp_path, *, count=3, captured='2026-10-05T00:00:00+00:00', relevant=True):
    from smi_ingestion.evidence_sets import SnapshotImporter
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications, KnowledgeStore
    from test_evidence_sets import altered_snapshot, POLICY
    import json
    def change(data):
        data['records'] = data['records'][:count]
        data['collection_runs'] = list({r['provenance']['run_id'] for r in data['records']})
        for record in data['records']:
            record['captured_at'] = captured
            record['caption'] = 'Hero Cushion ヒーロークッション APRILSKIN' if relevant else 'A daily routine'
    tmp_path = tmp_path / 'caption-support'
    tmp_path.mkdir()
    manifest = altered_snapshot(tmp_path, change)
    config = json.loads(manifest.read_text())
    config.update(expected_posts=count, expected_accounts=count)
    manifest.write_text(json.dumps(config))
    imported = SnapshotImporter(stack[1]).import_snapshot(manifest, HUMAN, POLICY)
    document = json.loads((tmp_path / 'observations.json').read_text())
    knowledge = KnowledgeStore(app.tasks.db)
    prepared = knowledge.prepare(document['dataset_id'], 'beauty-caption-lexicon-v1', HUMAN, include_synthetic=True)
    claims = knowledge.read(prepared['run_id'], HUMAN, include_synthetic=True)['interpretations']
    publications = KnowledgePublications(app.tasks.db)
    publications.publish(IngestedEvidence(app.tasks.db).select_run(imported['run_id'], HUMAN, include_synthetic=True),
        AUTOMATION, request_id='captions', interpretation_ids=tuple(c['id'] for c in claims if c['state'] == 'supported'), include_synthetic=True)
    return imported


def test_sufficient_supported_literal_candidates_do_not_request_discovery(stack, tmp_path, monkeypatch):
    freeze_clock(monkeypatch)
    app, campaign, _ = journey(stack, tmp_path)
    publish_captions(app, stack, tmp_path)
    result = recommend(app, campaign, include_synthetic=True)
    view = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    coverage = view['shortlist']['coverage_assessment']
    assert len(view['shortlist']['selected']) == 3
    assert coverage['result'] == {'sufficient': True, 'reasons': [], 'eligible_candidates': 3,
        'relevant_candidates': 3, 'fresh_candidates': 3, 'stale_candidates': 0, 'unknown_capture_candidates': 0}
    assert view['enrichment']['status'] == 'not_needed'
    assert app.tasks.list(HUMAN) == []


def test_thin_supported_result_queues_discovery_without_replacing_its_members(stack, tmp_path, monkeypatch):
    freeze_clock(monkeypatch)
    app, campaign, evidence = journey(stack, tmp_path)
    publish_captions(app, stack, tmp_path, count=1)
    result = recommend(app, campaign, include_synthetic=True)
    saved = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    assert len(saved['shortlist']['selected']) == 1
    assert saved['shortlist']['coverage_assessment']['result']['eligible_candidates'] == 1
    task_id = saved['enrichment']['task_id']
    from smi_tasks import OfflineTaskWorker
    from test_tasks import WORKER
    completed = OfflineTaskWorker(app.tasks.db, evidence.root).run_one(task_id, WORKER)
    assert completed['outcome'] == 'no_usable_update'
    assert app.read(result['shortlist_id'], HUMAN, include_synthetic=True)['shortlist'] == saved['shortlist']
    assert app.tasks.read(task_id, HUMAN)['scope']['discovery']['published_before'] == '2026-10-21T00:00:00+00:00'


def test_stale_capture_is_reported_even_when_publication_and_import_are_new(stack, tmp_path, monkeypatch):
    freeze_clock(monkeypatch)
    app, campaign, _ = journey(stack, tmp_path)
    publish_captions(app, stack, tmp_path, captured='2026-01-01T00:00:00+00:00')
    result = recommend(app, campaign, include_synthetic=True)
    view = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    coverage = view['shortlist']['coverage_assessment']
    assert len(view['shortlist']['selected']) == 3
    assert coverage['result']['reasons'] == ['insufficient_freshness']
    assert coverage['result']['stale_candidates'] == 3
    assert coverage['result']['fresh_candidates'] == 0
    assert view['enrichment']['status'] == 'submitted'


def test_relevance_remains_unknown_for_eligible_accounts_without_supported_criterion_judgments(stack, tmp_path, monkeypatch):
    freeze_clock(monkeypatch)
    app, campaign, _ = journey(stack, tmp_path)
    publish_captions(app, stack, tmp_path, relevant=False)
    result = recommend(app, campaign, include_synthetic=True)
    view = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    coverage = view['shortlist']['coverage_assessment']['result']
    assert len(view['shortlist']['selected']) == 3
    assert coverage['reasons'] == ['insufficient_relevance']
    assert coverage['relevant_candidates'] == 0
    assert view['enrichment']['status'] == 'submitted'


def test_concurrent_retry_and_changed_clock_route_brief_reopen_exact_historical_disposition(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from test_campaigns import BRIEF
    from smi_tasks import CampaignRecommendations, AcquisitionTasks
    freeze_clock(monkeypatch)
    app, campaign, _ = journey(stack, tmp_path)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: recommend(app, campaign), range(2)))
    assert len({r['shortlist_id'] for r in results}) == 1
    result = results[0]
    original = app.read(result['shortlist_id'], HUMAN)
    freeze_clock(monkeypatch, '2027-01-01T00:00:00+00:00')
    app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Different question'), HUMAN,
        expected_version=1, request_id='revise')
    app.tasks.route.manifest_path.unlink()
    reopened = CampaignRecommendations(CampaignStore(app.tasks.db), AcquisitionTasks(app.tasks.db, authority=app.tasks.authority))
    assert recommend(reopened, campaign)['shortlist_id'] == result['shortlist_id']
    assert reopened.read(result['shortlist_id'], HUMAN)['enrichment'] == original['enrichment']
    assert reopened.read(result['shortlist_id'], HUMAN)['shortlist']['coverage_assessment'] == original['shortlist']['coverage_assessment']
    assert len(app.tasks.list(HUMAN)) == 1


def test_interrupted_admission_keeps_saved_result_and_rolls_back_task_until_retry(stack, tmp_path):
    import psycopg
    import pytest
    app, campaign, _ = journey(stack, tmp_path)
    with app.tasks.db.connect() as setup:
        setup.execute("CREATE FUNCTION interrupt_admission() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'interrupt'; END $$")
        setup.execute('CREATE TRIGGER interrupt_admission BEFORE INSERT ON campaign_discovery_requests FOR EACH ROW EXECUTE FUNCTION interrupt_admission()')
    with pytest.raises(psycopg.Error):
        recommend(app, campaign)
    history = app.campaigns.read_campaign(campaign['campaign_id'], HUMAN)
    assert len(history['shortlists']) == 1
    shortlist_id = history['shortlists'][0]['id']
    original = app.campaigns.read_shortlist(shortlist_id, HUMAN)
    assert original['selected'] == [] and original['coverage_assessment']['result']['sufficient'] is False
    assert app.tasks.list(HUMAN) == []
    assert app.tasks.read_campaign_discovery(shortlist_id, HUMAN) is None
    with app.tasks.db.connect() as setup:
        setup.execute('DROP TRIGGER interrupt_admission ON campaign_discovery_requests')
    assert recommend(app, campaign)['shortlist_id'] == shortlist_id
    assert len(app.tasks.list(HUMAN)) == 1
    assert app.campaigns.read_shortlist(shortlist_id, HUMAN) == original


def test_source_admission_refusal_is_durable_and_leaves_empty_shortlist_available(stack, tmp_path):
    import json
    app, campaign, _ = journey(stack, tmp_path)
    manifest = app.tasks.route.manifest_path
    document = json.loads(manifest.read_text())
    document['policy']['can_process'] = False
    manifest.write_text(json.dumps(document))
    result = recommend(app, campaign)
    original = app.read(result['shortlist_id'], HUMAN)
    assert original['shortlist']['selected'] == []
    assert original['enrichment']['status'] == 'refused'
    assert original['enrichment']['reason'] == 'source_policy_disallows_discovery'
    assert app.tasks.list(HUMAN) == []
    manifest.unlink()
    assert recommend(app, campaign)['shortlist_id'] == result['shortlist_id']
    assert app.read(result['shortlist_id'], HUMAN) == original


def test_worker_cost_refusal_remains_waiting_beside_the_original_shortlist(stack, tmp_path):
    from smi_tasks import OfflineTaskWorker
    from test_tasks import WORKER
    from test_costs import accounting
    from test_cost_admission import ceiling
    app, campaign, evidence = journey(stack, tmp_path)
    costs = accounting(app.tasks)
    costs.configure_route('offline-keyword-json', 'fixture-oct', HUMAN, max_units='1')
    ceiling(costs, '0.001')
    result = recommend(app, campaign)
    original = app.read(result['shortlist_id'], HUMAN)
    task_id = original['enrichment']['task_id']
    waiting = OfflineTaskWorker(app.tasks.db, evidence.root).run_one(task_id, WORKER)
    assert waiting['outcome'] is None and waiting['execution']['state'] == 'waiting'
    assert waiting['progress']['reason'] == 'cost_allowance_exhausted'
    view = app.read(result['shortlist_id'], HUMAN)
    assert view['shortlist'] == original['shortlist']
    assert view['enrichment']['task']['progress']['reason'] == 'cost_allowance_exhausted'
    assert costs.allowance('fixture-oct', HUMAN)['actual_amount'] == '0'
    from smi_review import ReviewApp
    from test_review import request, running
    with running(ReviewApp(app.tasks.db)) as url:
        page = request(url, path='/shortlists/' + result['shortlist_id'])[2]
        assert 'No accounts selected' in page and 'cost_allowance_exhausted' in page
        assert 'cost_allowance_exhausted' in request(url, path='/tasks/' + task_id)[2]


def test_assistant_cannot_select_campaign_authority_or_skip_exact_human_approval(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_tasks import EnrichmentProposal
    app, campaign, _ = journey(stack, tmp_path)
    result = recommend(app, campaign)
    assistant = ActorContext('local', 'assistant', 'automation')
    with pytest.raises(EvidenceError, match='campaign_task_authority_required'):
        app.tasks.submit_campaign_discovery(result['shortlist_id'], assistant)
    with pytest.raises(EvidenceError, match='invalid_enrichment_proposal'):
        EnrichmentProposal.from_document({'purpose': 'Need more', 'intent': 'fill', 'origin': 'campaign'})
    with pytest.raises(EvidenceError, match='proposal_approval_required'):
        app.tasks.submit_approved(campaign['campaign_id'], assistant, approval_id=campaign['brief_id'], scope_digest='forged', request_id='forged')
    assert len(app.tasks.list(HUMAN)) == 1


def test_client_task_request_cannot_preclaim_the_automatic_discovery_identity(stack, tmp_path):
    import json
    from smi_tasks import AcquisitionTasks, OfflineRoute, TaskAuthority
    app, campaign, _ = journey(stack, tmp_path)
    saved = app.campaigns.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=0, request_id='recommend')
    manifest = tmp_path / 'supplied-reference.json'
    manifest.write_text(json.dumps({'adapter': 'fixture-json', 'synthetic': True, 'items': []}))
    supplied = AcquisitionTasks(app.tasks.db, route=OfflineRoute(manifest), authority=TaskAuthority.for_human(HUMAN.actor_id))
    preclaimed = supplied.submit_campaign(campaign['campaign_id'], HUMAN, brief_id=campaign['brief_id'],
        purpose='Ordinary supplied reference work', request_id='campaign-coverage:' + saved['shortlist_id'])
    result = recommend(app, campaign)
    disposition = app.tasks.read_campaign_discovery(result['shortlist_id'], HUMAN)
    assert disposition['status'] == 'submitted'
    assert disposition['task_id'] != preclaimed['task_id']
    assert disposition['task']['scope']['route'] == 'offline-keyword-json'
    assert len(app.tasks.list(HUMAN)) == 2


def test_unknown_source_capture_never_becomes_fresh_at_import_or_publication(stack, tmp_path, monkeypatch):
    from smi_tasks import OfflineTaskWorker
    from test_keyword_discovery import approved_task, record
    from test_tasks import WORKER
    import hashlib
    import json
    freeze_clock(monkeypatch)
    app, campaign, evidence = journey(stack, tmp_path)
    response = tmp_path / 'discovery-response.json'
    item = record('unknown-capture')
    item.pop('captured_at')
    response.write_text(json.dumps({'records': [item]}))
    manifest = app.tasks.route.manifest_path
    document = json.loads(manifest.read_text())
    document['response_sha256'] = hashlib.sha256(response.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(document))
    # Assistant fixtures retain the existing exact human approval journey.
    from smi_tasks import AcquisitionTasks, TaskAuthority
    from test_tasks import HUMAN as APPROVER
    proposals = AcquisitionTasks(app.tasks.db, route=app.tasks.route, authority=TaskAuthority.for_human(APPROVER.actor_id))
    OfflineTaskWorker(app.tasks.db, evidence.root).run_one(approved_task(proposals), WORKER)
    result = recommend(app, campaign, include_synthetic=True)
    coverage = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)['shortlist']['coverage_assessment']['result']
    assert coverage['eligible_candidates'] == 1
    assert coverage['fresh_candidates'] == 0 and coverage['unknown_capture_candidates'] == 1
    assert 'insufficient_freshness' in coverage['reasons']


def test_current_policy_withholds_coverage_explanations_without_reconstructing_purged_inputs(stack, tmp_path, monkeypatch):
    freeze_clock(monkeypatch)
    app, campaign, _ = journey(stack, tmp_path)
    publish_captions(app, stack, tmp_path)
    result = recommend(app, campaign, include_synthetic=True)
    before = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    comparison = app.campaigns.read_comparison(before['shortlist']['comparison_id'], HUMAN, include_synthetic=True)
    observation_id = comparison['candidates'][0]['body']['observations'][0]
    stack[1].revoke(observation_id)
    hidden = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    coverage = hidden['shortlist']['coverage_assessment']
    assert coverage['support_state'] == 'unavailable'
    assert coverage['result'] is coverage['inputs'] is None
    assert coverage['profile'] == before['shortlist']['coverage_assessment']['profile']
    assert coverage['assessed_at'] == before['shortlist']['coverage_assessment']['assessed_at']
    assert hidden['enrichment'] == before['enrichment']
    assert recommend(app, campaign, include_synthetic=True)['shortlist_id'] == result['shortlist_id']
    assert app.read(result['shortlist_id'], HUMAN, include_synthetic=True)['shortlist']['coverage_assessment'] == coverage


def test_current_shortlist_is_available_while_worker_holds_active_execution(stack, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from smi_ingestion.contracts import CollectedBatch
    from smi_tasks import OfflineTaskWorker
    from test_tasks import WORKER
    app, campaign, evidence = journey(stack, tmp_path)
    result = recommend(app, campaign)
    original = app.read(result['shortlist_id'], HUMAN)
    started, release = Event(), Event()
    class Source:
        def collect(self, manifest, checkpoint, limits):
            started.set()
            assert release.wait(10)
            return CollectedBatch((), {}, True, request_attempts=1)
    with ThreadPoolExecutor(max_workers=1) as executor:
        running = executor.submit(OfflineTaskWorker(app.tasks.db, evidence.root, collector=Source()).run_one,
            original['enrichment']['task_id'], WORKER)
        try:
            assert started.wait(10)
            view = app.read(result['shortlist_id'], HUMAN)
            assert view['shortlist'] == original['shortlist']
            assert view['enrichment']['task']['execution']['state'] == 'running'
        finally:
            release.set()
        assert running.result(timeout=10)['outcome'] == 'no_usable_update'


def test_http_unconfigured_discovery_shows_refusal_beside_saved_supported_result(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    app, campaign, _ = journey(stack, tmp_path)
    path = '/campaigns/' + campaign['campaign_id']
    with running(ReviewApp(app.tasks.db)) as url:
        fields = form(request(url, path=path)[2], path + '/recommendations')
        status, headers, _ = request(url, 'POST', path + '/recommendations', fields)
        assert status == 303
        page = request(url, path=headers['Location'])[2]
        assert 'No accounts selected' in page and 'refused' in page
        assert 'offline_task_route_unconfigured' in page
        assert app.tasks.list(HUMAN) == []


def test_ranked_recommendation_pins_same_coverage_and_submits_without_an_extra_model_call(stack, tmp_path, monkeypatch):
    from test_criteria_interpretation import configured
    from test_ranked_recommendations import RankingTransport
    from smi_tasks import CampaignRecommendations
    freeze_clock(monkeypatch)
    app, campaign, _ = journey(stack, tmp_path)
    store, _, _ = configured((app.campaigns,))
    transport = RankingTransport()
    store.model_transport = transport
    app = CampaignRecommendations(store, app.tasks)
    publish_captions(app, stack, tmp_path, count=1)
    result = recommend(app, campaign, ranked=True, include_synthetic=True)
    assert result['status'] == 'succeeded'
    view = app.read(result['shortlist_id'], HUMAN, include_synthetic=True)
    assert view['shortlist']['ordering'] == 'llm_assessment_order'
    assert view['shortlist']['coverage_assessment']['result']['eligible_candidates'] == 1
    assert view['enrichment']['status'] == 'submitted', view['enrichment']
    assert view['enrichment']['task']['scope']['shortlist_id'] == result['shortlist_id']
    assert recommend(app, campaign, ranked=True, include_synthetic=True)['shortlist_id'] == result['shortlist_id']
    assert len(transport.calls) == 1 and len(app.tasks.list(HUMAN)) == 1


def test_upgrade_leaves_legacy_coverage_unrecorded_and_cannot_infer_historical_need(stack, tmp_path):
    app, campaign, _ = journey(stack, tmp_path)
    saved = app.campaigns.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=0, request_id='recommend')
    with app.tasks.db.connect() as setup:
        setup.execute('ALTER TABLE shortlist_revisions DROP COLUMN coverage_assessment')
    app.campaigns.migrate()
    assert recommend(app, campaign)['shortlist_id'] == saved['shortlist_id']
    view = app.read(saved['shortlist_id'], HUMAN)
    assert view['shortlist']['coverage_assessment'] is None
    assert view['enrichment']['status'] == 'refused' and view['enrichment']['reason'] == 'campaign_coverage_unrecorded'
    assert app.tasks.list(HUMAN) == []


def test_stale_human_brief_prevents_new_admission_but_preserves_saved_coverage(stack, tmp_path):
    from dataclasses import replace
    from test_campaigns import BRIEF
    app, campaign, _ = journey(stack, tmp_path)
    saved = app.campaigns.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=0, request_id='recommend')
    original = app.campaigns.read_shortlist(saved['shortlist_id'], HUMAN)
    app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Changed campaign question'), HUMAN,
        expected_version=1, request_id='revise')
    assert recommend(app, campaign)['shortlist_id'] == saved['shortlist_id']
    view = app.read(saved['shortlist_id'], HUMAN)
    assert view['shortlist']['coverage_assessment'] == original['coverage_assessment']
    assert view['enrichment']['status'] == 'refused' and view['enrichment']['reason'] == 'brief_version_conflict'
    assert app.tasks.list(HUMAN) == []


def test_discovery_scope_respects_human_publication_window_instead_of_widening_it(stack, tmp_path, monkeypatch):
    from dataclasses import replace
    from test_campaigns import BRIEF
    freeze_clock(monkeypatch)
    app, _, _ = journey(stack, tmp_path)
    campaign = app.campaigns.start(replace(BRIEF, publication_from='2026-10-01T00:00:00+00:00',
        publication_to='2026-10-10T00:00:00+00:00'), HUMAN, request_id='window-campaign')
    saved = recommend(app, campaign)
    discovery = app.read(saved['shortlist_id'], HUMAN)['enrichment']['task']['scope']['discovery']
    assert discovery['published_from'] == '2026-10-01T00:00:00+00:00'
    assert discovery['published_before'] == '2026-10-10T00:00:00+00:00'


def test_unavailable_campaign_platform_and_empty_human_window_refuse_without_losing_results(stack, tmp_path, monkeypatch):
    from dataclasses import replace
    from test_campaigns import BRIEF
    freeze_clock(monkeypatch)
    app, _, _ = journey(stack, tmp_path)
    platform = app.campaigns.start(replace(BRIEF, platforms=('x',)), HUMAN, request_id='unsupported-platform')
    saved = recommend(app, platform)
    view = app.read(saved['shortlist_id'], HUMAN)
    assert view['shortlist']['selected'] == []
    assert view['enrichment']['status'] == 'refused'
    assert view['enrichment']['reason'] == 'keyword_discovery_unavailable_campaign_platform'
    old = app.campaigns.start(replace(BRIEF, publication_from='2026-01-01T00:00:00+00:00',
        publication_to='2026-02-01T00:00:00+00:00'), HUMAN, request_id='old-window')
    saved = recommend(app, old)
    view = app.read(saved['shortlist_id'], HUMAN)
    assert view['enrichment']['reason'] == 'campaign_discovery_window_unavailable'
    assert app.tasks.list(HUMAN) == []
