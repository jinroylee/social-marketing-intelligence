"""Operational review journeys with real PostgreSQL and simulated external I/O."""

import copy
import json

import pytest

from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from test_assistant import configured, publish
from test_publications import HUMAN
from test_recent_monitoring import no_external_io as recent_no_external_io

no_external_io = recent_no_external_io


def test_answer_packet_pins_exact_membership_with_pending_human_fields(stack):
    from smi_review.quality import OperationalReviews

    _, observation = publish(stack, value='肌の調子は不明。')
    assistant, _, model = configured(stack[0])
    answer = assistant.ask('What is known?', HUMAN, request_id='answer')
    reviews = OperationalReviews(stack[0])
    reviews.migrate()
    packet = reviews.export('answer', answer['answer_id'], HUMAN, request_id='packet')
    assert packet['membership'] == answer['selected_support_ids']
    assert packet['input_support_ids'] == answer['input_support_ids']
    assert packet['sources'][0]['observation_id'] == observation.id
    assert packet['sources'][0]['texts'][0]['original_text'] == '肌の調子は不明。'
    assert packet['sources'][0]['captured_at'] == '2026-10-01T00:00:00+00:00'
    assert packet['versions']['model_version'] == 'synthetic-model-revision-v1'
    assert packet['review'] is None
    assert packet['pending_fields']['translation'] is None
    assert packet['pending_fields']['reviewer'] is None
    assert packet['quality'] == {'technical': 'pending', 'translation_assisted': 'pending',
        'japanese_original': 'not_validated', 'marketer_usefulness': 'pending'}
    assert packet['denominators'] == {'selected': 1, 'submitted': 0, 'countable': 0, 'unavailable': 0}
    assert OperationalReviews(stack[0]).read(packet['packet_id'], HUMAN) == packet
    assert reviews.export('answer', answer['answer_id'], HUMAN, request_id='packet') == packet
    assert len(model.calls) == 1


def review(packet):
    """Synthetic actors/annotations exercise software; they are not quality receipts."""
    return {'reviewer': HUMAN.actor_id, 'attested': True, 'reviewed_at': '2026-10-29T10:00:00+09:00',
        'method_version': 'synthetic-translation-review-v1', 'denominator': len(packet['membership']),
        'items': [{'item_id': identity, 'translation': 'Synthetic translation, not verified truth.',
            'translator': {'actor_id': 'synthetic-translator', 'kind': 'automation',
                'method_version': 'synthetic-translation-v1', 'model_version': 'synthetic-model-v1'},
            'label': 'ambiguous', 'ambiguity': 'Synthetic ambiguity.', 'material_error': False,
            'error': None, 'correction': None} for identity in packet['membership']],
        'marketer_usefulness': None}


def answer_packet(stack):
    from smi_review.quality import OperationalReviews
    publish(stack, value='肌の調子は不明。')
    assistant, _, _ = configured(stack[0])
    answer = assistant.ask('What is known?', HUMAN, request_id='answer')
    owner = OperationalReviews(stack[0])
    owner.migrate()
    return owner, owner.export('answer', answer['answer_id'], HUMAN, request_id='packet')


def test_explicit_synthetic_review_reopens_without_inventing_other_quality_gates(stack):
    from smi_review.quality import OperationalReviews
    owner, packet = answer_packet(stack)
    body = review(packet)
    recorded = owner.record(packet['packet_id'], body, HUMAN, request_id='review')
    assert recorded['review'] == body
    assert recorded['quality'] == {'technical': 'pending', 'translation_assisted': 'recorded',
        'japanese_original': 'not_validated', 'marketer_usefulness': 'pending'}
    assert recorded['denominators'] == {'selected': 1, 'submitted': 1, 'countable': 1, 'unavailable': 0}
    assert recorded['label_counts'] == {'supported': 0, 'unsupported': 0, 'ambiguous': 1, 'not_assessable': 0}
    assert OperationalReviews(stack[0]).read(packet['packet_id'], HUMAN) == recorded
    assert owner.record(packet['packet_id'], body, HUMAN, request_id='review') == recorded
    changed = copy.deepcopy(body)
    changed['items'][0]['translation'] = 'A different translation'
    with pytest.raises(EvidenceError, match='review_record_request_conflict'):
        owner.record(packet['packet_id'], changed, HUMAN, request_id='review')


