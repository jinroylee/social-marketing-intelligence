"""Human planning intent and feedback, distinct from observed commercial outcomes."""

from dataclasses import asdict, dataclass

from ..contracts import require, text


@dataclass(frozen=True)
class MeasurementPlan:
    """Proposed definitions and prerequisites; this contract contains no result fields."""

    objective: str
    outcome_definition: str
    product_ids: tuple[str, ...]
    gaps: tuple[str, ...]
    intended_source: str | None = None
    source_owner: str | None = None
    listing: str | None = None
    currency: str | None = None
    period: str | None = None
    baseline: str | None = None
    matching_approach: str | None = None
    attribution_assumptions: str | None = None

    def document(self):
        """Return a validated proposed plan with explicit unknown prerequisites."""
        require(text(self.objective) and text(self.outcome_definition), "invalid_measurement_plan.definition")
        for name in ("product_ids", "gaps"):
            values = getattr(self, name)
            require(isinstance(values, tuple) and all(text(v) for v in values) and len(set(values)) == len(values), f"invalid_measurement_plan.{name}")
        require(bool(self.gaps), "measurement_plan_requires_gaps")
        for name in ("intended_source", "source_owner", "listing", "currency", "period", "baseline", "matching_approach", "attribution_assumptions"):
            require(getattr(self, name) is None or text(getattr(self, name)), f"invalid_measurement_plan.{name}")
        return {**asdict(self), "product_ids": list(self.product_ids), "gaps": list(self.gaps)}

    @classmethod
    def from_document(cls, document):
        """Reject outcome/actor fields; optional prerequisites remain unknown."""
        require(isinstance(document, dict) and document.keys() <= cls.__dataclass_fields__.keys(), "invalid_measurement_plan")
        for name in ("objective", "outcome_definition", "product_ids", "gaps"):
            require(name in document, f"invalid_measurement_plan.{name}")
        require(isinstance(document["product_ids"], list) and isinstance(document["gaps"], list), "invalid_measurement_plan")
        result = cls(**{**document, "product_ids": tuple(document["product_ids"]), "gaps": tuple(document["gaps"])})
        result.document()
        return result


@dataclass(frozen=True)
class DecisionNote:
    """Attributable human feedback, conservatively dependent on its shortlist support."""

    text: str
    support_ids: tuple[str, ...] = ()

    def document(self):
        require(text(self.text) and isinstance(self.support_ids, tuple) and all(text(s) for s in self.support_ids), "invalid_decision_note")
        return {"text": self.text, "support_ids": sorted(set(self.support_ids))}

    @classmethod
    def from_document(cls, document):
        require(isinstance(document, dict) and "text" in document and document.keys() <= {"text", "support_ids"}
                and isinstance(document.get("support_ids", []), list), "invalid_decision_note")
        result = cls(document["text"], tuple(document.get("support_ids", [])))
        result.document()
        return result
