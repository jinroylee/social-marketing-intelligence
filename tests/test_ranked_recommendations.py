"""Ranked recommendations at public campaign/HTTP seams with simulated external I/O."""

import copy
import json
from dataclasses import replace

import pytest

from smi_campaigns import Criterion
from smi_ingestion.evidence import EvidenceError

from smi_campaigns import CampaignStore
from test_campaigns import AUTOMATION, BRIEF, campaigns as campaigns_fixture
from test_current_comparisons import current_campaign
from test_criteria_interpretation import configured
from test_knowledge_queries import publish_account
from test_publications import HUMAN


campaigns = campaigns_fixture


class RankingTransport:
    def __init__(self):
        self.calls = []
        self.on_call = None
        self.change = None

    def create(self, request, **bounds):
        self.calls.append(copy.deepcopy(request))
        if self.on_call:
            self.on_call()
        data = json.loads(request['input'][0]['content'][0]['text'])
        output = {'candidates': [{'candidate_id': c['candidate_id'], 'reasons': [
            {'criterion_id': j['criterion_id'], 'judgment': {'satisfied': 'supported_fit', 'not_satisfied_on_evidence': 'contradicted_preference', 'unknown': 'limited_evidence'}[j['state']],
             'support_ids': j['support_ids'] if j['state'] != 'unknown' else []} for j in c['judgments']]}
            for c in reversed(data['candidates'])]}
        if self.change:
            self.change(output)
        return json.dumps({'model': request['model'], 'service_tier': 'default', 'status': 'completed',
            'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed',
                        'content': [{'type': 'output_text', 'text': json.dumps(output)}]}],
            'usage': {'input_tokens': 100, 'output_tokens': 40, 'total_tokens': 140,
                      'input_tokens_details': {'cached_tokens': 20, 'cache_write_tokens': 10},
                      'output_tokens_details': {'reasoning_tokens': 12}}}).encode()


def configured_current(stack, **changes):
    base, campaign = current_campaign(stack, **changes)
    store, costs, _ = configured((base,))
    transport = RankingTransport()
    store.model_transport = transport
    return store, campaign, costs, transport


def rank(store, campaign, request_id='rank', **options):
    return store.recommend_ranked(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=0, request_id=request_id, **options)


def test_model_order_is_saved_with_incomplete_supported_profiles_and_exact_inputs(stack):
    store, campaign, costs, transport = configured_current(stack)
    _, first = publish_account(stack, 'first', native_id='first')
    _, second = publish_account(stack, 'second', native_id='second')
    result = rank(store, campaign)
    assert result['status'] == 'succeeded'
    view = CampaignStore(store.db).read_shortlist(result['shortlist_id'], HUMAN)
    assert [s['account_key']['native_id'] for s in view['selected']] == ['first', 'second']
    assert view['ordering'] == 'llm_assessment_order'
    assert view['execution_profile']['ranking'] == 'validated_llm_assessment'
    assert view['recorded_by'] == AUTOMATION.actor_id and view['actor_kind'] == 'automation'
    assert view['ranking_assessment']['status'] == 'succeeded'
    assert view['ranking_assessment']['configuration']['model_version'] == 'synthetic-model-revision-v1'
    assert view['ranking_assessment']['configuration']['schema_version'] == 'campaign-supported-ranking-v1'
    assessed = view['ranking_assessment']['candidates']
    assert {o for c in assessed for o in c['input']['observations']} == {first.id, second.id}
    assert all(c['input']['support_manifest'] for c in assessed)
    assert all(s['reason_basis'] == 'automated_model_judgment' and s['acknowledged_unknowns'] == [] for s in view['selected'])
    assert all({'audience_geography', 'fees', 'availability', 'sales_effectiveness'} <= set(s['gaps']) for s in view['selected'])
    assert costs.read(result['operation_id'], HUMAN)['actuals']['amount'] == '0.175'
    assert len(transport.calls) == 1


