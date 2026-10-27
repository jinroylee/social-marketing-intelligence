"""Escaped existing-KB context beside the independently governed recent sample."""

import json
import uuid

from . import alert_views, query_views, semantic_views
from .views import e, error_message, hidden, value


def form(kind, alert_id, csrf, submitted=None, error=None):
    """Offer one local-only query using server-selected frozen topic scope."""
    prefix = '/monitoring/alerts/' if kind == 'quantitative' else '/monitoring/semantic-alerts/'
    content = '<h2>Investigate using existing KB</h2><p>Save a bounded literal match to the frozen topic wording, with exact context and source dates. Missing context remains a gap.</p>'
    if error:
        content += error_message(error)
    content += f'<form method="post" action="{prefix}{e(alert_id)}/investigations">{hidden("csrf", csrf)}{hidden("request_id", value(submitted, "request_id", str(uuid.uuid4())))}'
    checked = ' checked' if value(submitted, 'include_synthetic') == 'yes' else ''
    content += f'<label><input type="checkbox" name="include_synthetic" value="yes"{checked}>Include synthetic development KB inputs</label>'
    return content + '<button type="submit">Save existing KB investigation</button></form>'


def detail(record, *, include_synthetic=False):
    """Separate original recent evidence, pinned KB support and derived uncertainty."""
    content = '<h1>Saved alert investigation</h1>'
    content += f'<p>Saved {e(record["recorded_at"])} by {e(record["recorded_by"])} ({e(record["actor_kind"])}). Method {e(record["method_version"])}.</p>'
    content += '<h2>Derived explanation</h2>'
    if record['explanation']:
        explanation = record['explanation']
        content += f'<p>{e(explanation["finding"])} Selected context members: {explanation["selected_context_members"]}. Historical alert outcome: {e(explanation["alert_outcome"])}.</p>'
    else:
        content += '<p>Source-dependent explanation unavailable. An original dependency was lost; reopening does not reconstruct it.</p>'
    content += '<p>' + e(record['uncertainty']) + '</p><p>Gaps: ' + e(', '.join(record['gaps']) or 'None established by this bounded selection; other unknowns remain.') + '</p>'
    content += '<h2>Recent monitoring evidence</h2>'
    renderer = alert_views.detail if record['alert_kind'] == 'quantitative' else semantic_views.detail
    content += renderer(record['recent_evidence'])
    content += '<h2>Original recent dependencies</h2><pre>' + e(json.dumps(record['recent_dependencies'], indent=2)) + '</pre>'
    content += '<h2>Existing KB context</h2>'
    return content + query_views.detail(record['knowledge_context'], include_synthetic=include_synthetic)
