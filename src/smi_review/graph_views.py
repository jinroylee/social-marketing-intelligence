"""Escaped bounded graph navigation and current governed evidence details."""

import json
import re
import uuid
from urllib.parse import urlencode

from smi_ingestion.evidence import EvidenceError
from smi_knowledge.graph import GraphScope, GraphTraversal

from .forms import one
from .views import e, hidden, source_link, value


FIELDS = {'csrf', 'request_id', 'text', 'platforms', 'namespaces', 'kinds', 'captured_from', 'captured_to',
          'member_limit', 'entity_limit', 'neighbor_limit', 'include_synthetic'}


TRAVERSAL_FIELDS = {'max_hops', 'node_limit', 'relationship_limit', 'work_limit', 'direction',
                    'kinds', 'platforms', 'namespaces', 'predicates', 'bases', 'observation_ids'}
NUMERIC_FIELDS = {'max_hops', 'node_limit', 'relationship_limit', 'work_limit'}
NAVIGATION_FIELDS = TRAVERSAL_FIELDS | {'entity', 'previous', 'include_synthetic'}


def navigation_from_query(query):
    """Parse opaque navigation context and finite traversal controls only."""
    if not query.keys() <= NAVIGATION_FIELDS or one(query, 'include_synthetic') not in {'', 'yes'}:
        raise EvidenceError('invalid_form')
    previous = one(query, 'previous')
    if previous and not re.fullmatch('[a-f0-9]{64}', previous):
        raise EvidenceError('invalid_graph_entity')
    controls = {}
    for key in query.keys() & TRAVERSAL_FIELDS:
        raw = one(query, key)
        controls[key] = int(raw) if key in NUMERIC_FIELDS else raw if key == 'direction' else tuple(v.strip() for v in raw.split(',') if v.strip())
    return {'entity_id': one(query, 'entity') or None, 'include_synthetic': one(query, 'include_synthetic') == 'yes',
            'traversal': GraphTraversal(**controls) if controls else None}, previous


def error_navigation(query):
    """Preserve valid source narrowing on errors; retain no submitted source wording."""
    controls, submitted = {}, {}
    for key in query.keys() & TRAVERSAL_FIELDS:
        try:
            raw = one(query, key)
            parsed = int(raw) if key in NUMERIC_FIELDS else raw if key == 'direction' else tuple(v.strip() for v in raw.split(',') if v.strip())
            GraphTraversal(**{key: parsed})
        except (EvidenceError, ValueError):
            if key in NUMERIC_FIELDS and len(query[key]) == 1 and re.fullmatch('[0-9]{1,6}', query[key][0]):
                submitted[key] = query[key]
            if key == 'observation_ids':
                controls[key] = ('00000000-0000-0000-0000-000000000000',)
            continue
        controls[key] = parsed
    safe = {key: query[key] for key in ('entity', 'previous', 'include_synthetic') if key in query and len(query[key]) == 1}
    for key in ('entity', 'previous'):
        if key in safe and not re.fullmatch('[a-f0-9]{64}', safe[key][0]):
            del safe[key]
    if safe.get('include_synthetic', [''])[0] != 'yes':
        safe.pop('include_synthetic', None)
    safe.update({key: [str(val) if key in NUMERIC_FIELDS or key == 'direction' else ','.join(val)] for key, val in controls.items()})
    kwargs, previous = navigation_from_query(safe)
    return kwargs, previous, submitted


def _navigation(graph, entity_id, synthetic, previous=None):
    query = {key: ','.join(val) if isinstance(val, (tuple, list)) else str(val) for key, val in graph['traversal'].items()}
    query['entity'] = entity_id
    if synthetic:
        query['include_synthetic'] = 'yes'
    if previous:
        query['previous'] = previous
    return f'/knowledge/graph/{graph["search_id"]}?{urlencode(query)}'


