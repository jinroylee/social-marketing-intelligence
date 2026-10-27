"""Escaped explicit scope and exact approval for an assistant's saved knowledge gap."""

import uuid

from . import proposal_views
from .views import e, hidden, value, options


def answer_actions(context, *, include_synthetic=False):
    """Offer acquisition only for a supported gap and keep existing journeys visible."""
    answer = context['answer']
    suffix = '?include_synthetic=yes' if include_synthetic else ''
    content = '<h2>Enrichment follow-up</h2>'
    if context['gap']:
        content += f'<p>Knowledge gap: {e(context["gap"])}. <a href="/knowledge/answers/{e(answer["answer_id"])}/enrichment/new{suffix}">Propose bounded enrichment</a></p>'
    else:
        content += '<p>No supported knowledge-gap proposal is available for this result. Model/configuration or accounting failures require their own recovery.</p>'
    for journey in context['journeys']:
        content += f'<p><a href="/assistant-enrichments/{e(journey["journey_id"])}{suffix}">Saved enrichment journey</a> · {e(journey["task"]["status"] if journey["task"] else "Awaiting exact proposal approval")}</p>'
    return content


def proposal_form(context, csrf, submitted=None, error=None, *, include_synthetic=False):
    """Require an exact query/subject/window; user prose never supplies route authority."""
    answer_id = context['answer']['answer_id']
    content = f'<h1>Propose bounded enrichment</h1><p>Knowledge gap: {e(context["gap"] or "unavailable")}.</p><p>Clarify ambiguous questions with the exact scope below. This template proposes research; it does not promise that retrieval can answer the question or supply an absent field. Saving grants no acquisition authority. A human must review the exact saved scope and limits.</p>'
    if error:
        content += f'<p role="alert">{e(error)}. Review the scope or reopen the original answer.</p>'
    content += f'<form action="/knowledge/answers/{e(answer_id)}/enrichments" method="post">{hidden("csrf", csrf)}{hidden("request_id", value(submitted, "request_id", str(uuid.uuid4())))}{hidden("include_synthetic", "yes" if include_synthetic else "")}'
    content += f'<label>Intent<select name="intent">{options([(i, i) for i in ("refresh", "fill", "expansion")], value(submitted, "intent", "refresh" if context["gap"] in {"stale_published_information", "published_support_unavailable"} else "fill"))}</select></label>'
    for name, label in [('subject_ids', 'Exact subject IDs (one per line)'), ('search_query', 'One exact keyword query'),
                        ('published_from', 'Published from (UTC ISO timestamp, inclusive)'), ('published_before', 'Published before (UTC ISO timestamp, exclusive)')]:
        content += f'<label>{e(label)}<textarea name="{e(name)}" required>{e(value(submitted, name))}</textarea></label>'
    return content + '<p>Bounded query discovery uses only the server-configured route and original request/record/byte/cost limits. On-demand scope may exceed scheduled keywords; broader work requires its own saved proposal and fresh approval.</p><button>Save exact proposal for review</button></form>'


def detail(journey, csrf, submitted=None, error=None, *, include_synthetic=False):
    """Display original ask, exact review, acknowledgment and the actual durable outcome."""
    suffix = '?include_synthetic=yes' if include_synthetic else ''
    answer_id, journey_id = journey['answer']['answer_id'], journey['journey_id']
    content = f'<h1>Assistant enrichment journey</h1><p><a href="/knowledge/answers/{e(answer_id)}{suffix}">Original answer</a> · <a href="/knowledge/questions">Ask again</a></p><p>Gap at proposal: {e(journey["gap"])}. The original answer stays unchanged. Only a later explicit question can use currently permitted published updates.</p>'
    if journey['proposal']:
        content += proposal_views.detail(journey['proposal'], csrf, submitted, error,
            approval_action=f'/assistant-enrichments/{journey_id}/approve',
            include_synthetic=include_synthetic)
    else:
        content += '<p>Proposal save interrupted. Retry the exact original scope request to reopen it.</p>'
        scope = journey['pending_scope']
        retry = {'request_id': [journey['request_id']], 'intent': [scope['intent']],
                 'subject_ids': ['\n'.join(scope['subject_ids'])], 'search_query': [scope['search_queries'][0]],
                 'published_from': [scope['published_from']], 'published_before': [scope['published_before']]}
        content += proposal_form({'answer': journey['answer'], 'gap': journey['gap']}, csrf, retry, error,
                                 include_synthetic=journey['include_synthetic'])
    task = journey['task']
    if task:
        content += f'<h2>Task acknowledged</h2><p><a href="/tasks/{e(task["task_id"])}">Exact task and limits</a> · {e(task["status"])} · {e(task["progress"])}</p>'
    if journey['completion']:
        event = journey['completion']
        content += f'<h2>Actual completion</h2><p>{e(event["message"])} <a href="/inbox/{e(event["event_id"])}">Durable completion and current publication links</a></p>'
    elif task:
        content += '<p>Completion is not recorded. Retrieved or pending material cannot answer the question before publication.</p>'
    return content