@pytest.mark.parametrize('invalid', ['actor', 'time', 'denominator', 'duplicate', 'label', 'translator', 'model', 'material', 'usefulness'])
def test_review_requires_actual_attribution_exact_membership_and_explicit_human_inputs(stack, invalid):
    owner, packet = answer_packet(stack)
    body = review(packet)
    if invalid == 'actor':
        body['reviewer'] = 'someone-else'
    elif invalid == 'time':
        body['reviewed_at'] = None
    elif invalid == 'denominator':
        body['denominator'] = 2
    elif invalid == 'duplicate':
        body['items'] *= 2
    elif invalid == 'label':
        body['items'][0]['label'] = 'verified-source-truth'
    elif invalid == 'translator':
        body['items'][0]['translator']['actor_id'] = None
    elif invalid == 'model':
        body['items'][0]['translator']['model_version'] = None
    elif invalid == 'material':
        body['items'][0]['material_error'] = True
    else:
        body['marketer_usefulness'] = {'useful': True}
    with pytest.raises(EvidenceError, match='invalid_review'):
        owner.record(packet['packet_id'], body, HUMAN, request_id='bad')
    assert owner.read(packet['packet_id'], HUMAN)['review'] is None
    for operation in (lambda **kw: owner.read(packet['packet_id'], HUMAN, **kw),
                      lambda **kw: owner.record(packet['packet_id'], review(packet), HUMAN, request_id='bad', **kw)):
        with pytest.raises(EvidenceError, match='invalid_synthetic_selection'):
            operation(include_synthetic='false')
    with pytest.raises(EvidenceError, match='invalid_review_identity'):
        owner.read('not-a-packet-id', HUMAN)
    with pytest.raises(EvidenceError, match='invalid_review_identity'):
        owner.record('not-a-packet-id', review(packet), HUMAN, request_id='bad')
    with pytest.raises(EvidenceError, match='human_action_required'):
        owner.record(packet['packet_id'], review(packet), ActorContext('local', 'worker', 'automation'), request_id='worker')


def test_unselected_answer_input_loss_purges_copied_annotations_and_cannot_count_as_a_pass(stack):
    from smi_review.quality import OperationalReviews
    _, unselected = publish(stack, native_id='older', value='古い未選択の入力')
    owner, packet = answer_packet(stack)
    assert len(packet['membership']) == 1 and len(packet['input_support_ids']) == 2
    body = review(packet)
    owner.record(packet['packet_id'], body, HUMAN, request_id='review')
    stack[1].revoke(unselected.id)
    reopened = OperationalReviews(stack[0]).read(packet['packet_id'], HUMAN)
    assert reopened['membership'] == packet['membership']
    assert reopened['input_support_ids'] == packet['input_support_ids']
    assert reopened['result'] is reopened['review'] is None
    assert reopened['records'][0]['purged'] is True
    assert reopened['records'][0]['attribution']['reviewer'] == HUMAN.actor_id
    assert reopened['denominators'] == {'selected': 1, 'submitted': 1, 'countable': 0, 'unavailable': 1}
    assert reopened['quality']['translation_assisted'] == 'pending'
    assert reopened['quality']['marketer_usefulness'] == 'pending'
    assert 'Synthetic translation' not in json.dumps(reopened)
    assert '古い未選択' not in json.dumps(reopened)
    assert owner.export('answer', packet['result_id'], HUMAN, request_id='packet') == reopened
    assert owner.record(packet['packet_id'], body, HUMAN, request_id='new-review')['recording_status'] == 'support_unavailable'
    assert len(owner.read(packet['packet_id'], HUMAN)['records']) == 1


