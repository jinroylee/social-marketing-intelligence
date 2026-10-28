"""Source-free graph search manifests and transient policy-filtered adjacency."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import uuid

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from ..queries import KnowledgeQueries, QueryScope
from ..store import KnowledgeStore


@dataclass(frozen=True)
class GraphScope:
    """Bounded entity filters over one exact selection of published support."""

    text: str = ''
    platforms: tuple[str, ...] = ()
    namespaces: tuple[str, ...] = ()
    kinds: tuple[str, ...] = ()
    captured_from: str | None = None
    captured_to: str | None = None
    member_limit: int = 100
    entity_limit: int = 50
    neighbor_limit: int = 20

    def __post_init__(self):
        QueryScope(text=self.text, platforms=self.platforms, captured_from=self.captured_from,
                   captured_to=self.captured_to, limit=self.member_limit)
        if (any(not isinstance(values, tuple) or len(values) > 10
                or any(not isinstance(v, str) or not v or len(v) > 100 for v in values)
                for values in (self.namespaces, self.kinds))
                or any(kind not in {'account', 'content', 'brand', 'product'} for kind in self.kinds)
                or type(self.entity_limit) is not int or not 1 <= self.entity_limit <= 100
                or type(self.neighbor_limit) is not int or not 1 <= self.neighbor_limit <= 50):
            raise EvidenceError('invalid_graph_scope')


def _identity(key):
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()


def _contains(value, text):
    if isinstance(value, dict):
        return any(_contains(item, text) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains(item, text) for item in value)
    return value is not None and text in str(value).casefold()


def _support(member, subject_id=None):
    dates = [a['value'] for a in member['assertions'] if a['subject_id'] == subject_id
             and a['field'] == 'published_at' and a['state'] == 'observed']
    return {**{key: member[key] for key in ('publication_id', 'observation_id', 'derivation_id',
            'source_reference', 'captured_at', 'source_as_of', 'ingested_at', 'method', 'synthetic', 'coverage', 'publication_context')},
            'source_subject_id': subject_id, 'source_published_at': dates[0] if dates and all(d == dates[0] for d in dates) else None}


def _projection(result, catalogs):
    nodes, edges, subjects = {}, [], {}

    def source_node(key, member, subject_id=None):
        identity = _identity(key)
        node = nodes.setdefault(identity, {'entity_id': identity, 'identity': key, 'label': key['native_id'],
            'basis': 'observed', 'attributes': [], 'metrics': [], 'unknowns': [], 'support': []})
        support = _support(member, subject_id)
        if support not in node['support']:
            node['support'].append(support)
        for unknown in member['unknowns']:
            if unknown not in node['unknowns']:
                node['unknowns'].append(unknown)
        return node

    for member in result['members']:
        for item in member['assertions'] + member['metrics']:
            key = {field: item[field] for field in ('platform', 'namespace', 'kind', 'native_id')}
            node = source_node(key, member, item['subject_id'])
            subjects[(member['publication_id'], member['observation_id'], item['subject_id'])] = node['entity_id']
            if 'field' in item:
                if not any(a['assertion_id'] == item['assertion_id'] for a in node['attributes']):
                    node['attributes'].append(item)
                if item['field'] in {'handle', 'display_name'} and item['state'] == 'observed' and isinstance(item['value'], str) and 'label_assertion_id' not in node:
                    node['label'] = item['value']
                    node['label_assertion_id'] = item['assertion_id']
                if item['state'] != 'observed':
                    node['unknowns'].append(f"{item['field']}:{item['state']}")
                if item['field'] == 'author_account' and item['state'] == 'observed':
                    author = item['value']
                    if (isinstance(author, dict) and set(author) == {'platform', 'namespace', 'kind', 'native_id'}
                            and author['kind'] == 'account' and all(isinstance(v, str) and v for v in author.values())):
                        target = source_node(author, member)
                        edges.append({'relationship_id': item['assertion_id'], 'source': node['entity_id'],
                            'target': target['entity_id'], 'predicate': 'author_account', 'basis': 'observed',
                            'assertion_id': item['assertion_id'], 'support': _support(member, item['subject_id'])})
            else:
                if not any(m['metric_id'] == item['metric_id'] for m in node['metrics']):
                    node['metrics'].append(item)

    def reference_node(kind, entry, member, catalog, subject_id):
        key = {'kind': kind, 'reference_id': entry['id']}
        identity = _identity(key)
        node = nodes.setdefault(identity, {'entity_id': identity, 'identity': key, 'label': entry['name'],
            'basis': 'human', 'attributes': [], 'metrics': [], 'unknowns': [], 'support': [], 'aliases': entry['aliases'], 'catalogs': []})
        support = _support(member, subject_id)
        if support not in node['support']:
            node['support'].append(support)
        attribution = {**{k: catalog[k] for k in ('catalog_id', 'digest', 'recorded_by', 'recorded_at')}, 'reference': entry}
        if attribution not in node['catalogs']:
            node['catalogs'].append(attribution)
        node['aliases'] = sorted(set(node['aliases']) | set(entry['aliases']))
        return node

    claims = {c['id']: c for c in result['interpretations']}
    manifest = {(m['publication_id'], m['observation_id']): m for m in result['manifest']}
    # One observation can have several published bundles. Bind each claim to
    # a bundle that actually selected it, preserving the query's newest-first
    # order rather than borrowing an older source-only publication's context.
    for member in result['members']:
        selected = manifest[(member['publication_id'], member['observation_id'])]
        for claim_id in selected['interpretation_ids']:
            claim = claims.get(claim_id)
            if not claim or claim['predicate'] not in {'brand_mention', 'product_mention'}:
                continue
            subject = (member['publication_id'], member['observation_id'], claim['subject_id'])
            if subject not in subjects or claim['source_assertion_id'] not in member['assertion_ids']:
                continue
            catalog = catalogs[claim['catalog_id']]
            kind = 'product' if claim['predicate'] == 'product_mention' else 'brand'
            entry = next(e for e in catalog['document'][kind + 's'] if e['id'] == claim['value'][kind + '_id'])
            target = reference_node(kind, entry, member, catalog, claim['subject_id'])
            edges.append({'relationship_id': claim['id'], 'source': subjects[subject],
                'target': target['entity_id'], 'predicate': claim['predicate'], 'basis': 'derived',
                'interpretation': claim, 'support': _support(member, claim['subject_id'])})
            if kind == 'product':
                brand = next(e for e in catalog['document']['brands'] if e['id'] == entry['brand_id'])
                brand_node = reference_node('brand', brand, member, catalog, claim['subject_id'])
                edges.append({'relationship_id': _identity([claim['id'], 'catalog_brand']), 'source': target['entity_id'],
                    'target': brand_node['entity_id'], 'predicate': 'catalog_brand', 'basis': 'human',
                    'catalog': {k: catalog[k] for k in ('catalog_id', 'digest', 'recorded_by', 'recorded_at')},
                    'support': _support(member, claim['subject_id'])})
    unique_edges = {}
    for edge in edges:
        unique_edges.setdefault(edge['relationship_id'], edge)
    return nodes, list(unique_edges.values())



class KnowledgeGraph:
    """Pin bounded support once; recompute permitted labels and immediate edges on read."""

    method_version = 'published-one-hop-graph-v1'

    def __init__(self, db: Database, workspace_id: str = 'local'):
        self.db, self.workspace_id = db, workspace_id
        self.queries = KnowledgeQueries(db, workspace_id)

    def migrate(self) -> None:
        """Install source-free graph manifests after the existing knowledge tables."""
        self.queries.migrate()
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def search(self, scope: GraphScope, actor: ActorContext, *, request_id: str,
               include_synthetic: bool = False) -> dict[str, Any]:
        """Save exact support and entity filters; changed producer/request payloads conflict."""
        actor.require_workspace(self.workspace_id)
        if not isinstance(scope, GraphScope) or not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200 or type(include_synthetic) is not bool:
            raise EvidenceError('invalid_graph_request')
        digest = _identity({'scope': asdict(scope), 'producer': asdict(actor), 'synthetic': include_synthetic, 'method_version': self.method_version})
        with self.db.connect() as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'knowledge-graph:{self.workspace_id}:{request_id}',))
            row = connection.execute('SELECT id,request_digest FROM knowledge_graph_searches WHERE workspace_id=%s AND request_id=%s',
                                     (self.workspace_id, request_id)).fetchone()
            if row:
                if row['request_digest'] != digest:
                    raise EvidenceError('graph_request_conflict')
                search_id = str(row['id'])
            else:
                search_id = str(uuid.uuid4())
                result = self.queries.search(QueryScope(platforms=scope.platforms, captured_from=scope.captured_from,
                    captured_to=scope.captured_to, limit=scope.member_limit), actor, request_id=f'graph:{search_id}',
                    include_synthetic=include_synthetic, connection=connection)
                connection.execute('INSERT INTO knowledge_graph_searches(id,workspace_id,request_id,request_digest,query_result_id,scope,producer_id,producer_kind,method_version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (search_id, self.workspace_id, request_id, digest, result['result_id'], Jsonb(asdict(scope)), actor.actor_id, actor.kind, self.method_version))
        return self.read(search_id, actor, include_synthetic=include_synthetic)

    def read(self, search_id: str, actor: ActorContext, *, entity_id: str | None = None,
             include_synthetic: bool = False) -> dict[str, Any]:
        """Reopen exact one-hop support with current process AND display rights.

        Entity filters select search matches. A selected entity's neighbors may
        have other kinds/namespaces; they retain their exact identities. Unknown
        or no-longer-permitted selection IDs return a content-free unavailable
        state. No second hop or later publication is substituted.
        """
        actor.require_workspace(self.workspace_id)
        try:
            if str(uuid.UUID(search_id)) != search_id or type(include_synthetic) is not bool:
                raise ValueError
        except (ValueError, TypeError, AttributeError) as error:
            raise EvidenceError('invalid_graph_selection') from error
        if entity_id is not None and (not isinstance(entity_id, str) or not re.fullmatch('[a-f0-9]{64}', entity_id)):
            raise EvidenceError('invalid_graph_entity')
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM knowledge_graph_searches WHERE id=%s AND workspace_id=%s',
                                     (search_id, self.workspace_id)).fetchone()
            if row is None:
                raise EvidenceError('graph_search_not_found')
            scope = GraphScope(**{**row['scope'], **{k: tuple(row['scope'][k]) for k in ('platforms', 'namespaces', 'kinds')}})
            process = self.queries.read(str(row['query_result_id']), actor, purpose='process', include_synthetic=include_synthetic, connection=connection)
            display = self.queries.read(str(row['query_result_id']), actor, include_synthetic=include_synthetic, connection=connection)
            usable = {m['observation_id'] for m in process['members'] if m['availability'] == 'available' and m['support_status'] == 'current' and m['policy']['can_retain']}
            versions = {(m['publication_id'], m['observation_id']): m for m in display['manifest']}
            members = [m for m in display['members'] if m['observation_id'] in usable and m['availability'] == 'available' and m['support_status'] == 'current']
            members = [{**m, 'publication_context': {k: versions[(m['publication_id'], m['observation_id'])][k] for k in ('publication_method', 'publication_time', 'publication_producer')}} for m in members]
            process_claims = {c['id'] for c in process['interpretations'] if c['state'] == 'supported'}
            claims = [c for c in display['interpretations'] if c['state'] == 'supported'
                      and c['id'] in process_claims and any(m['observation_id'] == c['observation_id'] for m in members)]
            catalogs = {catalog_id: KnowledgeStore(self.db, self.workspace_id).catalog_context(catalog_id, actor, connection=connection)
                        for catalog_id in {c['catalog_id'] for c in claims if c['predicate'] in {'brand_mention', 'product_mention'}}}
            nodes, edges = _projection({**display, 'members': members, 'interpretations': claims}, catalogs)
            matches = [node for node in nodes.values() if
                (not scope.kinds or node['identity']['kind'] in scope.kinds)
                and (not scope.namespaces or node['identity'].get('namespace') in scope.namespaces)
                and (not scope.platforms or 'platform' not in node['identity'] or node['identity']['platform'] in scope.platforms)
                and (not scope.text or _contains([node['identity'], node['label'], node['attributes'], node.get('aliases', [])], scope.text.casefold()))]
            matches.sort(key=lambda n: n['entity_id'])
            selected = nodes.get(entity_id) if entity_id else None
            incident = [edge for edge in edges if entity_id in (edge['source'], edge['target'])] if selected else []
            incident.sort(key=lambda edge: edge['relationship_id'])
            visible = incident[:scope.neighbor_limit]
            neighbors = {edge['target'] if edge['source'] == entity_id else edge['source'] for edge in visible}
            return {'search_id': search_id, 'workspace_id': self.workspace_id, 'query_result_id': display['result_id'],
                'method_version': self.method_version, 'selection_method_version': row['method_version'], 'created_at': row['created_at'].isoformat(),
                'producer': {'actor_id': row['producer_id'], 'kind': row['producer_kind']}, 'scope': row['scope'],
                'entities': matches[:scope.entity_limit], 'selected': selected,
                'selection_status': 'available' if selected else 'unavailable' if entity_id else 'not_selected',
                'neighbors': [nodes[key] for key in sorted(neighbors)], 'relationships': visible,
                'manifest': display['manifest'], 'coverage': display['coverage'],
                'current_coverage': {'permitted_members': len(members), 'unavailable_or_superseded_members': len(display['members']) - len(members),
                    'unavailable_or_review_interpretations': len(display['interpretations']) - len(claims),
                    'matching_entities': len(matches), 'entity_limit_reached': len(matches) > scope.entity_limit,
                    'immediate_relationships': len(incident), 'neighbor_limit_reached': len(incident) > scope.neighbor_limit},
                'limitations': ['bounded_published_support', 'not_complete_market_coverage',
                    'adjacency_does_not_establish_identity_equivalence', 'mentions_do_not_establish_use_or_endorsement']}
