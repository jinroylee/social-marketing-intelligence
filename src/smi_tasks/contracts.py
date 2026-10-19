"""Supplied proposals and operator-owned offline route and origin authority."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from smi_ingestion.contracts import RunLimits
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext


@dataclass(frozen=True)
class OfflineRoute:
    """Operator-selected synthetic fixture input and hard execution bounds."""

    manifest_path: Path
    version: str = 'offline-fixture-v1'
    limits: RunLimits = RunLimits(max_requests=10, max_pages=10, max_records=10)

    def snapshot(self) -> tuple[Path, str, dict[str, Any]]:
        """Validate configuration without reading payloads or performing collection."""
        if (not isinstance(self.version, str) or not self.version.strip() or len(self.version) > 100
                or not isinstance(self.limits, RunLimits)):
            raise EvidenceError('invalid_offline_route')
        if any(type(v) is not int or not 1 <= v <= bound for v, bound in (
            (self.limits.max_requests, 100), (self.limits.max_pages, 100),
            (self.limits.max_records, 100), (self.limits.max_bytes, 10_485_760),
        )):
            raise EvidenceError('invalid_task_limits')
        path = self.manifest_path.resolve()
        try:
            if path.stat().st_size > 1_048_576:
                raise EvidenceError('invalid_offline_route')
            raw = path.read_bytes()
            manifest = json.loads(raw)
            if (not isinstance(manifest, dict) or manifest.get('adapter') != 'fixture-json'
                    or manifest.get('synthetic') is not True):
                raise EvidenceError('unsupported_task_route')
            items = manifest.get('items')
            if (not isinstance(items, list) or len(items) > 100
                    or any(not isinstance(item, dict) or not isinstance(item.get('path'), str)
                           or not isinstance(item.get('reference', ''), str) for item in items)):
                raise EvidenceError('invalid_offline_route')
        except (OSError, ValueError, TypeError) as error:
            raise EvidenceError('invalid_offline_route') from error
        return path, hashlib.sha256(raw).hexdigest(), manifest


@dataclass(frozen=True)
class TaskAuthority:
    """Operator configuration, never populated from assistant or form content.

    Identities are local trusted principals, not hosted authentication. Give an
    assistant only proposal submission; campaign automation is a separate role.
    """

    campaign_humans: frozenset[str] = frozenset()
    campaign_automations: frozenset[str] = frozenset()
    proposal_approvers: frozenset[str] = frozenset()

    @classmethod
    def for_human(cls, actor_id: str) -> 'TaskAuthority':
        """Configure the named local CLI/server human for campaign and approval actions."""
        return cls(campaign_humans=frozenset({actor_id}), proposal_approvers=frozenset({actor_id}))

    def require_campaign(self, actor: ActorContext) -> None:
        """Deny campaign admission unless the operator assigned this exact role."""
        allowed = self.campaign_humans if actor.kind == 'human' else self.campaign_automations
        if actor.actor_id not in allowed:
            raise EvidenceError('campaign_task_authority_required')

    def require_approver(self, actor: ActorContext) -> None:
        """A submitted human label alone never grants proposal approval authority."""
        if actor.kind != 'human' or actor.actor_id not in self.proposal_approvers:
            raise EvidenceError('proposal_human_approval_required')


@dataclass(frozen=True)
class EnrichmentProposal:
    """Supplied purpose and bounded on-demand scope; saving this grants no authority."""

    purpose: str
    intent: str
    subject_ids: tuple[str, ...] = ()
    search_queries: tuple[str, ...] = ()

    def validate(self) -> None:
        """Reject ambiguous or unbounded proposal metadata before persistence."""
        if (not isinstance(self.purpose, str) or not self.purpose.strip() or len(self.purpose) > 1000
                or not isinstance(self.intent, str) or self.intent not in {'refresh', 'fill', 'expansion'}):
            raise EvidenceError('invalid_enrichment_proposal')
        for values in (self.subject_ids, self.search_queries):
            if (not isinstance(values, tuple) or len(values) > 30
                    or any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in values)
                    or len(set(values)) != len(values)):
                raise EvidenceError('invalid_enrichment_proposal')
        if not self.subject_ids and not self.search_queries:
            raise EvidenceError('invalid_enrichment_proposal')

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> 'EnrichmentProposal':
        """Parse supplied JSON scope, rejecting authority fields rather than trusting them."""
        if (not isinstance(document, dict) or not document.keys() <= {'purpose', 'intent', 'subject_ids', 'search_queries'}
                or not all(isinstance(document.get(k, []), list) for k in ('subject_ids', 'search_queries'))):
            raise EvidenceError('invalid_enrichment_proposal')
        proposal = cls(document.get('purpose'), document.get('intent'),
                       tuple(document.get('subject_ids', [])), tuple(document.get('search_queries', [])))
        proposal.validate()
        return proposal
