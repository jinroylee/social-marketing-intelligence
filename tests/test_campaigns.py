from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from smi_campaigns import Brief, CampaignStore, Criterion, Selection
from smi_campaigns import store as campaign_store_module
from smi_ingestion.canonical import CanonicalWriter
from smi_ingestion.contracts import ExternalKey, FieldCandidate, NormalizedBatch
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, SnapshotImporter
from smi_knowledge import Catalog, KnowledgeStore
from test_cli import _cli
from test_evidence_sets import DATASET, HUMAN, MANIFEST, POLICY


ROOT = Path(__file__).parents[1]
CATALOG_PATH = ROOT / "examples/catalogs/beauty-v1.json"
BRIEF_PATH = ROOT / "examples/campaigns/hero-cushion-brief.json"
BRIEF = Brief.from_document(json.loads(BRIEF_PATH.read_text()))
AUTOMATION = ActorContext("local", "comparison-worker", "automation")


@pytest.fixture
def campaigns(stack):
    db, evidence, _, _ = stack
    knowledge = KnowledgeStore(db)
    knowledge.migrate()
    SnapshotImporter(evidence).import_snapshot(MANIFEST, HUMAN, POLICY)
    knowledge.register_catalog(Catalog.load(CATALOG_PATH), HUMAN)
    run = knowledge.prepare(DATASET, BRIEF.catalog_id, HUMAN)
    store = CampaignStore(db)
    store.migrate()
    store.migrate()
    return store, evidence, run["run_id"]


def comparison(campaigns, brief=BRIEF):
    store, _, knowledge_run = campaigns
    created = store.start(brief, HUMAN, request_id="campaign-start")
    prepared = store.prepare_comparison(created["campaign_id"], created["brief_id"], knowledge_run,
                                        AUTOMATION, request_id="comparison-1")
    return created, store.read_comparison(prepared["comparison_id"], HUMAN)


def selection(view, *, candidate=None, reason="Source-supported cushion content merits further investigation."):
    if candidate is None:
        candidate = next(c for c in view["candidates"] if c["body"] and any(j["state"] == "satisfied" and j["criterion_id"] == "product-fit"
                                                                        for j in c["body"]["judgments"]))
    supports = next(j["support_ids"] for j in candidate["body"]["judgments"] if j["criterion_id"] == "product-fit")
    return Selection(candidate["candidate_id"], reason, tuple(supports), tuple(candidate["body"]["unknowns"]))


def save(store, view, choices=None, **overrides):
    return store.save_shortlist(view["comparison_id"], choices if choices is not None else (selection(view),), HUMAN,
                               **{"confirmed": True, "expected_version": 0, "request_id": "confirm-1", **overrides})


def test_campaign_path_reopens_exact_draft_and_human_confirmation_after_restart(campaigns):
    store, _, _ = campaigns
    created, view = comparison(campaigns)
    assert view["method"] == "rule_based"
    assert view["actor_kind"] == "automation"
    assert len(view["candidates"]) == 17
    assert store.read_campaign(created["campaign_id"], HUMAN)["shortlist_version"] == 0
    assert view["candidates"][0]["origin"] == "both"
    assert view["candidates"][0]["account_key"]["native_id"] == "6819904612390634498"
    chosen = selection(view)
    draft = save(store, view, (chosen,), confirmed=False, request_id="save-draft")
    before = store.read_shortlist(draft["shortlist_id"], HUMAN)
    assert before["status"] == "draft" and before["version"] == 1
    confirmed = save(store, view, (chosen,), expected_version=1)
    reopened = CampaignStore(store.db).read_shortlist(confirmed["shortlist_id"], HUMAN)
    assert reopened["status"] == "confirmed" and reopened["version"] == 2
    assert reopened["recorded_by"] == HUMAN.actor_id
    assert reopened["brief_id"] == created["brief_id"]
    assert reopened["selected"][0]["reason_basis"] == "human_supplied"
    assert reopened["selected"][0]["support_ids"] == list(chosen.support_ids)
    assert reopened["selected"][0]["evidence"]
    assert CampaignStore(store.db).read_shortlist(confirmed["shortlist_id"], HUMAN) == reopened
    assert store.read_shortlist(draft["shortlist_id"], HUMAN)["status"] == "draft"
    assert before["selected"] == store.read_shortlist(draft["shortlist_id"], HUMAN)["selected"]


