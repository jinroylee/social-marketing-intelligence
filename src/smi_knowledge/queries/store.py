"""Search committed publications; retain exact IDs without copying source facts."""

from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext
from smi_ingestion.support import IngestedEvidence, SupportReference

from ..publications import KnowledgePublications


@dataclass(frozen=True)
class QueryScope:
    """Literal text and platform scope; empty filters admit bounded published support."""

    text: str = ''
    platforms: tuple[str, ...] = ()
    subject_ids: tuple[str, ...] = ()
    captured_from: str | None = None
    captured_to: str | None = None
    max_age_seconds: int | None = None
    limit: int = 100

    def __post_init__(self):
        if (not isinstance(self.text, str) or len(self.text) > 500
                or not isinstance(self.platforms, tuple) or len(self.platforms) > 10
                or any(not isinstance(p, str) or not p or len(p) > 100 for p in self.platforms)
                or type(self.limit) is not int or not 1 <= self.limit <= 100):
            raise EvidenceError('invalid_knowledge_query_scope')
        try:
            if not isinstance(self.subject_ids, tuple) or len(self.subject_ids) > 20:
                raise ValueError
            for identity in self.subject_ids:
                if str(uuid.UUID(identity)) != identity:
                    raise ValueError
            if any(value is not None and (not isinstance(value, str) or not value) for value in (self.captured_from, self.captured_to)):
                raise ValueError
            start = _timestamp(self.captured_from) if self.captured_from else None
            end = _timestamp(self.captured_to) if self.captured_to else None
            if start and end and start >= end:
                raise ValueError
            if self.max_age_seconds is not None and (type(self.max_age_seconds) is not int or not 0 <= self.max_age_seconds <= 2**53 - 1):
                raise ValueError
        except (ValueError, TypeError, AttributeError) as error:
            raise EvidenceError('invalid_knowledge_query_scope') from error

    def document(self) -> dict[str, Any]:
        """Return the JSON-compatible, immutable query description."""
        return json.loads(json.dumps(asdict(self)))


def _timestamp(value):
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError('timezone_required')
    return timestamp


def _freshness(member, max_age_seconds, now):
    if member['availability'] != 'available':
        return {'state': 'unknown', 'reason': 'source_support_unavailable'}
    if max_age_seconds is None:
        return {'state': 'not_assessed', 'reason': 'freshness_threshold_not_configured'}
    if member['captured_at'] is None:
        return {'state': 'unknown', 'reason': 'capture_time_unknown', 'basis': 'source_capture'}
    age = (now - _timestamp(member['captured_at'])).total_seconds()
    if age < 0:
        return {'state': 'unknown', 'reason': 'capture_time_in_future', 'basis': 'source_capture'}
    return {'state': 'fresh' if age <= max_age_seconds else 'stale', 'basis': 'source_capture',
            'age_seconds': int(age), 'max_age_seconds': max_age_seconds}


def _contains_text(value, text):
    if isinstance(value, dict):
        return any(_contains_text(item, text) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_text(item, text) for item in value)
    return value is not None and text in str(value).casefold()


def _matches(member, claims, scope):
    assertions = member['assertions']
    if scope.platforms and not any(a['platform'] in scope.platforms for a in assertions + member['metrics']):
        return False
    if scope.subject_ids and not any(a['subject_id'] in scope.subject_ids for a in assertions + member['metrics']):
        return False
    if scope.captured_from or scope.captured_to:
        if member['captured_at'] is None:
            return False
        captured = _timestamp(member['captured_at'])
        if scope.captured_from and captured < _timestamp(scope.captured_from):
            return False
        if scope.captured_to and captured >= _timestamp(scope.captured_to):
            return False
    values = [a['value'] for a in assertions if a['state'] == 'observed']
    values.extend(a['native_id'] for a in assertions + member['metrics'])
    values.extend(c['value'] for c in claims)
    return not scope.text or _contains_text(values, scope.text.casefold())


