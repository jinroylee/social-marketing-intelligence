"""The small, provider-independent interface between ingestion modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class SourceReference:
    original: str
    platform: str | None = None
    resource_kind: str | None = None
    native_id_hint: str | None = None
    handle_hint: str | None = None


@dataclass(frozen=True)
class ExternalKey:
    platform: str
    namespace: str
    kind: str
    native_id: str


@dataclass(frozen=True)
class SourcePolicy:
    context_id: str
    can_process: bool
    can_retain: bool
    can_display: bool
    expires_at: datetime | None = None
    revoked: bool = False


@dataclass(frozen=True)
class ObservationDraft:
    source_item_key: str
    adapter_id: str
    provider_id: str
    format_version: str
    reference: SourceReference
    payload: bytes
    media_type: str
    captured_at: datetime | None
    source_as_of: datetime | None
    policy: SourcePolicy
    synthetic: bool
    coverage: dict[str, Any] = field(default_factory=dict)
    request_attempts: int = 1  # File reads count once; network adapters include retries.


@dataclass(frozen=True)
class CollectedBatch:
    items: tuple[ObservationDraft, ...]
    next_checkpoint: dict[str, Any]
    complete: bool


@dataclass(frozen=True)
class RawObservation:
    id: str
    run_id: str
    source_item_key: str
    adapter_id: str
    provider_id: str
    format_version: str
    reference: SourceReference
    media_type: str
    captured_at: datetime | None
    source_as_of: datetime | None
    ingested_at: datetime
    policy: SourcePolicy
    synthetic: bool
    payload_hash: str
    payload_path: str | None
    coverage: dict[str, Any]


@dataclass(frozen=True)
class FieldCandidate:
    subject: ExternalKey
    field: str
    state: str  # observed, not_returned, unavailable, removed
    value: Any
    locator: str
    reason: str | None = None


@dataclass(frozen=True)
class MetricCandidate:
    subject: ExternalKey
    definition: str
    native_name: str
    value: int | float | None
    raw_display: str | None
    precision: str  # exact or approximate
    unit: str
    measured_at: datetime | None
    locator: str


@dataclass(frozen=True)
class UnresolvedCandidate:
    kind: str
    locator: str
    reason: str


@dataclass(frozen=True)
class NormalizedBatch:
    entities: tuple[ExternalKey, ...]
    fields: tuple[FieldCandidate, ...]
    metrics: tuple[MetricCandidate, ...]
    issues: tuple[str, ...] = ()
    unresolved: tuple[UnresolvedCandidate, ...] = ()


@dataclass(frozen=True)
class RunLimits:
    max_requests: int = 10
    max_pages: int = 10
    max_records: int = 100
    max_bytes: int = 1_048_576

    def validate(self) -> None:
        if min(self.max_requests, self.max_pages, self.max_records, self.max_bytes) < 1:
            raise ValueError("All run limits must be positive")


class Collector(Protocol):
    def collect(
        self, manifest: dict[str, Any], checkpoint: dict[str, Any], limits: RunLimits
    ) -> CollectedBatch: ...


class Mapper(Protocol):
    version: str

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch: ...
