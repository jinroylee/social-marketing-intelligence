"""Explicitly gated Bright Data TikTok keyword discovery."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

from ..http import open_no_redirect
from ..local import parse_time
from ...contracts import RawObservation, RunLimits, ExternalKey, FieldCandidate, MetricCandidate, NormalizedBatch, ObservationDraft, SourcePolicy, SourceReference

from ...contracts import CollectedBatch
from ...evidence import EvidenceError

ROUTE = 'brightdata-tiktok-keyword'
FORMAT = 'tiktok-posts-2026-10-23'
DATASET = 'gd_lu702nij2f790tmv9h'


@dataclass(frozen=True)
class LiveDiscoveryConfig:
    """Trusted process configuration; default construction authorizes no source I/O.

    Credentials are transient and excluded from repr and persisted task scope.
    Source-use authorization is separate from technical HTTP access.
    """

    enabled: bool = False
    operation_authorized: bool = False
    source_use_authorized: bool = False
    api_key: str | None = field(default=None, repr=False)
    profile_supplementation_authorized: bool = False

    def unavailable_reason(self) -> str | None:
        """Return the first unmet external prerequisite without disclosing secrets."""
        if self.enabled is not True:
            return 'live_discovery_disabled'
        if self.operation_authorized is not True:
            return 'live_operation_authorization_required'
        if self.source_use_authorized is not True:
            return 'live_source_use_authorization_required'
        if not isinstance(self.api_key, str) or not self.api_key.strip() or len(self.api_key) > 4096 or not self.api_key.isascii() or any(c.isspace() for c in self.api_key):
            return 'live_discovery_credentials_required'
        return None


class LiveDiscoveryUnavailable(RuntimeError):
    """A recoverable runtime prerequisite failed before HTTP dispatch."""

    def __init__(self, reason: str, *, retry_not_before: str | None = None):
        super().__init__(reason)
        self.retry_not_before = retry_not_before


class TikTokKeywordCollector:
    """Collect only through the explicitly configured route and gates."""

    def __init__(self, scope: dict[str, Any], config: LiveDiscoveryConfig, *,
                 cost_configured: bool = False, clock: Callable[[], datetime] | None = None):
        self.scope, self.config = scope, config
        self.cost_configured = cost_configured
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def require_available(self, manifest: dict[str, Any], checkpoint: dict[str, Any] | None = None) -> None:
        """Keep source-use policy independent of credential/transport access."""
        reason = self.config.unavailable_reason()
        if reason:
            raise LiveDiscoveryUnavailable(reason)
        policy = manifest.get('policy', {})
        if not all(policy.get(k) is True for k in ('can_process', 'can_retain')) or policy.get('revoked'):
            raise LiveDiscoveryUnavailable('source_policy_disallows_discovery')
        expires = parse_time(policy.get('expires_at'))
        if expires is not None:
            if expires <= datetime.now(timezone.utc):
                raise LiveDiscoveryUnavailable('source_policy_disallows_discovery')
        if not self.cost_configured:
            raise LiveDiscoveryUnavailable('live_discovery_cost_configuration_required')
        if checkpoint and checkpoint.get('not_before'):
            due = parse_time(checkpoint['not_before'])
            if due is None:
                raise EvidenceError('invalid_discovery_checkpoint')
            if self.clock() < due:
                raise LiveDiscoveryUnavailable('provider_retry_not_due', retry_not_before=due.isoformat())

    def collect(self, manifest: dict[str, Any], checkpoint: dict[str, Any], limits: RunLimits) -> CollectedBatch:
        """Perform one bounded HTTPS attempt or reopen the saved snapshot phase."""
        self.require_available(manifest, checkpoint)
        phase = checkpoint.get('phase', 'start')
        if phase not in {'start', 'progress', 'download'}:
            raise EvidenceError('invalid_discovery_checkpoint')
        step = checkpoint.get('step', 0)
        if type(step) is not int or not 0 <= step < 100:
            raise EvidenceError('invalid_discovery_checkpoint')
        headers = {'Authorization': 'Bearer ' + self.config.api_key, 'Content-Type': 'application/json'}
        if phase == 'start':
            body = json.dumps({'input': [{'search_keyword': self.scope['query'], 'num_of_posts': 1}], 'limit_per_input': 1}).encode()
            if len(body) > 8192:
                raise LiveDiscoveryUnavailable('live_discovery_request_too_large')
            request = Request('https://api.brightdata.com/datasets/v3/scrape?dataset_id=' + DATASET
                              + '&type=discover_new&discover_by=keyword&format=json&include_errors=true',
                              data=body, headers=headers, method='POST')
        else:
            snapshot = checkpoint.get('snapshot_id')
            if not isinstance(snapshot, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', snapshot) is None:
                raise EvidenceError('invalid_discovery_checkpoint')
            endpoint = 'progress/' if phase == 'progress' else 'snapshot/'
            request = Request('https://api.brightdata.com/datasets/v3/' + endpoint + snapshot
                              + ('?format=json' if phase == 'download' else ''), headers=headers, method='GET')
        following = {**checkpoint, 'step': step + 1}

        def wait(code='provider_operation_ambiguous', consumed=0):
            return CollectedBatch((), following, False, code, 1, consumed)

        cap = min(65_536, limits.max_bytes)
        try:
            with open_no_redirect(request, timeout=75) as response:
                status = response.status
                retry_after = response.headers.get('Retry-After', '10')
                raw = response.read(cap)
        except (HTTPError, URLError, OSError, TimeoutError):
            return wait()
        if len(raw) >= cap:
            return wait(consumed=len(raw))
        try:
            records = json.loads(raw)
        except (ValueError, UnicodeError, RecursionError):
            return wait(consumed=len(raw))
        if phase == 'start' and status == 202:
            snapshot = records.get('snapshot_id') if isinstance(records, dict) else None
            if not isinstance(snapshot, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', snapshot) is None:
                return wait(consumed=len(raw))
            following.update(phase='progress', snapshot_id=snapshot)
            if not isinstance(retry_after, str) or re.fullmatch(r'[0-9]{1,4}', retry_after) is None or not 1 <= int(retry_after) <= 3600:
                return wait(consumed=len(raw))
            following.update(not_before=(self.clock() + timedelta(seconds=int(retry_after))).isoformat())
            return wait('provider_pending', len(raw))
        if phase == 'download' and status == 202:
            if (not isinstance(records, dict) or not isinstance(records.get('status'), str)
                    or not 1 <= len(records['status']) <= 64 or not isinstance(retry_after, str)
                    or re.fullmatch(r'[0-9]{1,4}', retry_after) is None or not 1 <= int(retry_after) <= 3600):
                return wait(consumed=len(raw))
            following['not_before'] = (self.clock() + timedelta(seconds=int(retry_after))).isoformat()
            return wait('provider_pending', len(raw))
        if status != 200:
            return wait(consumed=len(raw))
        terminal = None
        if phase == 'progress':
            if (not isinstance(records, dict) or records.get('snapshot_id') != snapshot
                    or records.get('dataset_id') != DATASET or records.get('status') not in {'starting', 'running', 'ready', 'failed', 'canceled'}):
                return wait(consumed=len(raw))
            if records['status'] in {'failed', 'canceled'}:
                terminal = records['status']
            else:
                if not isinstance(retry_after, str) or re.fullmatch(r'[0-9]{1,4}', retry_after) is None or not 1 <= int(retry_after) <= 3600:
                    return wait(consumed=len(raw))
                following['phase'] = 'download' if records['status'] == 'ready' else 'progress'
                following['not_before'] = (self.clock() + timedelta(seconds=0 if records['status'] == 'ready' else int(retry_after))).isoformat()
                return wait('provider_pending', len(raw))
        if terminal:
            draft = self._draft(raw, manifest, {'outcome': 'snapshot_' + terminal, 'terminal_failure': terminal,
                'http_status': 200, 'http_attempts': 1, 'row_count': 0, 'returned_records': 0,
                'eligible_records': 0, 'failed_records': 0})
            return CollectedBatch((draft,), {'phase': 'completed'}, True)
        if not isinstance(records, list) or len(records) > 1:
            return wait(consumed=len(raw))
        if not records:
            return CollectedBatch((), {'phase': 'completed'}, True, request_attempts=1, response_bytes=len(raw))
        record = records[0]
        eligible = False
        selection = 'unassessable'
        if (isinstance(record, dict) and isinstance(record.get('description'), str)
                and isinstance(record.get('create_time'), str)):
            try:
                published = parse_time(record.get('create_time'))
                eligible = (published is not None and parse_time(self.scope['published_from']) <= published < parse_time(self.scope['published_before'])
                            and all(term in record['description'].casefold() for term in self.scope['query'].casefold().split()))
                if published is not None:
                    selection = 'matched' if eligible else 'outside_scope'
            except (ValueError, TypeError, EvidenceError):
                pass
        draft = self._draft(raw, manifest,
            {'outcome': 'ok', 'http_status': 200, 'http_attempts': 1, 'row_count': 1,
             'returned_records': 1, 'eligible_records': int(eligible), 'failed_records': int(selection == 'unassessable'),
             'capture_time': 'not_returned', 'retrieved_at': self.clock().isoformat(),
             'unavailable_fields': [name for name in ('post_id', 'profile_id', 'description', 'create_time',
                  'profile_username', 'play_count', 'digg_count', 'comment_count', 'collect_count')
                  if not isinstance(record, dict) or record.get(name) is None], 'market_coverage': 'unknown',
             'discovery': {**self.scope, 'selection_status': selection,
                           'method': 'brightdata-keyword-caption-time-v1', 'subject_basis': 'approved_context_only'}})
        return CollectedBatch((draft,), {'phase': 'completed'}, True)

    def _draft(self, raw, manifest, coverage):
        policy = manifest['policy']
        return ObservationDraft('keyword-result', ROUTE, 'brightdata', FORMAT, SourceReference('brightdata://tiktok/keyword'),
            raw, 'application/json', None, None,
            SourcePolicy(policy['context_id'], policy['can_process'], policy['can_retain'], policy['can_display'],
                         expires_at=parse_time(policy.get('expires_at')), revoked=policy.get('revoked', False)), False, coverage)


class TikTokKeywordMapper:
    """Map this route's versioned source schema, never a fixture namespace."""

    version = 'v1'

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        """Validate optional full fields without inventing identity, capture or metric times."""
        if observation.format_version != FORMAT or observation.synthetic:
            raise EvidenceError('unsupported_discovery_format')
        if observation.coverage.get('terminal_failure') in {'failed', 'canceled'}:
            raise EvidenceError('provider_snapshot_' + observation.coverage['terminal_failure'])
        record = json.loads(payload)[0]
        if observation.coverage['discovery']['selection_status'] == 'outside_scope':
            return NormalizedBatch((), (), ())
        if (not isinstance(record, dict) or observation.coverage['discovery']['selection_status'] != 'matched'
                or 'error' in record or 'error_code' in record):
            raise EvidenceError('discovery_selection_unassessable')
        post_id, profile_id = record.get('post_id'), record.get('profile_id')
        if (not isinstance(post_id, str) or re.fullmatch(r'[0-9]{1,30}', post_id) is None
                or not isinstance(profile_id, str) or re.fullmatch(r'[0-9]{1,30}', profile_id) is None):
            raise EvidenceError('discovery_native_identity_missing')
        handle = record.get('profile_username')
        url = record.get('url')
        if not isinstance(url, str) or re.fullmatch(r'https://www\.tiktok\.com/@[A-Za-z0-9._]{1,64}/video/' + post_id, url) is None:
            raise EvidenceError('discovery_identity_conflict')
        if handle is not None and (not isinstance(handle, str) or re.fullmatch(r'[A-Za-z0-9._]{1,64}', handle) is None):
            raise EvidenceError('discovery_identity_conflict')
        if handle is not None and url.split('/')[3] != '@' + handle:
            raise EvidenceError('discovery_identity_conflict')
        post = ExternalKey('tiktok', 'brightdata:tiktok-posts', 'content', post_id)
        account = ExternalKey('tiktok', 'brightdata:tiktok-posts', 'account', profile_id)
        fields = [FieldCandidate(account, 'handle', 'observed' if handle else 'not_returned', handle, '$[0].profile_username'),
                  FieldCandidate(post, 'author_account', 'observed', {'platform': account.platform, 'namespace': account.namespace,
                      'kind': account.kind, 'native_id': account.native_id}, '$[0].profile_id'),
                  FieldCandidate(post, 'caption', 'observed', record['description'], '$[0].description'),
                  FieldCandidate(post, 'published_at', 'observed', record['create_time'], '$[0].create_time')]
        metrics = []
        for name in ('play_count', 'digg_count', 'comment_count', 'collect_count'):
            value = record.get(name)
            if value is None:
                fields.append(FieldCandidate(post, 'metric:' + name, 'not_returned', None, '$[0].' + name))
            elif type(value) is not int or value < 0:
                raise EvidenceError('invalid_discovery_metric')
            else:
                metrics.append(MetricCandidate(post, 'brightdata.tiktok.' + name + '.v1', name, value, str(value),
                                               'exact', 'count', None, '$[0].' + name))
        return NormalizedBatch((account, post), tuple(fields), tuple(metrics))
