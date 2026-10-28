"""Escaped topic configuration and policy-aware recent X window/timeline panels."""

import json
import uuid

from .views import e, hidden, value, error_message


DEFAULT_SETTINGS = {'query': 'cushion', 'cadence_minutes': 60, 'window_minutes': 120, 'max_records': 50,
                    'retention_hours': 24, 'source_policy_id': 'offline-x'}


def configuration(csrf, topic=None, submitted=None):
    key = topic['topic_key'] if topic else ''
    settings = topic['revisions'][-1]['document'] if topic else DEFAULT_SETTINGS
    action = '/monitoring/topics/' + key if topic else '/monitoring/topics'
    return f'''<form method="post" action="{e(action)}">{hidden('csrf', csrf)}
{hidden('request_id', value(submitted, 'request_id', str(uuid.uuid4())))}
{hidden('expected_version', value(submitted, 'expected_version', topic['version'] if topic else 0))}
<label>Stable topic key<input name="topic_key" value="{e(value(submitted, 'topic_key', key))}" required></label>
<label>Topic settings JSON<textarea name="settings" rows="10" required>{e(value(submitted, 'settings', json.dumps(settings, indent=2)))}</textarea></label>
<p>The source policy must already be configured by a trusted operator. Cadence is an explicit UTC epoch boundary; collection is manually invoked.</p>
<button type="submit">Save topic revision</button></form>'''


def index(topics, csrf, operator, submitted=None, error=None):
    content = '<h1>Recent X monitoring topics</h1><p>Bounded offline fixture evidence, independent of scheduled KB keywords and frozen snapshot investigations.</p>'
    if error:
        content += error_message(error)
    content += ''.join(f'<p><a href="/monitoring/topics/{e(t["topic_key"])}">{e(t["topic_key"])}</a> · revision {t["version"]}</p>' for t in topics)
    if operator:
        content += '<section class="panel"><h2>Configure a topic</h2>' + configuration(csrf, submitted=submitted) + '</section>'
    return content


def observation(record):
    content = f'<section class="panel"><h2>X post {e(record["native_id"])}</h2><p><a href="/monitoring/observations/{e(record["observation_id"])}">Capture detail</a> · <a href="{e(record["source_reference"])}" rel="noreferrer">Source reference</a></p>'
    if record['body'] is None:
        content += f'<p>Evidence unavailable: {e(record["state"])}</p>'
    else:
        content += f'<p class="lede">{e(record["body"]["text"])}</p><p>Source metrics: {e(json.dumps(record["body"]["metrics"], sort_keys=True))}</p>'
    content += '<dl>' + ''.join(f'<dt>{e(k)}</dt><dd>{e(record[k] if record[k] is not None else "Unknown")}</dd>' for k in ('captured_at', 'published_at', 'metric_measured_at', 'imported_at', 'retain_until')) + '</dl>'
    content += f'<p>Missing fields: {e(", ".join(record["missing_fields"]) or "None reported")}</p><p>Original capture: {e(record["capture_id"])} · policy: {e(record["policy_context_id"])}</p>'
    content += '<details><summary>Acquisition and metric meanings</summary><pre>' + e(json.dumps(record['acquisition'], indent=2)) + '</pre><ul>' + ''.join(f'<li>{e(k)}: {e(v)}</li>' for k, v in record['metric_definitions'].items()) + '</ul></details></section>'
    return content


