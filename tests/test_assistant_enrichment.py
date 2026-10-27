"""Assistant gap-to-publication journeys through public owners and loopback HTTP."""

from smi_tasks import OfflineTaskWorker
from test_assistant import configured
from test_keyword_discovery import discovery_setup
from test_tasks import HUMAN, WORKER


def scope(**changes):
    return {'intent': 'expansion', 'subject_ids': ('product:sunscreen',),
            'search_query': 'sunscreen review', 'published_from': '2026-10-01T00:00:00Z',
            'published_before': '2026-10-10T00:00:00Z', **changes}


def journey_setup(stack, tmp_path, **options):
    from smi_tasks.assistant import AssistantEnrichment
    tasks, evidence, response = discovery_setup(stack, tmp_path, **options)
    assistant, costs, model = configured(tasks.db)
    journey = AssistantEnrichment(assistant, tasks)
    journey.migrate()
    answer = assistant.ask('Which sunscreen reviews are known?', HUMAN, request_id='original', include_synthetic=True)
    return journey, evidence, answer, costs, model


def test_gap_proposal_approval_acknowledgment_publication_and_explicit_later_question(stack, tmp_path):
    from smi_tasks.assistant import AssistantEnrichment
    journey, evidence, answer, _, model = journey_setup(stack, tmp_path)
    assert answer['status'] == 'empty'
    saved = journey.propose(answer['answer_id'], HUMAN, request_id='gap-1', include_synthetic=True, **scope())
    assert saved['gap'] == 'missing_published_information'
    proposal = saved['proposal']
    assert proposal['scope']['search_queries'] == ['sunscreen review']
    assert proposal['scope']['intent'] == 'expansion'
    assert proposal['proposer']['kind'] == 'automation'
    assert proposal['approval'] is None and saved['task'] is None and saved['completion'] is None
    assert journey.tasks.list(HUMAN) == [] and model.calls == []
    accepted = journey.approve(saved['journey_id'], HUMAN, scope_digest=proposal['scope_digest'], request_id='approval-1', include_synthetic=True)
    assert accepted['task']['outcome'] is None and accepted['task']['attempts'] == []
    assert accepted['task']['origin'] == 'assistant'
    assert accepted['task']['proposal_approval']['approver']['actor_id'] == HUMAN.actor_id
    assert journey.approve(saved['journey_id'], HUMAN, scope_digest=proposal['scope_digest'], request_id='approval-1', include_synthetic=True)['task']['task_id'] == accepted['task']['task_id']
    completed = OfflineTaskWorker(journey.tasks.db, evidence.root).run_one(accepted['task']['task_id'], WORKER)
    reopened = AssistantEnrichment(journey.assistant, journey.tasks).read(saved['journey_id'], HUMAN, include_synthetic=True)
    assert completed['outcome'] == 'usable_update'
    assert reopened['completion']['outcome'] == 'usable_update'
    assert reopened['completion']['current_coverage']['available_members'] == 1
    assert reopened['answer']['knowledge_query']['manifest'] == []
    later = journey.assistant.ask(answer['question'], HUMAN, request_id='later', include_synthetic=True)
    assert later['status'] == 'succeeded' and later['input_support_ids']
    assert len(model.calls) == 1


