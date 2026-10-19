"""Human investigation scope independent of campaign initiation."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from smi_ingestion.evidence import EvidenceError


def require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceError(code)


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def instant(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None, "investigation_window_requires_timezone")
        return result
    except (AttributeError, ValueError) as error:
        raise EvidenceError("invalid_investigation_window") from error


@dataclass(frozen=True)
class InvestigationScope:
    """A product/topic question, intended context and explicit retrieval constraints."""

    catalog_id: str
    question: str
    market_context: str
    platforms: tuple[str, ...]
    brand_ids: tuple[str, ...] = ()
    product_ids: tuple[str, ...] = ()
    topic_ids: tuple[str, ...] = ()
    caption_language: str | None = None
    publication_from: str | None = None
    publication_to: str | None = None

    def document(self) -> dict[str, Any]:
        """Validate and return a fresh JSON scope; unsupported language stays explicit."""
        for name in ("catalog_id", "question", "market_context"):
            require(text(getattr(self, name)), f"invalid_investigation.{name}")
        for name in ("platforms", "brand_ids", "product_ids", "topic_ids"):
            values = getattr(self, name)
            require(isinstance(values, tuple) and all(text(v) for v in values) and len(set(values)) == len(values), f"invalid_investigation.{name}")
        require(bool(self.platforms), "invalid_investigation.platforms")
        require(bool(self.brand_ids or self.product_ids or self.topic_ids), "invalid_investigation.references")
        require(self.caption_language is None or text(self.caption_language), "invalid_investigation.caption_language")
        start, end = instant(self.publication_from), instant(self.publication_to)
        require(start is None or end is None or start <= end, "invalid_investigation.window_order")
        result = asdict(self)
        for name in ("platforms", "brand_ids", "product_ids", "topic_ids"):
            result[name] = list(getattr(self, name))
        return result

    @classmethod
    def from_document(cls, document: dict[str, Any]):
        """Restore a submitted scope with explicit missing/unknown-field failures."""
        require(isinstance(document, dict), "invalid_investigation")
        for name in ("catalog_id", "question", "market_context", "platforms"):
            require(name in document, f"invalid_investigation.{name}")
        require(document.keys() <= cls.__dataclass_fields__.keys(), "unknown_investigation_field")
        fields = dict(document)
        for name in ("platforms", "brand_ids", "product_ids", "topic_ids"):
            require(isinstance(fields.get(name, []), list), f"invalid_investigation.{name}")
            fields[name] = tuple(fields.get(name, []))
        result = cls(**fields)
        result.document()
        return result
