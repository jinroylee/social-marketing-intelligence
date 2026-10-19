"""Synthetic review records test gate behavior, never stand in for marketer feedback."""

import importlib.util
from pathlib import Path

from psycopg.types.json import Jsonb

from test_monitoring_planning import HUMAN, DATASET, insight, monitoring as monitoring_fixture, planning
from test_campaigns import campaigns as campaigns_fixture


campaigns = campaigns_fixture
monitoring = monitoring_fixture
spec = importlib.util.spec_from_file_location("pilot_evaluation", Path(__file__).parents[1] / "tools/pilot_evaluation.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def completed_record():
    record = evaluation.review_template()
    record.update(reviewer=HUMAN.actor_id, reviewer_attested=True, reviewed_at="2026-10-14T12:00:00+09:00")
    record["manual_baseline"].update(completed_before_assistance=True, prior_exposure="Synthetic test: prior sample exposure disclosed.",
        monitoring_answer="Synthetic manual answer", account_choices=[], task_seconds=100, inspected_posts=19)
    record["assisted"].update(monitoring_seconds=50, campaign_seconds=60, inspected_posts=6, useful_observation="Synthetic useful observation",
        finding_useful=True, reusable_decision="defer", reuse_reason="Synthetic reusable defer explanation", decision_reusable=True, missing_evidence="Audience and outcomes unknown.")
    record["language_review"]["items"] = [{"translation": "Synthetic translation", "translator_method": "synthetic-fixture-v1",
        "label": "supported", "material_error": False, "corrected": False}]
    return record


def test_technical_success_cannot_fill_missing_human_review():
    result = evaluation.assess_review(evaluation.review_template(), {"status": "passed", "tests": 178})
    assert result["translation_assisted"]["status"] == result["usefulness"]["status"] == result["overall"] == "pending"
    assert result["japanese_original_accuracy"] == "not_validated"


def test_uncorrected_material_error_fails_both_human_gates_and_no_speed_target():
    record = completed_record()
    assert evaluation.assess_review(record, {"status": "passed"}, links_valid=False)["overall"] == "pending"
    result = evaluation.assess_review(record, {"status": "passed"}, links_valid=True)
    assert result["overall"] == "passed" and result["usefulness"]["speed_target"] is None
    record["language_review"]["items"][0]["material_error"] = True
    result = evaluation.assess_review(record, {"status": "passed"}, links_valid=True)
    assert result["translation_assisted"]["status"] == result["usefulness"]["status"] == "failed"


def test_review_links_resolve_same_corpus_and_current_human_records(monitoring, campaigns):
    store = monitoring[0]
    _, prepared, result = insight(monitoring)
    _, _, _, shortlist = planning(campaigns)
    finding = next(f for f in result["findings"] if f["body"]["predicate"] == "product_mention")
    record = completed_record()
    record["assisted"].update(insight_id=prepared["insight_id"], finding_id=finding["finding_id"], shortlist_id=shortlist["shortlist_id"])
    claim = finding["evidence"][0]
    record["language_review"]["items"][0].update(observation_id=claim["observation_id"], source_assertion_id=claim["source_assertion_id"])
    assert evaluation.validate_links(record, store.db) is True
    confirmed_id = record["assisted"]["shortlist_id"]
    original = campaigns[0].read_shortlist(confirmed_id, HUMAN)
    draft = campaigns[0].save_shortlist(original["comparison_id"], (), HUMAN, confirmed=False, expected_version=1, request_id="unconfirmed-review")
    record["assisted"]["shortlist_id"] = draft["shortlist_id"]
    assert evaluation.validate_links(record, store.db) is False
    record["assisted"]["shortlist_id"] = confirmed_id
    member = store.evidence.read(DATASET, HUMAN)["members"][0]
    with store.db.connect() as connection:
        connection.execute("UPDATE source_observations SET policy=%s WHERE id=%s", (Jsonb({**member["policy"], "revoked": True}), member["observation_id"]))
    assert evaluation.validate_links(record, store.db) is False
