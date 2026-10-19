from __future__ import annotations

import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from smi_campaigns.planning import CampaignPlanning, DecisionNote, MeasurementPlan
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
from smi_ingestion.evidence_sets import ActorContext
from smi_monitoring import InvestigationScope, MonitoringStore
from smi_monitoring import store as monitoring_module
from smi_monitoring.summary import build_summary
from smi_knowledge import Catalog
from smi_review import ReviewApp
from test_campaigns import BRIEF, comparison, save, selection, campaigns as campaigns_fixture
from test_evidence_sets import DATASET, HUMAN
from test_review import chosen_form, form, prepare, request, running


campaigns = campaigns_fixture
ROOT = Path(__file__).parents[1]
SCOPE = InvestigationScope.from_document(json.loads((ROOT / "examples/monitoring/hero-cushion-scope.json").read_text()))
PLAN = MeasurementPlan.from_document(json.loads((ROOT / "examples/campaigns/sales-measurement-plan.json").read_text()))
WORKER = ActorContext("local", "monitoring-worker", "automation")


@pytest.fixture
def monitoring(campaigns):
    store = MonitoringStore(campaigns[0].db)
    store.migrate()
    store.migrate()
    return store, campaigns[2]


def insight(monitoring, scope=SCOPE):
    store, run_id = monitoring
    created = store.start(scope, HUMAN, request_id="investigate")
    prepared = store.prepare_insight(created["investigation_id"], created["scope_id"], run_id, WORKER, expected_version=0, request_id="insight-1")
    return created, prepared, store.read_insight(prepared["insight_id"], HUMAN)


def planning(campaigns):
    created, view = comparison(campaigns)
    shortlist = save(campaigns[0], view)
    return CampaignPlanning(campaigns[0].db), created, view, shortlist


def test_independent_snapshot_counts_exact_support_and_reopen_without_campaign(monitoring):
    store = monitoring[0]
    created, prepared, result = insight(monitoring)
    product = next(f for f in result["findings"] if f["body"]["predicate"] == "product_mention")
    assert product["body"]["post_count"] == 6
    assert len(result["coverage"]["actual_observation_ids"]) == 6
    assert result["coverage"]["baseline"] is None and result["coverage"]["trend_status"] == "not_assessable"
    assert result["review_status"] == "provisional" and result["actor_kind"] == "automation"
    source = store.evidence.read(DATASET, HUMAN)
    captions = {a["assertion_id"]: a["value"] for m in source["members"] for a in m["assertions"] if a["field"] == "caption"}
    for finding in result["findings"]:
        assert finding["evidence"]
        for claim in finding["evidence"]:
            assert claim["span"]["text"] == captions[claim["source_assertion_id"]][claim["span"]["start"]:claim["span"]["end"]]
    with store.db.connect() as connection:
        for table in ("campaigns", "comparison_drafts", "shortlist_revisions"):
            assert connection.execute(f"SELECT count(*) AS count FROM {table}").fetchone()["count"] == 0
    assert MonitoringStore(store.db).read_insight(prepared["insight_id"], HUMAN) == result
    assert store.start(SCOPE, HUMAN, request_id="investigate")["status"] == "duplicate"
    assert store.read_investigation(created["investigation_id"], HUMAN)["insight_version"] == 1


def test_repeated_captures_are_not_additional_posts(monitoring):
    store, run_id = monitoring
    source = store.evidence.read(DATASET, HUMAN, purpose="process")
    knowledge = store.knowledge.read(run_id, HUMAN, purpose="process")
    duplicate = copy.deepcopy(source["members"][0])
    original_id = duplicate["observation_id"]
    duplicate["observation_id"] = str(uuid.uuid4())
    source["members"].append(duplicate)
    knowledge["interpretations"].extend({**c, "observation_id": duplicate["observation_id"], "id": str(uuid.uuid4())}
                                       for c in list(knowledge["interpretations"]) if c["observation_id"] == original_id)
    findings, coverage = build_summary(SCOPE, source, knowledge, store.knowledge.catalog(SCOPE.catalog_id, HUMAN).document)
    assert next(f["body"]["post_count"] for f in findings if f["body"]["predicate"] == "product_mention") == 6
    assert len(coverage["actual_observation_ids"]) == 7


@pytest.mark.parametrize("scope,language", [(replace(SCOPE, publication_from="2040-01-01T00:00:00+00:00"), False),
                                           (replace(SCOPE, caption_language="ja"), True)])
