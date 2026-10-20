"""Escaped completion messages composed by the policy-aware inbox owner."""

from .views import e


def index(events):
    """List bounded completion events without copying source or task-purpose text."""
    content = '<h1>Completion inbox</h1><p>Latest 100 task completions. Publication availability is checked when reopened.</p>'
    for event in events:
        content += f'<section class="panel"><a href="/inbox/{e(event["event_id"])}">Completion {e(event["created_at"])}</a>'
        content += detail(event, heading=False) + '</section>'
    return content if events else content + '<p>No completed tasks yet.</p>'


def detail(event, *, heading=True):
    """Show historical counts separately from current permitted publication links."""
    content = '<h1>Task completion</h1><p><a href="/inbox">Completion inbox</a></p>' if heading else ''
    content += f'<p>{e(event["message"])}</p><p><a href="{e(event["task_href"])}">Task {e(event["task_id"])}</a></p>'
    content += f'<p>Outcome: {e(event["outcome"])} · Completed: {e(event["created_at"])}</p>'
    coverage = event['coverage']
    content += '<p>' + ' · '.join(f'{label}: {e(coverage.get(field, "unknown"))}' for label, field in (
        ('Requested inputs', 'requested_inputs'), ('Collected', 'collected_observations'),
        ('Ingested', 'ingested_observations'), ('Quarantined', 'quarantined_observations'),
    )) + '</p><p>Coverage is limited to requested inputs. Market coverage is unknown.</p>'
    for publication in event['publications']:
        if publication['href']:
            content += f'<p><a href="{e(publication["href"])}">Publication {e(publication["publication_id"])}</a></p>'
        else:
            content += f'<p>Publication {e(publication["publication_id"])}: current support unavailable.</p>'
    return content
