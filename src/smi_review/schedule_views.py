"""Escaped operator configuration and source-free daily occurrence/task status."""

import json

from .views import e, error_message, hidden, value


def settings(schedule, csrf, can_configure, submitted=None, error=None):
    """Show recorded activation, shared allowance and durable history."""
    content = ('<h1>Registered keyword discovery</h1><p>Recorded live activation. Runtime credentials, source authorization '
               'and cost admission are still required.</p>' if schedule['live_activation'] else
               '<h1>Offline registered keyword discovery</h1><p>Live activation is disabled.</p>')
    content += '<p>These keywords are independent of monitoring topics.</p>'
    content += '<p>The configurable daily new-post admission allowance is initially 50 total across at most 10 registered keywords. It is not throughput, a per-keyword yield, a request count or a cost estimate. Atomic unique new-post admission is enforced at canonical ingestion. Fewer records can be returned because of overlap, ineligible records, source coverage or limits.</p>'
    content += '<p>Daily local-time cadence; accounting days begin at local midnight. The accounting timezone is fixed after the first save. A due tick acknowledges bounded tasks; execute each through the separate existing worker. Earlier missed days are not replayed.</p>'
    if error:
        content += error_message(error)
    if schedule['daily_allowance']:
        content += allowance_panel(schedule['daily_allowance'])
    document = schedule['document'] or {'timezone': 'UTC', 'daily_at': '09:00', 'lookback_days': 7, 'daily_allowance': 50, 'keywords': []}
    if can_configure:
        content += '<form action="/schedules" method="post">' + hidden('csrf', csrf)
        content += hidden('expected_version', value(submitted, 'expected_version', str(schedule['version'])))
        for name, label in (('timezone', 'IANA accounting timezone'), ('daily_at', 'Daily local time (HH:MM)'),
                            ('lookback_days', 'Publication lookback days (1–30)'), ('daily_allowance', 'Daily admission allowance')):
            content += f'<label>{e(label)}<input name="{name}" required value="{e(value(submitted, name, str(document[name])))}"></label>'
        mode = value(submitted, 'execution_mode', 'live' if schedule['live_activation'] else 'offline')
        content += '<label>Execution mode<select name="execution_mode">'
        for key, label in (('offline', 'Offline'), ('live', 'Explicitly activate configured live keyword route')):
            content += f'<option value="{key}"' + (' selected' if mode == key else '') + f'>{label}</option>'
        content += '</select></label><p>A live save records this exact operator route and limits. It grants no runtime credentials or permission.</p>'
        content += '<p>Keywords JSON: at most 10 objects, each with a stable key, one literal query and subject_ids. Preserve the key when editing; an empty list pauses future occurrences.</p>'
        content += f'<label>Registered keywords<textarea name="keywords" required>{e(value(submitted, "keywords", json.dumps(document["keywords"], ensure_ascii=False, indent=2)))}</textarea></label><button type="submit">Save successor configuration</button></form>'
        if schedule['version']:
            content += '<form action="/schedules/tick" method="post">' + hidden('csrf', csrf) + '<button type="submit">Acknowledge due tasks</button></form>'
    else:
        content += '<p>A trusted configured operator role is required to change settings or acknowledge due tasks.</p>'
    content += f'<p>Configuration version: {e(schedule["version"])} · Last tick: {e(schedule["last_tick_at"] or "None")}</p>'
    for occurrence in schedule['occurrences']:
        content += f'<p>{e(occurrence["accounting_day"])} · {e(occurrence["keyword_key"])} · configuration {e(occurrence["configuration_version"])} · {e(occurrence["status"])} · {e(occurrence["reason"] or "")}'
        if occurrence['task']:
            task = occurrence['task']
            content += f' · <a href="/tasks/{e(task["task_id"])}">Task</a> · {e(task["status"])} · {e(task["outcome"] or "Pending")}'
        content += '</p>'
    content += '<details><summary>Configuration history</summary>'
    for configuration in schedule['configurations']:
        content += f'<pre>{e(json.dumps(configuration, ensure_ascii=False, indent=2))}</pre>'
    return content + '</details>'


def allowance_panel(allowance):
    """Render actual shared consumption separately from immutable task authority."""
    return (f'<section class="panel"><h2>Shared daily new-post allowance</h2><p>Day: {e(allowance["accounting_day"])} '
            f'· {e(allowance["accounting_timezone"])} · Limit: {e(allowance["limit"])} · Used: {e(allowance["used"])} '
            f'· Remaining: {e(allowance["remaining"])}</p><p>Fewer records can be returned because of overlap, '
            'ineligible records, source coverage or limits. This allowance is independent of requests, record caps and costs.</p>'
            f'<pre>{e(json.dumps(allowance, ensure_ascii=False))}</pre></section>')