def test_http_ranked_save_protects_authority_and_reopens_escaped_provenance_after_restart(stack):
    from smi_review import ReviewApp
    from test_review import running, request, form
    store, campaign, _, transport = configured_current(stack, original_input='Prefer <script>unsafe</script>')
    publish_account(stack, 'minimal')
    app = ReviewApp(store.db, HUMAN.actor_id, model_route=store.model_route,
                    model_transport=transport, model_credential=store.model_credential)
    path = '/campaigns/' + campaign['campaign_id']
    action = path + '/ranked-recommendations'
    with running(app) as url:
        status, _, page = request(url, path=path)
        assert status == 200
        fields = form(page, action)
        assert request(url, 'POST', action, {**fields, 'task_approval': ['yes']})[0] == 422
        assert request(url, 'POST', action, fields, headers={'Origin': 'http://evil.invalid'})[0] == 403
        assert request(url, 'POST', action, {**fields, 'csrf': ['bad']})[0] == 422
        status, headers, page = request(url, 'POST', action, fields)
        assert status == 303, page
        saved_path = headers['Location']
        assert saved_path.startswith('/shortlists/')
        _, _, page = request(url, path=saved_path)
        assert 'Validated LLM assessment order' in page and 'Generated relative-fit judgment' in page
        assert 'Deterministic and unranked' not in page
        assert '&lt;script&gt;unsafe&lt;/script&gt;' in page and '<script>unsafe' not in page
        assert request(url, 'POST', action, fields)[1]['Location'] == saved_path
    assert len(transport.calls) == 1
    with running(ReviewApp(store.db, HUMAN.actor_id)) as url:
        assert 'Validated LLM assessment order' in request(url, path=saved_path)[2]
        _, _, page = request(url, path=path)
        assert 'succeeded' in page and 'synthetic-model-revision-v1' in page
    saved = store.read_shortlist(saved_path.split('/')[-1], HUMAN)
    assert saved['recorded_by'] == 'local-rule-preparation'


@pytest.mark.parametrize('deferred', [False, True])
def test_empty_or_fully_deferred_batches_save_truthful_empty_without_model_configuration(stack, deferred):
    changes = {'criteria': (Criterion('audience', 'Audience in Japan', 'audience_geography', 'JP', True, 'include', 'defer'),)} if deferred else {}
    store, campaign = current_campaign(stack, **changes)
    if deferred:
        publish_account(stack, 'deferred')
    result = rank(store, campaign)
    assert result['status'] == 'succeeded' and result['operation_id'] is None
    view = store.read_shortlist(result['shortlist_id'], HUMAN)
    assert view['selected'] == []
    assert view['ranking_assessment']['configuration']['model_status'] == 'not_called_empty_batch'
    assert view['execution_profile']['ranking'] == 'not_assessed_empty_batch'
    assert view['ordering'] == 'empty_eligible_batch'
    assert view['selection_summary']['empty_reason'] == ('required_criteria_not_met' if deferred else 'no_supported_candidates_in_scope')
    assert view['selection_summary']['deferred_count'] == int(deferred)


def test_missing_route_does_not_mislabel_nonempty_assessment_or_fall_back(stack):
    store, campaign = current_campaign(stack)
    publish_account(stack, 'supported')
    result = rank(store, campaign)
    assert result['status'] == 'blocked' and result['reason'] == 'model_route_unavailable'
    assert result['shortlist_id'] is None and result['operation_id'] is None
    assert result['configuration']['model_status'] == 'not_requested'
    assert store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists'] == []


@pytest.mark.parametrize('invalid', ['invented', 'missing', 'duplicate', 'extra_fact', 'unknown_positive', 'invented_support', 'forged_authority', 'foreign_criterion', 'missing_reason'])
def test_invalid_or_unsupported_output_never_saves_a_successful_fallback_and_still_accounts_usage(stack, invalid):
    store, campaign, costs, transport = configured_current(stack)
    publish_account(stack, 'first')
    publish_account(stack, 'second', native_id='second')
    def corrupt(output):
        rows = output['candidates']
        if invalid == 'invented':
            rows[0]['candidate_id'] = '00000000-0000-0000-0000-000000000001'
        elif invalid == 'missing':
            rows.pop()
        elif invalid == 'duplicate':
            rows[1] = copy.deepcopy(rows[0])
        elif invalid == 'extra_fact':
            rows[0]['reasons'][0]['fact'] = 'Audience and sales are verified in Japan'
        elif invalid == 'unknown_positive':
            rows[0]['reasons'][0].update(judgment='supported_fit', support_ids=['00000000-0000-0000-0000-000000000001'])
        elif invalid == 'invented_support':
            rows[0]['reasons'][0]['support_ids'] = ['invented']
        elif invalid == 'forged_authority':
            output['task_approval'] = 'yes'
        elif invalid == 'foreign_criterion':
            rows[0]['reasons'][0]['criterion_id'] = 'not-assessed'
        elif invalid == 'missing_reason':
            rows[0]['reasons'].pop()
    transport.change = corrupt
    result = rank(store, campaign)
    assert result['status'] == 'invalid' and result['shortlist_id'] is None
    assert all(c['judgment'] is None for c in result['candidates'])
    assert store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists'] == []
    assert costs.read(result['operation_id'], HUMAN)['actuals']['amount'] == '0.175'
    assert rank(CampaignStore(store.db), campaign) == result
    assert len(transport.calls) == 1


