from __future__ import annotations

from dataclasses import replace

from smi_campaigns import CampaignStore, Criterion
from smi_ingestion.contracts import ExternalKey
from smi_knowledge import KnowledgeStore
from test_campaigns import AUTOMATION, BRIEF, CATALOG_PATH, campaigns as campaigns_fixture

campaigns = campaigns_fixture
from smi_knowledge import Catalog
from test_publications import HUMAN
from test_knowledge_queries import publish_account


def current_campaign(stack, **changes):
    db, _, _, _ = stack
    knowledge = KnowledgeStore(db)
    knowledge.migrate()
    knowledge.register_catalog(Catalog.load(CATALOG_PATH), HUMAN)
    store = CampaignStore(db)
    store.migrate()
    brief = replace(BRIEF, platforms=("test",), known_accounts=(ExternalKey("test", "public", "account", "seed-only"),), **changes)
    return store, store.start(brief, HUMAN, request_id="campaign")


def prepare(store, campaign, request_id="current", **options):
    prepared = store.prepare_current_comparison(campaign["campaign_id"], campaign["brief_id"], AUTOMATION,
                                               request_id=request_id, **options)
    return store.read_comparison(prepared["comparison_id"], HUMAN)


def test_minimal_published_account_is_eligible_and_uningested_reference_is_only_a_gap(stack):
    store, campaign = current_campaign(stack, criteria=(Criterion("audience", "Japanese audience", "audience_geography", "JP", True, "include", "defer"),))
    publication, observation = publish_account(stack, "minimal")
    view = prepare(store, campaign)
    assert view["method"] == "rule_based" and view["source_mode"] == "current_knowledge"
    assert view["brief_id"] == campaign["brief_id"]
    assert view["executable_profile"]["brief_version"] == 1
    assert view["knowledge_query"]["manifest"][0]["publication_id"] == publication["publication_id"]
    assert view["coverage"]["discovery_seeds"][0]["native_id"] == "seed-only"
    assert len(view["candidates"]) == 1
    candidate = view["candidates"][0]
    assert candidate["account_key"] == {"platform": "test", "namespace": "public", "kind": "account", "native_id": "account-1"}
    assert candidate["body"]["observations"] == [observation.id]
    assert candidate["body"]["assessment"] == "deferred_unknown_requirements"
    assert candidate["body"]["judgments"][0]["state"] == "unknown"
    assert "caption_interpretations_not_published" in candidate["body"]["unknowns"]
    assert candidate["body"]["support_manifest"][0]["selected_freshness"]["state"] == "not_assessed"
    assert candidate["evidence"] == []
    assert store.read_campaign(campaign["campaign_id"], HUMAN)["shortlists"] == []


def test_history_is_pinned_across_new_publications_namespaces_and_retention_withdrawal(stack):
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import FieldCandidate, NormalizedBatch
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_publications import ingest_account

    store, campaign = current_campaign(stack)
    _, first = publish_account(stack, "first")
    original = prepare(store, campaign)
    run_id, second = ingest_account(stack)
    key = ExternalKey("test", "separate-provider", "account", "account-1")
    CanonicalWriter(store.db).apply(second.id, NormalizedBatch((key,), (FieldCandidate(key, "handle", "not_returned", None, "$.handle"),), ()), "namespace:v2")
    KnowledgePublications(store.db).publish(IngestedEvidence(store.db).select_run(run_id, HUMAN), AUTOMATION, request_id="second")
    newer = prepare(store, campaign, "newer", max_age_seconds=1)
    assert [c["account_key"]["namespace"] for c in newer["candidates"]] == ["separate-provider", "public"]
    assert newer["candidates"][0]["body"]["support_manifest"][0]["selected_freshness"]["state"] == "stale"
    retried = prepare(store, campaign)
    assert retried["candidates"] == original["candidates"]
    assert retried["knowledge_query"]["manifest"] == original["knowledge_query"]["manifest"]
    stack[1].revoke(first.id)
    withdrawn = CampaignStore(store.db).read_comparison(original["comparison_id"], HUMAN)
    assert len(withdrawn["candidates"]) == 1
    assert withdrawn["candidates"][0]["body"] is None
    assert withdrawn["candidates"][0]["account_key"]["namespace"] == "public"
    assert withdrawn["knowledge_query"]["manifest"] == original["knowledge_query"]["manifest"]
    assert len(prepare(store, campaign, "after-withdrawal")["candidates"]) == 1