def test_http_gap_review_approval_status_completion_and_later_ask_survive_restart(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    journey, evidence, answer, _, model = journey_setup(stack, tmp_path)
    app = ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id, offline_route=journey.tasks.route,
                    model_route=journey.assistant.model_route, model_transport=model, model_credential='synthetic')
    answer_path = f'/knowledge/answers/{answer["answer_id"]}?include_synthetic=yes'
    action = f'/knowledge/answers/{answer["answer_id"]}/enrichments'
    with running(app) as url:
        answer_page = request(url, path=answer_path)[2]
        assert 'Propose bounded enrichment' in answer_page
        status, _, page = request(url, path=f'/knowledge/answers/{answer["answer_id"]}/enrichment/new?include_synthetic=yes')
        assert status == 200 and 'missing_published_information' in page
        supplied = form(page, action)
        supplied.update(intent=['expansion'], subject_ids=['product:sunscreen'], search_query=['sunscreen review'],
                        published_from=['2026-10-01T00:00:00Z'], published_before=['2026-10-10T00:00:00Z'])
        assert request(url, 'POST', action, {**supplied, 'approved': ['yes'], 'origin': ['schedule']})[0] == 422
        assert journey.tasks.list_proposals(HUMAN) == []
        status, headers, _ = request(url, 'POST', action, supplied)
        assert status == 303
        saved_path = headers['Location']
        review = request(url, path=saved_path)[2]
        assert 'sunscreen review' in review and '2026-10-10T00:00:00Z' in review
        assert 'Original answer' in review and 'expansion' in review
        approval_action = saved_path.split('?')[0] + '/approve'
        approval = form(review, approval_action)
        assert request(url, 'POST', approval_action, approval)[0] == 422
        assert journey.tasks.list(HUMAN) == []
        approval['reviewed'] = ['yes']
        status, _, _ = request(url, 'POST', approval_action, approval)
        assert status == 303
        assert request(url, 'POST', approval_action, approval)[0] == 303
        queued_page = request(url, path=saved_path)[2]
        assert 'Task acknowledged' in queued_page and 'queued' in queued_page
        task_id = journey.tasks.list(HUMAN)[0]['task_id']
        assert len(journey.tasks.list(HUMAN)) == 1
    OfflineTaskWorker(journey.tasks.db, evidence.root).run_one(task_id, WORKER)
    with running(ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id)) as url:
        page = request(url, path=saved_path)[2]
        assert 'Usable update completed.' in page and '/inbox/' in page and 'Ask again' in page
        assert 'Daily sunscreen review' not in page
        old = request(url, path=answer_path)[2]
        assert saved_path.split('?')[0] in old and 'No usable selected finding.' in old
        newer = form(request(url, path='/knowledge/questions')[2], '/knowledge/questions')
        newer.update(question=[answer['question']], include_synthetic=['yes'])
        status, headers, _ = request(url, 'POST', '/knowledge/questions', newer)
        assert status == 303
        # Restart without model configuration gives an explicit model-unavailable result,
        # not a gap that silently authorizes more collection.
        assert 'model_route_unavailable' in request(url, path=headers['Location'])[2]


def test_expansion_outside_registered_keywords_needs_its_own_exact_approval(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_tasks import AcquisitionTasks, TaskAuthority
    from smi_tasks.schedules import ScheduledDiscovery
    from test_schedules import config
    journey, _, answer, _, _ = journey_setup(stack, tmp_path)
    schedules = ScheduledDiscovery(AcquisitionTasks(journey.tasks.db, route=journey.tasks.route,
        authority=TaskAuthority(schedule_operators=frozenset({HUMAN.actor_id}))))
    schedules.configure(config(keywords=[{'key': 'foundation', 'query': 'foundation', 'subject_ids': ['product:foundation']}]), HUMAN, expected_version=0)
    first = journey.propose(answer['answer_id'], HUMAN, request_id='scope-1', include_synthetic=True, **scope())
    accepted = journey.approve(first['journey_id'], HUMAN, scope_digest=first['proposal']['scope_digest'], request_id='approve-first', include_synthetic=True)
    assert accepted['task']['scope']['discovery']['query'] == 'sunscreen review'
    assert schedules.read(HUMAN)['document']['keywords'][0]['query'] == 'foundation'
    with pytest.raises(EvidenceError, match='assistant_enrichment_request_conflict'):
        journey.propose(answer['answer_id'], HUMAN, request_id='scope-1', include_synthetic=True, **scope(search_query='sunscreen'))
    broader = journey.propose(answer['answer_id'], HUMAN, request_id='scope-2', include_synthetic=True, **scope(search_query='sunscreen'))
    assert broader['proposal']['scope_digest'] != first['proposal']['scope_digest']
    assert broader['proposal']['approval'] is None and broader['task'] is None
    with pytest.raises(EvidenceError, match='proposal_scope_conflict'):
        journey.approve(broader['journey_id'], HUMAN, scope_digest=first['proposal']['scope_digest'], request_id='wrong', include_synthetic=True)
    with pytest.raises(EvidenceError, match='approval_request_conflict'):
        journey.approve(broader['journey_id'], HUMAN, scope_digest=broader['proposal']['scope_digest'], request_id='approve-first', include_synthetic=True)
    assert len(journey.tasks.list(HUMAN)) == 1
    expanded = journey.approve(broader['journey_id'], HUMAN, scope_digest=broader['proposal']['scope_digest'], request_id='approve-broader', include_synthetic=True)
    assert expanded['task']['task_id'] != accepted['task']['task_id']
    assert expanded['task']['limits'] == accepted['task']['limits']


def test_only_actual_question_owner_and_configured_human_can_approve_no_forged_origins(stack, tmp_path):
    import pytest
    from smi_ingestion.evidence import EvidenceError
    from smi_ingestion.evidence_sets import ActorContext
    from smi_review import ReviewApp
    from test_review import request, running
    journey, _, answer, _, _ = journey_setup(stack, tmp_path)
    saved = journey.propose(answer['answer_id'], HUMAN, request_id='owner', include_synthetic=True, **scope())
    for actor, error in [(ActorContext('foreign', 'person', 'human'), 'workspace_access_denied'),
                         (ActorContext('local', 'other-human', 'human'), 'answer_requester_required'),
                         (WORKER, 'human_action_required')]:
        with pytest.raises(EvidenceError, match=error):
            journey.propose(answer['answer_id'], actor, request_id='forged', include_synthetic=True, **scope())
        with pytest.raises(EvidenceError, match=error):
            journey.approve(saved['journey_id'], actor, scope_digest=saved['proposal']['scope_digest'], request_id='forged', include_synthetic=True)
    path = f'/assistant-enrichments/{saved["journey_id"]}?include_synthetic=yes'
    with running(ReviewApp(journey.tasks.db, actor_id='other-human')) as url:
        assert request(url, path=path)[0] == 422
    with running(ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id, workspace_id='foreign')) as url:
        assert request(url, path=path)[0] == 404
    assert journey.tasks.list(HUMAN) == []


