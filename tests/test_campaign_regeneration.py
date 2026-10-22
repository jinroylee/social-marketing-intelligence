"""Explicit campaign regeneration at public owner and protected HTTP seams."""

import pytest

from smi_tasks import CompletionInbox, OfflineTaskWorker
from test_campaign_coverage import freeze_clock, journey, recommend
from test_keyword_discovery import record
from test_publications import HUMAN
from test_tasks import WORKER


def completed_discovery(stack, tmp_path, monkeypatch, *, mode='usable', ranked=False, initial_support=False, display_denied=False):
    import hashlib
    import json
    freeze_clock(monkeypatch)
    app, campaign, evidence = journey(stack, tmp_path)
    response = tmp_path / 'discovery-response.json'
    records = [record('campaign-update', caption='Hero Cushion source-only-regeneration-secret', subjects=('product:aprilskin-hero-cushion',))]
    if mode == 'none':
        records = []
    elif mode == 'partial':
        records.append({'invalid': 'record'})
    response.write_text(json.dumps({'records': records}))
    manifest = app.tasks.route.manifest_path
    document = json.loads(manifest.read_text())
    if display_denied:
        document['policy']['can_display'] = False
    document['response_sha256'] = hashlib.sha256(response.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(document))
    if ranked:
        from test_criteria_interpretation import configured
        from test_ranked_recommendations import RankingTransport
        app.campaigns, _, _ = configured((app.campaigns,))
        app.campaigns.model_transport = RankingTransport()
    if initial_support:
        from test_campaign_coverage import publish_captions
        publish_captions(app, stack, tmp_path, count=1)
    saved = recommend(app, campaign, ranked=ranked, include_synthetic=True)
    original = app.campaigns.read_shortlist(saved['shortlist_id'], HUMAN, include_synthetic=True)
    task_id = app.read(saved['shortlist_id'], HUMAN, include_synthetic=True)['enrichment']['task_id']
    if mode == 'failure':
        response.unlink()
    completed = OfflineTaskWorker(app.tasks.db, evidence.root).run_one(task_id, WORKER)
    return app, campaign, original, completed


@pytest.mark.parametrize('initial_support', [False, True])
def test_campaign_completion_offers_exact_regeneration_without_changing_saved_history(stack, tmp_path, monkeypatch, initial_support):
    app, campaign, original, completed = completed_discovery(stack, tmp_path, monkeypatch, initial_support=initial_support)
    assert completed['outcome'] == 'usable_update'
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    assert event['campaign_discovery'] == {
        'campaign_id': campaign['campaign_id'], 'shortlist_id': original['shortlist_id'],
        'regeneration_href': '/inbox/' + event['event_id'] + '/regenerate', 'reason': None}
    assert [p['publication_id'] for p in event['publications']] == completed['publication_ids']
    assert app.campaigns.read_shortlist(original['shortlist_id'], HUMAN, include_synthetic=True) == original
    assert app.campaigns.read_campaign(campaign['campaign_id'], HUMAN)['shortlist_version'] == 1


def test_explicit_marketer_action_saves_attributed_current_successor_and_reopens_exact_retry(stack, tmp_path, monkeypatch):
    from dataclasses import replace
    from smi_tasks import CampaignRecommendations, AcquisitionTasks
    from smi_campaigns import CampaignStore
    from test_campaigns import AUTOMATION, BRIEF
    app, campaign, original, completed = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    options = dict(brief_id=campaign['brief_id'], expected_brief_version=1, expected_shortlist_version=1,
                   request_id='explicit-regeneration', include_synthetic=True)
    from test_criteria_interpretation import configured
    app.campaigns, _, unused_model = configured((app.campaigns,))
    saved = app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options)
    assert unused_model.calls == []
    successor = app.campaigns.read_shortlist(saved['shortlist_id'], HUMAN, include_synthetic=True)
    assert successor['version'] == 2 and successor['selected'][0]['account_key']['native_id'] == 'creator-1'
    assert successor['method_version'] == original['method_version']
    assert successor['status'] == 'generated' and successor['recorded_by'] == AUTOMATION.actor_id
    assert successor['selected'][0]['acknowledged_unknowns'] == []
    assert {s['publication_id'] for s in successor['selected'][0]['support_manifest']} == set(completed['publication_ids'])
    app.tasks.migrate()
    action = app.read_regeneration('explicit-regeneration', HUMAN)
    assert action['initiator'] == {'actor_id': HUMAN.actor_id, 'kind': 'human'}
    assert action['event_id'] == event['event_id'] and action['source_shortlist_id'] == original['shortlist_id']
    app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Later needs'), HUMAN,
                              expected_version=1, request_id='later-brief')
    freeze_clock(monkeypatch, '2027-01-01T00:00:00+00:00')
    app.tasks.route.manifest_path.unlink()
    restarted = CampaignRecommendations(CampaignStore(app.tasks.db), AcquisitionTasks(app.tasks.db))
    assert restarted.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options) == saved
    assert restarted.read_regeneration('explicit-regeneration', HUMAN) == action
    assert restarted.campaigns.read_shortlist(original['shortlist_id'], HUMAN, include_synthetic=True)['selected'] == original['selected']
    assert restarted.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 2