def test_empty_scope_reports_discovery_gaps_and_keeps_campaign_history(stack):
    store, campaign = current_campaign(stack, publication_from="2040-01-01T00:00:00+00:00")
    publish_account(stack, "outside-window")
    view = prepare(store, campaign)
    assert view["candidates"] == []
    assert view["coverage"]["actual_observation_ids"] == []
    assert "no_eligible_supported_accounts_in_campaign_scope" in view["coverage"]["unknowns"]
    assert view["coverage"]["discovery_seeds"][0]["native_id"] == "seed-only"
    assert len(store.read_campaign(campaign["campaign_id"], HUMAN)["comparisons"]) == 1


def test_http_prepares_current_support_without_a_dataset_and_reopens_after_restart(stack):
    import re

    from smi_review import ReviewApp
    from test_review import request, running

    store, campaign = current_campaign(stack)
    _, observation = publish_account(stack, "http", native_id="<script>account</script>")
    campaign_path = "/campaigns/" + campaign["campaign_id"]
    with running(ReviewApp(store.db)) as url:
        status, _, page = request(url, path=campaign_path)
        assert status == 200
        assert "Compare current knowledge" in page
        csrf = re.search(r'name="csrf" value="([^"]+)"', page)[1]
        status, _, rejected = request(url, "POST", campaign_path + "/current-comparisons", {
            "csrf": csrf, "request_id": "invalid", "brief_id": campaign["brief_id"], "actor": "human",
        })
        assert status == 422 and "invalid_form" in rejected
        status, headers, _ = request(url, "POST", campaign_path + "/current-comparisons", {
            "csrf": csrf, "request_id": "http-current", "brief_id": campaign["brief_id"],
        })
        assert status == 303
        path = headers["Location"]
        status, _, page = request(url, path=path)
        assert status == 200
        assert "&lt;script&gt;account&lt;/script&gt;" in page and "<script>account</script>" not in page
        assert "current-kb-caption-comparison-v1" in page
        assert "Actual retrieved support manifest" in page
        assert observation.id in page
        assert "not_assessed" in page and "source_as_of_unknown" in page
        assert "local-rule-preparation" in page
        assert "seed-only" in page
    stack[1].revoke(observation.id)
    with running(ReviewApp(store.db)) as url:
        status, _, page = request(url, path=path)
        assert status == 200 and "Support unavailable or requires review" in page
        assert "example.test" not in page
    assert store.read_campaign(campaign["campaign_id"], HUMAN)["shortlists"] == []