def test_empty_window_and_unresolved_language_do_not_establish_market_absence(monitoring, scope, language):
    _, _, result = insight(monitoring, scope)
    assert result["findings"] == [] and result["coverage"]["actual_observation_ids"] == []
    assert (result["coverage"]["language_constraint"] == "not_assessable") == language
    assert any("No comparable baseline" in limit for limit in result["limitations"])


def test_insight_retries_conflicts_scope_successors_and_actor_separation(monitoring):
    store, run_id = monitoring
    created = store.start(SCOPE, HUMAN, request_id="investigate")
    call = lambda: store.prepare_insight(created["investigation_id"], created["scope_id"], run_id, WORKER, expected_version=0, request_id="insight-1")
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: call(), range(2)))
    assert {r["status"] for r in replies} == {"prepared", "duplicate"}
    assert len({r["insight_id"] for r in replies}) == 1
    old = store.read_insight(replies[0]["insight_id"], HUMAN)
    with pytest.raises(EvidenceError, match="insight_version_conflict"):
        store.prepare_insight(created["investigation_id"], created["scope_id"], run_id, WORKER, expected_version=0, request_id="competing")
    revised = store.revise_scope(created["investigation_id"], replace(SCOPE, question="Successor question"), HUMAN, expected_version=1, request_id="scope-2")
    with pytest.raises(EvidenceError, match="scope_version_conflict"):
        store.prepare_insight(created["investigation_id"], created["scope_id"], run_id, WORKER, expected_version=1, request_id="old-scope")
    store.prepare_insight(created["investigation_id"], revised["scope_id"], run_id, WORKER, expected_version=1, request_id="insight-2")
    assert store.read_insight(replies[0]["insight_id"], HUMAN) == old
    with pytest.raises(EvidenceError, match="human_action_required"):
        store.start(SCOPE, WORKER, request_id="fake-human")
    with pytest.raises(EvidenceError, match="workspace_access_denied"):
        store.list_investigations(ActorContext("foreign", "reader", "human"))


@pytest.mark.parametrize("change,purge", [({"can_display": False}, False), ({"can_retain": False}, True),
                                        ({"revoked": True}, True), ({"expires_at": "2000-01-01T00:00:00+00:00"}, True)])
def test_saved_findings_withhold_and_purge_copies_without_rewriting_counts(monitoring, change, purge):
    store = monitoring[0]
    _, prepared, original = insight(monitoring)
    product = next(f for f in original["findings"] if f["body"]["predicate"] == "product_mention")
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], **change}), member["observation_id"]))
    hidden = store.read_insight(prepared["insight_id"], HUMAN)
    affected = next(f for f in hidden["findings"] if f["finding_id"] == product["finding_id"])
    assert affected["body"] is None and not affected["evidence"]
    assert hidden["coverage"]["actual_observation_ids"] is None and hidden["prepared_at"] == original["prepared_at"]
    with store.db.connect() as connection:
        stored = connection.execute("SELECT coverage FROM insight_revisions WHERE id=%s", (prepared["insight_id"],)).fetchone()["coverage"]
        assert stored["actual_observation_ids"] == original["coverage"]["actual_observation_ids"]
        body = connection.execute("SELECT body FROM insight_findings WHERE id=%s", (product["finding_id"],)).fetchone()["body"]
        assert (body is None) == purge
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(member["policy"]), member["observation_id"]))
    restored = store.read_insight(prepared["insight_id"], HUMAN)
    assert (next(f for f in restored["findings"] if f["finding_id"] == product["finding_id"])["body"] is None) == purge


def test_support_withdrawal_before_insight_commit_rolls_back(monitoring, monkeypatch):
    store, run_id = monitoring
    created = store.start(SCOPE, HUMAN, request_id="investigate")
    build = monitoring_module.build_summary
    def withdraw(*args):
        result = build(*args)
        member = args[1]["members"][0]
        with store.db.connect() as connection:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], "can_process": False}), member["observation_id"]))
        return result
    monkeypatch.setattr(monitoring_module, "build_summary", withdraw)
    with pytest.raises(EvidenceError, match="insight_support_changed"):
        store.prepare_insight(created["investigation_id"], created["scope_id"], run_id, WORKER, expected_version=0, request_id="race")
    assert store.read_investigation(created["investigation_id"], HUMAN)["insight_version"] == 0