def test_http_restart_journey_requires_action_preserves_history_and_rejects_forged_authority(stack, tmp_path, monkeypatch):
    from smi_review import ReviewApp
    from test_review import form, request, running
    from test_knowledge_queries import publish_account
    from dataclasses import replace
    from test_campaigns import BRIEF
    app, campaign, original, completed = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    action = '/inbox/' + event['event_id'] + '/regenerate'
    publish_account(stack, 'after-discovery', native_id='current-account')
    revised = app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, platforms=('test', 'tiktok')), HUMAN,
                                       expected_version=1, request_id='current-context')
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id, offline_route=app.tasks.route)) as url:
        page = request(url, path='/inbox')[2]
        assert action in page and completed['publication_ids'][0] in page
        page = request(url, path=action)[2]
        assert 'Regenerate and save successor' in page and 'Deterministic and unranked' in page
        fields = form(page, action)
        assert fields['brief_id'] == [revised['brief_id']]
        assert fields['expected_brief_version'] == ['2'] and fields['expected_shortlist_version'] == ['1']
        assert app.campaigns.read_campaign(campaign['campaign_id'], HUMAN)['shortlist_version'] == 1
        for forged in ('actor', 'producer', 'method', 'ranked', 'provider', 'cost', 'approval', 'origin'):
            status, _, error = request(url, 'POST', action, {**fields, forged: ['forged-authority']})
            assert status == 422 and 'invalid_form' in error and 'forged-authority' not in error
        assert request(url, 'POST', action, fields, headers={'Origin': 'http://evil.invalid'})[0] == 403
        assert request(url, 'POST', action, fields, headers={'Host': 'evil.invalid'})[0] == 403
        assert request(url, 'POST', action, {**fields, 'csrf': ['bad']})[0] == 422
        status, headers, page = request(url, 'POST', action, fields)
        assert status == 303, page
        saved_path = headers['Location']
        assert saved_path.startswith('/shortlists/')
        assert request(url, 'POST', action, fields)[1]['Location'] == saved_path
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id)) as url:
        assert request(url, path=saved_path)[0] == 200
        assert request(url, path='/shortlists/' + original['shortlist_id'])[0] == 200
        history = request(url, path='/campaigns/' + campaign['campaign_id'])[2]
        assert saved_path in history and '/shortlists/' + original['shortlist_id'] in history
        page = request(url, path=action)[2]
        assert HUMAN.actor_id in page and saved_path in page
        fields['csrf'] = [form(page, action)['csrf'][0]]
        assert request(url, 'POST', action, fields)[1]['Location'] == saved_path
    successor = app.campaigns.read_shortlist(saved_path.split('/')[-1], HUMAN)
    assert successor['brief_id'] == revised['brief_id'] and successor['version'] == 2
    assert successor['selected'][0]['account_key']['native_id'] == 'current-account'
    assert app.campaigns.read_shortlist(original['shortlist_id'], HUMAN)['selected'] == original['selected']