def _traversal_form(graph, synthetic, previous, submitted):
    content = '<h2>Bounded traversal</h2><p>This is a current exploration over the original support sample. Graph membership is not an immutable campaign decision.</p>'
    content += f'<form method="get" action="/knowledge/graph/{e(graph["search_id"])}">'
    if graph['selected']:
        content += hidden('entity', graph['selected']['entity_id'])
    elif graph['selection_status'] == 'unavailable':
        content += hidden('entity', graph['requested_entity_id'])
    if synthetic:
        content += hidden('include_synthetic', 'yes')
    if previous:
        content += hidden('previous', previous)
    labels = {'max_hops': 'Maximum hops (1–3)', 'node_limit': 'Maximum nodes including selection (1–100)',
              'relationship_limit': 'Maximum relationships (1–50)', 'work_limit': 'Maximum traversal edge inspections (1–5000)',
              'direction': 'Direction: both, incoming, outgoing', 'kinds': 'Neighbor kinds (comma separated)',
              'platforms': 'Neighbor platforms (comma separated)', 'namespaces': 'Neighbor native namespaces (comma separated)',
              'predicates': 'Relationship predicates (comma separated)', 'bases': 'Bases: observed, derived, human (comma separated)',
              'observation_ids': 'Exact source observation IDs for all displayed facts (comma separated)'}
    for key, label in labels.items():
        val = graph['traversal'][key]
        default = ','.join(val) if isinstance(val, (tuple, list)) else str(val)
        content += f'<label>{e(label)}<input name="{e(key)}" value="{e(value(submitted, key, default))}"></label>'
    return content + '<p>Entity filters apply at each step; filtered entities cannot bridge a path. Work bounds count edge inspections after the finite saved-support projection is built.</p><button type="submit">Apply traversal filters</button></form>'


def scope_from_form(form):
    """Accept bounded filters only; identity, methods and source authority stay server-owned."""
    if not form.keys() <= FIELDS or one(form, 'include_synthetic') not in {'', 'yes'}:
        raise EvidenceError('invalid_form')
    return GraphScope(text=one(form, 'text'),
        **{k: tuple(v.strip() for v in one(form, k).split(',') if v.strip()) for k in ('platforms', 'namespaces', 'kinds')},
        **{k: one(form, k).strip() or None for k in ('captured_from', 'captured_to')},
        **{k: int(one(form, k, default)) for k, default in (('member_limit', '100'), ('entity_limit', '50'), ('neighbor_limit', '20'))})


def search_form(csrf, submitted=None, error=None):
    """Offer explicit bounded search without acquisition or model authority."""
    content = '<h1>Knowledge graph</h1><p>Search permitted published entities, then explicitly traverse bounded relationships and inspect their evidence. Matching handles do not establish a shared Creator.</p>'
    if error:
        content += f'<p role="alert">{e(error)}. Check the bounded filters and try again.</p>'
    content += '<form action="/knowledge/graph" method="post">' + hidden('csrf', csrf) + hidden('request_id', value(submitted, 'request_id', str(uuid.uuid4())))
    for name, label, default in (
        ('text', 'Literal entity text or native identity', ''), ('platforms', 'Platforms (comma separated)', ''),
        ('namespaces', 'Native namespaces (comma separated)', ''), ('kinds', 'Kinds: account, content, brand, product (comma separated)', ''),
        ('captured_from', 'Captured from (inclusive timestamp with timezone)', ''), ('captured_to', 'Captured before (timestamp with timezone)', ''),
        ('member_limit', 'Maximum source members (1–100)', '100'), ('entity_limit', 'Maximum entity matches (1–100)', '50'),
        ('neighbor_limit', 'Maximum immediate relationships (1–50)', '20'),
    ):
        content += f'<label>{e(label)}<input name="{e(name)}" value="{e(value(submitted, name, default))}"></label>'
    checked = ' checked' if value(submitted, 'include_synthetic') == 'yes' else ''
    content += f'<label><input type="checkbox" name="include_synthetic" value="yes"{checked}>Include synthetic development inputs</label>'
    return content + '<p>Search examines at most 100 recent publications. Filters select matches; immediate neighbors retain their own identities and may have other kinds or namespaces. Empty filters explore only that bounded sample.</p><button type="submit">Search entities</button></form>'


def _link(graph, node, synthetic):
    previous = graph['selected']['entity_id'] if graph['selected'] and graph['selected']['entity_id'] != node['entity_id'] else None
    return f'<a href="{e(_navigation(graph, node["entity_id"], synthetic, previous))}">{e(node["label"])}</a>'


def _node(node):
    content = f'<h3>{e(node["label"])}</h3><p>Identity: {e(json.dumps(node["identity"], ensure_ascii=False))}<br>Label basis: {e(node["basis"])}</p>'
    for label, data in (('Assertions', node['attributes']), ('Metrics', node['metrics']), ('Unknowns', node['unknowns']), ('Catalog attribution', node.get('catalogs', []))):
        content += f'<p>{e(label)}: {e(json.dumps(data, ensure_ascii=False))}</p>'
    return content