def test_saved_recommendation_packet_reopens_exact_model_order_and_full_support(stack):
    from smi_review.quality import OperationalReviews
    from test_ranked_recommendations import configured_current, rank
    store, campaign, _, model = configured_current(stack)
    _, source = publish(stack, value='化粧品の効果は不明。')
    result = rank(store, campaign)
    saved = store.read_shortlist(result['shortlist_id'], HUMAN)
    owner = OperationalReviews(stack[0])
    owner.migrate()
    packet = owner.export('recommendation', result['shortlist_id'], HUMAN, request_id='recommendation')
    assert packet['membership'] == [s['candidate_id'] for s in saved['selected']]
    assert packet['result']['selected'][0]['reason_basis'] == 'automated_model_judgment'
    assert packet['result_context']['brief_id'] == campaign['brief_id']
    assert packet['versions']['model_version'] == 'synthetic-model-revision-v1'
    assert packet['sources'][0]['texts'][0]['original_text'] == '化粧品の効果は不明。'
    body = review(packet)
    owner.record(packet['packet_id'], body, HUMAN, request_id='review')
    stack[1].revoke(source.id)
    reopened = owner.read(packet['packet_id'], HUMAN)
    assert reopened['result'] is reopened['review'] is None
    assert reopened['denominators']['countable'] == 0 and reopened['records'][0]['purged'] is True
    assert '化粧品の効果' not in json.dumps(reopened)
    assert len(model.calls) == 1


def test_semantic_packet_keeps_exact_original_spans_and_partial_review_denominators(stack, tmp_path):
    from smi_review.quality import OperationalReviews
    from test_semantic_alerts import collected, semantic
    recent, window = collected(stack, tmp_path)
    semantic_owner, _, model = semantic(recent)
    from test_recent_monitoring import OPERATOR
    alert = semantic_owner.detect(window, OPERATOR, request_id='alert')
    owner = OperationalReviews(stack[0], recent=recent)
    owner.migrate()
    packet = owner.export('semantic_alert', alert['alert_id'], HUMAN, request_id='semantic')
    assert packet['membership'] == alert['input_observation_ids']
    assert packet['sources'][0]['spans'] == [{'start': 0, 'end': 31, 'excerpt': 'cushion quality failed <sample>'}]
    assert packet['result']['comparison'] == {'baseline_window_id': None, 'change_status': 'not_assessed'}
    body = review(packet)
    body['items'] = body['items'][:1]
    recorded = owner.record(packet['packet_id'], body, HUMAN, request_id='partial')
    assert recorded['denominators'] == {'selected': 3, 'submitted': 1, 'countable': 1, 'unavailable': 0}
    assert recorded['quality']['translation_assisted'] == 'pending'
    assert recorded['quality']['japanese_original'] == 'not_validated'
    assert recorded['review']['marketer_usefulness'] is None
    from test_recent_monitoring import OPERATOR
    recent.withdraw('13', OPERATOR)
    reopened = owner.record(packet['packet_id'], body, HUMAN, request_id='after-loss')
    assert reopened['review'] is reopened['result'] is None and reopened['records'][0]['purged'] is True
    assert reopened['denominators'] == {'selected': 3, 'submitted': 1, 'countable': 0, 'unavailable': 3}
    assert len(model.calls) == 1


def test_material_errors_and_explicit_corrections_remain_attributed_revisions(stack):
    owner, packet = answer_packet(stack)
    body = review(packet)
    body['items'][0].update(label='unsupported', material_error=True, error='Synthetic error changes the decision.')
    body['marketer_usefulness'] = {'useful': True, 'rationale': 'Synthetic test judgment.', 'task_seconds': 25, 'inspected_posts': 1}
    failed = owner.record(packet['packet_id'], body, HUMAN, request_id='error')
    assert failed['quality']['translation_assisted'] == failed['quality']['marketer_usefulness'] == 'failed'
    body['items'][0]['correction'] = 'Synthetic correction explicitly supplied by the reviewer.'
    corrected = owner.record(packet['packet_id'], body, HUMAN, request_id='correction')
    assert corrected['quality']['translation_assisted'] == corrected['quality']['marketer_usefulness'] == 'recorded'
    assert corrected['quality']['technical'] == 'pending' and corrected['quality']['japanese_original'] == 'not_validated'
    assert corrected['review']['marketer_usefulness']['task_seconds'] == 25
    assert len(corrected['records']) == 2
    assert corrected['label_counts']['unsupported'] == 1