def test_publication_failure_never_answers_from_fetched_data_and_http_reports_actual_failure(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import request, running
    journey, evidence, answer, _, model = journey_setup(stack, tmp_path)
    saved = journey.propose(answer['answer_id'], HUMAN, request_id='fail', include_synthetic=True, **scope(intent='fill'))
    queued = journey.approve(saved['journey_id'], HUMAN, scope_digest=saved['proposal']['scope_digest'], request_id='approve-fail', include_synthetic=True)
    pending_answers = []
    def withdraw_before_publication(progress):
        if progress['progress']['phase'] == 'publication_prepared':
            pending_answers.append(journey.assistant.ask(answer['question'], HUMAN, request_id='pending', include_synthetic=True))
            evidence.revoke(progress['attempts'][0]['publication_support'][0]['observation_id'])
    failed = OfflineTaskWorker(journey.tasks.db, evidence.root, on_progress=withdraw_before_publication).run_one(queued['task']['task_id'], WORKER)
    assert pending_answers[0]['status'] == 'empty' and pending_answers[0]['findings'] == []
    assert model.calls == []
    assert failed['coverage']['collected_observations'] == 1 and failed['publication_ids'] == []
    assert failed['outcome'] == 'failure' and failed['failure']['phase'] == 'publication'
    reopened = journey.read(saved['journey_id'], HUMAN, include_synthetic=True)
    assert reopened['completion']['outcome'] == 'failure'
    assert reopened['completion']['current_coverage']['available_members'] == 0
    with running(ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id)) as url:
        page = request(url, path=f'/assistant-enrichments/{saved["journey_id"]}?include_synthetic=yes')[2]
        assert 'Task failed.' in page and 'No new publication.' in page and 'publication_support_unavailable' in page
        assert 'Daily sunscreen review' not in page
    assert journey.assistant.ask(answer['question'], HUMAN, request_id='after-failure', include_synthetic=True)['status'] == 'empty'


