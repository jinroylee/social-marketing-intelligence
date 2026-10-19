"""Deterministic account comparison over exact, permitted caption evidence."""

from __future__ import annotations

import json
from typing import Any

from .contracts import Brief, window_time


METHOD_VERSION = "campaign-caption-comparison-v1"
BASE_UNKNOWNS = ["audience_geography", "fees", "availability", "sales_effectiveness", "recent_post_history"]
VALUE_FIELDS = {"brand_mention": "brand_id", "product_mention": "product_id", "topic_mention": "topic_id",
                "script_evidence": "script", "literal_marker": "marker"}


def account_token(key: dict[str, str]) -> str:
    """Stable identity including the namespace; handles are never matching keys."""
    return json.dumps(key, sort_keys=True, separators=(",", ":"))


def build_comparison(brief: Brief, source: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return bounded candidate judgments; absent evidence remains unknown."""
    candidates = {}
    for key in brief.document()["known_accounts"]:
        candidates[account_token(key)] = {"account_key": key, "account_id": None, "origin": "marketer_known", "members": []}
    eligible = []
    start, end = window_time(brief.publication_from), window_time(brief.publication_to)
    for member in source["members"]:
        if (member["availability"] != "available" or not member["policy"]["can_retain"]
                or member["support_status"] != "current"):
            continue
        fields = {a["field"]: a for a in member["assertions"] if a["state"] == "observed"}
        author = fields.get("author_account")
        if author is None or author["value"]["platform"] not in brief.platforms:
            continue
        published = window_time(fields["published_at"]["value"]) if "published_at" in fields else None
        if (start is not None or end is not None) and (published is None
                or start is not None and published < start or end is not None and published > end):
            continue
        eligible.append(member["observation_id"])
        key = author["value"]
        token = account_token(key)
        candidate = candidates.setdefault(token, {"account_key": key, "account_id": None, "origin": "retrieved", "members": []})
        if candidate["origin"] == "marketer_known":
            candidate["origin"] = "both"
        candidate["members"].append(member)
        if "handle" in fields:
            candidate["account_id"] = fields["handle"]["subject_id"]
    output = []
    for candidate in candidates.values():
        member_ids = {m["observation_id"] for m in candidate["members"]}
        claims = [c for c in knowledge["interpretations"] if c["state"] == "supported" and c["observation_id"] in member_ids]
        judgments = []
        for criterion in brief.criteria:
            field = VALUE_FIELDS.get(criterion.kind)
            matched = [c for c in claims if c["predicate"] == criterion.kind and field is not None
                       and c["value"].get(field) == criterion.value and "ambiguity" not in c["value"]]
            state = "unknown"
            if matched:
                state = "satisfied" if criterion.operator == "include" else "not_satisfied_on_evidence"
            judgments.append({"criterion_id": criterion.id, "label": criterion.label, "state": state,
                              "required": criterion.required, "unknown_handling": criterion.unknown_handling,
                              "reason": "Literal support in the selected captions; semantic review is provisional." if matched
                              else "The selected evidence does not establish this criterion.",
                              "support_ids": [c["id"] for c in matched], "review_status": "provisional" if matched else "not_assessable"})
        dependencies = []
        for member in candidate["members"]:
            for assertion in member["assertions"]:
                if assertion["field"] == "author_account" and assertion["state"] == "observed":
                    dependencies.append({"observation_id": member["observation_id"], "source_assertion_id": assertion["assertion_id"],
                                         "interpretation_id": None})
        supported_ids = {sid for judgment in judgments for sid in judgment["support_ids"]}
        dependencies.extend({"observation_id": c["observation_id"], "source_assertion_id": c["source_assertion_id"],
                             "interpretation_id": c["id"]} for c in claims if c["id"] in supported_ids)
        unknowns = BASE_UNKNOWNS + [f"criterion:{j['criterion_id']}" for j in judgments if j["state"] == "unknown"]
        output.append({"account_key": candidate["account_key"], "account_id": candidate["account_id"], "origin": candidate["origin"],
                       "body": {"judgments": judgments, "unknowns": unknowns, "coverage": "selected_caption_observations",
                                "observations": sorted(member_ids), "exploratory": True}, "dependencies": dependencies})
    return output, {"requested": source["coverage"], "actual_observation_ids": eligible,
                    "candidate_count": len(output), "requested_publication_from": brief.publication_from,
                    "requested_publication_to": brief.publication_to, "scope": "fixed_selected_observations"}