def test_campaign_and_comparison_requests_return_original_or_reject_changed_payload(campaigns):
    store, _, knowledge_run = campaigns
    created, view = comparison(campaigns)
    retried = store.start(BRIEF, HUMAN, request_id="campaign-start")
    assert retried == {**created, "status": "duplicate"}
    with pytest.raises(EvidenceError, match="campaign_request_conflict"):
        store.start(replace(BRIEF, objective="Different campaign"), HUMAN, request_id="campaign-start")
    retried_comparison = store.prepare_comparison(created["campaign_id"], created["brief_id"], knowledge_run,
                                                  AUTOMATION, request_id="comparison-1")
    assert retried_comparison == {"status": "duplicate", "comparison_id": view["comparison_id"]}
    revised = store.revise_brief(created["campaign_id"], replace(BRIEF, objective="Successor question"), HUMAN,
                                 expected_version=1, request_id="brief-2")
    with pytest.raises(EvidenceError, match="comparison_request_conflict"):
        store.prepare_comparison(created["campaign_id"], revised["brief_id"], knowledge_run,
                                 AUTOMATION, request_id="comparison-1")


def test_support_withdrawal_between_preparation_and_commit_leaves_no_draft(campaigns, monkeypatch):
    store, _, knowledge_run = campaigns
    created = store.start(BRIEF, HUMAN, request_id="campaign-start")
    build = campaign_store_module.build_comparison

    def withdraw_after_preparation(brief, source, knowledge):
        candidates, coverage = build(brief, source, knowledge)
        member = source["members"][0]
        with store.db.connect() as connection:
            connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s",
                               (Jsonb({**member["policy"], "can_retain": False}), member["observation_id"]))
        return candidates, coverage

    monkeypatch.setattr(campaign_store_module, "build_comparison", withdraw_after_preparation)
    with pytest.raises(EvidenceError, match="comparison_support_changed"):
        store.prepare_comparison(created["campaign_id"], created["brief_id"], knowledge_run,
                                 AUTOMATION, request_id="withdrawn-before-commit")
    with store.db.connect() as connection:
        assert connection.execute("SELECT count(*) AS count FROM comparison_drafts").fetchone()["count"] == 0
        assert connection.execute("SELECT count(*) AS count FROM comparison_candidates").fetchone()["count"] == 0


@pytest.mark.parametrize("field", ["brand_id", "objective", "target_market", "platforms", "criteria"])
def test_missing_brief_elements_fail_with_field_context(campaigns, field):
    document = BRIEF.document()
    document.pop(field)
    with pytest.raises(EvidenceError, match=f"invalid_brief.{field}"):
        campaigns[0].start(Brief.from_document(document), HUMAN, request_id="invalid")


def test_automation_can_prepare_but_cannot_start_revise_or_save_human_decisions(campaigns):
    store, _, _ = campaigns
    created, view = comparison(campaigns)
    with pytest.raises(EvidenceError, match="human_action_required"):
        store.start(BRIEF, AUTOMATION, request_id="forged-start")
    with pytest.raises(EvidenceError, match="human_action_required"):
        store.revise_brief(created["campaign_id"], BRIEF, AUTOMATION, expected_version=1, request_id="forged-brief")
    for confirmed in (False, True):
        with pytest.raises(EvidenceError, match="human_action_required"):
            store.save_shortlist(view["comparison_id"], (selection(view),), AUTOMATION,
                                 confirmed=confirmed, expected_version=0, request_id="forged-confirm")
    with pytest.raises(EvidenceError, match="workspace_access_denied"):
        store.read_campaign(created["campaign_id"], ActorContext("foreign", "user", "human"))


def test_known_absent_and_cross_namespace_accounts_stay_unverified(campaigns):
    extra = ExternalKey("tiktok", "web:public", "account", "9999999999999999999")
    other_namespace = replace(BRIEF.known_accounts[0], namespace="tiktok:public")
    _, view = comparison(campaigns, replace(BRIEF, known_accounts=BRIEF.known_accounts + (extra, other_namespace)))
    assert len(view["candidates"]) == 19
    missing = [c for c in view["candidates"] if c["origin"] == "marketer_known"]
    assert len(missing) == 2
    assert all(c["account_id"] is None and not c["evidence"] for c in missing)
    assert all(j["state"] == "unknown" for c in missing for j in c["body"]["judgments"])
    with pytest.raises(EvidenceError, match="selection_requires_relevance_support"):
        save(campaigns[0], view, (selection(view, candidate=missing[0]),))