@pytest.mark.parametrize('mode,outcome,offered', [('partial', 'partial_update', True), ('none', 'no_usable_update', False), ('failure', 'failure', False)])
def test_notification_offers_only_actual_usable_published_campaign_updates(stack, tmp_path, monkeypatch, mode, outcome, offered):
    from smi_ingestion.evidence import EvidenceError
    from test_campaigns import AUTOMATION
    app, campaign, original, completed = completed_discovery(stack, tmp_path, monkeypatch, mode=mode)
    assert completed['outcome'] == outcome
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    assert bool(event['campaign_discovery']['regeneration_href']) is offered
    if not offered:
        assert 'No new publication.' in event['message']
        with pytest.raises(EvidenceError, match='campaign_regeneration_unavailable'):
            app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, brief_id=campaign['brief_id'],
                expected_brief_version=1, expected_shortlist_version=1, request_id='not-offered')
    assert app.campaigns.read_campaign(campaign['campaign_id'], HUMAN)['shortlist_version'] == 1
    assert app.campaigns.read_shortlist(original['shortlist_id'], HUMAN, include_synthetic=True) == original


def test_ranked_regeneration_preserves_actual_method_and_completed_retry_never_calls_again(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from smi_campaigns import CampaignStore
    from smi_tasks import AcquisitionTasks, CampaignRecommendations
    from test_campaigns import AUTOMATION, BRIEF
    app, campaign, original, _ = completed_discovery(stack, tmp_path, monkeypatch, ranked=True)
    transport = app.campaigns.model_transport
    assert transport.calls == []  # Original empty ranked assessment made no call.
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    options = dict(brief_id=campaign['brief_id'], expected_brief_version=1, expected_shortlist_version=1,
                   request_id='ranked-action', include_synthetic=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options), range(2)))
    saved = next(r for r in results if r.get('shortlist_id'))
    successor = app.campaigns.read_shortlist(saved['shortlist_id'], HUMAN, include_synthetic=True)
    assert successor['ordering'] == 'llm_assessment_order' and successor['method_version'] == original['method_version']
    assert successor['ranking_assessment']['status'] == 'succeeded'
    assert successor['ranking_assessment']['operation_id']
    assert len(transport.calls) == 1
    app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Changed after completion'), HUMAN,
                              expected_version=1, request_id='later')
    restarted = CampaignRecommendations(CampaignStore(app.tasks.db), AcquisitionTasks(app.tasks.db))
    assert restarted.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options) == saved
    assert len(transport.calls) == 1
    assert restarted.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 2


def test_regeneration_identity_retains_body_actual_actor_and_server_producer(stack, tmp_path, monkeypatch):
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from test_campaigns import AUTOMATION
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    options = dict(brief_id=campaign['brief_id'], expected_brief_version=1, expected_shortlist_version=1,
                   request_id='identity', include_synthetic=True)
    app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options)
    changes = [({'expected_shortlist_version': 2}, HUMAN, AUTOMATION), ({'include_synthetic': False}, HUMAN, AUTOMATION),
               ({}, ActorContext('local', 'other-marketer', 'human'), AUTOMATION),
               ({}, HUMAN, ActorContext('local', 'other-automation', 'automation'))]
    for changed, actor, producer in changes:
        with pytest.raises(EvidenceError, match='campaign_regeneration_request_conflict'):
            app.regenerate(event['event_id'], actor, producer=producer, **{**options, **changed})
    with pytest.raises(EvidenceError, match='human_action_required'):
        app.regenerate(event['event_id'], AUTOMATION, producer=AUTOMATION, **options)
    with pytest.raises(EvidenceError, match='campaign_task_authority_required'):
        app.regenerate(event['event_id'], HUMAN, producer=changes[-1][2], **{**options, 'request_id': 'unauthorized'})


@pytest.mark.parametrize('changed', ['brief', 'shortlist'])
def test_stale_http_action_preserves_retry_context_and_recovers_with_new_current_request(stack, tmp_path, monkeypatch, changed):
    from dataclasses import replace
    from smi_review import ReviewApp
    from test_campaigns import AUTOMATION, BRIEF
    from test_review import form, request, running
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    action = '/inbox/' + event['event_id'] + '/regenerate'
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id, offline_route=app.tasks.route)) as url:
        fields = form(request(url, path=action)[2], action)
        if changed == 'brief':
            app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='New campaign context'), HUMAN,
                                      expected_version=1, request_id='changed')
        else:
            app.campaigns.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
                expected_brief_version=1, expected_shortlist_version=1, request_id='another-save')
        status, _, page = request(url, 'POST', action, fields)
        assert status == 409 and changed + '_version_conflict' in page
        preserved = form(page, action)
        for key in ('request_id', 'brief_id', 'expected_brief_version', 'expected_shortlist_version'):
            assert preserved[key] == fields[key]
        assert 'Reload current context for a new request' in page
        fresh = form(request(url, path=action)[2], action)
        assert fresh['request_id'] != fields['request_id']
        status, headers, page = request(url, 'POST', action, fresh)
        assert status == 303, page
        saved = app.campaigns.read_shortlist(headers['Location'].split('/')[-1], HUMAN)
        assert saved['version'] == (2 if changed == 'brief' else 3)
        assert saved['execution_profile']['brief_version'] == (2 if changed == 'brief' else 1)


