"""Supplied enrichment scope and exact named-human approval, without generation."""

import json
import uuid

from .views import checked, e, error_message, hidden, options, value


def index(proposals):
    """List immutable proposal revisions separately from submitted tasks."""
    content = '<h1>Enrichment proposals</h1><p><a href="/proposals/new">Supply an enrichment proposal</a></p>'
    for proposal in proposals:
        content += f'<p><a href="/proposals/{e(proposal["proposal_id"])}">{e(proposal["purpose"])}</a> · {e(proposal["created_at"])}</p>'
    return content


def supplied_form(csrf, route, submitted=None, error=None):
    """Accept direct supplied scope; route and authority remain server configuration."""
    content = '<h1>Supply an enrichment proposal</h1><p>Save a supplied proposal for review. Saving does not approve or submit acquisition. Each saved revision is immutable; changes need a new proposal.</p>'
    if error:
        content += error_message(error)
    if route is None:
        return content + '<p>Offline task route is not configured.</p>'
    content += '<form action="/proposals" method="post">' + hidden('csrf', csrf) + hidden('request_id', value(submitted, 'request_id', str(uuid.uuid4())))
    content += f'<label>Purpose<textarea name="purpose" required maxlength="1000">{e(value(submitted, "purpose"))}</textarea></label>'
    intents = [('refresh', 'Refresh'), ('fill', 'Fill gaps'), ('expansion', 'Expansion')]
    intent = value(submitted, 'intent', 'refresh')
    if intent not in {key for key, _ in intents}:
        intents.append((intent, intent))
    content += f'<label>Intent<select name="intent">{options(intents, intent)}</select></label>'
    content += f'<label>Subject IDs, one per line<textarea name="subject_ids">{e(value(submitted, "subject_ids"))}</textarea></label>'
    content += f'<label>Search queries, one per line<textarea name="search_queries">{e(value(submitted, "search_queries"))}</textarea></label>'
    return content + '<button type="submit">Save proposal for review</button></form>'


def detail(proposal, csrf, submitted=None, error=None):
    """Display the exact revision/configuration and an explicit approval interaction."""
    content = f'<h1>Review enrichment proposal</h1><p>Immutable proposal revision {e(proposal["proposal_id"])}</p><p><a href="/proposals">All proposals</a></p>'
    if error:
        content += error_message(error)
    for label, item in (('Workspace', proposal['workspace_id']), ('Proposed by', proposal['proposer']),
                         ('Created', proposal['created_at']), ('Purpose', proposal['scope']['purpose']),
                         ('Refresh / fill / expansion intent', proposal['scope']['intent']), ('Exact subject / search and input scope', proposal['scope']),
                         ('Limits', proposal['limits']), ('Scope version', proposal['scope_version']), ('Scope digest', proposal['scope_digest'])):
        content += f'<p>{e(label)}: {e(json.dumps(item, ensure_ascii=False))}</p>'
    content += '<p>The synthetic fixture route reads only the listed supplied references. Search queries describe approved intent; this route does not perform query discovery. Approval does not grant live access or expand task limits.</p>'
    approval = proposal['approval']
    if approval:
        content += f'<p>Human approval: {e(json.dumps(approval, ensure_ascii=False))}</p>'
        if approval['task_id']:
            return content + f'<p><a href="/tasks/{e(approval["task_id"])}">Resulting acquisition task</a></p>'
    content += f'<form action="/proposals/{e(proposal["proposal_id"])}/approve" method="post">'
    content += hidden('csrf', csrf) + hidden('request_id', approval['request_id'] if approval else value(submitted, 'request_id', str(uuid.uuid4()))) + hidden('scope_digest', proposal['scope_digest'])
    content += f'<label><input type="checkbox" name="reviewed" value="yes"{checked(value(submitted, "reviewed") == "yes")} required>I approve this exact proposal revision, scope and limits in this workspace.</label>'
    return content + '<button type="submit">Approve exact scope and submit offline task</button></form>'
