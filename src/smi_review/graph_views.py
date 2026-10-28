"""Escaped one-hop graph navigation and current governed evidence details."""

import json
import uuid
from urllib.parse import urlencode

from smi_ingestion.evidence import EvidenceError
from smi_knowledge.graph import GraphScope

from .forms import one
from .views import e, hidden, source_link, value


FIELDS = {'csrf', 'request_id', 'text', 'platforms', 'namespaces', 'kinds', 'captured_from', 'captured_to',
          'member_limit', 'entity_limit', 'neighbor_limit', 'include_synthetic'}


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
    content = '<h1>Knowledge graph</h1><p>Search permitted published entities, then inspect one immediate relationship at a time. Matching handles do not establish a shared Creator.</p>'
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


def _link(search_id, node, synthetic):
    query = {'entity': node['entity_id']}
    if synthetic:
        query['include_synthetic'] = 'yes'
    return f'<a href="/knowledge/graph/{e(search_id)}?{e(urlencode(query))}">{e(node["label"])}</a>'


def _node(node):
    content = f'<h3>{e(node["label"])}</h3><p>Identity: {e(json.dumps(node["identity"], ensure_ascii=False))}<br>Label basis: {e(node["basis"])}</p>'
    for label, data in (('Assertions', node['attributes']), ('Metrics', node['metrics']), ('Unknowns', node['unknowns']), ('Catalog attribution', node.get('catalogs', []))):
        content += f'<p>{e(label)}: {e(json.dumps(data, ensure_ascii=False))}</p>'
    return content


def detail(graph, *, include_synthetic=False):
    """Render only values in the graph owner's currently permitted projection."""
    content = '<h1>Knowledge graph</h1><p><a href="/knowledge/graph">New entity search</a></p>'
    content += f'<p>Saved {e(graph["created_at"])} by {e(graph["producer"]["actor_id"])} ({e(graph["producer"]["kind"])})<br>Projection method: {e(graph["method_version"])}<br>Original selection method: {e(graph["selection_method_version"])}</p>'
    suffix = '?include_synthetic=yes' if include_synthetic else ''
    content += f'<p><a href="/knowledge/results/{e(graph["query_result_id"])}{suffix}">Exact original support selection</a></p>'
    for label, data in (('Original coverage', graph['coverage']), ('Current graph coverage and bounds', graph['current_coverage']), ('Limitations', graph['limitations'])):
        content += f'<p>{e(label)}: {e(json.dumps(data, ensure_ascii=False))}</p>'
    if not graph['current_coverage']['unavailable_or_superseded_members']:
        content += f'<p>Original human filters: {e(json.dumps(graph["scope"], ensure_ascii=False))}</p>'
    content += '<p>Adjacency does not establish identity equivalence. Literal mentions do not establish use or endorsement. Source publication, capture, source-as-of and ingestion dates remain distinct; unknown dates remain unknown.</p>'
    if include_synthetic:
        content += '<p>Synthetic development inputs explicitly enabled.</p>'
    content += '<h2>Entity matches</h2><ul>'
    for node in graph['entities']:
        content += '<li>' + _link(graph['search_id'], node, include_synthetic) + f' · {e(json.dumps(node["identity"], ensure_ascii=False))}</li>'
    content += '</ul>'
    if not graph['entities']:
        content += '<p>No matching permitted entities in this bounded support selection. This does not establish market absence.</p>'
    if graph['selection_status'] == 'unavailable':
        return content + '<p>Selected entity unavailable under the current support, policy or selection. Dependent labels and relationships are withheld.</p>'
    if graph['selection_status'] == 'not_selected':
        return content + '<p>Select an entity to inspect immediate relationships.</p>'
    selected = graph['selected']
    content += '<section class="panel">' + _node(selected) + '</section><h2>Immediate relationships</h2>'
    nodes = {n['entity_id']: n for n in graph['neighbors']}
    nodes[selected['entity_id']] = selected
    if not graph['relationships']:
        content += '<p>No immediate permitted relationships in this bounded selection.</p>'
    for edge in graph['relationships']:
        content += '<article class="panel"><div class="graph-edge">'
        content += '<span>' + _link(graph['search_id'], nodes[edge['source']], include_synthetic) + '</span>'
        content += f'<span aria-label="directed relationship">→ {e(edge["predicate"])} ({e(edge["basis"])}) →</span>'
        content += '<span>' + _link(graph['search_id'], nodes[edge['target']], include_synthetic) + '</span></div>'
        content += f'<p>Relationship {e(edge["relationship_id"])} · basis {e(edge["basis"])}</p>'
        if 'interpretation' in edge:
            content += f'<p>Provisional interpretation: {e(json.dumps(edge["interpretation"], ensure_ascii=False))}</p>'
        if 'catalog' in edge:
            content += f'<p>Human catalog configuration: {e(json.dumps(edge["catalog"], ensure_ascii=False))}</p>'
        content += f'<p>{source_link(edge["support"]["source_reference"])}</p><p>Exact support and dates: {e(json.dumps(edge["support"], ensure_ascii=False))}</p></article>'
    content += '<h2>Selected entity support</h2>'
    for support in selected['support']:
        content += f'<p>{source_link(support["source_reference"])}</p><p>{e(json.dumps(support, ensure_ascii=False))}</p>'
    content += '<h2>Immediate neighbor details</h2>'
    for node in graph['neighbors']:
        content += '<section class="panel">' + _node(node) + '</section>'
    return content