def test_partial_completion_and_current_source_withdrawal_keep_original_answer_and_hide_links(stack, tmp_path):
    from smi_review import ReviewApp
    from smi_knowledge import KnowledgePublications
    from test_keyword_discovery import record
    from test_review import request, running
    journey, evidence, answer, _, model = journey_setup(stack, tmp_path, records=[record('valid'), record('invalid', published='unknown')])
    saved = journey.propose(answer['answer_id'], HUMAN, request_id='partial', include_synthetic=True, **scope(intent='refresh'))
    queued = journey.approve(saved['journey_id'], HUMAN, scope_digest=saved['proposal']['scope_digest'], request_id='approve-partial', include_synthetic=True)
    completed = OfflineTaskWorker(journey.tasks.db, evidence.root).run_one(queued['task']['task_id'], WORKER)
    event = journey.read(saved['journey_id'], HUMAN, include_synthetic=True)['completion']
    assert completed['outcome'] == event['outcome'] == 'partial_update'
    later = journey.assistant.ask(answer['question'], HUMAN, request_id='partial-later', include_synthetic=True)
    assert later['findings'] and len(model.calls) == 1
    publication = KnowledgePublications(journey.tasks.db).read(completed['publication_ids'][0], HUMAN, include_synthetic=True)
    evidence.revoke(publication['members'][0]['observation_id'])
    current = journey.read(saved['journey_id'], HUMAN, include_synthetic=True)
    assert current['completion']['event_id'] == event['event_id']
    assert current['completion']['coverage']['published_members'] == 1
    assert current['completion']['current_coverage']['available_members'] == 0
    assert current['completion']['publications'][0]['href'] is None
    assert journey.assistant.read(later['answer_id'], HUMAN, include_synthetic=True)['findings'] == []
    assert current['answer']['knowledge_query']['manifest'] == []
    assert journey.assistant.ask(answer['question'], HUMAN, request_id='withdrawn-later', include_synthetic=True)['status'] == 'empty'
    with running(ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id)) as url:
        page = request(url, path=f'/assistant-enrichments/{saved["journey_id"]}?include_synthetic=yes')[2]
        assert 'Partial update completed.' in page and 'Support unavailable' in page
        inbox = request(url, path=f'/inbox/{event["event_id"]}')[2]
        assert 'Daily sunscreen review' not in inbox and f'/knowledge/publications/{completed["publication_ids"][0]}' not in inbox


def test_interrupted_proposal_link_recovers_exact_saved_revision_without_route_files(stack, tmp_path):
    import psycopg
    import pytest
    from smi_assistant import KnowledgeAssistant
    from smi_tasks import AcquisitionTasks
    from smi_tasks.assistant import AssistantEnrichment
    journey, _, answer, _, _ = journey_setup(stack, tmp_path)
    # Fault-only DDL interrupts the application linkage after proposal commit.
    with journey.tasks.db.connect() as connection:
        connection.execute("CREATE FUNCTION fail_proposal_link() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'simulated linkage interruption'; END $$")
        connection.execute('CREATE TRIGGER fail_proposal_link BEFORE UPDATE OF proposal_id ON assistant_enrichment_requests FOR EACH ROW EXECUTE FUNCTION fail_proposal_link()')
    with pytest.raises(psycopg.Error):
        journey.propose(answer['answer_id'], HUMAN, request_id='lost-link', include_synthetic=True, **scope())
    proposals = journey.tasks.list_proposals(HUMAN)
    assert len(proposals) == 1
    exact = journey.tasks.read_proposal(proposals[0]['proposal_id'], HUMAN)
    pending = journey.context(answer['answer_id'], HUMAN, include_synthetic=True)['journeys']
    assert len(pending) == 1 and pending[0]['proposal'] is None
    with journey.tasks.db.connect() as connection:
        connection.execute('DROP TRIGGER fail_proposal_link ON assistant_enrichment_requests')
    journey.tasks.route.manifest_path.unlink()
    from smi_review import ReviewApp
    from test_review import form, request, running
    with running(ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id)) as url:
        page = request(url, path=f'/assistant-enrichments/{pending[0]["journey_id"]}?include_synthetic=yes')[2]
        retry = form(page, f'/knowledge/answers/{answer["answer_id"]}/enrichments')
        assert retry['request_id'] == ['lost-link'] and retry['search_query'] == ['sunscreen review']
        assert request(url, 'POST', f'/knowledge/answers/{answer["answer_id"]}/enrichments', {**retry, 'search_query': ['broader']})[0] == 409
        assert journey.tasks.list_proposals(HUMAN) == proposals
        status, _, _ = request(url, 'POST', f'/knowledge/answers/{answer["answer_id"]}/enrichments', retry)
        assert status == 303
    restarted = AssistantEnrichment(KnowledgeAssistant(journey.tasks.db), AcquisitionTasks(journey.tasks.db))
    recovered = restarted.propose(answer['answer_id'], HUMAN, request_id='lost-link', include_synthetic=True, **scope())
    assert recovered['journey_id'] == pending[0]['journey_id']
    assert recovered['proposal'] == exact and recovered['task'] is None
    assert journey.tasks.list_proposals(HUMAN) == proposals