def test_completed_retry_reopens_original_after_restart_new_knowledge_and_brief_without_another_call(stack):
    store, campaign, _, transport = configured_current(stack)
    publish_account(stack, 'first')
    result = rank(store, campaign)
    original = store.read_shortlist(result['shortlist_id'], HUMAN)
    publish_account(stack, 'new', native_id='new-account')
    from test_campaigns import BRIEF
    store.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='A successor question'), HUMAN, expected_version=1, request_id='revise')
    reopened = CampaignStore(store.db)
    assert rank(reopened, campaign) == result
    assert reopened.read_shortlist(result['shortlist_id'], HUMAN) == original
    with pytest.raises(EvidenceError, match='ranking_request_conflict'):
        rank(store, campaign, max_age_seconds=1)
    from smi_ingestion.evidence_sets import ActorContext
    with pytest.raises(EvidenceError, match='ranking_request_conflict'):
        store.recommend_ranked(campaign['campaign_id'], campaign['brief_id'], ActorContext('local', 'different-worker', 'automation'),
            expected_brief_version=1, expected_shortlist_version=0, request_id='rank')
    with pytest.raises(EvidenceError, match='automation_action_required'):
        store.recommend_ranked(campaign['campaign_id'], campaign['brief_id'], HUMAN,
            expected_brief_version=1, expected_shortlist_version=0, request_id='human')
    with pytest.raises(EvidenceError, match='brief_version_conflict'):
        rank(store, campaign, request_id='new-stale')
    assert len(transport.calls) == 1


@pytest.mark.parametrize('race', ['brief', 'shortlist', 'withdrawal', 'supersession'])
def test_provider_io_holds_no_database_lock_and_changed_support_or_heads_cannot_publish(stack, race):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
    from test_campaigns import BRIEF
    store, campaign, costs, transport = configured_current(stack)
    _, observation = publish_account(stack, 'first')
    entered, release = Event(), Event()
    def wait():
        entered.set()
        assert release.wait(10)
    transport.on_call = wait
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(rank, store, campaign)
        assert entered.wait(5)
        retry = rank(CampaignStore(store.db), campaign)
        assert retry['status'] == 'in_progress' and retry['shortlist_id'] is None
        with pytest.raises(EvidenceError, match='ranking_in_progress_or_uncertain'):
            rank(store, campaign, request_id='concurrent-generation')
        if race == 'brief':
            change = pool.submit(store.revise_brief, campaign['campaign_id'], replace(BRIEF, objective='Changed'), HUMAN, expected_version=1, request_id='change')
        elif race == 'shortlist':
            change = pool.submit(store.recommend, campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
                                 expected_brief_version=1, expected_shortlist_version=0, request_id='deterministic-successor')
        elif race == 'withdrawal':
            change = pool.submit(stack[1].revoke, observation.id)
        else:
            key = ExternalKey('test', 'public', 'account', 'account-1')
            change = pool.submit(CanonicalWriter(store.db).apply, observation.id, NormalizedBatch((key,), (
                FieldCandidate(key, 'handle', 'observed', 'changed', '$.handle'),), ()), 'corrected:v2')
        # Public mutations must finish while the provider remains blocked.
        change.result(5)
        release.set()
        result = pending.result(5)
    assert result['status'] == 'stale' and result['shortlist_id'] is None
    assert costs.read(result['operation_id'], HUMAN)['actuals']['amount'] == '0.175'
    assert rank(CampaignStore(store.db), campaign) == result
    if race == 'withdrawal':
        assert result['candidates'][0]['input'] is result['candidates'][0]['judgment'] is None
    assert len(transport.calls) == 1