@pytest.mark.parametrize('change', [{'can_process': False}, {'can_display': False}, {'can_retain': False},
    {'revoked': True}, {'expires_at': '2026-10-28T12:00:00Z'}])
def test_current_recent_permissions_rechecked_on_export_record_and_read(stack, tmp_path, change):
    from smi_review.quality import OperationalReviews
    from test_recent_monitoring import OPERATOR, POLICY
    from test_semantic_alerts import collected, semantic
    recent, window = collected(stack, tmp_path)
    semantic_owner, _, _ = semantic(recent)
    alert = semantic_owner.detect(window, OPERATOR, request_id='alert')
    owner = OperationalReviews(stack[0], recent=recent)
    owner.migrate()
    packet = owner.export('semantic_alert', alert['alert_id'], HUMAN, request_id='packet')
    body = review(packet)
    owner.record(packet['packet_id'], body, HUMAN, request_id='before')
    recent.set_policy({**POLICY, **change}, OPERATOR, expected_version=1)
    exported = owner.export('semantic_alert', alert['alert_id'], HUMAN, request_id='packet')
    assert exported['result'] is exported['review'] is None
    assert exported['denominators']['countable'] == 0
    assert all(not s['texts'] and not s['spans'] for s in exported['sources'])
    assert owner.record(packet['packet_id'], body, HUMAN, request_id='after')['recording_status'] == 'support_unavailable'
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    reopened = owner.read(packet['packet_id'], HUMAN)
    assert reopened['review'] is None and reopened['quality']['translation_assisted'] == 'pending'
    with pytest.raises(EvidenceError, match='workspace_access_denied'):
        owner.read(packet['packet_id'], ActorContext('different', HUMAN.actor_id, 'human'))