def test_generic_product_and_caption_language_never_become_sales_or_audience_evidence(campaigns):
    _, view = comparison(campaigns)
    states = [j for c in view["candidates"] for j in c["body"]["judgments"]]
    assert all(j["state"] == "unknown" for j in states if j["criterion_id"] == "audience-fit")
    assert all("sales_effectiveness" in c["body"]["unknowns"] for c in view["candidates"])
    generic = next(c for c in view["candidates"] if c["body"]["judgments"][0]["state"] == "unknown")
    assert not generic["body"]["judgments"][0]["support_ids"]
    require_language = Criterion("language", "Japanese language", "caption_language", "ja")
    store, _, _ = campaigns
    created = store.start(replace(BRIEF, criteria=BRIEF.criteria + (require_language,)), HUMAN, request_id="language-campaign")
    prepared = store.prepare_comparison(created["campaign_id"], created["brief_id"], campaigns[2], AUTOMATION, request_id="language-comparison")
    compared = store.read_comparison(prepared["comparison_id"], HUMAN)
    assert all(c["body"]["judgments"][-1]["state"] == "unknown" for c in compared["candidates"])


def test_publication_window_returns_empty_scope_and_no_invented_discovery(campaigns):
    _, view = comparison(campaigns, replace(BRIEF, publication_from="2040-01-01T00:00:00+00:00", known_accounts=()))
    assert view["candidates"] == [] and view["coverage"]["actual_observation_ids"] == []
    result = save(campaigns[0], view, ())
    assert campaigns[0].read_shortlist(result["shortlist_id"], HUMAN)["selected"] == []


@pytest.mark.parametrize("mutation,code", [
    (lambda s: replace(s, reason=None), "selection_reason_or_support_unavailable"),
    (lambda s: replace(s, support_ids=()), "selection_requires_relevance_support"),
    (lambda s: replace(s, support_ids=("00000000-0000-0000-0000-000000000000",)), "invalid_selection_support"),
    (lambda s: replace(s, acknowledged_unknowns=()), "selection_unknowns_not_acknowledged"),
    (lambda s: replace(s, acknowledged_unknowns=s.acknowledged_unknowns + ("undeclared-free-text",)), "invalid_selection_unknowns"),
    (lambda s: replace(s, candidate_id="00000000-0000-0000-0000-000000000000"), "selection_not_in_comparison"),
])
def test_confirmation_rejects_missing_or_fabricated_basis(campaigns, mutation, code):
    _, view = comparison(campaigns)
    with pytest.raises(EvidenceError, match=code):
        save(campaigns[0], view, (mutation(selection(view)),))
    assert campaigns[0].read_campaign(view["campaign_id"], HUMAN)["shortlist_version"] == 0


def test_required_exclusions_and_unknown_defer_rules_are_enforced(campaigns):
    for suffix, criterion in (("exclude-pr", Criterion("no-pr", "Exclude literal PR markers", "literal_marker", "pr_marker", operator="exclude")),
                              ("defer-fee", Criterion("fee", "Fee required before selection", "fee", unknown_handling="defer"))):
        store = campaigns[0]
        brief = replace(BRIEF, criteria=BRIEF.criteria + (criterion,))
        created = store.start(brief, HUMAN, request_id=suffix)
        prepared = store.prepare_comparison(created["campaign_id"], created["brief_id"], campaigns[2], AUTOMATION, request_id="compare")
        view = store.read_comparison(prepared["comparison_id"], HUMAN)
        chosen = selection(view, candidate=view["candidates"][0])
        with pytest.raises(EvidenceError, match="selection_requirement_not_met"):
            save(store, view, (chosen,))


def test_concurrent_retries_and_conflicting_saves_are_transactional(campaigns):
    store = campaigns[0]
    _, view = comparison(campaigns)
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: save(store, view), range(2)))
    assert {r["status"] for r in replies} == {"confirmed", "duplicate"}
    assert len({r["shortlist_id"] for r in replies}) == 1
    with pytest.raises(EvidenceError, match="shortlist_request_conflict"):
        save(store, view, (selection(view, reason="Different body under the same retry ID"),))
    with pytest.raises(EvidenceError, match="shortlist_version_conflict"):
        save(store, view, request_id="competing-save")
    old = store.read_shortlist(replies[0]["shortlist_id"], HUMAN)
    new = save(store, view, (), request_id="defer-all", expected_version=1)
    assert store.read_shortlist(new["shortlist_id"], HUMAN)["selected"] == []
    assert store.read_shortlist(old["shortlist_id"], HUMAN)["selected"] == old["selected"]


