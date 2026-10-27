"""Escaped question form and governed extractive answer panels."""

import json
import uuid

from . import query_views
from .views import e, hidden, value


def question_form(csrf, submitted=None, error=None):
    """Offer one bounded current-KB read without acquisition approval or tools."""
    content = '<h1>Ask current knowledge</h1><p>Ask a free-form question with no enrichment approval. This bounded extractive answer selects relevant published findings; it does not verify claims or provide unrestricted synthesis.</p>'
    if error:
        content += f'<p role="alert">{e(error)}. Check the question or reopen a new form.</p>'
    content += '<form action="/knowledge/questions" method="post">' + hidden('csrf', csrf)
    content += hidden('request_id', value(submitted, 'request_id', str(uuid.uuid4())))
    content += f'<label>Question (at most 4,000 UTF-8 bytes)<textarea name="question" required>{e(value(submitted, "question"))}</textarea></label>'
    content += f'<label>Optional literal support filter<input name="text" value="{e(value(submitted, "text"))}"></label>'
    checked = ' checked' if value(submitted, 'include_synthetic') == 'yes' else ''
    content += f'<label><input type="checkbox" name="include_synthetic" value="yes"{checked}>Include synthetic development inputs</label>'
    return content + '<p>At most 100 recent publications, 20 members and 100 exact facts. Capture age is assessed against 30 days. No external search or enrichment is performed. Missing model configuration and unavailable/invalid results remain explicit.</p><button>Ask and preserve answer</button></form>'


def detail(answer, *, include_synthetic=False):
    """Keep actual historical context visible while current source policy gates findings."""
    content = f'<h1>Saved KB answer</h1><p><a href="/knowledge/questions">Ask another question</a></p><h2>{e(answer["question"])}</h2>'
    content += f'<p>Requested by {e(answer["requested_by"]["actor_id"])} ({e(answer["requested_by"]["kind"])}) · {e(answer["recorded_at"])}<br>Model selection status: {e(answer["status"])} · {e(answer["reason"] or "")}<br>Answer basis: bounded extractive findings; generated relevance is not verified factual accuracy or completeness.</p>'
    if answer['status'] == 'in_progress':
        content += '<p>In progress or interrupted with unknown outcome. Reopening never reissues the model call.</p>'
    if answer['status'] == 'succeeded' and not answer['usable']:
        content += '<p role="alert">Generated selection withheld: actual input support is unavailable or superseded. Historical support and model context remain pinned.</p>'
    if answer['limitation'] == 'ambiguous_question':
        content += '<p>The question is ambiguous. Clarify the subject or requested evidence.</p>'
    if answer['limitation'] == 'missing_information' or answer['status'] == 'empty':
        content += '<p>The question cannot be answered fully from this bounded support. Required information is missing; no unsupported answer is supplied.</p>'
    content += '<h2>Supported findings</h2><p>These are observed source values or provisional interpretations selected for relevance, not independent verification. Dates and freshness apply to the cited observation.</p>'
    if not answer['findings']:
        content += '<p>No usable selected finding.</p>'
    for finding in answer['findings']:
        label = finding['detail'].get('field') or finding['detail'].get('predicate') or finding['detail'].get('definition')
        content += f'<article><h3>{e(label)} · {e(finding["kind"])}</h3><pre>{e(json.dumps(finding["value"], ensure_ascii=False))}</pre><p>Citation: {e(finding["support_id"])}<br>Observation: {e(finding["observation_id"])}<br>Captured: {e(finding["captured_at"])} · source as of: {e(finding["source_as_of"] or "unknown")}<br>Freshness: {e(json.dumps(finding["freshness"]))}</p></article>'
    for label, document in [('Missing information', answer['missing_information']), ('Uncertainty and limits', answer['limits']),
                            ('Actual model and method context', answer['configuration']), ('Usage', answer['usage']),
                            ('Exact model input support IDs', answer['input_support_ids'])]:
        content += f'<h2>{e(label)}</h2><pre>{e(json.dumps(document, ensure_ascii=False, indent=2))}</pre>'
    if answer['operation_id']:
        content += f'<p><a href="/costs/{e(answer["operation_id"])}">Costs for this answer</a></p>'
    content += '<p>No external search, tools, acquisition approval or task submission is authorized by this answer.</p>'
    return content + query_views.detail(answer['knowledge_query'], include_synthetic=include_synthetic)