def _unknowns(member, claims):
    unknowns = [a['field'] + ':' + a['state'] for a in member.get('assertions', []) if a['state'] != 'observed']
    coverage = member.get('coverage', {})
    declared_missing = coverage.get('unavailable_fields', []) if isinstance(coverage, dict) else []
    if isinstance(declared_missing, list):
        unknowns.extend(field for field in declared_missing if isinstance(field, str))
    if member['availability'] == 'available' and member.get('source_as_of') is None:
        unknowns.append('source_as_of_unknown')
    if not claims:
        unknowns.append('caption_interpretations_not_published')
    return unknowns


class KnowledgeQueries:
    """Materialize bounded current-KB selections and reopen their immutable support."""

    method_version = 'published-literal-query-v1'
    publication_limit = 100

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db = db
        self.workspace_id = workspace_id
        self.publications = KnowledgePublications(db, workspace_id)

    def migrate(self) -> None:
        """Install knowledge-owned result manifests after ingestion migrations."""
        self.publications.migrate()

    def search(self, scope: QueryScope, actor: ActorContext, *, request_id: str,
               purpose: Literal['display', 'process'] = 'display', include_synthetic: bool = False, connection=None) -> dict[str, Any]:
        """Pin the actual permitted selection; same producer/request retries stay exact."""
        actor.require_workspace(self.workspace_id)
        if purpose not in {'display', 'process'}:
            raise EvidenceError('invalid_evidence_purpose')
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200:
            raise EvidenceError('invalid_knowledge_query_request_id')
        document = {'scope': scope.document(), 'purpose': purpose, 'include_synthetic': include_synthetic,
                    'producer': {'actor_id': actor.actor_id, 'kind': actor.kind}, 'method_version': self.method_version}
        digest = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'knowledge-query:{self.workspace_id}:{request_id}',))
            existing = connection.execute('SELECT id,request_digest FROM knowledge_query_results WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            if existing:
                if existing['request_digest'] != digest:
                    raise EvidenceError('knowledge_query_request_conflict')
                result_id = str(existing['id'])
            else:
                self.publications.lock_current(actor, connection=connection)
                result_id = str(uuid.uuid4())
                queried_at = datetime.now(timezone.utc)
                publications = self.publications.list(actor, include_synthetic=include_synthetic,
                                                      limit=self.publication_limit + 1, newest_first=True, connection=connection)
                coverage = {'scope': 'bounded_committed_publications', 'publications_scanned': min(len(publications), self.publication_limit),
                            'publication_limit': self.publication_limit, 'publication_limit_reached': len(publications) > self.publication_limit,
                            'unavailable_members': 0, 'process_denied_members': 0, 'superseded_members': 0, 'stale_members': 0, 'fresh_members': 0, 'freshness_unknown_members': 0, 'matched_members': 0, 'result_limit_reached': False}
                selected = []
                seen = set()
                for metadata in publications[:self.publication_limit]:
                    process_publication = self.publications.read(metadata['publication_id'], actor, purpose='process',
                                                                 include_synthetic=include_synthetic, connection=connection)
                    publication = process_publication if purpose == 'process' else self.publications.read(
                        metadata['publication_id'], actor, purpose=purpose, include_synthetic=include_synthetic, connection=connection)
                    process_members = {m['observation_id']: m for m in process_publication['members']}
                    process_claim_ids = {c['id'] for c in process_publication['interpretations'] if c['state'] == 'supported'}
                    for member in publication['members']:
                        process_member = process_members[member['observation_id']]
                        if process_member['availability'] != 'available':
                            coverage['process_denied_members'] += 1
                            coverage['unavailable_members'] += 1
                            continue
                        if member['availability'] != 'available':
                            coverage['unavailable_members'] += 1
                            continue
                        if member['support_status'] != 'current':
                            coverage['superseded_members'] += 1
                            continue
                        claims = [c for c in publication['interpretations'] if c['observation_id'] == member['observation_id'] and c['state'] == 'supported' and c['id'] in process_claim_ids]
                        if not _matches(member, claims, scope):
                            continue
                        identity = (member['observation_id'], member['derivation_id'], tuple(member['assertion_ids']), tuple(member['metric_ids']), tuple(c['id'] for c in claims))
                        if identity in seen:
                            continue
                        seen.add(identity)
                        if len(selected) == scope.limit:
                            coverage['result_limit_reached'] = True
                            continue
                        versions = {'selected_freshness': _freshness(member, scope.max_age_seconds, queried_at), 'method': member['method'], 'publication_method': publication['method_version'],
                                    'publication_time': publication['published_at'], 'publication_producer': publication['producer'],
                                    'interpretations': [{'id': c['id'], 'run_id': c['run_id'], 'method_version': c['method_version'], 'catalog_id': c['catalog_id']} for c in claims]}
                        selected.append((publication['publication_id'], member, claims, versions))
                coverage['matched_members'] = len(selected)
                for _, _, _, versions in selected:
                    state = versions['selected_freshness']['state']
                    coverage[{'stale': 'stale_members', 'fresh': 'fresh_members'}.get(state, 'freshness_unknown_members')] += 1
                unknowns = ['not_complete_market_coverage']
                if not selected:
                    unknowns.append('no_matching_permitted_published_support')
                connection.execute('INSERT INTO knowledge_query_results(id,workspace_id,request_id,request_digest,method_version,query_scope,purpose,synthetic,producer_id,producer_kind,coverage,unknowns,queried_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (result_id, self.workspace_id, request_id, digest, self.method_version, Jsonb(scope.document()), purpose,
                                    any(m['synthetic'] for _, m, _, _ in selected), actor.actor_id, actor.kind, Jsonb(coverage), Jsonb(unknowns), queried_at))
                for position, (publication_id, member, claims, versions) in enumerate(selected):
                    connection.execute('INSERT INTO knowledge_query_members(result_id,position,publication_id,observation_id,derivation_id,assertion_ids,metric_ids,interpretation_ids,versions) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                       (result_id, position, publication_id, member['observation_id'], member['derivation_id'],
                                        list(member['assertion_ids']), list(member['metric_ids']), [c['id'] for c in claims], Jsonb(versions)))
            return self.read(result_id, actor, purpose=purpose, include_synthetic=include_synthetic, connection=connection)

    def read(self, result_id: str, actor: ActorContext, *, purpose: Literal['display', 'process'] = 'display',
             include_synthetic: bool = False, connection=None) -> dict[str, Any]:
        """Reopen exact actual support under current purpose policy, never rerunning search."""
        actor.require_workspace(self.workspace_id)
        if purpose not in {'display', 'process'}:
            raise EvidenceError('invalid_evidence_purpose')
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            row = connection.execute('SELECT * FROM knowledge_query_results WHERE id=%s AND workspace_id=%s', (result_id, self.workspace_id)).fetchone()
            if row is None:
                raise EvidenceError('knowledge_query_result_not_found')
            if row['synthetic'] and not include_synthetic:
                raise EvidenceError('synthetic_evidence_excluded')
            rows = connection.execute('SELECT * FROM knowledge_query_members WHERE result_id=%s ORDER BY position', (result_id,)).fetchall()
            manifest, members, interpretations, cache = [], [], [], {}
            for selected in rows:
                publication_id = str(selected['publication_id'])
                if publication_id not in cache:
                    cache[publication_id] = self.publications.read(publication_id, actor, purpose=purpose,
                                                                  include_synthetic=include_synthetic, connection=connection)
                publication = cache[publication_id]
                member = next(m for m in publication['members'] if m['observation_id'] == str(selected['observation_id']))
                claim_ids = {str(i) for i in selected['interpretation_ids']}
                claims = [c for c in publication['interpretations'] if c['id'] in claim_ids]
                reference = {'publication_id': publication_id, 'observation_id': str(selected['observation_id']),
                             'derivation_id': str(selected['derivation_id']), 'assertion_ids': [str(i) for i in selected['assertion_ids']],
                             'metric_ids': [str(i) for i in selected['metric_ids']], 'interpretation_ids': [str(i) for i in selected['interpretation_ids']], **selected['versions']}
                manifest.append(reference)
                members.append({**member, 'assertion_ids': reference['assertion_ids'], 'metric_ids': reference['metric_ids'], 'publication_id': publication_id, 'freshness': _freshness(member, row['query_scope']['max_age_seconds'], datetime.now(timezone.utc)),
                                'unknowns': _unknowns(member, claims)})
                interpretations.extend(claims)
        return {'result_id': result_id, 'workspace_id': self.workspace_id, 'scope': row['query_scope'], 'purpose': row['purpose'],
                'read_purpose': purpose, 'queried_at': row['queried_at'].isoformat(), 'method_version': row['method_version'],
                'producer': {'actor_id': row['producer_id'], 'kind': row['producer_kind']}, 'coverage': row['coverage'],
                'unknowns': row['unknowns'], 'manifest': manifest, 'members': members, 'interpretations': interpretations,
                'current_coverage': {'available_members': sum(m['availability'] == 'available' for m in members),
                                     'unavailable_members': sum(m['availability'] != 'available' for m in members),
                                     'superseded_members': sum(m['support_status'] != 'current' for m in members)}}

    def statuses(self, result_id: str, actor: ActorContext, *, include_synthetic: bool = False, connection=None) -> dict[str, dict[str, bool]]:
        """Lock exact source policy/derivation health without locking interpretation copies."""
        actor.require_workspace(self.workspace_id)
        with nullcontext(connection) if connection is not None else self.db.connect() as connection:
            row = connection.execute('SELECT synthetic FROM knowledge_query_results WHERE id=%s AND workspace_id=%s', (result_id, self.workspace_id)).fetchone()
            if row is None:
                raise EvidenceError('knowledge_query_result_not_found')
            if row['synthetic'] and not include_synthetic:
                raise EvidenceError('synthetic_evidence_excluded')
            rows = connection.execute('SELECT * FROM knowledge_query_members WHERE result_id=%s ORDER BY position', (result_id,)).fetchall()
            statuses = {}
            for selected in rows:
                reference = SupportReference(str(selected['observation_id']), str(selected['derivation_id']),
                                             tuple(str(i) for i in selected['assertion_ids']), tuple(str(i) for i in selected['metric_ids']))
                member = IngestedEvidence(self.db, self.workspace_id).read((reference,), actor, include_synthetic=include_synthetic, connection=connection)[0]
                statuses[member['observation_id']] = {**member['policy'], 'current': member['support_status'] == 'current'}
        return statuses

    def account_support(self, result: dict[str, Any], actor: ActorContext) -> dict[str, Any]:
        """Expose stable account keys from permitted exact support, including incomplete profiles.

        The input is a search/read result from this owner. Handles and source URLs
        never establish account identity. Post author assertions and account subject
        identities both support eligibility; metrics need no profile assertion.
        """
        actor.require_workspace(self.workspace_id)
        if result['workspace_id'] != self.workspace_id:
            raise EvidenceError('workspace_access_denied')
        members = []
        for member in result['members']:
            accounts = {}
            if member['availability'] == 'available' and member['support_status'] == 'current':
                for item in member['assertions'] + member['metrics']:
                    key = {field: item[field] for field in ('platform', 'namespace', 'kind', 'native_id')}
                    if key['kind'] == 'account':
                        accounts[json.dumps(key, sort_keys=True)] = key
                    if item.get('field') == 'author_account' and item['state'] == 'observed':
                        key = item['value']
                        if isinstance(key, dict) and key.keys() == {'platform', 'namespace', 'kind', 'native_id'} and key['kind'] == 'account' and all(isinstance(v, str) and v for v in key.values()):
                            accounts[json.dumps(key, sort_keys=True)] = key
            members.append({**member, 'account_keys': list(accounts.values())})
        return {**result, 'members': members}
