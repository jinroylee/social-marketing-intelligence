"""Small typed campaign contracts with visible requirements and unknowns."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from smi_ingestion.contracts import ExternalKey
from smi_ingestion.evidence import EvidenceError


SUPPORTED_KINDS = {"brand_mention", "product_mention", "topic_mention", "script_evidence", "literal_marker",
                   "caption_language", "audience_geography", "fee", "availability", "sales", "recent_history", "custom"}
CONTEXT_FIELDS = {"campaign_dates", "budget", "currency", "audience_detail"}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceError(code)


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def window_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(instant.tzinfo is not None, "brief_window_requires_timezone")
        return instant
    except (AttributeError, ValueError) as error:
        raise EvidenceError("invalid_brief_window") from error


@dataclass(frozen=True)
class Criterion:
    """An inspectable marketer criterion; unknown handling is independent of importance."""

    id: str
    label: str
    kind: str
    value: str | None = None
    required: bool = True
    operator: str = "include"
    unknown_handling: str = "acknowledge"

    def validate(self) -> None:
        require(text(self.id) and text(self.label), "invalid_brief.criterion")
        require(isinstance(self.kind, str) and self.kind in SUPPORTED_KINDS, "invalid_brief.criterion_kind")
        require(self.value is None or text(self.value), "invalid_brief.criterion_value")
        require(type(self.required) is bool and isinstance(self.operator, str) and self.operator in {"include", "exclude"}
                and isinstance(self.unknown_handling, str) and self.unknown_handling in {"acknowledge", "defer"}, "invalid_brief.criterion_policy")


@dataclass(frozen=True)
class Brief:
    """Human-authored campaign needs; dates/budget can remain explicit unknowns."""

    catalog_id: str
    brand_id: str
    product_ids: tuple[str, ...]
    objective: str
    target_market: str
    platforms: tuple[str, ...]
    criteria: tuple[Criterion, ...]
    known_accounts: tuple[ExternalKey, ...] = ()
    context: dict[str, str | None] = field(default_factory=dict)
    publication_from: str | None = None
    publication_to: str | None = None
    original_input: str | None = None

    def validate(self) -> None:
        for name in ("catalog_id", "brand_id", "objective", "target_market"):
            require(text(getattr(self, name)), f"invalid_brief.{name}")
        require(isinstance(self.product_ids, tuple) and all(text(p) for p in self.product_ids)
                and len(set(self.product_ids)) == len(self.product_ids), "invalid_brief.product_ids")
        require(isinstance(self.platforms, tuple) and bool(self.platforms) and all(text(p) for p in self.platforms)
                and len(set(self.platforms)) == len(self.platforms), "invalid_brief.platforms")
        require(isinstance(self.criteria, tuple) and bool(self.criteria), "invalid_brief.criteria")
        for criterion in self.criteria:
            require(isinstance(criterion, Criterion), "invalid_brief.criterion")
            criterion.validate()
        require(len({c.id for c in self.criteria}) == len(self.criteria), "duplicate_brief_criterion")
        require(isinstance(self.known_accounts, tuple), "invalid_brief.known_accounts")
        for account in self.known_accounts:
            require(isinstance(account, ExternalKey) and account.kind == "account"
                    and all(text(v) for v in asdict(account).values()), "invalid_brief.known_account")
        require(len(set(self.known_accounts)) == len(self.known_accounts), "duplicate_known_account")
        require(isinstance(self.context, dict) and self.context.keys() <= CONTEXT_FIELDS
                and all(v is None or text(v) for v in self.context.values()), "invalid_brief.context")
        require(self.original_input is None or text(self.original_input), "invalid_brief.original_input")
        start, end = window_time(self.publication_from), window_time(self.publication_to)
        require(start is None or end is None or start <= end, "invalid_brief.window_order")

    def document(self) -> dict[str, Any]:
        """Return a fresh JSON-shaped brief after validating all required fields."""
        self.validate()
        result = asdict(self)
        result["product_ids"] = list(self.product_ids)
        result["platforms"] = list(self.platforms)
        result["criteria"] = [asdict(c) for c in self.criteria]
        result["known_accounts"] = [asdict(a) for a in self.known_accounts]
        result["context"] = {key: self.context.get(key) for key in sorted(CONTEXT_FIELDS)}
        # Preserve the request digest of pre-profile structured briefs on retries.
        if self.original_input is None:
            del result["original_input"]
        return result

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> Brief:
        """Restore a persisted/submitted document with field-specific validation errors."""
        require(isinstance(document, dict), "invalid_brief")
        required = {"catalog_id", "brand_id", "product_ids", "objective", "target_market", "platforms", "criteria"}
        for key in required:
            require(key in document, f"invalid_brief.{key}")
        for key in ("product_ids", "platforms", "criteria"):
            require(isinstance(document[key], list), f"invalid_brief.{key}")
        require(isinstance(document.get("known_accounts", []), list), "invalid_brief.known_accounts")
        require(document.keys() <= required | {"known_accounts", "context", "publication_from", "publication_to", "original_input"}, "unknown_brief_field")
        try:
            brief = cls(**{**document,
                           "product_ids": tuple(document["product_ids"]), "platforms": tuple(document["platforms"]),
                           "criteria": tuple(Criterion(**c) for c in document["criteria"]),
                           "known_accounts": tuple(ExternalKey(**a) for a in document.get("known_accounts", []))})
        except (TypeError, ValueError) as error:
            raise EvidenceError("invalid_brief") from error
        brief.validate()
        return brief


@dataclass(frozen=True)
class Selection:
    """A human's selected comparison candidate, reason and explicitly acknowledged gaps."""

    candidate_id: str
    reason: str | None = None
    support_ids: tuple[str, ...] = ()
    acknowledged_unknowns: tuple[str, ...] = ()

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> Selection:
        """Restore a submitted selection without accepting actor/confirmation fields."""
        require(isinstance(document, dict) and "candidate_id" in document
                and document.keys() <= {"candidate_id", "reason", "support_ids", "acknowledged_unknowns"}, "invalid_selection")
        require(isinstance(document.get("support_ids", []), list) and isinstance(document.get("acknowledged_unknowns", []), list), "invalid_selection")
        return cls(document["candidate_id"], document.get("reason"), tuple(document.get("support_ids", [])),
                   tuple(document.get("acknowledged_unknowns", [])))
