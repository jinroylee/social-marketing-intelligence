"""Prepare/assess an explicit human review record without fabricating acceptance."""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree

import psycopg

from smi_campaigns import CampaignStore
from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext, EvidenceSetReader
from smi_monitoring import MonitoringStore


def review_template():
    """Return unanswered baseline, assisted-task and language-review fields."""
    return {"rubric": "local-marketer-review-v1", "dataset_id": "jp-kbeauty-tiktok-public-video-sample-2026-10-05",
            "reviewer": None, "reviewer_attested": False, "reviewed_at": None,
            "manual_baseline": {"completed_before_assistance": None, "prior_exposure": None, "monitoring_answer": None,
                                "account_choices": None, "task_seconds": None, "inspected_posts": None},
            "assisted": {"insight_id": None, "finding_id": None, "shortlist_id": None, "monitoring_seconds": None,
                         "campaign_seconds": None, "inspected_posts": None, "useful_observation": None, "finding_useful": None,
                         "reusable_decision": None, "reuse_reason": None, "decision_reusable": None, "missing_evidence": None},
            "language_review": {"method": "translation_assisted", "review_set": "selected_development_items", "items": []},
            "notes": None}


def technical_result(path):
    if path is None:
        return {"status": "pending", "tests": None}
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    return {"status": "passed" if totals["tests"] > totals["skipped"] and not totals["failures"] and not totals["errors"] else "failed",
            **totals, "evidence": str(path), "scope": "Automated repository checks; live visual/semantic/usefulness review is separate."}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def seconds(value):
    return type(value) in {int, float} and 0 <= value < float("inf")


def timestamp(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except (AttributeError, ValueError):
        return False


def validate_links(record, db):
    """Resolve actual same-corpus, human-attributed records and reviewed source IDs."""
    actor = ActorContext("local", record["reviewer"], "human")
    monitoring, campaigns = MonitoringStore(db), CampaignStore(db)
    assisted = record["assisted"]
    insight = monitoring.read_insight(assisted["insight_id"], actor)
    investigation = monitoring.read_investigation(insight["investigation_id"], actor)
    shortlist = campaigns.read_shortlist(assisted["shortlist_id"], actor)
    campaign = campaigns.read_campaign(shortlist["campaign_id"], actor)
    comparison = campaigns.read_comparison(shortlist["comparison_id"], actor)
    available_findings = {f["finding_id"] for f in insight["findings"] if f["support_state"] == "available"}
    source = EvidenceSetReader(db).read(record["dataset_id"], actor)
    caption_refs = {(m["observation_id"], a["assertion_id"]) for m in source["members"] if m["availability"] == "available"
                    and m["policy"]["can_retain"] and m["support_status"] == "current" for a in m["assertions"] if a["field"] == "caption"}
    reviewed_refs = [(item.get("observation_id"), item.get("source_assertion_id")) for item in record["language_review"]["items"]]
    return (insight["dataset_id"] == comparison["dataset_id"] == record["dataset_id"] and insight["digest"] == comparison["digest"]
            and assisted["finding_id"] in available_findings and not shortlist["review_required"]
            and shortlist["status"] == "confirmed" and (assisted.get("reusable_decision") != "keep" or bool(shortlist["selected"]))
            and investigation["owner_id"] == campaign["owner_id"] == shortlist["recorded_by"] == actor.actor_id
            and len(set(reviewed_refs)) == len(reviewed_refs) and all(ref in caption_refs for ref in reviewed_refs))


def assess_review(record, technical=None, *, links_valid=False):
    """Separate technical, translation-assisted and human-usefulness gates."""
    if record.get("rubric") != "local-marketer-review-v1":
        raise ValueError("unknown review rubric")
    baseline, assisted, language = record["manual_baseline"], record["assisted"], record["language_review"]
    items = language["items"]
    labels = {"supported", "unsupported", "ambiguous", "not_assessable"}
    uncorrected = any(item.get("material_error") is True and item.get("corrected") is not True for item in items)
    attested = (record.get("reviewer_attested") is True and nonempty(record.get("reviewer")) and timestamp(record.get("reviewed_at")))
    language_done = (attested and links_valid and language["method"] == "translation_assisted" and bool(items)
                     and all(nonempty(i.get("translation")) and nonempty(i.get("translator_method")) and i.get("label") in labels
                             and type(i.get("material_error")) is bool for i in items))
    language_status = "failed" if uncorrected else "passed" if language_done else "pending"
    baseline_done = (baseline.get("completed_before_assistance") is True and nonempty(baseline.get("prior_exposure"))
                     and nonempty(baseline.get("monitoring_answer")) and isinstance(baseline.get("account_choices"), list)
                     and seconds(baseline.get("task_seconds")) and type(baseline.get("inspected_posts")) is int and baseline["inspected_posts"] >= 0)
    assisted_done = (seconds(assisted.get("monitoring_seconds")) and seconds(assisted.get("campaign_seconds"))
                     and type(assisted.get("inspected_posts")) is int and assisted["inspected_posts"] >= 0
                     and assisted.get("reusable_decision") in {"keep", "exclude", "defer"}
                     and nonempty(assisted.get("reuse_reason")) and nonempty(assisted.get("useful_observation"))
                     and nonempty(assisted.get("missing_evidence"))
                     and type(assisted.get("finding_useful")) is bool and type(assisted.get("decision_reusable")) is bool)
    usefulness = "failed" if uncorrected else "pending"
    if attested and baseline_done and assisted_done and links_valid and language_status == "passed":
        usefulness = "passed" if assisted["finding_useful"] and assisted["decision_reusable"] else "failed"
    technical = technical or {"status": "pending", "tests": None}
    reviewed = sum(nonempty(i.get("translation")) and nonempty(i.get("translator_method")) and i.get("label") in labels
                   and type(i.get("material_error")) is bool for i in items) if attested and links_valid else 0
    return {"rubric": record["rubric"], "reviewer": record.get("reviewer"), "technical": technical,
            "translation_assisted": {"status": language_status, "selected_items": len(items), "reviewed_items": reviewed, "reference_provenance": language["review_set"]},
            "usefulness": {"status": usefulness, "speed_target": None, "sales_improvement_claim": None},
            "japanese_original_accuracy": "not_validated", "links_valid": links_valid,
            "overall": "passed" if technical["status"] == language_status == usefulness == "passed" else "failed" if "failed" in {technical["status"], language_status, usefulness} else "pending"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--technical-results", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dsn", default=os.environ.get("SMI_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi"))
    parser.add_argument("--schema", default=os.environ.get("SMI_DATABASE_SCHEMA"))
    args = parser.parse_args()
    try:
        if args.init:
            args.record.parent.mkdir(parents=True, exist_ok=True)
            with args.record.open("x") as output:
                json.dump(review_template(), output, ensure_ascii=False, indent=2)
                output.write("\n")
            print("Created unanswered human review record.")
            return 0
        record = json.loads(args.record.read_text())
        assisted = record["assisted"]
        links_valid = False
        if nonempty(record.get("reviewer")) and all(nonempty(assisted.get(k)) for k in ("insight_id", "finding_id", "shortlist_id")):
            links_valid = validate_links(record, Database(args.dsn, args.schema))
        result = assess_review(record, technical_result(args.technical_results), links_valid=links_valid)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered)
        print(rendered, end="")
        return 1 if result["overall"] == "failed" else 0
    except (OSError, ValueError, KeyError, TypeError, psycopg.Error, EvidenceError, ElementTree.ParseError):
        print("Could not read or verify the review record; check its fields and local database setup.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