@pytest.mark.parametrize('failure', ['credential', 'ceiling', 'bounds', 'request_bytes'])
def test_missing_config_or_shared_admission_stops_dispatch_and_retains_visible_attempt(stack, failure):
    store, campaign, costs, transport = configured_current(stack)
    publish_account(stack, 'first')
    if failure == 'credential':
        store.model_credential = None
    elif failure == 'ceiling':
        scope = costs.allowance('synthetic-model', HUMAN)
        costs.configure_ceiling('synthetic-model', HUMAN, amount='0', currency='USD',
                                period_start=scope['period_start'], period_end=scope['period_end'])
    elif failure == 'bounds':
        store.model_route = replace(store.model_route, max_output_tokens=0)
    else:
        store.model_route = replace(store.model_route, max_request_bytes=10)
    result = rank(store, campaign)
    assert result['status'] == 'blocked' and result['shortlist_id'] is None and transport.calls == []
    assert rank(CampaignStore(store.db), campaign) == result


@pytest.mark.parametrize('outcome', ['success', 'incomplete', 'missing_usage', 'timeout'])
def test_ranking_uses_existing_concrete_http_route_and_provider_reported_cost_contract(stack, outcome):
    from io import BytesIO
    from smi_campaigns.interpretation import ResponsesHTTPTransport
    from smi_costs import CostScope
    store, campaign, costs, fixture = configured_current(stack, original_input='SENSITIVE human input')
    publish_account(stack, 'first')
    requests = []
    class Response(BytesIO):
        status = 200
        def read1(self, size):
            return self.read(size)
    class Connection:
        sock = None
        def __init__(self, host, *, timeout):
            assert host == 'api.openai.com' and timeout == 2
        def connect(self):
            if outcome == 'timeout':
                raise TimeoutError('SENSITIVE provider details')
        def request(self, method, path, body, headers):
            assert method == 'POST' and path == '/v1/responses'
            assert headers['Authorization'] == 'Bearer synthetic-test-key-not-a-real-credential'
            requests.append(json.loads(body))
        def getresponse(self):
            response = json.loads(fixture.create(requests[-1]))
            if outcome == 'incomplete':
                response['status'] = 'incomplete'
            if outcome == 'missing_usage':
                response['usage'] = None
            return Response(json.dumps(response).encode())
        def close(self):
            pass
    costs.configure_scope(CostScope('synthetic-provider-contract', 'openai', 'responses', 'metered', 'USD',
        '2020-01-01T00:00:00Z', '2100-01-01T00:00:00Z', unit='weighted_token', rate_version='synthetic-rates-v1',
        unit_rate='0.001', measurement_basis='provider_reported'), HUMAN)
    costs.configure_ceiling('synthetic-provider-contract', HUMAN, amount='1000', currency='USD',
        period_start='2020-01-01T00:00:00Z', period_end='2100-01-01T00:00:00Z')
    store.model_route = replace(store.model_route, model='gpt-5.4-mini-2026-03-17', model_version='gpt-5.4-mini-2026-03-17',
        scope_id='synthetic-provider-contract', max_input_tokens=272000, cache_write_weight='1',
        execution_mode='provider', measurement_policy='verified-model-context-v1',
        model_contract_version='openai-gpt-5.4-mini-2026-03-17:2026-10-20')
    store.model_transport = ResponsesHTTPTransport(connection_factory=Connection)
    assert rank(store, campaign, request_id='disabled')['status'] == 'blocked' and not requests
    store.model_transport = ResponsesHTTPTransport(enabled=True, connection_factory=Connection)
    result = rank(store, campaign)
    assert result['status'] == {'success': 'succeeded', 'incomplete': 'incomplete', 'missing_usage': 'meter_failure', 'timeout': 'transport_uncertain'}[outcome]
    cost = costs.read(result['operation_id'], HUMAN)
    assert cost['actor']['actor_id'] == AUTOMATION.actor_id
    assert 'SENSITIVE' not in json.dumps(cost)
    assert 'SENSITIVE provider' not in json.dumps(result)
    if outcome in {'success', 'incomplete'}:
        assert cost['actuals']['amount'] == '0.17'
        assert cost['actuals']['synthetic'] is False and cost['actuals']['commercial_charge'] is None
        assert cost['admission']['state'] == 'settled'
    else:
        assert cost['actuals']['amount'] is None and cost['admission']['state'] == 'dispatched'
    if outcome == 'success':
        view = store.read_shortlist(result['shortlist_id'], HUMAN)
        assert view['ranking_assessment']['configuration']['model'] == 'gpt-5.4-mini-2026-03-17'
        assert requests[0]['store'] is False and requests[0]['tools'] == []
        assert requests[0]['text']['format']['strict'] is True
        assert requests[0]['truncation'] == 'disabled' and requests[0]['service_tier'] == 'default'
    else:
        assert result['shortlist_id'] is None
    assert rank(CampaignStore(store.db), campaign) == result
    assert len(requests) == (0 if outcome == 'timeout' else 1)


