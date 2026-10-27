"""Escaped configured sample comparisons and governed original alert support."""

import json
import uuid
from dataclasses import asdict

from . import recent_views
from .views import e, error_message, hidden, value


def index(assessments, csrf, operator, threshold, submitted=None, error=None):
    """Show saved limitations alongside supported alerts, with explicit pair selection."""
    content = '<h1>Quantitative X assessments</h1><p>Distinct native posts in explicit comparable windows. Synthetic sample thresholds do not establish independent statistical proof or complete market coverage.</p>'
    if error:
        content += error_message(error)
    if operator and threshold:
        content += '<p>Configured thresholds: ' + e(json.dumps(asdict(threshold), sort_keys=True)) + '</p>'
        content += f'<form method="post" action="/monitoring/assessments">{hidden("csrf", csrf)}{hidden("request_id", value(submitted, "request_id", str(uuid.uuid4())))}'
        content += f'<label>Detection window ID<input name="detection_window_id" value="{e(value(submitted, "detection_window_id"))}" required></label>'
        content += f'<label>Baseline window ID (empty records missing baseline)<input name="baseline_window_id" value="{e(value(submitted, "baseline_window_id"))}"></label><button type="submit">Assess volume</button></form>'
    else:
        content += '<p>Detection requires a trusted monitoring operator and explicit server threshold configuration.</p>'
    content += '<h2>Latest 100 assessments</h2>'
    for record in assessments:
        content += f'<p><a href="/monitoring/assessments/{e(record["assessment_id"])}">{e(record["recorded_at"])}</a> · historical outcome {e(record["outcome"])} · current support {e(record["current_support"])}</p>'
    return content


def detail(record):
    """Render numbers only when the alert owner makes current comparison available."""
    content = '<p><a href="/monitoring/assessments">← Assessment history</a> · <a href="/inbox">Inbox</a></p><h1>Quantitative X assessment</h1>'
    content += f'<p>Historical outcome: {e(record["outcome"])} · current support: {e(record["current_support"])}</p>'
    if record['comparison']:
        comparison = record['comparison']
        content += f'<p>Scoped sample: {comparison["baseline_posts"]} → {comparison["detection_posts"]} distinct X posts; increase {comparison["increase_posts"]}; ratio {comparison["ratio"]}.</p>'
    else:
        content += '<p>No current quantitative claim. Evidence or comparison is unavailable or insufficient.</p>'
    content += '<p>Limitations: ' + e(', '.join(record['limitations']) or 'None for this configured sample comparison') + '</p>'
    content += '<pre>' + e(json.dumps(record['method'], indent=2)) + '</pre>'
    content += f'<p>Recorded by {e(record["recorded_by"])} ({e(record["actor_kind"])}) at {e(record["recorded_at"])}.</p>'
    if record['alert_id']:
        content += f'<p>Retained alert: <a href="/monitoring/alerts/{e(record["alert_id"])}">{e(record["alert_id"])}</a> · local notification {e(record["notification_id"])}</p>'
    for name, window in record['windows'].items():
        content += f'<h2>{e(name.title())} window</h2>'
        content += recent_views.window(window) if window else '<p>Baseline missing.</p>'
    return content
