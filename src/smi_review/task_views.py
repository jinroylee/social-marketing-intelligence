"""Escaped local offline-task submission and source-free operational lineage."""

import json
import uuid
from dataclasses import asdict

from .views import e, error_message, hidden, value


def index(tasks):
    """List durable acknowledgments and their distinct terminal outcomes."""
    content = '<h1>Acquisition tasks</h1><p>Submission accepts bounded work. Collection alone does not establish a usable knowledge update.</p>'
    for task in tasks:
        content += f'<p><a href="/tasks/{e(task["task_id"])}">{e(task["task_id"])}</a> · {e(task["status"])} · {e(task["outcome"] or "Pending")}</p>'
    return content if tasks else content + '<p>No submitted tasks. Open a campaign to submit configured offline work.</p>'


def submit_form(campaign, brief, csrf, route, submitted=None, error=None):
    """Show trusted campaign/configuration scope before acknowledging work."""
    content = f'<h1>Submit offline acquisition</h1><p>Campaign <a href="/campaigns/{e(campaign["campaign_id"])}">{e(campaign["campaign_id"])}</a> · brief version {e(brief["version"])}</p>'
    if error:
        content += error_message(error)
    if brief['version'] != campaign['brief_version']:
        content += f'<p>This brief is stale. <a href="/campaigns/{e(campaign["campaign_id"])}/tasks/new">Review the current brief before submitting a new task.</a></p>'
    if route is None:
        return content + '<p>Offline task route is not configured. Ask the local operator to configure a synthetic fixture manifest.</p>'
    _, digest, manifest = route.snapshot()
    if route.capability()['query_discovery']:
        return content + '<p>Keyword discovery requires an explicit query, subject and publication-time scope. <a href="/proposals/new">Supply and review an exact discovery proposal.</a></p>'
    content += '<p>This synthetic development route performs local fixture reads only. A separate bounded worker executes the queued task.</p>'
    content += f'<p>Route: fixture-json · configuration {e(route.version)} · manifest {e(digest)}</p>'
    content += f'<p>Limits: {e(json.dumps(asdict(route.limits)))}</p><p>References: {e(json.dumps([i.get("reference", "") for i in manifest["items"]]))}</p>'
    content += f'<form action="/campaigns/{e(campaign["campaign_id"])}/tasks" method="post">'
    content += hidden('csrf', csrf) + hidden('request_id', value(submitted, 'request_id', str(uuid.uuid4()))) + hidden('brief_id', brief['id'])
    return content + f'<label>Purpose<textarea name="purpose" required maxlength="1000">{e(value(submitted, "purpose", "Fill campaign evidence coverage"))}</textarea></label><button type="submit">Submit offline task</button></form>'


def detail(task):
    """Show exact attribution, phases, counts and permitted-publication navigation."""
    content = f'<h1>Offline acquisition task</h1><p>{e(task["task_id"])}</p><p><a href="/tasks">All tasks</a></p>'
    content += f'<p><a href="/tasks/{e(task["task_id"])}/costs">Usage and costs</a></p>'
    content += f'<p>Status: {e(task["status"])} · Outcome: {e(task["outcome"] or "Pending")}</p>'
    content += '<p>Synthetic development inputs. Retrieved material becomes usable only after ingestion and publication. No usable update does not establish market absence.</p>'
    for label, item in (('Workspace', task['workspace_id']), ('Origin', task['origin']), ('Proposal approval', task['proposal_approval']), ('Initiator', task['initiator']), ('Submitted', task['submitted_at']),
                        ('Scope version', task['scope_version']), ('Immutable scope', task['scope']), ('Limits', task['limits']),
                        ('Attempt limit', task['attempt_limit']), ('Execution', task['execution']), ('Progress', task['progress']), ('Coverage', task['coverage']), ('Failure', task['failure']), ('Attempts', task['attempts'])):
        content += f'<p>{e(label)}: {e(json.dumps(item, ensure_ascii=False))}</p>'
    if task['proposal_approval']:
        proposal_id = task['proposal_approval']['proposal_id']
        content += f'<p><a href="/proposals/{e(proposal_id)}">Exact approved proposal</a></p>'
    for publication_id in task['publication_ids']:
        content += f'<p><a href="/knowledge/publications/{e(publication_id)}?include_synthetic=yes">Publication {e(publication_id)}</a></p>'
    return content