def test_published_caption_rules_apply_exclusions_without_promoting_language_or_pr_to_facts(campaigns):
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_evidence_sets import DATASET

    store, _, knowledge_run = campaigns
    source = store.evidence.read(DATASET, HUMAN)
    claims = store.knowledge.read(knowledge_run, HUMAN)["interpretations"]
    # One exact caption with kana and a literal PR marker provides independent
    # expected source evidence; it does not establish commercial/audience facts.
    pr = next(c for c in claims if c["predicate"] == "literal_marker")
    supported = tuple(c["id"] for c in claims if c["observation_id"] == pr["observation_id"])
    refs = tuple(r for r in IngestedEvidence(store.db).select_run(source["run_id"], HUMAN)
                 if r.observation_id == pr["observation_id"])
    KnowledgePublications(store.db).publish(refs, AUTOMATION, request_id="caption", interpretation_ids=supported)
    brief = replace(BRIEF, known_accounts=(), criteria=(
        Criterion("no-pr", "Exclude PR markers", "literal_marker", pr["value"]["marker"], True, "exclude"),
        Criterion("audience", "Japan audience", "audience_geography", "JP"),
        Criterion("language", "Japanese language", "caption_language", "ja"),
        Criterion("sales", "Sales", "sales", "proven"),
    ))
    campaign = store.start(brief, HUMAN, request_id="caption-campaign")
    view = prepare(store, campaign)
    body = view["candidates"][0]["body"]
    assert body["assessment"] == "excluded_on_required_evidence"
    assert [j["state"] for j in body["judgments"]] == ["not_satisfied_on_evidence", "unknown", "unknown", "unknown"]
    assert {"contracts", "sales_effectiveness", "audience_geography"} <= set(body["unknowns"])
    assert pr["id"] in body["support_manifest"][0]["interpretation_ids"]
    assert view["candidates"][0]["evidence"][0]["source_assertion_id"] == pr["source_assertion_id"]
    # The exact human profile is retained; execution describes the actual current-KB method.
    assert view["execution_profile"]["method_version"] == "current-kb-caption-comparison-v1"
    assert view["execution_profile"]["ranking"] == "unranked"
    from smi_campaigns import Selection
    from smi_campaigns.planning import CampaignPlanning, DecisionNote
    from smi_review import ReviewApp
    from test_review import request, running

    shortlist = store.save_shortlist(view['comparison_id'], (Selection(view['candidates'][0]['candidate_id']),), HUMAN,
                                     confirmed=False, expected_version=0, request_id='caption-draft')
    planning = CampaignPlanning(store.db)
    planning.add_note(campaign['campaign_id'], shortlist['shortlist_id'], DecisionNote('Review PR context'), HUMAN,
                      expected_version=0, request_id='caption-note')
    assert planning.read(campaign['campaign_id'], HUMAN)['notes'][0]['text'] == 'Review PR context'
    with running(ReviewApp(store.db)) as url:
        status, _, page = request(url, path='/comparisons/' + view['comparison_id'])
        assert status == 200 and 'Original captions and provenance' in page
        assert pr['source_assertion_id'] in page


def test_selected_model_profile_is_pinned_and_comparison_never_dispatches_another_model(campaigns):
    import pytest

    from smi_ingestion.evidence import EvidenceError
    from test_criteria_interpretation import configured, interpret

    store, _, transport = configured(campaigns)
    campaign = store.start(replace(BRIEF, original_input="Prefer skincare"), HUMAN, request_id="profile")
    interpretation = interpret(store, campaign)
    view = prepare(store, campaign, interpretation_id=interpretation["interpretation_id"])
    assert view["criteria_interpretation_id"] == interpretation["interpretation_id"]
    assert view["executable_profile"] == interpretation["executable_profile"]
    assert len(transport.calls) == 1
    store.revise_brief(campaign["campaign_id"], replace(BRIEF, original_input="Successor"), HUMAN,
                       expected_version=1, request_id="successor")
    assert prepare(store, campaign, interpretation_id=interpretation["interpretation_id"])["comparison_id"] == view["comparison_id"]
    with pytest.raises(EvidenceError, match="brief_version_conflict"):
        prepare(store, campaign, "stale-new", interpretation_id=interpretation["interpretation_id"])
    other = store.start(BRIEF, HUMAN, request_id="other")
    with pytest.raises(EvidenceError, match="criteria_interpretation_not_executable"):
        prepare(store, other, "foreign", interpretation_id=interpretation["interpretation_id"])
    with pytest.raises(EvidenceError, match="comparison_request_conflict"):
        prepare(store, campaign)
    assert len(transport.calls) == 1


