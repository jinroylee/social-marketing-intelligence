"""Local bounded knowledge-search form and exact-result evidence panels."""

import json
import uuid

from smi_ingestion.evidence import EvidenceError
from smi_knowledge import QueryScope

from . import publication_views
from .forms import one
from .views import e, hidden, value


def scope_from_form(form):
    """Parse bounded filters; browser callers cannot choose their actor or process purpose."""
    allowed = {'csrf', 'request_id', 'text', 'platforms', 'subject_ids', 'captured_from', 'captured_to', 'max_age_seconds', 'limit', 'include_synthetic'}
    if not form.keys() <= allowed or one(form, 'include_synthetic') not in {'', 'yes'}:
        raise EvidenceError('invalid_form')
    return QueryScope(text=one(form, 'text'), platforms=tuple(p.strip() for p in one(form, 'platforms').split(',') if p.strip()),
                      subject_ids=tuple(p.strip() for p in one(form, 'subject_ids').split(',') if p.strip()),
                      captured_from=one(form, 'captured_from').strip() or None, captured_to=one(form, 'captured_to').strip() or None,
                      max_age_seconds=int(one(form, 'max_age_seconds')) if one(form, 'max_age_seconds') else None,
                      limit=int(one(form, 'limit', '100')))


def search_form(csrf, submitted=None, error=None):
    """Offer an immediate local query which saves its actual selected support."""
    content = '<h1>Search current knowledge</h1><p>Search committed permitted publications. Each search preserves its exact support for reopening.</p>'
    if error:
        content += f'<p role="alert">{e(error)}. Check the bounded filters and try again.</p>'
    content += '<form action="/knowledge/search" method="post">' + hidden('csrf', csrf) + hidden('request_id', value(submitted, 'request_id', str(uuid.uuid4())))
    for name, label, default in (
        ('text', 'Literal text', ''), ('platforms', 'Platforms (comma separated)', ''),
        ('subject_ids', 'Subject UUIDs (comma separated)', ''), ('captured_from', 'Captured from (inclusive timestamp with timezone)', ''),
        ('captured_to', 'Captured before (timestamp with timezone)', ''), ('max_age_seconds', 'Freshness threshold in seconds (optional)', ''),
        ('limit', 'Maximum source members (1–100)', '100'),
    ):
        content += f'<label>{e(label)}<input name="{e(name)}" value="{e(value(submitted, name, default))}"></label>'
    checked = ' checked' if value(submitted, 'include_synthetic') == 'yes' else ''
    content += f'<label><input type="checkbox" name="include_synthetic" value="yes"{checked}>Include synthetic development inputs</label>'
    content += '<p>At most 100 recent publications are examined. Empty filters search that bounded scope. A freshness threshold evaluates capture age; publishing old evidence does not refresh it.</p>'
    return content + '<button type="submit">Search and preserve result</button></form>'


def detail(result, *, include_synthetic=False):
    """Show immutable membership with current support health and independently assessed age."""
    content = f'<h1>Saved knowledge search</h1><p>{e(result["result_id"])}</p>'
    content += '<p><a href="/knowledge/search">New search</a></p>'
    content += f'<p>Queried {e(result["queried_at"])} by {e(result["producer"]["actor_id"])} ({e(result["producer"]["kind"])})<br>Method: {e(result["method_version"])}<br>Purpose: {e(result["purpose"])}</p>'
    for label, item in (('Filters', result['scope']), ('Original coverage', result['coverage']),
                        ('Current support', result['current_coverage']), ('Unknowns', result['unknowns'])):
        content += f'<p>{e(label)}: {e(json.dumps(item, ensure_ascii=False))}</p>'
    if include_synthetic:
        content += '<p>Synthetic development inputs explicitly enabled.</p>'
    if not result['members']:
        content += '<p>No matching permitted published support. Unknown information remains unknown.</p>'
    for member in result['members']:
        content += f'<p>Observation {e(member["observation_id"])} · freshness: {e(json.dumps(member["freshness"]))}<br>Unknowns: {e(json.dumps(member["unknowns"]))}</p>'
    content += '<h2>Actual support manifest</h2>'
    content += f'<pre>{e(json.dumps(result["manifest"], ensure_ascii=False, indent=2))}</pre>'
    content += publication_views.support(result['members'], result['interpretations'])
    return content
