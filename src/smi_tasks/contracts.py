"""Supplied proposals and operator-owned offline capabilities and origin authority."""

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
from typing import Any

from smi_ingestion.contracts import RunLimits
from smi_ingestion.adapters.keyword_fixture import ROUTE, validate_keyword_scope
from smi_ingestion.adapters.tiktok_keyword import ROUTE as LIVE_ROUTE, FORMAT
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from .discovery import DiscoveryPolicy


@dataclass(frozen=True)
class OfflineRoute:
    """Operator-selected source manifest and hard bounds; live execution needs separate gates."""

    manifest_path: Path
    version: str = 'offline-fixture-v1'
    limits: RunLimits = RunLimits(max_requests=10, max_pages=10, max_records=10)
    discovery_policy: DiscoveryPolicy | None = None

    def discovery_configuration(self, manifest: dict[str, Any]) -> dict[str, Any]:
        """Pin input identity and explicit policy on newly admitted discovery only."""
        result = {'discovery_context': {'response_sha256': manifest.get('response_sha256'),
                  'provider_id': manifest.get('provider_id'), 'format_version': manifest.get('format_version')}}
        if self.discovery_policy is not None:
            result['discovery_policy'] = asdict(self.discovery_policy)
        return result

    def validate(self) -> None:
        """Validate immutable operator version and hard limits without touching input files."""
        if self.discovery_policy is not None:
            if not isinstance(self.discovery_policy, DiscoveryPolicy):
                raise EvidenceError('invalid_discovery_policy')
            self.discovery_policy.validate()
        if (not isinstance(self.version, str) or not self.version.strip() or len(self.version) > 100
                or not isinstance(self.limits, RunLimits)):
            raise EvidenceError('invalid_offline_route')
        if any(type(v) is not int or not 1 <= v <= bound for v, bound in (
            (self.limits.max_requests, 100), (self.limits.max_pages, 100),
            (self.limits.max_records, 100), (self.limits.max_bytes, 10_485_760),
        )):
            raise EvidenceError('invalid_task_limits')

    def capability(self) -> dict[str, Any]:
        """Report configured query capability without pretending supplied references are a search."""
        _, _, manifest = self.snapshot()
        discovery = manifest['adapter'] in {ROUTE, LIVE_ROUTE}
        return {'route': manifest['adapter'], 'query_discovery': discovery,
                'method': 'brightdata-keyword-caption-time-v1' if manifest['adapter'] == LIVE_ROUTE else 'literal-caption-subject-time-v1' if discovery else 'supplied-reference-fixture-v1',
                'unavailable_reason': None if discovery else 'keyword_discovery_unavailable_supplied_reference_route'}

    def snapshot(self) -> tuple[Path, str, dict[str, Any]]:
        """Validate configuration without reading payloads or performing collection."""
        self.validate()
        path = self.manifest_path.resolve()
        try:
            if path.stat().st_size > 1_048_576:
                raise EvidenceError('invalid_offline_route')
            raw = path.read_bytes()
            manifest = json.loads(raw)
            if (not isinstance(manifest, dict) or manifest.get('adapter') not in {'fixture-json', ROUTE, LIVE_ROUTE}
                    or manifest.get('synthetic') is not (manifest.get('adapter') != LIVE_ROUTE)):
                raise EvidenceError('unsupported_task_route')
            if manifest['adapter'] == LIVE_ROUTE:
                if (manifest.get('provider_id') != 'brightdata' or manifest.get('format_version') != FORMAT
                        or set(manifest) != {'adapter', 'provider_id', 'format_version', 'synthetic', 'policy'}
                        or not isinstance(manifest.get('policy'), dict)):
                    raise EvidenceError('invalid_live_discovery_route')
                policy = manifest['policy']
                if (not isinstance(policy.get('context_id'), str) or not policy['context_id'].strip() or len(policy['context_id']) > 200
                        or not {'context_id', 'can_process', 'can_retain', 'can_display'} <= policy.keys()
                        or not policy.keys() <= {'context_id', 'can_process', 'can_retain', 'can_display', 'expires_at', 'revoked'}
                        or any(type(policy[k]) is not bool for k in ('can_process', 'can_retain', 'can_display'))
                        or type(policy.get('revoked', False)) is not bool
                        or policy.get('expires_at') is not None and not isinstance(policy['expires_at'], str)):
                    raise EvidenceError('invalid_live_discovery_route')
                from smi_ingestion.adapters.local import parse_time
                parse_time(policy.get('expires_at'))
                return path, hashlib.sha256(raw).hexdigest(), manifest
            if manifest['adapter'] == ROUTE:
                if (not isinstance(manifest.get('response_path'), str) or not manifest['response_path']
                        or not isinstance(manifest.get('response_sha256'), str)
                        or len(manifest['response_sha256']) != 64
                        or any(c not in '0123456789abcdef' for c in manifest['response_sha256'])):
                    raise EvidenceError('invalid_offline_route')
                return path, hashlib.sha256(raw).hexdigest(), manifest
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
    schedule_operators: frozenset[str] = frozenset()
    schedule_automations: frozenset[str] = frozenset()

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


    def require_schedule_operator(self, actor: ActorContext) -> None:
        """Only an operator-configured human may change registered keyword authority."""
        if actor.kind != 'human' or actor.actor_id not in self.schedule_operators:
            raise EvidenceError('schedule_operator_authority_required')

    def require_schedule_tick(self, actor: ActorContext) -> None:
        """Tick authority is a configured human operator or an exact scheduled service."""
        allowed = self.schedule_operators if actor.kind == 'human' else self.schedule_automations
        if actor.actor_id not in allowed:
            raise EvidenceError('schedule_tick_authority_required')


