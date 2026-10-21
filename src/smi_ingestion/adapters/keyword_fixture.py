"""Deterministic bounded query discovery over a pinned synthetic source response."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import json
from pathlib import Path
from typing import Any

from ..contracts import CollectedBatch, ObservationDraft, RunLimits, SourcePolicy, RawObservation, NormalizedBatch
from ..evidence import EvidenceError
from ..references import parse_reference
from .json_fixture import JsonFixtureMapper
from .local import parse_time

ROUTE = 'offline-keyword-json'
METHOD = 'literal-caption-subject-time-v1'


def validate_keyword_scope(scope: dict[str, Any]) -> None:
    """Require one literal all-term query, explicit subjects and a finite UTC-aware window."""
    try:
        if set(scope) != {'query', 'subject_ids', 'published_from', 'published_before'}:
            raise ValueError
        query, subjects = scope['query'], scope['subject_ids']
        if (not isinstance(query, str) or not query.strip() or len(query) > 500
                or not isinstance(subjects, list) or not 1 <= len(subjects) <= 30
                or any(not isinstance(s, str) or not s.strip() or len(s) > 500 for s in subjects)
                or len(set(subjects)) != len(subjects)):
            raise ValueError
        if any(not isinstance(scope[key], str) or len(scope[key]) > 100 for key in ('published_from', 'published_before')):
            raise ValueError
        start, end = parse_time(scope['published_from']), parse_time(scope['published_before'])
        if start is None or end is None or not timedelta(0) < end - start <= timedelta(days=366):
            raise ValueError
    except (TypeError, ValueError, AttributeError, EvidenceError) as error:
        raise EvidenceError('invalid_keyword_discovery_scope') from error


class KeywordFixtureMapper(JsonFixtureMapper):
    """Map source-shaped fixture fields in their own stable source namespace."""

    namespace = 'offline-keyword:public'

    def normalize(self, observation: RawObservation, payload: bytes) -> NormalizedBatch:
        """Quarantine unassessable source selection before canonical mapping."""
        if observation.coverage.get('discovery', {}).get('selection_status') == 'unassessable':
            raise EvidenceError('discovery_selection_unassessable')
        return super().normalize(observation, payload)


class KeywordFixtureCollector:
    """Select a single deterministic source page per simulated request, with no network.

    The immutable task supplies scope; source data cannot choose query or authority.
    A pinned corpus has at most 100 records and 1 MiB. All caption terms, any exact
    supplied subject, and the half-open publication window must match. Missing
    selection fields produce quarantined evidence rather than inferred relevance or time.
    """

    def __init__(self, scope: dict[str, Any], route_version: str):
        validate_keyword_scope(scope)
        self.scope, self.route_version = scope, route_version

    def collect(self, manifest: dict[str, Any], checkpoint: dict[str, Any], limits: RunLimits) -> CollectedBatch:
        if manifest.get('adapter') != ROUTE or manifest.get('synthetic') is not True:
            raise EvidenceError('unsupported_task_route')
        base = Path(manifest['_base']).resolve()
        path = (base / manifest['response_path']).resolve()
        if not path.is_relative_to(base):
            raise EvidenceError('input_outside_manifest_directory')
        if path.stat().st_size > 1_048_576:
            raise EvidenceError('discovery_response_limit_reached')
        with path.open('rb') as source:
            raw = source.read(1_048_577)
        if len(raw) > 1_048_576:
            raise EvidenceError('discovery_response_limit_reached')
        if hashlib.sha256(raw).hexdigest() != manifest['response_sha256']:
            raise EvidenceError('discovery_response_changed')
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError) as error:
            raise EvidenceError('invalid_discovery_response') from error
        if not isinstance(data, dict) or not isinstance(data.get('records'), list) or len(data['records']) > 100:
            raise EvidenceError('invalid_discovery_response')
        start, end = parse_time(self.scope['published_from']), parse_time(self.scope['published_before'])
        selected = []
        unassessable = 0
        for index, record in enumerate(data['records']):
            video = record.get('video') if isinstance(record, dict) else None
            if not isinstance(video, dict):
                selected.append((index, record, 'unassessable'))
                unassessable += 1
                continue
            subjects = record.get('subjects')
            caption = video.get('caption')
            try:
                published = parse_time(video.get('published_at'))
            except (EvidenceError, ValueError, TypeError, AttributeError):
                published = None
            if (not isinstance(caption, str) or not isinstance(subjects, list) or not subjects
                    or any(not isinstance(subject, str) or not subject.strip() for subject in subjects)
                    or published is None):
                selected.append((index, record, 'unassessable'))
                unassessable += 1
                continue
            if (any(s in subjects for s in self.scope['subject_ids'])
                    and all(term in caption.casefold() for term in self.scope['query'].casefold().split())
                    and published is not None and start <= published < end):
                selected.append((index, record, 'matched'))
        position = checkpoint.get('position', 0)
        if type(position) is not int or not 0 <= position <= len(selected):
            raise EvidenceError('invalid_discovery_checkpoint')
        if position == len(selected):
            return CollectedBatch((), {'position': position}, True, request_attempts=1)
        source_index, record, selection_status = selected[position]
        source_record = record if isinstance(record, dict) else {}
        payload = json.dumps(record, sort_keys=True).encode()
        if len(payload) > limits.max_bytes:
            raise EvidenceError('byte_limit_reached')
        policy = manifest['policy']
        draft = ObservationDraft(
            source_item_key=f'record:{source_index}', adapter_id=ROUTE,
            provider_id=manifest['provider_id'], format_version=manifest['format_version'],
            reference=parse_reference(source_record.get('reference', '') if isinstance(source_record.get('reference', ''), str) else ''), payload=payload, media_type='application/json',
            captured_at=parse_time(source_record.get('captured_at')), source_as_of=parse_time(source_record.get('source_as_of')),
            policy=SourcePolicy(policy['context_id'], policy['can_process'], policy['can_retain'], policy['can_display'],
                                expires_at=parse_time(policy.get('expires_at')), revoked=policy.get('revoked', False)),
            synthetic=True,
            coverage={'requested_input': 1, 'truncated': False, 'market_coverage': 'unknown',
                      'discovery': {**self.scope, 'route': ROUTE, 'route_version': self.route_version,
                                    'response_sha256': manifest['response_sha256'], 'source_position': source_index + 1,
                                    'selection_position': position + 1, 'selection_status': selection_status,
                                    'matching_records': len(selected) - unassessable, 'unassessable_records': unassessable,
                                    'corpus_records': len(data['records']), 'priority': 'source_response_order', 'method': METHOD}})
        return CollectedBatch((draft,), {'position': position + 1}, position + 1 == len(selected))