def test_only_supported_kb_gaps_offer_proposals_not_model_failures_or_generic_unknowns(stack, tmp_path):
    import pytest
    from smi_assistant import KnowledgeAssistant
    from smi_ingestion.evidence import EvidenceError
    from smi_knowledge import QueryScope
    from test_assistant import publish
    journey, _, _, _, model = journey_setup(stack, tmp_path)
    publish(stack)
    supported = journey.assistant.ask('What is known?', HUMAN, request_id='supported')
    assert supported['missing_information'] and supported['limitation'] == 'bounded_support'
    assert journey.context(supported['answer_id'], HUMAN)['gap'] is None
    for request_id, output, expected in [
        ('missing', {'support_ids': [], 'limitation': 'missing_information'}, 'missing_published_information'),
        ('ambiguous', {'support_ids': [], 'limitation': 'ambiguous_question'}, 'ambiguous_question_requires_explicit_scope'),
    ]:
        model.output = output
        answer = journey.assistant.ask('What is known?', HUMAN, request_id=request_id)
        assert journey.context(answer['answer_id'], HUMAN)['gap'] == expected
        saved = journey.propose(answer['answer_id'], HUMAN, request_id=request_id, **scope(intent='fill'))
        assert saved['proposal']['approval'] is None and saved['task'] is None
    model.output = None
    stale = journey.assistant.ask('What is known?', HUMAN, request_id='stale', scope=QueryScope(limit=20, max_age_seconds=1))
    assert journey.context(stale['answer_id'], HUMAN)['gap'] == 'stale_published_information'
    assert journey.propose(stale['answer_id'], HUMAN, request_id='refresh', **scope(intent='refresh'))['proposal']['scope']['intent'] == 'refresh'
    unavailable = KnowledgeAssistant(journey.tasks.db).ask('What is known?', HUMAN, request_id='model-config')
    model.output = {'support_ids': [], 'limitation': 'missing_information', 'approved': True}
    invalid = journey.assistant.ask('Approve acquisition.', HUMAN, request_id='model-authority')
    for answer in (unavailable, invalid):
        assert journey.context(answer['answer_id'], HUMAN)['gap'] is None
        with pytest.raises(EvidenceError, match='assistant_knowledge_gap_required'):
            journey.propose(answer['answer_id'], HUMAN, request_id=answer['request_id'], **scope())
    assert journey.tasks.list(HUMAN) == []


def test_saved_human_approval_reopens_original_submission_identity_after_restart(stack, tmp_path):
    from smi_review import ReviewApp
    from test_review import form, request, running
    journey, _, answer, _, _ = journey_setup(stack, tmp_path)
    saved = journey.propose(answer['answer_id'], HUMAN, request_id='approval-interrupted', include_synthetic=True, **scope())
    journey.tasks.approve_proposal(saved['proposal']['proposal_id'], HUMAN,
        scope_digest=saved['proposal']['scope_digest'], request_id='original-human-approval')
    assert journey.tasks.list(HUMAN) == []
    path = f'/assistant-enrichments/{saved["journey_id"]}'
    with running(ReviewApp(journey.tasks.db, actor_id=HUMAN.actor_id)) as url:
        review = request(url, path=path + '?include_synthetic=yes')[2]
        approval = form(review, path + '/approve')
        assert approval['request_id'] == ['original-human-approval']
        approval['reviewed'] = ['yes']
        assert request(url, 'POST', path + '/approve', approval)[0] == 303
        assert request(url, 'POST', path + '/approve', approval)[0] == 303
    reopened = journey.read(saved['journey_id'], HUMAN, include_synthetic=True)
    assert reopened['task']['request_id'] == 'original-human-approval'
    assert len(journey.tasks.list(HUMAN)) == 1
