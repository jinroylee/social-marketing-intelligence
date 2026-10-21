from __future__ import annotations

from smi_campaigns import CampaignStore
from test_campaigns import AUTOMATION, campaigns as campaigns_fixture
from test_current_comparisons import current_campaign
from test_knowledge_queries import publish_account
from test_publications import HUMAN

campaigns = campaigns_fixture


def recommend(store, campaign, request_id='recommend', **options):
    return store.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
                           expected_brief_version=1, expected_shortlist_version=0,
                           request_id=request_id, **options)


def test_recommendation_automatically_saves_order_and_actual_automation_without_human_review(stack):
    store, campaign = current_campaign(stack)
    publish_account(stack, 'older', native_id='older-account')
    publish_account(stack, 'newer', native_id='newer-account')
    saved = recommend(store, campaign)
    view = CampaignStore(store.db).read_shortlist(saved['shortlist_id'], HUMAN)
    assert saved['status'] == view['status'] == 'generated'
    assert view['recorded_by'] == AUTOMATION.actor_id and view['actor_kind'] == 'automation'
    assert view['ordering'] == 'comparison_order' and view['method_version'] == 'current-kb-deterministic-shortlist-v1'
    assert view['executable_profile']['brief_id'] == campaign['brief_id']
    assert view['execution_profile']['ranking'] == 'unranked'
    assert [s['account_key']['native_id'] for s in view['selected']] == ['newer-account', 'older-account']
    assert [s['position'] for s in view['selected']] == [0, 1]
    assert all(s['reason_basis'] == 'automated_deterministic' and s['reason'] for s in view['selected'])
    assert all(s['acknowledged_unknowns'] == [] for s in view['selected'])
    assert all('audience_geography' in s['gaps'] and s['support_manifest'] for s in view['selected'])
    assert [r['id'] for r in store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists']] == [view['shortlist_id']]


def test_retries_reopen_original_without_reassessment_after_restart_and_new_knowledge(stack):
    from dataclasses import replace

    import pytest

    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from test_campaigns import BRIEF

    store, campaign = current_campaign(stack)
    publish_account(stack, 'first')
    saved = recommend(store, campaign)
    original = store.read_shortlist(saved['shortlist_id'], HUMAN)
    publish_account(stack, 'new', native_id='later-account')
    store.revise_brief(campaign['campaign_id'], replace(BRIEF, original_input='New needs'), HUMAN,
                       expected_version=1, request_id='successor')
    # DDL fails any new assessment at its actual commit seam. Reopen must not
    # compute a successor, even though both the KB and human brief have changed.
    with store.db.connect() as setup:
        setup.execute("CREATE FUNCTION reject_reassessment() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'unexpected reassessment'; END $$")
        setup.execute('CREATE TRIGGER reject_reassessment BEFORE INSERT ON comparison_drafts FOR EACH ROW EXECUTE FUNCTION reject_reassessment()')
    reopened_store = CampaignStore(store.db)
    assert recommend(reopened_store, campaign) == {**saved, 'status': 'duplicate'}
    assert reopened_store.read_shortlist(saved['shortlist_id'], HUMAN) == original
    with pytest.raises(EvidenceError, match='shortlist_request_conflict'):
        recommend(store, campaign, max_age_seconds=1)
    with pytest.raises(EvidenceError, match='shortlist_request_conflict'):
        store.recommend(campaign['campaign_id'], campaign['brief_id'], ActorContext('local', 'other-worker', 'automation'),
                        expected_brief_version=1, expected_shortlist_version=0, request_id='recommend')
    with pytest.raises(EvidenceError, match='automation_action_required'):
        store.recommend(campaign['campaign_id'], campaign['brief_id'], HUMAN,
                        expected_brief_version=1, expected_shortlist_version=0, request_id='human')
    with pytest.raises(EvidenceError, match='brief_version_conflict'):
        recommend(store, campaign, 'new-stale-request')


def test_empty_or_deferred_results_save_without_inventing_evidence_or_acknowledgement(stack):
    from smi_campaigns import Criterion

    store, campaign = current_campaign(stack, criteria=(Criterion('audience', 'Japan audience', 'audience_geography', 'JP', True, 'include', 'defer'),))
    empty = recommend(store, campaign, 'empty')
    view = store.read_shortlist(empty['shortlist_id'], HUMAN)
    assert view['selected'] == [] and view['status'] == 'generated'
    assert view['selection_summary'] == {'candidate_count': 0, 'selected_count': 0, 'excluded_count': 0, 'deferred_count': 0, 'empty_reason': 'no_supported_candidates_in_scope'}
    assert view['coverage']['discovery_seeds'][0]['native_id'] == 'seed-only'
    assert 'no_eligible_supported_accounts_in_campaign_scope' in view['coverage']['unknowns']
    publish_account(stack, 'supported-but-deferred')
    deferred = store.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
                              expected_brief_version=1, expected_shortlist_version=1, request_id='deferred')
    view = store.read_shortlist(deferred['shortlist_id'], HUMAN)
    comparison = store.read_comparison(view['comparison_id'], HUMAN)
    assert view['selected'] == [] and view['version'] == 2
    assert view['selection_summary'] == {'candidate_count': 1, 'selected_count': 0, 'excluded_count': 0, 'deferred_count': 1, 'empty_reason': 'required_criteria_not_met'}
    assert comparison['candidates'][0]['body']['assessment'] == 'deferred_unknown_requirements'