@pytest.mark.parametrize('policy', ['withdrawn', 'display_denied'])
def test_unavailable_publication_withholds_offer_and_source_wording_on_action_and_errors(stack, tmp_path, monkeypatch, policy):
    from smi_knowledge import KnowledgePublications
    from smi_review import ReviewApp
    from test_review import form, request, running
    app, campaign, original, completed = completed_discovery(stack, tmp_path, monkeypatch, display_denied=policy == 'display_denied')
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    action = '/inbox/' + event['event_id'] + '/regenerate'
    publication = KnowledgePublications(app.tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id)) as url:
        if policy == 'withdrawn':
            fields = form(request(url, path=action)[2], action)
        else:
            fields = form(request(url, path='/campaigns/' + campaign['campaign_id'])[2], '/campaigns/' + campaign['campaign_id'] + '/recommendations')
        observation = publication['members'][0]['observation_id']
        if policy == 'withdrawn':
            stack[1].revoke(observation)
        for path in ('/inbox', '/inbox/' + event['event_id'], action):
            status, _, page = request(url, path=path)
            assert status == 200
            assert '/knowledge/publications/' + completed['publication_ids'][0] not in page
            assert 'source-only-regeneration-secret' not in page and 'creator-1' not in page and 'synthetic://' not in page
            assert 'Offer to regenerate' not in page and 'Regenerate and save successor' not in page
        status, _, page = request(url, 'POST', action, fields)
        assert status == 422 and 'campaign_regeneration_unavailable' in page
        assert 'source-only-regeneration-secret' not in page and 'creator-1' not in page and 'synthetic://' not in page
        assert form(page, action)['request_id'] == fields['request_id']
    assert app.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 1
    assert CompletionInbox(app.tasks.db).read(event['event_id'], HUMAN)['coverage']['published_members'] == 1



def test_nonempty_ranked_original_offers_current_context_and_retains_method_after_support_withdrawal(stack, tmp_path, monkeypatch):
    from test_campaigns import AUTOMATION
    app, campaign, original, _ = completed_discovery(stack, tmp_path, monkeypatch, ranked=True, initial_support=True)
    assert len(original['selected']) == 1
    assert len(app.campaigns.model_transport.calls) == 1
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    assert app.regeneration_offer(event['event_id'], HUMAN)['ranked'] is True
    for support in original['selected'][0]['support_manifest']:
        stack[1].revoke(support['observation_id'])
    offer = app.regeneration_offer(event['event_id'], HUMAN)
    assert offer['ranked'] is True and 'Hero Cushion' not in str(offer['actions'])
    saved = app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, brief_id=campaign['brief_id'],
        expected_brief_version=1, expected_shortlist_version=1, request_id='ranked-after-withdrawal', include_synthetic=True)
    successor = app.campaigns.read_shortlist(saved['shortlist_id'], HUMAN, include_synthetic=True)
    assert successor['method_version'] == original['method_version'] and successor['ordering'] == 'llm_assessment_order'
    assert len(app.campaigns.model_transport.calls) == 2
    assert app.regeneration_offer(event['event_id'], HUMAN)['actions'][0]['outcome']['shortlist_id'] == saved['shortlist_id']