def test_current_policy_hides_and_retention_purges_assessed_inputs_judgments_and_reasons(stack):
    from dataclasses import asdict
    from psycopg.types.json import Jsonb
    store, campaign, _, transport = configured_current(stack)
    _, observation = publish_account(stack, 'first')
    result = rank(store, campaign)
    original = store.read_shortlist(result['shortlist_id'], HUMAN)
    policy = asdict(stack[1].get(observation.id).policy)
    def change_policy(**changes):
        policy.update(changes)
        with store.db.connect() as setup:
            setup.execute('UPDATE source_observations SET policy=%s WHERE id=%s', (Jsonb(policy), observation.id))
    change_policy(can_display=False)
    hidden = store.read_shortlist(result['shortlist_id'], HUMAN)
    assert hidden['selected'][0]['reason'] is None
    assert hidden['ranking_assessment']['candidates'][0]['input'] is hidden['ranking_assessment']['candidates'][0]['judgment'] is None
    assert hidden['selected'][0]['position'] == 0
    assert hidden['recorded_by'] == original['recorded_by']
    change_policy(can_display=True)
    assert store.read_shortlist(result['shortlist_id'], HUMAN) == original
    change_policy(can_retain=False)
    assert store.read_ranking_assessment(result['assessment_id'], HUMAN)['candidates'][0]['input'] is None
    change_policy(can_retain=True)
    retried = rank(CampaignStore(store.db), campaign)
    assert retried['candidates'][0]['input'] is retried['candidates'][0]['judgment'] is None
    assert store.read_shortlist(result['shortlist_id'], HUMAN)['selected'][0]['reason'] is None
    assert len(transport.calls) == 1


def test_interrupted_final_save_never_reissues_a_paid_assessment_after_restart(stack):
    import psycopg
    store, campaign, costs, transport = configured_current(stack)
    publish_account(stack, 'first')
    with store.db.connect() as setup:
        setup.execute("CREATE FUNCTION fail_ranked_save() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'simulated final write failure'; END $$")
        setup.execute('CREATE TRIGGER fail_ranked_save BEFORE INSERT ON shortlist_revisions FOR EACH ROW EXECUTE FUNCTION fail_ranked_save()')
    with pytest.raises(psycopg.Error):
        rank(store, campaign)
    with store.db.connect() as setup:
        setup.execute('DROP TRIGGER fail_ranked_save ON shortlist_revisions')
    retry = rank(CampaignStore(store.db), campaign)
    assert retry['status'] == 'in_progress' and retry['shortlist_id'] is None
    assert all(c['judgment'] is None for c in retry['candidates'])
    assert costs.read(retry['operation_id'], HUMAN)['actuals']['amount'] == '0.175'
    assert store.read_campaign(campaign['campaign_id'], HUMAN)['shortlists'] == []
    with pytest.raises(EvidenceError, match='ranking_in_progress_or_uncertain'):
        rank(store, campaign, request_id='new-paid-attempt')
    assert len(transport.calls) == 1