def test_http_recommends_and_saves_with_server_producer_without_review_then_reopens(stack):
    from smi_review import ReviewApp
    from test_review import form, request, running

    store, campaign = current_campaign(stack)
    publish_account(stack, 'http', native_id='<script>account</script>')
    path = '/campaigns/' + campaign['campaign_id']
    action = path + '/recommendations'
    with running(ReviewApp(store.db, actor_id='actual-marketer')) as url:
        status, _, page = request(url, path=path)
        assert status == 200 and 'Recommend and save automatically' in page
        fields = form(page, action)
        for forged in ({'actor': ['human']}, {'recorded_by': ['actual-marketer']}, {'confirmed': ['yes']}, {'origin': ['campaign']}):
            status, _, rejected = request(url, 'POST', action, {**fields, **forged})
            assert status == 422 and 'invalid_form' in rejected
        status, headers, _ = request(url, 'POST', action, fields)
        assert status == 303
        shortlist_path = headers['Location']
        status, _, page = request(url, path=shortlist_path)
        assert status == 200 and 'generated' in page
        assert 'local-rule-preparation' in page and 'automation' in page
        assert 'Human inclusion reason' not in page and 'Acknowledged unknowns' not in page
        assert 'Deterministic inclusion rationale' in page and 'Explicit gaps' in page
        assert 'current-kb-deterministic-shortlist-v1' in page and 'unranked' in page
        assert '&lt;script&gt;account&lt;/script&gt;' in page and '<script>account</script>' not in page
        status, headers, _ = request(url, 'POST', action, fields)
        assert status == 303 and headers['Location'] == shortlist_path
    with running(ReviewApp(store.db)) as url:
        status, _, page = request(url, path=shortlist_path)
        assert status == 200 and 'local-rule-preparation' in page
    view = store.read_shortlist(shortlist_path.split('/')[-1], HUMAN)
    assert view['actor_kind'] == 'automation' and view['recorded_by'] == 'local-rule-preparation'
    assert view['selected'][0]['acknowledged_unknowns'] == []


def test_competing_requests_conflict_and_identical_concurrent_retry_reopens_one_revision(stack):
    from concurrent.futures import ThreadPoolExecutor

    from smi_ingestion.evidence import EvidenceError

    store, campaign = current_campaign(stack)
    publish_account(stack, 'race')
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: recommend(CampaignStore(store.db), campaign), range(2)))
    assert {r['status'] for r in results} == {'generated', 'duplicate'}
    assert len({r['shortlist_id'] for r in results}) == 1

    def successor(identity):
        try:
            return store.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
                                   expected_brief_version=1, expected_shortlist_version=1, request_id=identity)
        except EvidenceError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(successor, ['successor-a', 'successor-b']))
    assert sum(isinstance(r, dict) and r['status'] == 'generated' for r in results) == 1
    assert 'shortlist_version_conflict' in results
    history = store.read_campaign(campaign['campaign_id'], HUMAN)
    assert [r['version'] for r in history['shortlists']] == [1, 2]


