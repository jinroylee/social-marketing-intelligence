"""Pure, conservative caption rules with exact source support."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from smi_ingestion.evidence import EvidenceError

from .catalog import Catalog


METHOD_VERSION = "caption-literal-rules-v1"
PREDICATES = {"brand_mention", "product_mention", "script_evidence", "topic_mention", "literal_marker"}


@dataclass(frozen=True)
class Interpretation:
    """A provisional typed value supported by one exact caption span."""

    predicate: str
    value: dict[str, Any]
    start: int
    end: int
    excerpt: str


def _matches(text: str, alias: str):
    # ASCII word boundaries keep short Latin brand names out of unrelated words.
    left = r"(?<![A-Za-z0-9])" if alias[0].isascii() and alias[0].isalnum() else ""
    right = r"(?![A-Za-z0-9])" if alias[-1].isascii() and alias[-1].isalnum() else ""
    return re.finditer(left + re.escape(alias) + right, text, re.IGNORECASE)


def extract(caption: str, catalog: Catalog) -> tuple[Interpretation, ...]:
    """Return literal mentions without inferring stance, geography, efficacy or sales."""
    found = []
    for group, predicate, key in (("brands", "brand_mention", "brand_id"),
                                   ("products", "product_mention", "product_id"),
                                   ("topics", "topic_mention", "topic_id")):
        for entry in catalog.document[group]:
            for alias in entry["aliases"]:
                for match in _matches(caption, alias):
                    value = {key: entry["id"], "interpretation": "literal_catalog_alias", "stance": "not_assessed"}
                    if group == "products":
                        value.update(brand_id=entry["brand_id"], specificity=entry["specificity"])
                    found.append(Interpretation(predicate, value, match.start(), match.end(), match.group()))
    for match in re.finditer(r"[ぁ-ゖァ-ヺーｦ-ﾟ]+", caption):
        found.append(Interpretation("script_evidence", {"script": "kana", "language": "unknown"},
                                    match.start(), match.end(), match.group()))
    for pattern, marker in ((r"#pr(?=$|[^\w])", "pr_marker"), (r"(?<![A-Za-z0-9])qoo10(?![A-Za-z0-9])", "qoo10_reference")):
        for match in re.finditer(pattern, caption, re.IGNORECASE):
            found.append(Interpretation("literal_marker", {"marker": marker}, match.start(), match.end(), match.group()))
    # Overlapping aliases for the same object should not create duplicate claims.
    unique = {(c.predicate, str(sorted(c.value.items())), c.start, c.end): c for c in found}
    claims = list(unique.values())
    for claim in claims:
        if claim.predicate == "product_mention":
            alternatives = {c.value["product_id"] for c in claims if c.predicate == "product_mention"
                            and (c.start, c.end) == (claim.start, claim.end)}
            if len(alternatives) > 1:
                claim.value["ambiguity"] = "multiple_catalog_products"
    return tuple(sorted(claims, key=lambda c: (c.start, c.end, c.predicate, str(c.value))))


def validate_support(claim: Interpretation, caption: str) -> None:
    """Reject fabricated spans and unsupported predicate/value shapes at persistence."""
    if (claim.predicate not in PREDICATES or type(claim.start) is not int or type(claim.end) is not int
            or not 0 <= claim.start < claim.end <= len(caption)
            or caption[claim.start:claim.end] != claim.excerpt or not isinstance(claim.value, dict)):
        raise EvidenceError("invalid_interpretation_support")
    required = {
        "brand_mention": {"brand_id", "interpretation", "stance"},
        "product_mention": {"product_id", "brand_id", "specificity", "interpretation", "stance"},
        "topic_mention": {"topic_id", "interpretation", "stance"},
        "script_evidence": {"script", "language"},
        "literal_marker": {"marker"},
    }[claim.predicate]
    allowed = required | ({"ambiguity"} if claim.predicate == "product_mention" else set())
    if (not required <= claim.value.keys() <= allowed
            or not all(isinstance(v, str) and v for v in claim.value.values())):
        raise EvidenceError("invalid_interpretation_value")
    if ("stance" in claim.value and claim.value["stance"] != "not_assessed"
            or claim.predicate == "product_mention" and claim.value["specificity"] not in {"family", "variant"}
            or claim.predicate == "script_evidence" and claim.value != {"script": "kana", "language": "unknown"}
            or claim.predicate == "literal_marker" and claim.value["marker"] not in {"pr_marker", "qoo10_reference"}):
        raise EvidenceError("invalid_interpretation_value")