def test_corrected_derivation_requires_review_without_substituting_new_caption(monitoring):
    store, run_id = monitoring
    created, prepared, original = insight(monitoring)
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    caption = next(a for a in member["assertions"] if a["field"] == "caption")
    key = ExternalKey(caption["platform"], caption["namespace"], caption["kind"], caption["native_id"])
    CanonicalWriter(store.db).apply(member["observation_id"], NormalizedBatch((key,),
        (FieldCandidate(key, "caption", "removed", None, "$.caption"),), ()), "correction:v2")
    hidden = store.read_insight(prepared["insight_id"], HUMAN)
    product = next(f for f in original["findings"] if f["body"]["predicate"] == "product_mention")
    assert next(f for f in hidden["findings"] if f["finding_id"] == product["finding_id"])["support_state"] == "review_required"
    assert hidden["coverage"]["actual_observation_ids"] is None
    refreshed = store.prepare_insight(created["investigation_id"], created["scope_id"], run_id, WORKER, expected_version=1, request_id="current-only")
    fresh = store.read_insight(refreshed["insight_id"], HUMAN)
    assert next(f["body"]["post_count"] for f in fresh["findings"] if f["body"]["predicate"] == "product_mention") == 5
    assert store.read_insight(prepared["insight_id"], HUMAN)["coverage"]["actual_observation_ids"] is None


def test_proposed_measurement_missing_sources_and_human_notes_reopen_exactly(campaigns):
    store, created, view, shortlist = planning(campaigns)
    plan = store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], PLAN, HUMAN, expected_version=0, request_id="plan-1")
    chosen = selection(view)
    note = store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("NOTE_SENTINEL", chosen.support_ids), HUMAN, expected_version=0, request_id="note-1")
    result = CampaignPlanning(store.db).read(created["campaign_id"], HUMAN)
    assert result["plans"][0]["plan_id"] == plan["plan_id"] and result["plans"][0]["status"] == "proposed"
    assert result["plans"][0]["outcomes"] is None and result["plans"][0]["outcome_access"] == "not_verified"
    assert result["plans"][0]["document"]["baseline"] is None and result["plans"][0]["document"]["source_owner"] is None
    assert result["notes"][0]["note_id"] == note["note_id"] and result["notes"][0]["text"] == "NOTE_SENTINEL"
    assert result["notes"][0]["basis"] == "human_supplied" and result["notes"][0]["recorded_by"] == HUMAN.actor_id
    assert CampaignPlanning(store.db).read(created["campaign_id"], HUMAN) == result


@pytest.mark.parametrize("field", ["revenue", "sales_lift", "actor_id"])
def test_measurement_plan_rejects_outcome_and_actor_fields(field):
    with pytest.raises(EvidenceError, match="invalid_measurement_plan"):
        MeasurementPlan.from_document({**PLAN.document(), field: 42})


def test_planning_concurrency_conflicts_invalid_refs_and_human_only_writes(campaigns):
    store, created, view, shortlist = planning(campaigns)
    call = lambda: store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], PLAN, HUMAN, expected_version=0, request_id="plan-1")
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: call(), range(2)))
    assert {r["status"] for r in replies} == {"proposed", "duplicate"}
    assert len({r["plan_id"] for r in replies}) == 1
    with pytest.raises(EvidenceError, match="measurement_plan_version_conflict"):
        store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], PLAN, HUMAN, expected_version=0, request_id="plan-2")
    with pytest.raises(EvidenceError, match="planning_request_conflict"):
        store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], replace(PLAN, objective="Different"), HUMAN, expected_version=0, request_id="plan-1")
    with pytest.raises(EvidenceError, match="human_action_required"):
        store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("Fake confirmation"), WORKER, expected_version=0, request_id="fake")
    with pytest.raises(EvidenceError, match="invalid_decision_note_support"):
        store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("Unsupported", (str(uuid.uuid4()),)), HUMAN, expected_version=0, request_id="fake-support")
    other = campaigns[0].start(BRIEF, HUMAN, request_id="other-campaign")
    with pytest.raises(EvidenceError, match="planning_reference_mismatch"):
        store.add_note(other["campaign_id"], shortlist["shortlist_id"], DecisionNote("Unrelated"), HUMAN, expected_version=0, request_id="cross-campaign")
    assert store.read(created["campaign_id"], HUMAN)["note_version"] == 0