def detail(graph, *, include_synthetic=False, previous=None, submitted=None, error=None):
    """Render only values in the graph owner's currently permitted projection."""
    content = '<h1>Knowledge graph</h1><p><a href="/knowledge/graph">New entity search</a></p>'
    if error:
        content += f'<p role="alert">{e(error)}. Check traversal bounds and filters.</p>'
    content += _traversal_form(graph, include_synthetic, previous, submitted)
    if previous:
        content += f'<p><a href="{e(_navigation(graph, previous, include_synthetic))}">Back to previous selection</a></p>'
    content += f'<p>Saved {e(graph["created_at"])} by {e(graph["producer"]["actor_id"])} ({e(graph["producer"]["kind"])})<br>Saved search method: {e(graph["method_version"])}<br>Traversal method: {e(graph["traversal_method_version"])}<br>Original selection method: {e(graph["selection_method_version"])}</p>'
    suffix = '?include_synthetic=yes' if include_synthetic else ''
    content += f'<p><a href="/knowledge/results/{e(graph["query_result_id"])}{suffix}">Exact original support selection</a></p>'
    for label, data in (('Original coverage', graph['coverage']), ('Current graph coverage and bounds', graph['current_coverage']), ('Traversal coverage and bounds', graph['traversal_coverage']), ('Limitations', graph['limitations'])):
        content += f'<p>{e(label)}: {e(json.dumps(data, ensure_ascii=False))}</p>'
    if not graph['current_coverage']['unavailable_or_superseded_members']:
        content += f'<p>Original human filters: {e(json.dumps(graph["scope"], ensure_ascii=False))}</p>'
    content += '<p>Adjacency does not establish identity equivalence. Literal mentions do not establish use or endorsement. Source publication, capture, source-as-of and ingestion dates remain distinct; unknown dates remain unknown.</p>'
    if include_synthetic:
        content += '<p>Synthetic development inputs explicitly enabled.</p>'
    if graph['traversal_coverage']['truncated']:
        content += '<p role="status">Traversal truncated at the displayed hop, node, relationship or work bound. This is a partial view.</p>'
    content += '<h2>Entity matches</h2><ul>'
    for node in graph['entities']:
        content += '<li>' + _link(graph, node, include_synthetic) + f' · {e(json.dumps(node["identity"], ensure_ascii=False))}</li>'
    content += '</ul>'
    if not graph['entities']:
        content += '<p>No matching permitted entities in this bounded support selection. This does not establish market absence.</p>'
    if graph['selection_status'] == 'unavailable':
        return content + '<p>Selected entity unavailable under the current support, policy or selection. Dependent labels and relationships are withheld.</p>'
    if graph['selection_status'] == 'not_selected':
        return content + '<p>Select an entity to inspect immediate relationships.</p>'
    selected = graph['selected']
    heading = 'Immediate relationships' if graph['traversal']['max_hops'] == 1 else 'Traversed relationships'
    content += '<section class="panel">' + _node(selected) + f'</section><h2>{heading}</h2>'
    nodes = {n['entity_id']: n for n in graph['neighbors']}
    nodes[selected['entity_id']] = selected
    if not graph['relationships']:
        content += '<p>No permitted relationships match these traversal filters in this bounded selection.</p>'
    for edge in graph['relationships']:
        content += '<article class="panel"><div class="graph-edge">'
        content += '<span>' + _link(graph, nodes[edge['source']], include_synthetic) + '</span>'
        content += f'<span aria-label="directed relationship">→ {e(edge["predicate"])} ({e(edge["basis"])}) →</span>'
        content += '<span>' + _link(graph, nodes[edge['target']], include_synthetic) + '</span></div>'
        content += f'<p>Relationship {e(edge["relationship_id"])} · basis {e(edge["basis"])}</p>'
        if 'interpretation' in edge:
            content += f'<p>Provisional interpretation: {e(json.dumps(edge["interpretation"], ensure_ascii=False))}</p>'
        if 'catalog' in edge:
            content += f'<p>Human catalog configuration: {e(json.dumps(edge["catalog"], ensure_ascii=False))}</p>'
        content += f'<p>{source_link(edge["support"]["source_reference"])}</p><p>Exact support and dates: {e(json.dumps(edge["support"], ensure_ascii=False))}</p></article>'
    content += '<h2>Selected entity support</h2>'
    for support in selected['support']:
        content += f'<p>{source_link(support["source_reference"])}</p><p>{e(json.dumps(support, ensure_ascii=False))}</p>'
    content += '<h2>Reached entity details</h2>'
    for node in graph['neighbors']:
        content += '<section class="panel">' + _node(node) + '</section>'
    return content
