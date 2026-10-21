"""Deterministic account comparison over exact, permitted caption evidence."""

from __future__ import annotations

import json
from typing import Any

from .contracts import Brief, window_time


CURRENT_METHOD_VERSION = "current-kb-caption-comparison-v1"
METHOD_VERSION = "campaign-caption-comparison-v1"
BASE_UNKNOWNS = ["audience_geography", "fees", "availability", "sales_effectiveness", "recent_post_history"]
VALUE_FIELDS = {"brand_mention": "brand_id", "product_mention": "product_id", "topic_mention": "topic_id",
                "script_evidence": "script", "literal_marker": "marker"}


def structured_profile(document: dict[str, Any], brief_id: str, version: int) -> dict[str, Any]:
    """Snapshot the installed structured rules, without claiming ranking or coverage assessment."""
    return {"brief_id": brief_id, "brief_version": version, "basis": "human_structured_input",
            "criteria_profile_version": "structured-caption-criteria-v1", "comparison_method_version": METHOD_VERSION,
            "criteria": [{**c, "importance": "requirement" if c["required"] else "preference"}
                         for c in document["criteria"]],
            "ranking_profile": {"version": "unranked-caption-comparison-v1", "status": "unranked",
                                "ordering": "marketer_known_then_dataset_encounter_order"},
            "coverage_profile": {"version": "fixed-selected-observations-v1", "status": "descriptive_only",
                                 "scope": "fixed_selected_observations", "sufficiency_assessment": "not_implemented"},
            "baseline_unknowns": list(BASE_UNKNOWNS)}


def account_token(key: dict[str, str]) -> str:
    """Stable identity including the namespace; handles are never matching keys."""
    return json.dumps(key, sort_keys=True, separators=(",", ":"))


def build_comparison(brief: Brief, source: dict[str, Any], knowledge: dict[str, Any], *, current_knowledge: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return bounded candidate judgments; absent evidence remains unknown."""
    candidates = {}
    known_tokens = {account_token(key) for key in brief.document()['known_accounts']}
    for key in ([] if current_knowledge else brief.document()["known_accounts"]):
        candidates[account_token(key)] = {"account_key": key, "account_id": None, "origin": "marketer_known", "members": []}
    eligible = []
    candidate_limit_reached = False
    start, end = window_time(brief.publication_from), window_time(brief.publication_to)
    for member in source["members"]:
        if (member["availability"] != "available" or not member["policy"]["can_retain"]
                or member["support_status"] != "current"):
            continue
        fields = {a["field"]: a for a in member["assertions"] if a["state"] == "observed"}
        author = fields.get("author_account")
        keys = member.get("account_keys", []) if current_knowledge else ([author["value"]] if author else [])
        keys = [key for key in keys if key["platform"] in brief.platforms]
        if not keys:
            continue
        published = window_time(fields["published_at"]["value"]) if "published_at" in fields else None
        if (start is not None or end is not None) and (published is None
                or start is not None and published < start or end is not None and published > end):
            continue
        eligible.append(member["observation_id"])
        for key in keys:
            token = account_token(key)
            if current_knowledge and token not in candidates and len(candidates) == 100:
                candidate_limit_reached = True
                continue
            known = token in known_tokens
            candidate = candidates.setdefault(token, {"account_key": key, "account_id": None, "origin": "both" if known else "retrieved", "members": []})
            if candidate["origin"] == "marketer_known":
                candidate["origin"] = "both"
            candidate["members"].append(member)
            if current_knowledge:
                candidate['account_id'] = next((item['subject_id'] for item in member['assertions'] + member['metrics']
                                                if all(item[field] == key[field] for field in ('platform', 'namespace', 'kind', 'native_id'))), candidate['account_id'])
            elif "handle" in fields:
                candidate["account_id"] = fields["handle"]["subject_id"]
    output = []
    for candidate in candidates.values():
        member_ids = {m["observation_id"] for m in candidate["members"]}
        supported_subjects = {a['subject_id'] for m in candidate['members'] for a in m['assertions']
                              if (a['field'] == 'author_account' and a['state'] == 'observed' and a['value'] == candidate['account_key'])
                              or all(a[field] == candidate['account_key'][field] for field in ('platform', 'namespace', 'kind', 'native_id'))}
        claims = [c for c in knowledge["interpretations"] if c["state"] == "supported" and c["observation_id"] in member_ids
                  and (not current_knowledge or c["catalog_id"] == brief.catalog_id and c["subject_id"] in supported_subjects)]
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
            if current_knowledge and not any(d['observation_id'] == member['observation_id'] for d in dependencies):
                dependencies.append({'observation_id': member['observation_id'],
                                     'source_assertion_id': member['assertion_ids'][0] if member['assertion_ids'] else None,
                                     'interpretation_id': None})
        supported_ids = {sid for judgment in judgments for sid in judgment["support_ids"]}
        dependencies.extend({"observation_id": c["observation_id"], "source_assertion_id": c["source_assertion_id"],
                             "interpretation_id": c["id"]} for c in claims if c["id"] in supported_ids)
        unknowns = BASE_UNKNOWNS + [f"criterion:{j['criterion_id']}" for j in judgments if j["state"] == "unknown"]
        if current_knowledge:
            unknowns = list(dict.fromkeys(unknowns + ['contracts'] + [u for m in candidate['members'] for u in m['unknowns']]))
        output.append({"account_key": candidate["account_key"], "account_id": candidate["account_id"], "origin": candidate["origin"],
                       "body": {"judgments": judgments, "unknowns": unknowns, "coverage": "selected_caption_observations",
                                "observations": sorted(member_ids), "exploratory": True}, "dependencies": dependencies})
        if current_knowledge:
            body = output[-1]['body']
            body['support_manifest'] = [m for m in knowledge['manifest'] if m['observation_id'] in member_ids]
            body['source_dates'] = [{'observation_id': m['observation_id'], 'captured_at': m['captured_at'],
                                     'source_as_of': m['source_as_of'], 'ingested_at': m['ingested_at']} for m in candidate['members']]
            body['coverage'] = 'bounded_current_knowledge'
            body['assessment'] = ('excluded_on_required_evidence' if any(j['required'] and j['state'] == 'not_satisfied_on_evidence' for j in judgments)
                                  else 'deferred_unknown_requirements' if any(j['required'] and j['state'] == 'unknown' and j['unknown_handling'] == 'defer' for j in judgments)
                                  else 'eligible_with_explicit_gaps')
    coverage = {"requested": source["coverage"], "actual_observation_ids": eligible,
                    "candidate_count": len(output), "requested_publication_from": brief.publication_from,
                    "requested_publication_to": brief.publication_to, "scope": "fixed_selected_observations"}
    if current_knowledge:
        tokens = {account_token(c['account_key']) for c in output}
        coverage.update(scope='bounded_current_knowledge', candidate_limit=100, candidate_limit_reached=candidate_limit_reached, retrieval=knowledge['coverage'], unknowns=knowledge['unknowns'] + ([] if output else ['no_eligible_supported_accounts_in_campaign_scope']),
                        discovery_seeds=[k for k in brief.document()['known_accounts'] if account_token(k) not in tokens],
                        ordering='newest_publication_then_member_account_encounter_order', ranking='unranked')
    return output, coverage