def test_cli_export_record_reopen_uses_named_actor_and_does_not_fill_human_fields(stack, tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    owner, packet = answer_packet(stack)
    command = [sys.executable, str(Path(__file__).parents[1] / 'tools/operational_quality.py'),
        '--schema', stack[0].schema, '--actor', HUMAN.actor_id]
    env = {**os.environ, 'SMI_DATABASE_URL': stack[0].dsn}
    exported = json.loads(subprocess.check_output([*command, 'export', 'answer', packet['result_id'], '--request-id', 'cli'], text=True, env=env))
    assert exported['review_template']['reviewer'] is None
    assert exported['review_template']['reviewed_at'] is None
    assert all(i['translation'] is None and i['label'] is None for i in exported['review_template']['items'])
    source = tmp_path / 'synthetic-review.json'
    source.write_text(json.dumps(review(exported)))
    recorded = json.loads(subprocess.check_output([*command, 'record', exported['packet_id'], str(source), '--request-id', 'cli-review'], text=True, env=env))
    reopened = json.loads(subprocess.check_output([*command, 'read', exported['packet_id']], text=True, env=env))
    assert recorded == reopened
    assert reopened['records'][0]['attribution']['reviewer'] == HUMAN.actor_id
    assert reopened['quality']['japanese_original'] == 'not_validated'
    assert owner.read(packet['packet_id'], HUMAN)['review'] is None


def test_packet_spans_belong_to_the_exact_interpreted_publication(stack):
    from dataclasses import replace
    from smi_review.quality import OperationalReviews
    from test_graph import publish_product_mention
    claim = publish_product_mention(stack, source_only_first=True)
    assistant, _, _ = configured(stack[0])
    assistant.model_route = replace(assistant.model_route, max_request_bytes=200000)
    answer = assistant.ask('Which product was mentioned?', HUMAN, request_id='mention')
    assert answer['usable']
    owner = OperationalReviews(stack[0])
    owner.migrate()
    packet = owner.export('answer', answer['answer_id'], HUMAN, request_id='spans')
    sources = [s for s in packet['sources'] if s['observation_id'] == claim['observation_id']]
    assert len(sources) == 2
    source_only = next(s for s in sources if not next(m for m in packet['dependencies']
        if m['publication_id'] == s['publication_id'])['interpretation_ids'])
    interpreted = next(s for s in sources if s is not source_only)
    assert source_only['spans'] == []
    assert interpreted['spans'][0]['interpretation_id'] == claim['id']
    assert interpreted['spans'][0]['publication_id'] == interpreted['publication_id']
    assert interpreted['spans'][0]['source_subject_id'] == claim['subject_id']


def test_packet_publication_dates_belong_to_each_original_text_subject(stack):
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from smi_review.quality import OperationalReviews
    from test_publications import WORKER, ingest_account
    db = stack[0]
    run, observation = ingest_account(stack)
    posts = [ExternalKey('test', 'public', 'content', 'dated-' + str(i)) for i in (1, 2)]
    CanonicalWriter(db).apply(observation.id, NormalizedBatch(tuple(posts), (
        FieldCandidate(posts[0], 'caption', 'observed', 'First original', '$.first.caption'),
        FieldCandidate(posts[0], 'published_at', 'observed', '2026-09-01T00:00:00Z', '$.first.date'),
        FieldCandidate(posts[1], 'caption', 'observed', 'Second original', '$.second.caption'),
        FieldCandidate(posts[1], 'published_at', 'observed', '2026-09-21T00:00:00Z', '$.second.date'),
    ), ()), 'multi-post-review:v1')
    publications = KnowledgePublications(db)
    publications.migrate()
    publications.publish(IngestedEvidence(db).select_run(run, HUMAN), WORKER, request_id='two-posts')
    assistant, _, _ = configured(db)
    answer = assistant.ask('What posts are known?', HUMAN, request_id='dates')
    owner = OperationalReviews(db)
    owner.migrate()
    packet = owner.export('answer', answer['answer_id'], HUMAN, request_id='dates')
    source = packet['sources'][0]
    assert source['published_at'] is None
    assert {t['identity']['native_id']: t['source_published_at'] for t in source['texts']} == {
        'dated-1': '2026-09-01T00:00:00Z', 'dated-2': '2026-09-21T00:00:00Z'}
    assert all(t['source_subject_id'] and t['span']['start'] == 0 for t in source['texts'])


@pytest.mark.parametrize('rejected', ['invalid', 'conflicting'])
def test_rejected_record_cannot_rollback_retention_purge_and_resurrect_annotations(stack, tmp_path, rejected):
    from smi_review.quality import OperationalReviews
    from test_recent_monitoring import OPERATOR, POLICY
    from test_semantic_alerts import collected, semantic
    recent, window = collected(stack, tmp_path)
    semantic_owner, _, _ = semantic(recent)
    alert = semantic_owner.detect(window, OPERATOR, request_id='alert')
    owner = OperationalReviews(stack[0], recent=recent)
    owner.migrate()
    packet = owner.export('semantic_alert', alert['alert_id'], HUMAN, request_id='packet')
    body = review(packet)
    owner.record(packet['packet_id'], body, HUMAN, request_id='before')
    recent.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
    invalid = {} if rejected == 'invalid' else {**body, 'reviewed_at': '2026-10-29T11:00:00+09:00'}
    denied = owner.record(packet['packet_id'], invalid, HUMAN, request_id='before')
    assert denied['recording_status'] == 'support_unavailable'
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    reopened = owner.read(packet['packet_id'], HUMAN)
    assert reopened['records'][0]['purged'] is True
    assert reopened['review'] is None and reopened['denominators']['countable'] == 0
    assert 'Synthetic translation' not in json.dumps(reopened)


@pytest.mark.parametrize('kind', ['answer', 'recommendation'])
def test_record_holds_full_input_policy_through_its_commit(stack, kind):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from smi_review.quality import OperationalReviews
    if kind == 'answer':
        _, dependency = publish(stack, native_id='unselected', value='Unselected actual input')
        owner, packet = answer_packet(stack)
        assert len(packet['input_support_ids']) == 2
    else:
        from test_ranked_recommendations import configured_current, rank
        campaigns, campaign, _, _ = configured_current(stack)
        _, dependency = publish(stack)
        result = rank(campaigns, campaign)
        owner = OperationalReviews(stack[0])
        owner.migrate()
        packet = owner.export(kind, result['shortlist_id'], HUMAN, request_id='packet')
    # Fault-only DDL pauses a real public write; diagnostics inspect blocking,
    # while all business outcomes are observed through public review readers.
    with stack[0].connect() as setup:
        setup.execute('CREATE FUNCTION pause_review() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(937438); RETURN NEW; END $$')
        setup.execute('CREATE TRIGGER pause_review BEFORE INSERT ON operational_review_records FOR EACH ROW EXECUTE FUNCTION pause_review()')
    with stack[0].connect() as gate, ThreadPoolExecutor(max_workers=2) as pool:
        gate.execute('SELECT pg_advisory_xact_lock(937438)')
        pending = pool.submit(owner.record, packet['packet_id'], review(packet), HUMAN, request_id='race')
        deadline, pid = time.monotonic() + 5, None
        while time.monotonic() < deadline:
            with stack[0].connect() as diagnostic:
                row = diagnostic.execute("SELECT pid FROM pg_locks WHERE locktype='advisory' AND objid=937438 AND NOT granted").fetchone()
            if row:
                pid = row['pid']
                break
            time.sleep(0.01)
        if pid is None:
            gate.commit()
        assert pid is not None, 'review did not reach the injected commit pause'
        mutation = pool.submit(stack[1].revoke, dependency.id)
        blocked = False
        while time.monotonic() < deadline:
            with stack[0].connect() as diagnostic:
                blocked = diagnostic.execute('SELECT EXISTS (SELECT FROM pg_stat_activity WHERE %s=ANY(pg_blocking_pids(pid))) AS blocked', (pid,)).fetchone()['blocked']
            if blocked:
                break
            time.sleep(0.01)
        gate.commit()
        recorded = pending.result(timeout=5)
        mutation.result(timeout=5)
        assert blocked, 'source policy mutation escaped the review commit'
    assert recorded['review'] is not None
    reopened = owner.read(packet['packet_id'], HUMAN)
    assert reopened['review'] is None and reopened['records'][0]['purged'] is True
    assert reopened['denominators']['countable'] == 0


def test_unavailable_new_export_commits_existing_annotation_cleanup(stack, tmp_path):
    from smi_review.quality import OperationalReviews
    from test_recent_monitoring import OPERATOR, POLICY
    from test_semantic_alerts import collected, semantic
    recent, window = collected(stack, tmp_path)
    semantic_owner, _, _ = semantic(recent)
    alert = semantic_owner.detect(window, OPERATOR, request_id='alert')
    owner = OperationalReviews(stack[0], recent=recent)
    owner.migrate()
    packet = owner.export('semantic_alert', alert['alert_id'], HUMAN, request_id='packet')
    owner.record(packet['packet_id'], review(packet), HUMAN, request_id='before')
    recent.set_policy({**POLICY, 'can_retain': False}, OPERATOR, expected_version=1)
    denied = owner.export('semantic_alert', alert['alert_id'], HUMAN, request_id='new-export')
    assert denied['packet_id'] is None and denied['recording_status'] == 'support_unavailable'
    assert denied['sources'] == []
    recent.set_policy(POLICY, OPERATOR, expected_version=2)
    reopened = owner.read(packet['packet_id'], HUMAN)
    assert reopened['records'][0]['purged'] is True and reopened['review'] is None


def test_review_history_has_explicit_append_bound_and_old_exact_retries_recover(stack):
    owner, packet = answer_packet(stack)
    body = review(packet)
    for number in range(50):
        recorded = owner.record(packet['packet_id'], body, HUMAN, request_id='revision-' + str(number))
    assert len(recorded['records']) == 50
    assert recorded['bounds']['record_limit'] == 50
    with pytest.raises(EvidenceError, match='operational_review_record_limit'):
        owner.record(packet['packet_id'], body, HUMAN, request_id='revision-51')
    assert owner.record(packet['packet_id'], body, HUMAN, request_id='revision-0') == recorded