def test_interruption_after_ranked_save_reopens_same_successor_without_redispatch_after_withdrawal(stack, tmp_path, monkeypatch):
    import psycopg
    from dataclasses import replace
    from smi_campaigns import CampaignStore
    from smi_tasks import CampaignRecommendations, AcquisitionTasks
    from smi_knowledge import KnowledgePublications
    from test_campaigns import AUTOMATION, BRIEF
    app, campaign, _, completed = completed_discovery(stack, tmp_path, monkeypatch, ranked=True)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    options = dict(brief_id=campaign['brief_id'], expected_brief_version=1, expected_shortlist_version=1,
                   request_id='lost-action-ack', include_synthetic=True)
    with app.tasks.db.connect() as setup:
        setup.execute("CREATE FUNCTION interrupt_regeneration() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'lost action acknowledgment'; END $$")
        setup.execute('CREATE TRIGGER interrupt_regeneration BEFORE UPDATE ON campaign_regeneration_requests FOR EACH ROW EXECUTE FUNCTION interrupt_regeneration()')
    with pytest.raises(psycopg.Error):
        app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options)
    action = app.read_regeneration('lost-action-ack', HUMAN)
    assert action['outcome'] is None and len(app.campaigns.model_transport.calls) == 1
    publication = KnowledgePublications(app.tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)
    stack[1].revoke(publication['members'][0]['observation_id'])
    app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='After interrupted acknowledgment'), HUMAN,
                              expected_version=1, request_id='changed-after-save')
    with app.tasks.db.connect() as setup:
        setup.execute('DROP TRIGGER interrupt_regeneration ON campaign_regeneration_requests')
    restarted = CampaignRecommendations(CampaignStore(app.tasks.db), AcquisitionTasks(app.tasks.db, authority=app.tasks.authority))
    saved = restarted.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options)
    assert saved['shortlist_id'] and restarted.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 2
    assert len(app.campaigns.model_transport.calls) == 1
    assert restarted.read_regeneration('lost-action-ack', HUMAN)['outcome'] == saved
    successor = restarted.campaigns.read_shortlist(saved['shortlist_id'], HUMAN, include_synthetic=True)
    assert successor['selected'][0]['reason'] is None and successor['selected'][0]['support_manifest'] is None
    assert restarted.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options) == saved


def test_ranked_action_failure_is_visible_without_deterministic_fallback_or_later_reissue(stack, tmp_path, monkeypatch):
    from smi_campaigns import CampaignStore
    from smi_tasks import AcquisitionTasks, CampaignRecommendations
    from test_campaigns import AUTOMATION
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch, ranked=True)
    configured_store = app.campaigns
    app.campaigns = CampaignStore(app.tasks.db)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    options = dict(brief_id=campaign['brief_id'], expected_brief_version=1, expected_shortlist_version=1,
                   request_id='blocked-model', include_synthetic=True)
    blocked = app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options)
    assert blocked['status'] == 'blocked' and blocked['reason'] == 'model_route_unavailable'
    assert blocked['shortlist_id'] is None and app.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 1
    restarted = CampaignRecommendations(configured_store, AcquisitionTasks(app.tasks.db))
    assert restarted.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options) == blocked
    assert configured_store.model_transport.calls == []
    assert restarted.regeneration_offer(event['event_id'], HUMAN)['actions'][0]['outcome'] == blocked



def test_same_ranked_action_can_reopen_in_flight_without_holding_database_locks_or_calling_again(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from test_campaigns import AUTOMATION
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch, ranked=True)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    entered, release = Event(), Event()
    def pause_external_transport():
        entered.set()
        assert release.wait(10)
    app.campaigns.model_transport.on_call = pause_external_transport
    options = dict(brief_id=campaign['brief_id'], expected_brief_version=1, expected_shortlist_version=1,
                   request_id='in-flight', include_synthetic=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(app.regenerate, event['event_id'], HUMAN, producer=AUTOMATION, **options)
        try:
            assert entered.wait(10)
            duplicate = executor.submit(app.regenerate, event['event_id'], HUMAN, producer=AUTOMATION, **options).result(timeout=5)
            assert duplicate['status'] == 'in_progress' and duplicate['shortlist_id'] is None
            assert app.read_regeneration('in-flight', HUMAN)['outcome'] is None
        finally:
            release.set()
        saved = first.result(timeout=10)
    assert saved['shortlist_id'] and len(app.campaigns.model_transport.calls) == 1
    assert app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, **options) == saved


