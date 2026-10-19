"""Literal snapshot summaries with exact member support and bounded counts."""

import json

from .contracts import InvestigationScope, instant


METHOD_VERSION = "caption-snapshot-summary-v1"
LIMITS = ["Selected observations only; no representative market sampling frame.",
          "No comparable baseline; market growth or change is not established.",
          "Literal wording and mentions remain provisional; author stance and efficacy are unknown.",
          "Audience geography, sales and complete account histories are unknown."]
REFERENCE_FIELDS = {"brand_mention": "brand_id", "product_mention": "product_id", "topic_mention": "topic_id"}


def build_summary(scope: InvestigationScope, source, knowledge, catalog):
    """Count distinct posts/accounts; repeated captures never become extra posts."""
    requested = {"brand_mention": set(scope.brand_ids), "product_mention": set(scope.product_ids), "topic_mention": set(scope.topic_ids)}
    start, end = instant(scope.publication_from), instant(scope.publication_to)
    scanned, matched, members = [], [], {}
    language_unresolved = scope.caption_language is not None
    for member in source["members"]:
        if member["availability"] != "available" or not member["policy"]["can_retain"] or member["support_status"] != "current":
            continue
        fields = {a["field"]: a for a in member["assertions"] if a["state"] == "observed"}
        author = fields.get("author_account")
        if author is None or author["value"]["platform"] not in scope.platforms:
            continue
        published = instant(fields["published_at"]["value"]) if "published_at" in fields else None
        if (start is not None or end is not None) and (published is None or start is not None and published < start or end is not None and published > end):
            continue
        scanned.append(member["observation_id"])
        claims = [c for c in knowledge["interpretations"] if c["observation_id"] == member["observation_id"]
                  and c["state"] == "supported" and "ambiguity" not in c["value"]]
        relevant = [c for c in claims if c["predicate"] in requested
                    and c["value"].get(REFERENCE_FIELDS[c["predicate"]]) in requested[c["predicate"]]]
        if not relevant or language_unresolved:
            continue
        matched.append(member["observation_id"])
        members[member["observation_id"]] = (member, fields, claims)
    names = {entry["id"]: entry["name"] for group in ("brands", "products", "topics") for entry in catalog[group]}
    groups = {}
    for observation_id, (member, fields, claims) in members.items():
        for claim in claims:
            predicate = claim["predicate"]
            if predicate in REFERENCE_FIELDS:
                key = claim["value"][REFERENCE_FIELDS[predicate]]
                if key not in requested[predicate]:
                    continue
            elif predicate == "literal_marker":
                key = claim["value"]["marker"]
            else:
                continue
            group = groups.setdefault((predicate, key), [])
            group.append((claim, member, fields))
    findings = []
    for (predicate, key), supported in sorted(groups.items()):
        posts = {claim["subject_id"] for claim, _, _ in supported}
        accounts = {json.dumps(fields["author_account"]["value"], sort_keys=True) for _, _, fields in supported}
        observations = sorted({member["observation_id"] for _, member, _ in supported})
        label = names.get(key, {"pr_marker": "literal PR marker", "qoo10_reference": "Qoo10 reference"}.get(key, key))
        body = {"label": label, "predicate": predicate, "reference_id": key,
                "statement": f"{label}: literal support in {len(posts)} distinct selected posts from {len(accounts)} observed accounts.",
                "post_count": len(posts), "account_count": len(accounts), "observation_ids": observations,
                "support_ids": sorted({claim["id"] for claim, _, _ in supported}), "review_status": "provisional", "basis": "derived"}
        dependencies = []
        seen = set()
        for claim, member, fields in supported:
            for assertion_id, interpretation_id in ((claim["source_assertion_id"], claim["id"]), (fields["author_account"]["assertion_id"], None)):
                dependency = (member["observation_id"], assertion_id, interpretation_id)
                if dependency not in seen:
                    dependencies.append({"observation_id": dependency[0], "source_assertion_id": dependency[1], "interpretation_id": dependency[2]})
                    seen.add(dependency)
        findings.append({"body": body, "dependencies": dependencies})
    return findings, {"requested": source["coverage"], "scanned_observation_ids": scanned, "actual_observation_ids": matched,
                      "scope": "fixed_selected_observations", "language_constraint": "not_assessable" if language_unresolved else "not_requested",
                      "baseline": None, "trend_status": "not_assessable"}