def test_brief_revisions_invalidate_confirmation_without_mutating_history(campaigns):
    store = campaigns[0]
    created, view = comparison(campaigns)
    first = save(store, view)
    old = store.read_shortlist(first["shortlist_id"], HUMAN)
    changed = replace(BRIEF, objective="Explore a successor campaign question")
    revised = store.revise_brief(created["campaign_id"], changed, HUMAN, expected_version=1, request_id="brief-edit")
    assert revised["brief_version"] == 2
    assert store.revise_brief(created["campaign_id"], changed, HUMAN, expected_version=1, request_id="brief-edit")["status"] == "duplicate"
    with pytest.raises(EvidenceError, match="brief_version_conflict"):
        save(store, view, request_id="stale-confirm", expected_version=1)
    assert store.read_shortlist(first["shortlist_id"], HUMAN) == old
    latest = store.prepare_comparison(created["campaign_id"], revised["brief_id"], campaigns[2], AUTOMATION, request_id="new-comparison")
    refreshed = store.read_comparison(latest["comparison_id"], HUMAN)
    second = save(store, refreshed, request_id="successor", expected_version=1)
    assert store.read_shortlist(second["shortlist_id"], HUMAN)["brief_id"] == revised["brief_id"]


@pytest.mark.parametrize("change,purge", [({"can_display": False}, False), ({"can_retain": False}, True),
                                          ({"revoked": True}, True), ({"expires_at": "2000-01-01T00:00:00+00:00"}, True)])
def test_policy_changes_redact_saved_reasons_and_preserve_selected_metadata(campaigns, change, purge):
    store = campaigns[0]
    _, view = comparison(campaigns)
    chosen = selection(view, reason="SOURCE_DERIVED_REASON_SENTINEL")
    saved = save(store, view, (chosen,))
    original = store.read_shortlist(saved["shortlist_id"], HUMAN)
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], **change}), member["observation_id"]))
    hidden = store.read_shortlist(saved["shortlist_id"], HUMAN)
    assert "SOURCE_DERIVED_REASON_SENTINEL" not in json.dumps(hidden)
    assert hidden["review_required"] is True
    assert hidden["selected"][0]["reason"] is None and hidden["selected"][0]["evidence"] == []
    assert hidden["recorded_by"] == original["recorded_by"] and hidden["recorded_at"] == original["recorded_at"]
    assert hidden["selected"][0]["account_key"] == original["selected"][0]["account_key"]
    with store.db.connect() as connection:
        row = connection.execute("SELECT s.reason,s.reason_withdrawn,c.body FROM shortlist_selections s "
                                 "JOIN comparison_candidates c ON c.id=s.candidate_id WHERE s.revision_id=%s", (saved["shortlist_id"],)).fetchone()
    assert (row["reason"] is None and row["body"] is None and row["reason_withdrawn"]) == purge
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb(member["policy"]), member["observation_id"]))
    restored = store.read_shortlist(saved["shortlist_id"], HUMAN)
    assert (restored["selected"][0]["reason"] is None) == purge
    if purge:
        assert "SOURCE_DERIVED_REASON_SENTINEL" not in json.dumps(restored)
        assert save(store, view, (chosen,))["status"] == "duplicate"
        assert store.read_shortlist(saved["shortlist_id"], HUMAN)["selected"] == restored["selected"]


def test_denied_processing_prevents_confirmation_and_new_evidence_use(campaigns):
    store = campaigns[0]
    created, view = comparison(campaigns)
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], "can_process": False}), member["observation_id"]))
    with pytest.raises(EvidenceError, match="selection_support_not_permitted"):
        save(store, view)
    refreshed = store.prepare_comparison(created["campaign_id"], created["brief_id"], campaigns[2], AUTOMATION, request_id="new-after-denial")
    fresh = store.read_comparison(refreshed["comparison_id"], HUMAN)
    assert member["observation_id"] not in fresh["coverage"]["actual_observation_ids"]
    known = fresh["candidates"][0]
    assert known["origin"] == "marketer_known" and not known["evidence"]