def test_http_unavailable_outcome_and_stale_form_retain_exact_retry_identity(stack):
    from smi_review import ReviewApp
    from test_review import running, request, form
    from test_campaigns import BRIEF
    store, campaign = current_campaign(stack)
    publish_account(stack, 'first')
    path = '/campaigns/' + campaign['campaign_id']
    action = path + '/ranked-recommendations'
    with running(ReviewApp(store.db, HUMAN.actor_id)) as url:
        fields = form(request(url, path=path)[2], action)
        assert request(url, 'POST', action, fields)[0] == 303
        page = request(url, path=path)[2]
        assert 'Model ranking assessment · blocked' in page and 'model_route_unavailable' in page
        assert request(url, 'POST', action, fields)[0] == 303
        assert len(store.read_campaign(campaign['campaign_id'], HUMAN)['ranking_assessments']) == 1
        fields = form(page, action)
        store.revise_brief(campaign['campaign_id'], replace(BRIEF, objective='Successor question'), HUMAN, expected_version=1, request_id='revise')
        status, _, page = request(url, 'POST', action, fields)
        assert status == 409
        recovered = form(page, action)
        for key in ('request_id', 'brief_id', 'expected_brief_version', 'expected_shortlist_version', 'interpretation_id'):
            assert recovered[key] == fields[key]


@pytest.mark.parametrize('cross_candidate', [False, True])
def test_positive_fit_can_cite_only_exact_satisfied_candidate_support(campaigns, cross_candidate):
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_evidence_sets import DATASET
    store, _, run_id = campaigns
    source = store.evidence.read(DATASET, HUMAN)
    claims = store.knowledge.read(run_id, HUMAN)['interpretations']
    scripts = {}
    for claim in claims:
        if claim['predicate'] == 'script_evidence':
            scripts.setdefault(claim['subject_id'], claim)
    chosen = list(scripts.values())[:2]
    assert len(chosen) == 2
    observations = {c['observation_id'] for c in chosen}
    refs = tuple(r for r in IngestedEvidence(store.db).select_run(source['run_id'], HUMAN) if r.observation_id in observations)
    ids = tuple(c['id'] for c in chosen)
    KnowledgePublications(store.db).publish(refs, AUTOMATION, request_id='captions', interpretation_ids=ids)
    campaign = store.start(replace(BRIEF, criteria=(Criterion('script', 'Kana script in observed caption', 'script_evidence', 'kana'),)), HUMAN, request_id='script-campaign')
    store, costs, _ = configured((store,))
    transport = RankingTransport()
    if cross_candidate:
        def swap(output):
            first, second = output['candidates']
            first['reasons'][0]['support_ids'] = second['reasons'][0]['support_ids']
        transport.change = swap
    store.model_transport = transport
    result = rank(store, campaign)
    assert result['status'] == ('invalid' if cross_candidate else 'succeeded')
    if not cross_candidate:
        saved = store.read_shortlist(result['shortlist_id'], HUMAN)
        assert all(s['rationale'][0]['state'] == 'satisfied' for s in saved['selected'])
        assert {sid for s in saved['selected'] for sid in s['support_ids']} == set(ids)
        assert all('audience_geography' in s['gaps'] and 'sales_effectiveness' in s['gaps'] for s in saved['selected'])
    assert costs.read(result['operation_id'], HUMAN)['actuals']['amount'] == '0.175'


def test_required_exclusion_runs_before_dispatch_and_selected_interpretation_remains_exact(campaigns):
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_evidence_sets import DATASET
    from test_criteria_interpretation import interpret
    base, _, run_id = campaigns
    marker = next(c for c in base.knowledge.read(run_id, HUMAN)['interpretations'] if c['predicate'] == 'literal_marker')
    source = base.evidence.read(DATASET, HUMAN)
    refs = tuple(r for r in IngestedEvidence(base.db).select_run(source['run_id'], HUMAN) if r.observation_id == marker['observation_id'])
    KnowledgePublications(base.db).publish(refs, AUTOMATION, request_id='caption', interpretation_ids=(marker['id'],))
    brief = replace(BRIEF, criteria=(Criterion('no-pr', 'Exclude PR', 'literal_marker', marker['value']['marker'], True, 'exclude'),), original_input='Prefer skincare')
    campaign = base.start(brief, HUMAN, request_id='excluded')
    store, _, criteria_transport = configured((base,))
    criteria_transport.output['criteria'] = criteria_transport.output['criteria'][1:]
    interpretation = interpret(store, campaign)
    ranking_transport = RankingTransport()
    store.model_transport = ranking_transport
    result = rank(store, campaign, interpretation_id=interpretation['interpretation_id'])
    assert result['status'] == 'succeeded' and result['operation_id'] is None
    view = store.read_shortlist(result['shortlist_id'], HUMAN)
    assert view['selected'] == [] and view['selection_summary']['excluded_count'] == 1
    assert view['executable_profile'] == interpretation['executable_profile']
    assert len(criteria_transport.calls) == 1 and ranking_transport.calls == []