@pytest.mark.parametrize("change,purge", [({"can_display": False}, False), ({"can_retain": False}, True), ({"revoked": True}, True)])
def test_note_text_inherits_all_selected_dependencies_even_without_explicit_citations(campaigns, change, purge):
    store, created, _, shortlist = planning(campaigns)
    note = store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("NOTE_SENTINEL"), HUMAN, expected_version=0, request_id="note-1")
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], **change}), member["observation_id"]))
    result = store.read(created["campaign_id"], HUMAN)
    assert result["notes"][0]["text"] is None and "NOTE_SENTINEL" not in json.dumps(result)
    assert result["notes"][0]["recorded_by"] == HUMAN.actor_id
    with store.db.connect() as connection:
        assert (connection.execute("SELECT text FROM decision_note_revisions WHERE id=%s", (note["note_id"],)).fetchone()["text"] is None) == purge
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(member["policy"]), member["observation_id"]))
    assert (store.read(created["campaign_id"], HUMAN)["notes"][0]["text"] is None) == purge
    assert store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("NOTE_SENTINEL"), HUMAN, expected_version=0, request_id="note-1")["status"] == "duplicate"


def test_successor_plans_and_notes_preserve_history_and_reject_old_briefs(campaigns):
    store, created, _, shortlist = planning(campaigns)
    first = store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], PLAN, HUMAN, expected_version=0, request_id="plan-1")
    store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("First feedback"), HUMAN, expected_version=0, request_id="note-1")
    before = store.read(created["campaign_id"], HUMAN)
    store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("Successor feedback"), HUMAN, expected_version=1, request_id="note-2")
    with pytest.raises(EvidenceError, match="decision_note_version_conflict"):
        store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("Competing"), HUMAN, expected_version=1, request_id="note-3")
    campaigns[0].revise_brief(created["campaign_id"], replace(BRIEF, objective="New question"), HUMAN, expected_version=1, request_id="new-brief")
    assert store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], PLAN, HUMAN, expected_version=0, request_id="plan-1")["plan_id"] == first["plan_id"]
    with pytest.raises(EvidenceError, match="brief_version_conflict"):
        store.save_plan(created["campaign_id"], created["brief_id"], shortlist["shortlist_id"], PLAN, HUMAN, expected_version=1, request_id="stale-plan")
    after = store.read(created["campaign_id"], HUMAN)
    assert after["plans"] == before["plans"] and after["notes"][0] == before["notes"][0]


def test_denied_processing_blocks_new_notes_without_hiding_permitted_existing_display(campaigns):
    store, created, _, shortlist = planning(campaigns)
    store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("Permitted display"), HUMAN, expected_version=0, request_id="note-1")
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], "can_process": False}), member["observation_id"]))
    assert store.read(created["campaign_id"], HUMAN)["notes"][0]["text"] == "Permitted display"
    with pytest.raises(EvidenceError, match="decision_note_support_unavailable"):
        store.add_note(created["campaign_id"], shortlist["shortlist_id"], DecisionNote("New processing"), HUMAN, expected_version=1, request_id="note-2")


def test_other_category_market_uses_same_monitoring_campaign_and_plan_objects(monitoring, campaigns):
    store = monitoring[0]
    catalog = Catalog.from_document({"catalog_id": "camping-de-v1", "version": "v1",
        "brands": [{"id": "stove-brand", "name": "Stove Brand", "aliases": ["Stove Brand"]}],
        "products": [{"id": "camp-stove", "brand_id": "stove-brand", "name": "Camp Stove", "specificity": "family", "aliases": ["Camp Stove"]}],
        "topics": [{"id": "fuel", "name": "Fuel wording", "aliases": ["fuel"]}]})
    store.knowledge.register_catalog(catalog, HUMAN)
    scope = replace(SCOPE, catalog_id="camping-de-v1", product_ids=("camp-stove",), market_context="DE", question="Camping stove mentions in this dataset?")
    created = store.start(scope, HUMAN, request_id="camping-investigation")
    run = store.knowledge.prepare(DATASET, scope.catalog_id, WORKER)
    answer = store.prepare_insight(created["investigation_id"], created["scope_id"], run["run_id"], WORKER, expected_version=0, request_id="camping-insight")
    assert store.read_insight(answer["insight_id"], HUMAN)["findings"] == []
    brief = replace(BRIEF, catalog_id="camping-de-v1", brand_id="stove-brand", product_ids=("camp-stove",), target_market="DE", known_accounts=(),
                    criteria=(replace(BRIEF.criteria[0], value="camp-stove"),))
    campaign = campaigns[0].start(brief, HUMAN, request_id="camping-campaign")
    comparison = campaigns[0].prepare_comparison(campaign["campaign_id"], campaign["brief_id"], run["run_id"], WORKER, request_id="camping-comparison")
    shortlist = campaigns[0].save_shortlist(comparison["comparison_id"], (), HUMAN, confirmed=True, expected_version=0, request_id="defer-camping")
    plans = CampaignPlanning(store.db)
    plans.save_plan(campaign["campaign_id"], campaign["brief_id"], shortlist["shortlist_id"], replace(PLAN, product_ids=("camp-stove",)), HUMAN,
                    expected_version=0, request_id="camping-plan")
    assert plans.read(campaign["campaign_id"], HUMAN)["plans"][0]["document"]["product_ids"] == ["camp-stove"]