def test_recommendation_holds_source_and_brief_locks_until_shortlist_commit(stack):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from time import monotonic, sleep

    from test_campaigns import BRIEF

    store, campaign = current_campaign(stack)
    _, observation = publish_account(stack, 'before-race')
    gate = 150015
    with store.db.connect() as setup:
        setup.execute('CREATE FUNCTION shortlist_commit_gate() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(150015); RETURN NEW; END $$')
        setup.execute('CREATE TRIGGER shortlist_commit_gate BEFORE INSERT ON shortlist_revisions FOR EACH ROW EXECUTE FUNCTION shortlist_commit_gate()')
    with ThreadPoolExecutor(max_workers=3) as executor:
        with store.db.connect() as blocker:
            blocker.execute('SELECT pg_advisory_xact_lock(%s)', (gate,))
            saving = executor.submit(recommend, store, campaign)
            deadline = monotonic() + 10
            while monotonic() < deadline:
                if blocker.execute("SELECT 1 FROM pg_locks WHERE locktype='advisory' AND objid=%s AND NOT granted", (gate,)).fetchone():
                    break
                sleep(.01)
            else:
                raise AssertionError('recommendation did not reach shortlist commit gate')
            revising = executor.submit(store.revise_brief, campaign['campaign_id'], replace(BRIEF, original_input='Changed needs'), HUMAN,
                                       expected_version=1, request_id='racing-brief')
            withdrawing = executor.submit(stack[1].revoke, observation.id)
            deadline = monotonic() + 10
            while monotonic() < deadline:
                waits = blocker.execute('SELECT locktype FROM pg_locks WHERE NOT granted AND pid<>pg_backend_pid()').fetchall()
                if len(waits) >= 3:
                    break
                sleep(.01)
            else:
                raise AssertionError('brief/source updates did not wait for shortlist commit')
            assert not revising.done() and not withdrawing.done()
        saved = saving.result(timeout=10)
        revising.result(timeout=10)
        withdrawing.result(timeout=10)
    view = store.read_shortlist(saved['shortlist_id'], HUMAN)
    assert view['brief_id'] == campaign['brief_id']
    assert view['selected'][0]['account_key']['native_id'] == 'account-1'
    assert view['selected'][0]['reason'] is None and view['selected'][0]['position'] == 0


def test_current_display_and_retention_withdrawal_preserve_order_producer_and_never_rebuild_text(stack):
    from dataclasses import asdict

    from psycopg.types.json import Jsonb

    store, campaign = current_campaign(stack)
    _, observation = publish_account(stack, 'policy')
    saved = recommend(store, campaign)
    original = store.read_shortlist(saved['shortlist_id'], HUMAN)
    policy = asdict(stack[1].get(observation.id).policy)

    def change_policy(**changes):
        policy.update(changes)
        with store.db.connect() as setup:
            setup.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(policy), observation.id))

    change_policy(can_display=False)
    hidden = store.read_shortlist(saved['shortlist_id'], HUMAN)
    selected = hidden['selected'][0]
    assert selected['reason'] is selected['gaps'] is selected['rationale'] is selected['support_manifest'] is None
    assert selected['evidence'] == [] and selected['position'] == 0
    assert hidden['recorded_by'] == AUTOMATION.actor_id and hidden['actor_kind'] == 'automation'
    assert selected['account_key'] == original['selected'][0]['account_key']
    change_policy(can_display=True)
    assert store.read_shortlist(saved['shortlist_id'], HUMAN)['selected'] == original['selected']
    change_policy(can_retain=False)
    assert store.read_shortlist(saved['shortlist_id'], HUMAN)['selected'][0]['reason'] is None
    change_policy(can_retain=True)
    assert recommend(CampaignStore(store.db), campaign)['shortlist_id'] == saved['shortlist_id']
    assert store.read_shortlist(saved['shortlist_id'], HUMAN)['selected'][0]['reason'] is None