def test_publication_and_withdrawal_cannot_pass_a_comparison_commit_in_flight(stack):
    from concurrent.futures import ThreadPoolExecutor
    from time import monotonic, sleep

    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_publications import ingest_account

    store, campaign = current_campaign(stack)
    _, original = publish_account(stack, "before")
    next_run, _ = ingest_account(stack, native_id="later-account")
    next_support = IngestedEvidence(store.db).select_run(next_run, HUMAN)
    # Test-only DDL pauses the real INSERT after retrieval, without replacing any
    # store operation. SQL below observes lock coordination, never product outcomes.
    gate = 140014
    with store.db.connect() as setup:
        setup.execute("CREATE FUNCTION comparison_commit_gate() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(140014); RETURN NEW; END $$")
        setup.execute("CREATE TRIGGER comparison_commit_gate BEFORE INSERT ON comparison_drafts FOR EACH ROW EXECUTE FUNCTION comparison_commit_gate()")
    with ThreadPoolExecutor(max_workers=3) as executor:
        with store.db.connect() as blocker:
            blocker.execute("SELECT pg_advisory_xact_lock(%s)", (gate,))
            preparing = executor.submit(store.prepare_current_comparison, campaign["campaign_id"], campaign["brief_id"], AUTOMATION, request_id="raced")
            deadline = monotonic() + 10
            while monotonic() < deadline:
                if blocker.execute("SELECT 1 FROM pg_locks WHERE locktype='advisory' AND objid=%s AND NOT granted", (gate,)).fetchone():
                    break
                sleep(.01)
            else:
                raise AssertionError("comparison did not reach commit gate")
            withdrawing = executor.submit(stack[1].revoke, original.id)
            publishing = executor.submit(KnowledgePublications(store.db).publish, next_support, AUTOMATION, request_id="later")
            deadline = monotonic() + 10
            while monotonic() < deadline:
                waits = blocker.execute("SELECT locktype FROM pg_locks WHERE NOT granted AND pid<>pg_backend_pid()").fetchall()
                if any(w['locktype'] == 'advisory' for w in waits if w) and len(waits) >= 3:
                    break
                sleep(.01)
            else:
                raise AssertionError("source/publication writes did not wait for comparison commit")
            assert not withdrawing.done() and not publishing.done()
        prepared = preparing.result(timeout=10)
        withdrawing.result(timeout=10)
        publishing.result(timeout=10)
    view = store.read_comparison(prepared["comparison_id"], HUMAN)
    assert [c["account_key"]["native_id"] for c in view["candidates"]] == ["account-1"]
    assert view["candidates"][0]["body"] is None
    assert [c["account_key"]["native_id"] for c in prepare(store, campaign, "after")["candidates"]] == ["later-account"]


def test_human_draft_and_dependent_note_use_current_kb_policy_without_a_frozen_dataset(stack):
    from datetime import datetime, timezone

    from smi_campaigns import Selection
    from smi_campaigns.planning import CampaignPlanning, DecisionNote
    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import MetricCandidate, NormalizedBatch
    from smi_ingestion.support import IngestedEvidence
    from smi_knowledge import KnowledgePublications
    from test_publications import ingest_account

    store, campaign = current_campaign(stack)
    run_id, observation = ingest_account(stack)
    key = ExternalKey("test", "public", "account", "account-1")
    CanonicalWriter(store.db).apply(observation.id, NormalizedBatch((key,), (), (
        MetricCandidate(key, "test.followers.v1", "followers", 17, "17", "exact", "count", datetime(2026, 10, 1, tzinfo=timezone.utc), "$.followers"),
    )), "metric-only:v2")
    KnowledgePublications(store.db).publish(IngestedEvidence(store.db).select_run(run_id, HUMAN), AUTOMATION, request_id="metric-only")
    view = prepare(store, campaign)
    assert len(view["candidates"]) == 1
    assert view["candidates"][0]["body"]["support_manifest"][0]["assertion_ids"] == []
    shortlist = store.save_shortlist(view["comparison_id"], (Selection(view["candidates"][0]["candidate_id"]),), HUMAN,
                                     confirmed=False, expected_version=0, request_id="human-draft")
    planning = CampaignPlanning(store.db)
    planning.add_note(campaign["campaign_id"], shortlist["shortlist_id"], DecisionNote("Need more audience evidence"), HUMAN,
                      expected_version=0, request_id="note")
    assert planning.read(campaign["campaign_id"], HUMAN)["notes"][0]["text"] == "Need more audience evidence"
    stack[1].revoke(observation.id)
    assert planning.read(campaign["campaign_id"], HUMAN)["notes"][0]["text"] is None