def test_independent_investigation_and_campaign_planning_http_paths(monitoring):
    app = ReviewApp(monitoring[0].db, "marketer-reviewer")
    with running(app) as url:
        _, _, html = request(url, path="/investigations/new")
        fields = form(html, "/investigations")
        fields.update(question=[SCOPE.question], market_context=["JP"], product_ids=["aprilskin-hero-cushion"])
        status, headers, html = request(url, "POST", "/investigations", fields)
        assert status == 303, html
        investigation_path = headers["Location"]
        _, _, html = request(url, path=investigation_path)
        status, headers, html = request(url, "POST", investigation_path + "/insights", form(html, investigation_path + "/insights"))
        assert status == 303, html
        insight_path = headers["Location"]
        _, _, html = request(url, path=insight_path)
        assert "6 distinct selected posts" in html and "Original captions and provenance" in html
        assert "No comparable baseline" in html and not app.campaigns.list_campaigns(app.actor)
        with running(ReviewApp(app.campaigns.db, "marketer-reviewer")) as restarted:
            assert request(restarted, path=insight_path)[2] == html
        campaign_path, comparison_path = prepare((app, url))
        choices, _ = chosen_form((app, url), comparison_path)
        assert request(url, "POST", comparison_path + "/shortlists", choices)[0] == 303
        planning_path = campaign_path + "/planning"
        _, _, html = request(url, path=planning_path)
        plan_fields = form(html, campaign_path + "/plans")
        plan_fields["outcome_definition"] = [PLAN.outcome_definition]
        status, _, html = request(url, "POST", campaign_path + "/plans", plan_fields)
        assert status == 303, html
        _, _, html = request(url, path=planning_path)
        assert "No measured results" in html and "not verified" in html
        note_fields = form(html, campaign_path + "/notes")
        note_fields["text"] = ["HUMAN_HTTP_NOTE"]
        assert request(url, "POST", campaign_path + "/notes", note_fields)[0] == 303
        assert "HUMAN_HTTP_NOTE" in request(url, path=planning_path)[2]


def test_note_error_page_does_not_echo_withdrawn_source_text(monitoring):
    app = ReviewApp(monitoring[0].db, "marketer-reviewer")
    with running(app) as url:
        campaign_path, comparison_path = prepare((app, url))
        choices, _ = chosen_form((app, url), comparison_path)
        assert request(url, "POST", comparison_path + "/shortlists", choices)[0] == 303
        planning_path = campaign_path + "/planning"
        _, _, html = request(url, path=planning_path)
        fields = form(html, campaign_path + "/notes")
        fields["text"] = ["HTTP_SOURCE_COPY_SENTINEL"]
        assert request(url, "POST", campaign_path + "/notes", fields)[0] == 303
        member = app.evidence.read(DATASET, app.actor)["members"][0]
        with app.campaigns.db.connect() as connection:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], "revoked": True}), member["observation_id"]))
        fields.update(expected_version=["1"], request_id=["new-withdrawn-note"])
        status, _, html = request(url, "POST", campaign_path + "/notes", fields)
        assert status == 422 and "HTTP_SOURCE_COPY_SENTINEL" not in html
        assert "marketer-reviewer" in html and "decision_note_support_unavailable" in html