def test_optional_exclusion_keeps_supported_contradiction_in_generated_judgment(campaigns):
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_evidence_sets import DATASET
    base, _, run_id = campaigns
    marker = next(c for c in base.knowledge.read(run_id, HUMAN)['interpretations'] if c['predicate'] == 'literal_marker')
    source = base.evidence.read(DATASET, HUMAN)
    refs = tuple(r for r in IngestedEvidence(base.db).select_run(source['run_id'], HUMAN) if r.observation_id == marker['observation_id'])
    KnowledgePublications(base.db).publish(refs, AUTOMATION, request_id='caption', interpretation_ids=(marker['id'],))
    campaign = base.start(replace(BRIEF, criteria=(Criterion('prefer-no-pr', 'Prefer no PR marker', 'literal_marker', marker['value']['marker'], False, 'exclude'),)), HUMAN, request_id='optional')
    store, _, _ = configured((base,))
    store.model_transport = RankingTransport()
    result = rank(store, campaign)
    assert result['status'] == 'succeeded'
    assert result['candidates'][0]['judgment']['reasons'] == [
        {'criterion_id': 'prefer-no-pr', 'judgment': 'contradicted_preference', 'support_ids': [marker['id']]}]
    saved = store.read_shortlist(result['shortlist_id'], HUMAN)
    assert 'contradicted_preference' in saved['selected'][0]['reason']
    assert 'contracts' in saved['selected'][0]['gaps']


def test_explicit_new_generation_saves_successor_without_mutating_prior_assessed_artifact(stack):
    store, campaign, _, transport = configured_current(stack)
    publish_account(stack, 'first')
    first = rank(store, campaign)
    prior = store.read_shortlist(first['shortlist_id'], HUMAN)
    publish_account(stack, 'second', native_id='second')
    second = store.recommend_ranked(campaign['campaign_id'], campaign['brief_id'], AUTOMATION,
        expected_brief_version=1, expected_shortlist_version=1, request_id='successor')
    assert second['status'] == 'succeeded' and second['shortlist_id'] != first['shortlist_id']
    current = store.read_shortlist(second['shortlist_id'], HUMAN)
    assert current['version'] == 2 and len(current['selected']) == 2
    assert store.read_shortlist(first['shortlist_id'], HUMAN) == {**prior, 'current_shortlist_version': 2}
    assert rank(CampaignStore(store.db), campaign) == first
    assert len(transport.calls) == 2


@pytest.mark.parametrize('shape', ['refusal', 'tool', 'malformed', 'duplicate_keys'])
def test_refused_malformed_or_tool_shaped_output_is_visible_without_retaining_raw_text(stack, shape):
    store, campaign, costs, transport = configured_current(stack)
    publish_account(stack, 'first')
    class EnvelopeTransport:
        def create(self, request, **bounds):
            envelope = json.loads(transport.create(request, **bounds))
            if shape == 'refusal':
                envelope['output'][0]['content'] = [{'type': 'refusal', 'refusal': 'SENSITIVE raw model refusal'}]
            elif shape == 'tool':
                envelope['output'] = [{'type': 'function_call', 'name': 'approve_enrichment', 'arguments': 'SENSITIVE'}]
            else:
                envelope['output'][0]['content'][0]['text'] = 'SENSITIVE malformed' if shape == 'malformed' else '{"candidates":[],"candidates":[]}'
            return json.dumps(envelope).encode()
    store.model_transport = EnvelopeTransport()
    result = rank(store, campaign)
    assert result['status'] == ('refused' if shape == 'refusal' else 'invalid')
    assert result['shortlist_id'] is None and 'SENSITIVE' not in json.dumps(result)
    cost = costs.read(result['operation_id'], HUMAN)
    assert cost['actuals']['amount'] == '0.175' and 'SENSITIVE' not in json.dumps(cost)
    assert rank(CampaignStore(store.db), campaign) == result
    assert len(transport.calls) == 1