def test_legacy_human_upgrade_keeps_status_author_history_and_unrecorded_order(campaigns):
    from smi_campaigns import Selection
    from test_campaigns import HUMAN as LEGACY_HUMAN, comparison, save, selection

    store, _, _ = campaigns
    campaign, comparison_view = comparison(campaigns)
    chosen = selection(comparison_view)
    draft = save(store, comparison_view, (Selection(chosen.candidate_id),), confirmed=False, request_id='human-draft')
    confirmed = save(store, comparison_view, (chosen,), expected_version=1, request_id='human-confirmed')
    before = [store.read_shortlist(result['shortlist_id'], HUMAN) for result in (draft, confirmed)]
    # Reproduce the installed schema before automatic persistence; DDL is setup,
    # while every migration outcome is read through the campaign owner.
    with store.db.connect() as setup:
        setup.execute('ALTER TABLE shortlist_revisions DROP CONSTRAINT shortlist_revisions_status_check')
        setup.execute("ALTER TABLE shortlist_revisions ADD CONSTRAINT shortlist_revisions_status_check CHECK (status IN ('draft','confirmed'))")
        setup.execute('ALTER TABLE shortlist_revisions DROP COLUMN actor_kind, DROP COLUMN method_version, DROP COLUMN ordering, DROP COLUMN selection_summary')
        setup.execute('ALTER TABLE shortlist_selections DROP COLUMN position')
    restarted = CampaignStore(store.db)
    restarted.migrate()
    restarted.migrate()
    after = [restarted.read_shortlist(result['shortlist_id'], HUMAN) for result in (draft, confirmed)]
    assert after == before
    assert [view['status'] for view in after] == ['draft', 'confirmed']
    assert all(view['actor_kind'] == 'human' and view['recorded_by'] == LEGACY_HUMAN.actor_id and view['ordering'] is None for view in after)
    assert all(s['position'] is None for view in after for s in view['selected'])
    generated = restarted.recommend(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
                                    expected_brief_version=1, expected_shortlist_version=2, request_id='first-generated')
    restarted.migrate()
    assert restarted.read_shortlist(generated['shortlist_id'], HUMAN)['status'] == 'generated'
    assert restarted.read_shortlist(confirmed['shortlist_id'], HUMAN) == {**after[1], 'current_shortlist_version': 3}


def test_required_exclusion_stays_unselected_with_pinned_explanation(campaigns):
    from dataclasses import replace

    from smi_campaigns import Criterion
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_campaigns import BRIEF
    from test_evidence_sets import DATASET

    store, _, knowledge_run = campaigns
    claims = store.knowledge.read(knowledge_run, HUMAN)['interpretations']
    marker = next(c for c in claims if c['predicate'] == 'literal_marker')
    source = store.evidence.read(DATASET, HUMAN)
    refs = tuple(r for r in IngestedEvidence(store.db).select_run(source['run_id'], HUMAN) if r.observation_id == marker['observation_id'])
    KnowledgePublications(store.db).publish(refs, AUTOMATION, request_id='excluded', interpretation_ids=(marker['id'],))
    brief = replace(BRIEF, criteria=(Criterion('no-pr', 'Exclude PR marker', 'literal_marker', marker['value']['marker'], True, 'exclude'),))
    campaign = store.start(brief, HUMAN, request_id='exclude-campaign')
    saved = recommend(store, campaign)
    view = store.read_shortlist(saved['shortlist_id'], HUMAN)
    assert view['selected'] == []
    candidate = store.read_comparison(view['comparison_id'], HUMAN)['candidates'][0]
    assert candidate['body']['assessment'] == 'excluded_on_required_evidence'
    assert candidate['body']['judgments'][0]['support_ids'] == [marker['id']]
    assert marker['id'] in candidate['body']['support_manifest'][0]['interpretation_ids']