def test_corrected_source_requires_review_and_cannot_confirm_stale_interpretations(campaigns):
    store = campaigns[0]
    _, view = comparison(campaigns)
    saved = save(store, view)
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    caption = next(a for a in member["assertions"] if a["field"] == "caption")
    key = ExternalKey(caption["platform"], caption["namespace"], caption["kind"], caption["native_id"])
    CanonicalWriter(store.db).apply(member["observation_id"], NormalizedBatch((key,),
        (FieldCandidate(key, "caption", "removed", None, "$.caption"),), ()), "correction:v2")
    result = store.read_shortlist(saved["shortlist_id"], HUMAN)
    assert result["selected"][0]["reason_state"] == "review_required"
    with pytest.raises(EvidenceError):
        save(store, view, expected_version=1, request_id="after-correction")


def test_cli_campaign_comparison_confirmation_and_reopen_in_separate_process(campaigns, tmp_path):
    store, evidence, knowledge_run = campaigns
    started = _cli(store.db, evidence.root, "start-campaign", str(BRIEF_PATH), "--request-id", "cli-start")
    assert started.returncode == 0, started.stdout + started.stderr
    campaign = json.loads(started.stdout)
    prepared = _cli(store.db, evidence.root, "prepare-comparison", campaign["campaign_id"], campaign["brief_id"], knowledge_run,
                    "--request-id", "cli-compare")
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    comparison_id = json.loads(prepared.stdout)["comparison_id"]
    view = store.read_comparison(comparison_id, HUMAN)
    chosen = selection(view)
    path = tmp_path / "selections.json"
    path.write_text(json.dumps([{"candidate_id": chosen.candidate_id, "reason": chosen.reason,
                                "support_ids": chosen.support_ids, "acknowledged_unknowns": chosen.acknowledged_unknowns}]))
    confirmed = _cli(store.db, evidence.root, "save-shortlist", comparison_id, str(path), "--confirm", "--expected-version", "0",
                     "--request-id", "cli-confirm")
    assert confirmed.returncode == 0, confirmed.stdout + confirmed.stderr
    shortlist_id = json.loads(confirmed.stdout)["shortlist_id"]
    reopened = _cli(store.db, evidence.root, "inspect-shortlist", shortlist_id)
    assert reopened.returncode == 0 and json.loads(reopened.stdout)["status"] == "confirmed"


def test_structured_profile_reopens_exact_human_input_and_revision_after_restart(campaigns):
    store = campaigns[0]
    original = "Find Japan campaign partners; fees and availability need checking."
    brief = replace(BRIEF, original_input=original, criteria=(
        Criterion("mention", "Product relevance", "product_mention", "hero-cushion"),
        Criterion("audience", "Japan audience", "audience_geography", "JP", unknown_handling="defer"),
        Criterion("fees", "Fee preference", "fee", "within budget", required=False),
        Criterion("exclude", "Avoid PR marker", "literal_marker", "pr_marker", operator="exclude"),
    ))
    created = store.start(brief, HUMAN, request_id="structured-start")
    reopened = CampaignStore(store.db).read_campaign(created["campaign_id"], HUMAN)["briefs"][0]
    assert reopened["document"]["original_input"] == original
    profile = reopened["executable_profile"]
    assert profile["brief_id"] == created["brief_id"]
    assert profile["brief_version"] == 1
    assert profile["basis"] == "human_structured_input"
    assert profile["criteria_profile_version"] == "structured-caption-criteria-v1"
    assert [(c["id"], c["importance"], c["operator"], c["unknown_handling"]) for c in profile["criteria"]] == [
        ("mention", "requirement", "include", "acknowledge"),
        ("audience", "requirement", "include", "defer"),
        ("fees", "preference", "include", "acknowledge"),
        ("exclude", "requirement", "exclude", "acknowledge"),
    ]
    assert profile["ranking_profile"] == {"version": "unranked-caption-comparison-v1", "status": "unranked",
                                          "ordering": "marketer_known_then_dataset_encounter_order"}
    assert profile["coverage_profile"] == {"version": "fixed-selected-observations-v1", "status": "descriptive_only",
                                           "scope": "fixed_selected_observations", "sufficiency_assessment": "not_implemented"}
    assert profile["baseline_unknowns"] == ["audience_geography", "fees", "availability", "sales_effectiveness", "recent_post_history"]
    assert reopened["recorded_by"] == HUMAN.actor_id
    assert store.start(brief, HUMAN, request_id="structured-start")["brief_id"] == created["brief_id"]