def test_current_policy_and_supersession_overlay_history_without_replacing_support(stack):
    from dataclasses import asdict

    from psycopg.types.json import Jsonb

    from smi_ingestion.canonical import CanonicalWriter
    from smi_ingestion.contracts import FieldCandidate, NormalizedBatch
    from test_publications import ingest_account

    store, campaign = current_campaign(stack)
    _, observation = publish_account(stack, "policy")
    ingest_account(stack, native_id="unpublished-account")
    original = prepare(store, campaign)
    policy = asdict(stack[1].get(observation.id).policy)

    def change_policy(**changes):
        policy.update(changes)
        with store.db.connect() as connection:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(policy), observation.id))

    change_policy(can_process=False)
    assert prepare(store, campaign, "process-denied")["candidates"] == []
    assert store.read_comparison(original["comparison_id"], HUMAN)["candidates"][0]["body"] is not None
    change_policy(can_process=True, can_display=False)
    denied = prepare(store, campaign, "display-denied")
    assert len(denied["candidates"]) == 1 and denied["candidates"][0]["body"] is None
    change_policy(can_display=True, can_retain=False)
    assert store.read_comparison(original["comparison_id"], HUMAN)["candidates"][0]["body"] is None
    change_policy(can_retain=True)
    assert store.read_comparison(original["comparison_id"], HUMAN)["candidates"][0]["body"] is None
    fresh = prepare(store, campaign, "explicit-recovery")
    assert fresh["candidates"][0]["body"] is not None
    key = ExternalKey("test", "public", "account", "account-1")
    CanonicalWriter(store.db).apply(observation.id, NormalizedBatch((key,), (
        FieldCandidate(key, "handle", "observed", "changed-handle", "$.handle"),
    ), ()), "corrected:v2")
    reopened = store.read_comparison(fresh["comparison_id"], HUMAN)
    assert reopened["candidates"][0]["support_state"] == "review_required"
    assert reopened["candidates"][0]["body"] is None
    assert reopened["knowledge_query"]["manifest"] == fresh["knowledge_query"]["manifest"]
    assert prepare(store, campaign, "after-supersession")["candidates"] == []


def test_stale_current_comparison_form_preserves_exact_brief_profile_and_retry_identity(campaigns):
    from smi_review import ReviewApp
    from test_criteria_interpretation import configured, interpret
    from test_review import form, request, running

    store, _, _ = configured(campaigns)
    campaign = store.start(replace(BRIEF, original_input="Prefer skincare"), HUMAN, request_id="stale-form")
    interpreted = interpret(store, campaign)
    path = "/campaigns/" + campaign["campaign_id"]
    action = path + "/current-comparisons"
    with running(ReviewApp(store.db)) as url:
        _, _, page = request(url, path=path)
        fields = form(page, action)
        fields["interpretation_id"] = [interpreted["interpretation_id"]]
        store.revise_brief(campaign["campaign_id"], replace(BRIEF, original_input="Changed needs"), HUMAN,
                           expected_version=1, request_id="revised-form")
        status, _, page = request(url, "POST", action, fields)
        assert status == 409
        retry = form(page, action)
        assert retry["request_id"] == fields["request_id"]
        assert retry["brief_id"] == [campaign["brief_id"]]
        assert retry["interpretation_id"] == [interpreted["interpretation_id"]]
    assert store.read_campaign(campaign["campaign_id"], HUMAN)["comparisons"] == []