def topic(topic, timeline, csrf, operator, submitted=None, error=None):
    key = topic['topic_key']
    content = f'<p><a href="/monitoring/topics">← Topics</a></p><h1>{e(key)}</h1><p>Topic revision {topic["version"]}. Current source policy: {e(json.dumps(topic["source_policy"], sort_keys=True))}</p>'
    if error:
        content += error_message(error)
    if operator:
        content += '<details class="panel"><summary>Revise settings</summary>' + configuration(csrf, topic, submitted) + '</details>'
        content += f'<form method="post" action="/monitoring/topics/{e(key)}/poll">{hidden("csrf", csrf)}<label>Window end (explicit UTC cadence boundary)<input name="window_end" value="{e(value(submitted, "window_end"))}" placeholder="2026-10-28T12:00:00+00:00" required></label><button type="submit">Collect bounded offline window</button></form>'
    content += '<p><a href="/monitoring/assessments">Assess volume / retained assessment history</a> · <a href="/monitoring/semantic-assessments">Assess possible controversy / semantic history</a></p>'
    content += '<h2>Original collection windows</h2><p>Latest 100 windows. Empty or partial fixture coverage does not establish market absence.</p>'
    content += ''.join(f'<p><a href="/monitoring/windows/{e(w["id"])}">{e(w["window_start"])} → {e(w["window_end"])}</a></p>' for w in topic['windows'])
    content += '<h2>Retained capture timeline</h2><p>Distinct captures; repeated windows do not refresh source or import times. This is not a trend or alert.</p>'
    content += ''.join(observation(o) for o in timeline['observations']) or '<p>No captures retained.</p>'
    if timeline['has_more']:
        content += f'<p><a href="/monitoring/topics/{e(key)}?offset={timeline["offset"] + timeline["limit"]}">Next captures</a></p>'
    content += '<details><summary>Configuration history</summary><pre>' + e(json.dumps(topic['revisions'], indent=2)) + '</pre></details>'
    return content


def window(record, csrf=None, operator=False, submitted=None, error=None):
    content = f'<p><a href="/monitoring/topics/{e(record["topic_key"])}">← Topic</a></p><h1>Recent X collection window</h1><p>Window ID: {e(record["window_id"])} · <a href="/monitoring/assessments">Assess volume</a></p><p>{e(record["window_start"])} → {e(record["window_end"])}</p><p>Market coverage: {e(record["coverage"]["market_coverage"])}</p>'
    content += '<pre>' + e(json.dumps({'coverage': record['coverage'], 'acquisition': record['acquisition'], 'topic_revision_id': record['topic_revision_id'], 'collected_by': record['collected_by'], 'imported_at': record['imported_at']}, indent=2)) + '</pre>'
    if error:
        content += error_message(error)
    if operator:
        content += f'<form method="post" action="/monitoring/windows/{e(record["window_id"])}/promote">{hidden("csrf", csrf)}{hidden("request_id", value(submitted, "request_id", str(uuid.uuid4())))}<h2>Promote selected observations</h2><p>Choose at most twenty retained captures for normal knowledge ingestion/publication. Original synthetic status and source restrictions remain applicable. No new source request is made.</p>'
        for item in record['observations']:
            if item['body'] is not None:
                checked = ' checked' if submitted and item['observation_id'] in submitted.get('selected', []) else ''
                content += f'<label><input type="checkbox" name="selected" value="{e(item["observation_id"])}"{checked}>X post {e(item["native_id"])} · {e(item["captured_at"] or "Unknown capture time")}</label>'
        content += '<button type="submit">Promote selected</button></form>'
    return content + ''.join(observation(o) for o in record['observations'])


def promotion_result(record):
    content = f'<h1>Monitoring promotion result</h1><p>Original outcome: {e(record["status"])} · selected by {e(record["recorded_by"])} at {e(record["recorded_at"])}</p><p><a href="/monitoring/windows/{e(record["window_id"])}">Original monitoring window</a></p><p>Historical publication links do not establish current support permission. Open the publication to inspect current availability. Synthetic evidence requires explicit development visibility.</p>'
    for item in record['items']:
        content += f'<section class="panel"><p>Monitoring capture <a href="/monitoring/observations/{e(item["monitoring_observation_id"])}">{e(item["monitoring_observation_id"])}</a> · original result: {e(item["state"])}</p>'
        if item.get('publication_id'):
            content += f'<p><a href="/knowledge/publications/{e(item["publication_id"])}?include_synthetic=yes">Knowledge publication (include synthetic)</a> · ingestion run: {e(item["run_id"])} · source observation: {e(item["observation_id"])}</p>'
        content += '</section>'
    return content