def test_profile_successors_keep_unknown_needs_and_retry_identity(campaigns):
    store, _, knowledge_run = campaigns
    brief = replace(BRIEF, original_input="Japan audience and agreed fees, availability and sales are needs, not facts.",
                    criteria=tuple(Criterion(kind, kind, kind, "desired", unknown_handling="defer")
                                   for kind in ("audience_geography", "fee", "availability", "sales")))
    created = store.start(brief, HUMAN, request_id="profile-start")
    before = store.read_campaign(created["campaign_id"], HUMAN)["briefs"][0]
    prepared = store.prepare_comparison(created["campaign_id"], created["brief_id"], knowledge_run, AUTOMATION, request_id="unknown-needs")
    for candidate in store.read_comparison(prepared["comparison_id"], HUMAN)["candidates"]:
        assert [(j["criterion_id"], j["state"], j["support_ids"]) for j in candidate["body"]["judgments"]] == [
            ("audience_geography", "unknown", []), ("fee", "unknown", []),
            ("availability", "unknown", []), ("sales", "unknown", []),
        ]
    edited = replace(brief, original_input="Check fees first.", criteria=(replace(brief.criteria[1], required=False),))
    other = ActorContext("local", "second-marketer", "human")
    revised = store.revise_brief(created["campaign_id"], edited, other, expected_version=1, request_id="profile-revise")
    with pytest.raises(EvidenceError, match="brief_version_conflict"):
        store.revise_brief(created["campaign_id"], brief, HUMAN, expected_version=1, request_id="stale-profile")
    for changed, actor in ((brief, other), (edited, HUMAN)):
        with pytest.raises(EvidenceError, match="campaign_request_conflict"):
            store.revise_brief(created["campaign_id"], changed, actor, expected_version=1, request_id="profile-revise")
    assert store.revise_brief(created["campaign_id"], edited, other, expected_version=1, request_id="profile-revise")["brief_id"] == revised["brief_id"]
    history = CampaignStore(store.db).read_campaign(created["campaign_id"], HUMAN)["briefs"]
    assert history[0] == before
    assert history[1]["recorded_by"] == "second-marketer"
    assert history[1]["executable_profile"]["brief_id"] == revised["brief_id"]
    assert history[1]["executable_profile"]["brief_version"] == 2
    assert history[1]["executable_profile"]["criteria"][0]["id"] == "fee"
    assert history[1]["executable_profile"]["criteria"][0]["importance"] == "preference"
    prepared = store.prepare_comparison(created["campaign_id"], revised["brief_id"], knowledge_run, AUTOMATION, request_id="profile-compare")
    view = store.read_comparison(prepared["comparison_id"], HUMAN)
    assert view["executable_profile"] == history[1]["executable_profile"]
    for candidate in view["candidates"]:
        assert candidate["body"]["judgments"][0]["state"] == "unknown"
        assert candidate["body"]["judgments"][0]["support_ids"] == []
        assert {"audience_geography", "fees", "availability", "sales_effectiveness"} <= set(candidate["body"]["unknowns"])


def test_upgrade_preserves_unprofiled_history_and_existing_request_identity(campaigns):
    store = campaigns[0]
    created = store.start(BRIEF, HUMAN, request_id="before-profiles")
    before = store.read_campaign(created["campaign_id"], HUMAN)["briefs"][0]
    # Simulate the prior physical schema, which had no executable-profile column.
    with store.db.connect() as connection:
        connection.execute("ALTER TABLE campaign_briefs DROP COLUMN executable_profile")
    store.migrate()
    store.migrate()
    reopened = CampaignStore(store.db).read_campaign(created["campaign_id"], HUMAN)["briefs"][0]
    assert reopened == {**before, "executable_profile": None}
    assert store.start(BRIEF, HUMAN, request_id="before-profiles") == {**created, "status": "duplicate"}
    revised = store.revise_brief(created["campaign_id"], BRIEF, HUMAN, expected_version=1, request_id="after-profiles")
    history = store.read_campaign(created["campaign_id"], HUMAN)["briefs"]
    assert history[0] == reopened
    assert history[1]["executable_profile"]["brief_id"] == revised["brief_id"]