@dataclass(frozen=True)
class EnrichmentProposal:
    """Supplied purpose and bounded on-demand scope; saving this grants no authority."""

    purpose: str
    intent: str
    subject_ids: tuple[str, ...] = ()
    search_queries: tuple[str, ...] = ()
    published_from: str | None = None
    published_before: str | None = None

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
        if self.published_from is not None or self.published_before is not None:
            self.keyword_scope()
        if not self.subject_ids and not self.search_queries:
            raise EvidenceError('invalid_enrichment_proposal')

    def keyword_scope(self) -> dict[str, Any]:
        """Resolve the explicit discovery selection without deriving query scope from prose."""
        if len(self.search_queries) != 1:
            raise EvidenceError('invalid_keyword_discovery_scope')
        scope = {'query': self.search_queries[0], 'subject_ids': list(self.subject_ids),
                 'published_from': self.published_from, 'published_before': self.published_before}
        validate_keyword_scope(scope)
        return scope

    def document(self) -> dict[str, Any]:
        """Keep legacy supplied-reference scope serialization and digests stable."""
        result = {'purpose': self.purpose, 'intent': self.intent,
                  'subject_ids': self.subject_ids, 'search_queries': self.search_queries}
        if self.published_from is not None or self.published_before is not None:
            result.update(published_from=self.published_from, published_before=self.published_before)
        return result

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> 'EnrichmentProposal':
        """Parse supplied JSON scope, rejecting authority fields rather than trusting them."""
        if (not isinstance(document, dict) or not document.keys() <= {'purpose', 'intent', 'subject_ids', 'search_queries', 'published_from', 'published_before'}
                or not all(isinstance(document.get(k, []), list) for k in ('subject_ids', 'search_queries'))):
            raise EvidenceError('invalid_enrichment_proposal')
        proposal = cls(document.get('purpose'), document.get('intent'),
                       tuple(document.get('subject_ids', [])), tuple(document.get('search_queries', [])),
                       document.get('published_from'), document.get('published_before'))
        proposal.validate()
        return proposal


def execution_configuration_digest(scope: dict[str, Any], limits: dict[str, int], manifest_path: str) -> str:
    """Pin discovery selection and operator bounds while preserving legacy fixture hashes."""
    return hashlib.sha256(json.dumps({'scope': scope, 'limits': limits, 'manifest_path': manifest_path}, sort_keys=True).encode()).hexdigest()