def test_http_recovers_exact_interrupted_action_after_restart_without_appending_another_successor(stack, tmp_path, monkeypatch):
    from smi_review import ReviewApp
    from test_review import Forms, form, request, running
    app, campaign, original, _ = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    action = '/inbox/' + event['event_id'] + '/regenerate'
    with app.tasks.db.connect() as setup:
        setup.execute("CREATE FUNCTION interrupt_action_receipt() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'interrupted receipt'; END $$")
        setup.execute('CREATE TRIGGER interrupt_action_receipt BEFORE UPDATE ON campaign_regeneration_requests FOR EACH ROW EXECUTE FUNCTION interrupt_action_receipt()')
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id, offline_route=app.tasks.route)) as url:
        fields = form(request(url, path=action)[2], action)
        assert request(url, 'POST', action, fields)[0] == 503
    assert app.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 2
    with app.tasks.db.connect() as setup:
        setup.execute('DROP TRIGGER interrupt_action_receipt ON campaign_regeneration_requests')
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id)) as url:
        page = request(url, path=action)[2]
        assert 'Reopen exact request' in page
        recovered = next(fields_for_action for target, fields_for_action in Forms(page).forms
                         if target == action and fields_for_action['request_id'] == fields['request_id'])
        assert recovered['request_id'] == fields['request_id']
        assert recovered['expected_shortlist_version'] == ['1']
        status, headers, page = request(url, 'POST', action, recovered)
        assert status == 303, page
        assert request(url, path=headers['Location'])[0] == 200
    assert app.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 2


def test_offer_shows_current_human_needs_and_generated_profile_provenance_before_selection(stack, tmp_path, monkeypatch):
    from dataclasses import replace
    from smi_review import ReviewApp
    from test_campaigns import BRIEF
    from test_criteria_interpretation import configured
    from test_review import request, running
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch)
    current = app.campaigns.revise_brief(campaign['campaign_id'], replace(BRIEF, original_input='Exclude PR <script>needs</script>'), HUMAN,
        expected_version=1, request_id='new-needs')
    model, _, _ = configured((app.campaigns,))
    interpretation = model.interpret_criteria(campaign['campaign_id'], current['brief_id'], HUMAN,
        expected_version=2, request_id='visible-profile')
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    with running(ReviewApp(app.tasks.db, HUMAN.actor_id)) as url:
        page = request(url, path='/inbox/' + event['event_id'] + '/regenerate')[2]
        assert 'Original marketer input' in page and 'Saved executable profile' in page
        assert '&lt;script&gt;needs&lt;/script&gt;' in page and '<script>needs</script>' not in page
        assert interpretation['interpretation_id'] in page and 'Exclude PR' in page and 'Prefer skincare' in page
        assert 'synthetic-model-revision-v1' in page and 'campaign-criteria-responses-v1' in page



def test_public_request_preclaim_cannot_supply_the_regeneration_assessment(stack, tmp_path, monkeypatch):
    from test_campaigns import AUTOMATION
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    preclaimed = app.campaigns.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=1, request_id='regeneration:collision')
    saved = app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, brief_id=campaign['brief_id'],
        expected_brief_version=1, expected_shortlist_version=2, request_id='collision', include_synthetic=True)
    assert saved['shortlist_id'] != preclaimed['shortlist_id'] and saved['version'] == 3
    assert app.campaigns.read_shortlist(saved['shortlist_id'], HUMAN, include_synthetic=True)['selected'][0]['account_key']['native_id'] == 'creator-1'


def test_competing_new_actions_preserve_expected_head_instead_of_appending_both(stack, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from smi_ingestion.evidence import EvidenceError
    from test_campaigns import AUTOMATION
    app, campaign, _, _ = completed_discovery(stack, tmp_path, monkeypatch)
    event = CompletionInbox(app.tasks.db).list(HUMAN)[0]
    def submit(request_id):
        try:
            return app.regenerate(event['event_id'], HUMAN, producer=AUTOMATION, brief_id=campaign['brief_id'],
                expected_brief_version=1, expected_shortlist_version=1, request_id=request_id)
        except EvidenceError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, ['one', 'two']))
    assert sum(isinstance(r, dict) and r.get('shortlist_id') is not None for r in results) == 1
    assert 'shortlist_version_conflict' in results
    assert app.campaigns.list_campaigns(HUMAN)[0]['shortlist_version'] == 2