def test_exact_selected_model_profile_is_saved_without_another_model_dispatch(campaigns):
    from dataclasses import replace

    from test_campaigns import BRIEF
    from test_criteria_interpretation import configured, interpret

    store, _, transport = configured(campaigns)
    campaign = store.start(replace(BRIEF, original_input='Prefer skincare'), HUMAN, request_id='model-profile')
    interpreted = interpret(store, campaign)
    saved = recommend(store, campaign, interpretation_id=interpreted['interpretation_id'])
    view = CampaignStore(store.db).read_shortlist(saved['shortlist_id'], HUMAN)
    assert view['executable_profile'] == interpreted['executable_profile']
    assert view['execution_profile']['criteria_interpretation_id'] == interpreted['interpretation_id']
    assert view['execution_profile']['method_version'] == 'current-kb-caption-comparison-v1'
    assert view['actor_kind'] == 'automation' and len(transport.calls) == 1


def test_stale_http_request_preserves_exact_profile_brief_heads_and_retry_identity(campaigns):
    from dataclasses import replace

    from smi_review import ReviewApp
    from test_campaigns import BRIEF
    from test_criteria_interpretation import configured, interpret
    from test_review import form, request, running

    store, _, _ = configured(campaigns)
    campaign = store.start(replace(BRIEF, original_input='Prefer skincare'), HUMAN, request_id='stale-http')
    interpreted = interpret(store, campaign)
    action = '/campaigns/' + campaign['campaign_id'] + '/recommendations'
    with running(ReviewApp(store.db)) as url:
        _, _, page = request(url, path='/campaigns/' + campaign['campaign_id'])
        fields = form(page, action)
        fields['interpretation_id'] = [interpreted['interpretation_id']]
        store.revise_brief(campaign['campaign_id'], replace(BRIEF, original_input='Changed needs'), HUMAN,
                           expected_version=1, request_id='stale-http-successor')
        status, _, page = request(url, 'POST', action, fields)
        assert status == 409 and 'brief_version_conflict' in page
        retry = form(page, action)
        for key in ('request_id', 'brief_id', 'interpretation_id', 'expected_brief_version', 'expected_shortlist_version'):
            assert retry[key] == fields[key]
    history = store.read_campaign(campaign['campaign_id'], HUMAN)
    assert history['shortlists'] == [] and history['comparisons'] == []


def test_shortlist_failure_rolls_back_comparison_and_recovery_saves_one_revision(stack):
    import psycopg
    import pytest

    store, campaign = current_campaign(stack)
    publish_account(stack, 'atomic')
    with store.db.connect() as setup:
        setup.execute("CREATE FUNCTION reject_shortlist() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'simulated write failure'; END $$")
        setup.execute('CREATE TRIGGER reject_shortlist BEFORE INSERT ON shortlist_revisions FOR EACH ROW EXECUTE FUNCTION reject_shortlist()')
    with pytest.raises(psycopg.Error):
        recommend(store, campaign)
    history = store.read_campaign(campaign['campaign_id'], HUMAN)
    assert history['shortlists'] == [] and history['comparisons'] == []
    with store.db.connect() as setup:
        setup.execute('DROP TRIGGER reject_shortlist ON shortlist_revisions')
    saved = recommend(CampaignStore(store.db), campaign)
    assert saved['status'] == 'generated' and saved['version'] == 1
    assert len(store.read_campaign(campaign['campaign_id'], HUMAN)['comparisons']) == 1


def test_client_chosen_comparison_identity_cannot_supply_a_historical_assessment(stack):
    store, campaign = current_campaign(stack)
    _, observation = publish_account(stack, 'old-support')
    # A client can submit any comparison retry identity, including a formerly
    # predictable nested identity. It cannot make a new recommendation trust it.
    staged = store.prepare_current_comparison(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        request_id='recommendation:7eb737286abbb4c7341a296744e2b7dea585dee82839c8045ed66aa1075e27b4')
    stack[1].revoke(observation.id)
    saved = recommend(store, campaign)
    view = store.read_shortlist(saved['shortlist_id'], HUMAN)
    assert view['comparison_id'] != staged['comparison_id']
    assert view['selected'] == []
    assert view['selection_summary']['empty_reason'] == 'no_supported_candidates_in_scope'
