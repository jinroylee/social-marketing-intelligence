"""Optional human successors through campaign and browser public interfaces."""

from smi_campaigns import CampaignStore, Selection
from test_campaigns import campaigns as campaigns_fixture
from test_current_comparisons import current_campaign
from test_knowledge_queries import publish_account
from test_publications import HUMAN
from test_recommendations import recommend

campaigns = campaigns_fixture


def curate(store, original, choices, actor=HUMAN, request_id="curate", **options):
    return store.save_shortlist(original['comparison_id'], choices, actor, confirmed=False,
        expected_version=original['version'], request_id=request_id, source_shortlist_id=original['shortlist_id'], **options)


def test_human_can_select_and_reorder_generated_accounts_without_confirming_or_mutating_original(stack):
    store, campaign = current_campaign(stack)
    publish_account(stack, 'one', native_id='one')
    publish_account(stack, 'two', native_id='two')
    publish_account(stack, 'three', native_id='three')
    generated = recommend(store, campaign)
    original = store.read_shortlist(generated['shortlist_id'], HUMAN)
    choices = tuple(Selection(s['candidate_id'], 'Investigate this supported account.', (), ('fees',))
                    for s in (original['selected'][2], original['selected'][0]))
    saved = curate(store, original, choices)
    reopened = CampaignStore(store.db).read_shortlist(saved['shortlist_id'], HUMAN)
    assert reopened['status'] == 'draft' and reopened['actor_kind'] == 'human'
    assert reopened['recorded_by'] == HUMAN.actor_id
    assert reopened['source_shortlist_id'] == original['shortlist_id']
    assert reopened['method_version'] == 'human-shortlist-curation-v1' and reopened['ordering'] == 'human_selected_order'
    assert [s['account_key']['native_id'] for s in reopened['selected']] == ['one', 'three']
    assert [s['position'] for s in reopened['selected']] == [0, 1]
    assert all(s['reason_basis'] == 'human_supplied' and s['acknowledged_unknowns'] == ['fees'] for s in reopened['selected'])
    assert reopened['executable_profile'] == original['executable_profile']
    assert [s['support_manifest'] for s in reopened['selected']] == [original['selected'][i]['support_manifest'] for i in (2, 0)]
    assert store.read_shortlist(generated['shortlist_id'], HUMAN) == {**original, 'current_shortlist_version': 2}
    assert [r['id'] for r in store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists']] == [generated['shortlist_id'], saved['shortlist_id']]


def test_http_successor_form_keeps_generated_order_and_saves_explicit_human_order_without_review(stack):
    from smi_review import ReviewApp
    from test_review import form, request, running

    store, campaign = current_campaign(stack)
    for name in ('one', 'two', 'three'):
        publish_account(stack, name, native_id=name)
    generated = recommend(store, campaign)
    original = store.read_shortlist(generated['shortlist_id'], HUMAN)
    action = '/comparisons/' + original['comparison_id'] + '/shortlists'
    path = '/comparisons/' + original['comparison_id'] + '?shortlist_id=' + original['shortlist_id']
    with running(ReviewApp(store.db, actor_id='actual-curator')) as url:
        status, _, page = request(url, path=path)
        assert status == 200
        fields = form(page, action)
        assert fields['source_shortlist_id'] == [original['shortlist_id']]
        assert fields['selected'] == [s['candidate_id'] for s in original['selected']]
        assert [fields['position_' + s['candidate_id']] for s in original['selected']] == [['1'], ['2'], ['3']]
        first, second, third = original['selected']
        fields['selected'] = [first['candidate_id'], third['candidate_id']]
        fields['position_' + first['candidate_id']] = ['2']
        fields['position_' + third['candidate_id']] = ['1']
        fields['reason_' + third['candidate_id']] = ['<script>Human starting reason</script>']
        fields['unknown_' + third['candidate_id']] = ['fees']
        fields['action'] = ['draft']
        status, headers, _ = request(url, 'POST', action, fields)
        assert status == 303
        saved_path = headers['Location']
        status, _, page = request(url, path=saved_path)
        assert status == 200 and 'draft' in page and 'actual-curator' in page
        assert 'human_selected_order' in page and original['shortlist_id'] in page
        assert '&lt;script&gt;Human starting reason&lt;/script&gt;' in page and '<script>Human starting reason</script>' not in page
        status, headers, _ = request(url, 'POST', action, fields)
        assert status == 303 and headers['Location'] == saved_path
    saved = store.read_shortlist(saved_path.split('/')[-1], HUMAN)
    assert [s['account_key']['native_id'] for s in saved['selected']] == ['one', 'three']
    assert saved['status'] == 'draft' and saved['recorded_by'] == 'actual-curator'
    assert saved['selected'][0]['acknowledged_unknowns'] == ['fees']
    assert store.read_shortlist(original['shortlist_id'], HUMAN) == {**original, 'current_shortlist_version': 2}


def test_withdrawn_support_cannot_reenter_curation_or_error_forms_and_retry_never_rebuilds_reasons(stack):
    import json

    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_review import ReviewApp
    from test_review import form, request, running

    store, campaign = current_campaign(stack)
    _, observation = publish_account(stack, 'withdrawn')
    generated = recommend(store, campaign)
    original = store.read_shortlist(generated['shortlist_id'], HUMAN)
    selected = original['selected'][0]
    choices = (Selection(selected['candidate_id'], 'CURATED_SOURCE_SENTINEL'),)
    saved = curate(store, original, choices)
    curated = store.read_shortlist(saved['shortlist_id'], HUMAN)
    action = '/comparisons/' + curated['comparison_id'] + '/shortlists'
    path = '/comparisons/' + curated['comparison_id'] + '?shortlist_id=' + curated['shortlist_id']
    with running(ReviewApp(store.db)) as url:
        _, _, page = request(url, path=path)
        fields = {**form(page, action), 'action': ['draft']}
        assert 'CURATED_SOURCE_SENTINEL' in page
        stack[1].revoke(observation.id)
        with pytest.raises(EvidenceError, match='selection_reason_or_support_unavailable'):
            curate(store, curated, choices, request_id='withdrawn-new')
        status, _, page = request(url, 'POST', action, fields)
        assert status == 422 and 'selection_reason_or_support_unavailable' in page
        assert 'CURATED_SOURCE_SENTINEL' not in page
        retry = form(page, action)
        for key in ('request_id', 'source_shortlist_id', 'expected_version', 'selected', 'position_' + selected['candidate_id']):
            assert retry[key] == fields[key]
        retry['action'] = ['draft']
        status, headers, _ = request(url, 'POST', action, retry)
        assert status == 303
        membership_only = store.read_shortlist(headers['Location'].split('/')[-1], HUMAN)
        assert membership_only['selected'][0]['reason'] is None and membership_only['review_required']
    assert curate(CampaignStore(store.db), original, choices)['status'] == 'duplicate'
    for sid in (original['shortlist_id'], curated['shortlist_id']):
        view = CampaignStore(store.db).read_shortlist(sid, HUMAN)
        assert 'CURATED_SOURCE_SENTINEL' not in json.dumps(view)
        assert view['selected'][0]['reason'] is None and view['selected'][0]['evidence'] == []
        assert view['selected'][0]['position'] == 0


def test_curation_retries_conflicts_and_concurrent_heads_preserve_one_successor(stack):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace

    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from test_campaigns import AUTOMATION, BRIEF

    store, campaign = current_campaign(stack)
    publish_account(stack, 'retry')
    original = store.read_shortlist(recommend(store, campaign)['shortlist_id'], HUMAN)
    choices = (Selection(original['selected'][0]['candidate_id'], 'Human reason'),)
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: curate(CampaignStore(store.db), original, choices), range(2)))
    assert {r['status'] for r in replies} == {'draft', 'duplicate'}
    assert len({r['shortlist_id'] for r in replies}) == 1
    curated = store.read_shortlist(replies[0]['shortlist_id'], HUMAN)
    for selected, actor in (((), HUMAN), (choices, ActorContext('local', 'other-human', 'human'))):
        with pytest.raises(EvidenceError, match='shortlist_request_conflict'):
            curate(store, original, selected, actor)
    with pytest.raises(EvidenceError, match='shortlist_request_conflict'):
        curate(store, original, choices, include_synthetic=True)
    with pytest.raises(EvidenceError, match='human_action_required'):
        curate(store, original, choices, AUTOMATION, request_id='forged')
    with pytest.raises(EvidenceError, match='shortlist_version_conflict'):
        curate(store, original, choices, request_id='stale')
    with pytest.raises(EvidenceError, match='shortlist_version_conflict'):
        store.save_shortlist(original['comparison_id'], choices, HUMAN, confirmed=False, expected_version=2,
            request_id='retarget-stale-source', source_shortlist_id=original['shortlist_id'])

    def competing(identity):
        try:
            return curate(CampaignStore(store.db), curated, (), request_id=identity)
        except EvidenceError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(competing, ('first', 'second')))
    assert sum(isinstance(r, dict) and r['status'] == 'draft' for r in outcomes) == 1
    assert outcomes.count('shortlist_version_conflict') == 1
    latest_id = next(r['shortlist_id'] for r in outcomes if isinstance(r, dict))
    latest = store.read_shortlist(latest_id, HUMAN)
    assert latest['selected'] == [] and latest['source_shortlist_id'] == curated['shortlist_id']
    store.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Changed needs'), HUMAN,
        expected_version=1, request_id='new-brief')
    with pytest.raises(EvidenceError, match='brief_version_conflict'):
        curate(store, latest, (), request_id='stale-brief')
    assert curate(CampaignStore(store.db), original, choices)['status'] == 'duplicate'
    assert len(store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists']) == 3


def test_model_order_and_assessment_remain_exact_after_offline_human_curation(stack):
    from test_ranked_recommendations import configured_current, rank

    store, campaign, _, transport = configured_current(stack)
    publish_account(stack, 'one', native_id='one')
    publish_account(stack, 'two', native_id='two')
    original = store.read_shortlist(rank(store, campaign)['shortlist_id'], HUMAN)
    assert [s['account_key']['native_id'] for s in original['selected']] == ['one', 'two']
    offline = CampaignStore(store.db)
    choices = tuple(Selection(s['candidate_id'], s['reason'], tuple(s['support_ids']), ('fees',))
                    for s in reversed(original['selected']))
    curated = offline.read_shortlist(curate(offline, original, choices)['shortlist_id'], HUMAN)
    assert [s['account_key']['native_id'] for s in curated['selected']] == ['two', 'one']
    assert curated['ranking_assessment'] is None and curated['source_shortlist_id'] == original['shortlist_id']
    assert curated['execution_profile']['ranking'] == 'human_selection'
    assert len(transport.calls) == 1
    assert offline.read_shortlist(original['shortlist_id'], HUMAN) == {**original, 'current_shortlist_version': 2}


def test_curation_form_rejects_authority_and_invalid_order_and_preserves_stale_edits(stack):
    from smi_review import ReviewApp
    from test_review import form, request, running

    store, campaign = current_campaign(stack)
    publish_account(stack, 'one', native_id='one')
    publish_account(stack, 'two', native_id='two')
    original = store.read_shortlist(recommend(store, campaign)['shortlist_id'], HUMAN)
    action = '/comparisons/' + original['comparison_id'] + '/shortlists'
    path = '/comparisons/' + original['comparison_id'] + '?shortlist_id=' + original['shortlist_id']
    with running(ReviewApp(store.db)) as url:
        _, _, page = request(url, path=path)
        fields = {**form(page, action), 'action': ['draft']}
        cid = original['selected'][0]['candidate_id']
        fields['reason_' + cid] = ['KEEP_HUMAN_EDIT']
        for key in ('actor', 'actor_kind', 'recorded_by', 'origin', 'confirmed', 'method_version', 'model', 'configuration'):
            status, _, rejected = request(url, 'POST', action, {**fields, key: ['forged']})
            assert status == 422 and 'invalid_form' in rejected
        status, _, _ = request(url, 'POST', action, fields, headers={'Origin': 'https://foreign.test'})
        assert status == 403
        status, _, _ = request(url, 'POST', action, {**fields, 'csrf': ['forged']})
        assert status == 422
        status, _, rejected = request(url, 'POST', action, {**fields, 'action': ['confirm']})
        assert status == 422 and 'human_review_acknowledgement_required' in rejected
        invalid = {**fields, 'position_' + original['selected'][1]['candidate_id']: ['1']}
        status, _, rejected = request(url, 'POST', action, invalid)
        assert status == 422 and 'invalid_selection_order' in rejected
        retry = form(rejected, action)
        assert retry['reason_' + cid] == ['KEEP_HUMAN_EDIT']
        assert retry['source_shortlist_id'] == fields['source_shortlist_id']
        curate(store, original, (), request_id='competing')
        status, _, rejected = request(url, 'POST', action, fields)
        assert status == 409 and 'shortlist_version_conflict' in rejected
        retry = form(rejected, action)
        for key in ('request_id', 'expected_version', 'source_shortlist_id', 'selected', 'reason_' + cid, 'position_' + cid):
            assert retry[key] == fields[key]
    assert len(store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists']) == 2


def test_upgrade_keeps_historical_human_decisions_comparisons_plans_and_notes_exact(campaigns):
    from smi_campaigns.planning import CampaignPlanning, DecisionNote
    from test_campaigns import comparison, save
    from test_monitoring_planning import PLAN

    store = campaigns[0]
    campaign, compared = comparison(campaigns)
    draft = save(store, compared, (), confirmed=False, request_id='historical-draft')
    confirmed = save(store, compared, expected_version=1, request_id='historical-confirmed')
    planning = CampaignPlanning(store.db)
    planning.save_plan(campaign['campaign_id'], campaign['brief_id'], confirmed['shortlist_id'], PLAN, HUMAN,
        expected_version=0, request_id='historical-plan')
    planning.add_note(campaign['campaign_id'], confirmed['shortlist_id'], DecisionNote('Historical human note'), HUMAN,
        expected_version=0, request_id='historical-note')
    before_shortlists = [store.read_shortlist(r['shortlist_id'], HUMAN) for r in (draft, confirmed)]
    before_campaign = store.read_campaign(campaign['campaign_id'], HUMAN)
    before_planning = planning.read(campaign['campaign_id'], HUMAN)
    # Setup reproduces the prior schema. All outcomes use owning public readers.
    with store.db.connect() as setup:
        setup.execute('ALTER TABLE shortlist_revisions DROP COLUMN source_shortlist_id')
    restarted = CampaignStore(store.db)
    restarted.migrate()
    restarted.migrate()
    assert restarted.read_campaign(campaign['campaign_id'], HUMAN) == before_campaign
    assert restarted.read_comparison(compared['comparison_id'], HUMAN) == compared
    assert [restarted.read_shortlist(r['shortlist_id'], HUMAN) for r in (draft, confirmed)] == before_shortlists
    assert CampaignPlanning(store.db).read(campaign['campaign_id'], HUMAN) == before_planning
    assert all(v['source_shortlist_id'] is None and v['method_version'] is None and v['ordering'] is None for v in before_shortlists)
    assert all(s['position'] is None and s['reason_basis'] == 'human_supplied' for v in before_shortlists for s in v['selected'])
    assert save(restarted, compared, expected_version=1, request_id='historical-confirmed')['status'] == 'duplicate'


def test_supported_human_reasons_keep_exact_citations_and_confirmation_is_a_separate_action(campaigns):
    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_campaigns import AUTOMATION, BRIEF
    from test_evidence_sets import DATASET

    store, _, run_id = campaigns
    claim = next(c for c in store.knowledge.read(run_id, HUMAN)['interpretations']
                 if c['predicate'] == 'product_mention' and c['value']['product_id'] == 'aprilskin-hero-cushion')
    source = store.evidence.read(DATASET, HUMAN)
    refs = tuple(r for r in IngestedEvidence(store.db).select_run(source['run_id'], HUMAN)
                 if r.observation_id == claim['observation_id'])
    KnowledgePublications(store.db).publish(refs, AUTOMATION, request_id='supported', interpretation_ids=(claim['id'],))
    campaign = store.start(BRIEF, HUMAN, request_id='campaign')
    original = store.read_shortlist(recommend(store, campaign)['shortlist_id'], HUMAN)
    selected = original['selected'][0]
    choices = (Selection(selected['candidate_id'], 'Sampled product mention merits investigation.',
                         (claim['id'],), tuple(selected['gaps'])),)
    curated = store.read_shortlist(curate(store, original, choices)['shortlist_id'], HUMAN)
    assert curated['status'] == 'draft' and curated['selected'][0]['support_ids'] == [claim['id']]
    assert curated['selected'][0]['evidence'][0]['observation_id'] == claim['observation_id']
    with pytest.raises(EvidenceError, match='selection_unknowns_not_acknowledged'):
        store.save_shortlist(curated['comparison_id'], (Selection(selected['candidate_id'], 'Human reason', (claim['id'],)),),
            HUMAN, confirmed=True, expected_version=2, request_id='missing-unknowns', source_shortlist_id=curated['shortlist_id'])
    confirmed = store.save_shortlist(curated['comparison_id'], choices, HUMAN, confirmed=True, expected_version=2,
        request_id='separate-confirmation', source_shortlist_id=curated['shortlist_id'])
    assert store.read_shortlist(confirmed['shortlist_id'], HUMAN)['status'] == 'confirmed'
    assert store.read_shortlist(curated['shortlist_id'], HUMAN) == {**curated, 'current_shortlist_version': 3}
    assert store.read_shortlist(original['shortlist_id'], HUMAN) == {**original, 'current_shortlist_version': 3}


def test_display_denial_applies_to_new_copied_human_reasons_and_recoverable_forms(stack):
    import pytest

    from smi_ingestion.contracts import SourcePolicy
    from smi_ingestion.evidence import EvidenceError
    from smi_review import ReviewApp
    from test_review import form, request, running

    store, campaign = current_campaign(stack)
    publish_account(stack, 'private', policy=SourcePolicy('local-test', True, True, False))
    original = store.read_shortlist(recommend(store, campaign)['shortlist_id'], HUMAN)
    cid = original['selected'][0]['candidate_id']
    with pytest.raises(EvidenceError, match='selection_reason_or_support_unavailable'):
        curate(store, original, (Selection(cid, 'DENIED_COPY_SENTINEL'),))
    path = '/comparisons/' + original['comparison_id'] + '?shortlist_id=' + original['shortlist_id']
    action = '/comparisons/' + original['comparison_id'] + '/shortlists'
    with running(ReviewApp(store.db)) as url:
        _, _, page = request(url, path=path)
        fields = {**form(page, action), 'reason_' + cid: ['DENIED_COPY_SENTINEL'], 'action': ['draft']}
        status, _, page = request(url, 'POST', action, fields)
        assert status == 422 and 'DENIED_COPY_SENTINEL' not in page
        assert form(page, action)['source_shortlist_id'] == [original['shortlist_id']]
    assert store.read_campaign(campaign['campaign_id'], HUMAN)['shortlist_version'] == 1
