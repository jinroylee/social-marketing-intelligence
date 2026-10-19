"""Escaped publication metadata and current-policy source support."""

import json

from .views import e, source_link


def index(publications):
    """Link committed publications without reading or copying source text."""
    content = '<h1>Knowledge publications</h1><p>Bounded ingested support made available for knowledge use.</p>'
    for publication in publications:
        identity = publication['publication_id']
        content += f'<section class="panel"><h2><a href="/knowledge/publications/{e(identity)}">{e(identity)}</a></h2>'
        content += f'<p>Published {e(publication["published_at"])} by {e(publication["producer"]["actor_id"])} ({e(publication["producer"]["kind"])})</p>'
        content += f'<p>{e(publication["coverage"]["members"])} selected source members</p></section>'
    return content if publications else content + '<p>No publications yet.</p>'


def detail(publication):
    """Show exact pinned support, withholding denied and superseded source text."""
    content = f'<h1>Knowledge publication</h1><p>{e(publication["publication_id"])}</p>'
    content += f'<p>Published {e(publication["published_at"])} by {e(publication["producer"]["actor_id"])} ({e(publication["producer"]["kind"])})<br>Method: {e(publication["method_version"])}</p>'
    content += f'<p>Original coverage: {e(json.dumps(publication["coverage"]))}<br>Current support: {e(json.dumps(publication["current_coverage"]))}</p>'
    content += '<p>Publication time does not renew source capture time. Unknown profile and interpretation attributes remain unknown.</p>'
    for member in publication['members']:
        content += f'<section class="panel"><h2>Observation {e(member["observation_id"])}</h2><p>Derivation {e(member["derivation_id"])}</p>'
        content += f'<p>Assertion IDs: {e(", ".join(member["assertion_ids"]))}<br>Metric IDs: {e(", ".join(member["metric_ids"]))}</p>'
        if member['availability'] != 'available':
            content += '<p>Source support unavailable under current policy.</p></section>'
            continue
        if member['support_status'] != 'current':
            content += '<p>Superseded support — review required.</p></section>'
            continue
        content += f'<p>{source_link(member["source_reference"])}<br>Captured: {e(member["captured_at"] or "Unknown")}<br>Source as of: {e(member["source_as_of"] or "Unknown")}<br>Ingested: {e(member["ingested_at"])}</p>'
        content += f'<p>Source method: {e(json.dumps(member["method"]))}<br>Source coverage: {e(json.dumps(member["coverage"], ensure_ascii=False))}</p>'
        for assertion in member['assertions']:
            value = json.dumps(assertion['value'], ensure_ascii=False) if assertion['state'] == 'observed' else 'Unknown (' + assertion['state'] + ')'
            content += f'<p><strong>{e(assertion["kind"])} {e(assertion["native_id"])}</strong> · {e(assertion["field"])}: {e(value)}<br>{e(assertion["assertion_id"])}</p>'
        for metric in member['metrics']:
            content += f'<p>{e(metric["definition"])}: {e(metric["value"])} · {e(metric["measured_at"] or "Unknown")}<br>{e(metric["metric_id"])}</p>'
        content += '</section>'
    content += '<h2>Caption interpretations</h2>'
    if not publication['interpretations']:
        content += '<p>Unknown — no caption interpretations were published.</p>'
    for claim in publication['interpretations']:
        content += f'<section class="panel"><h3>{e(claim["id"])}</h3><p>Run {e(claim["run_id"])} · {e(claim["method_version"])} · catalog {e(claim["catalog_id"])}</p>'
        if claim['state'] == 'supported':
            content += f'<p>{e(claim["predicate"])}: {e(json.dumps(claim["value"], ensure_ascii=False))}<br>{e(claim["span"]["text"])} · {e(claim["review_status"])} · {e(claim["basis"])}</p>'
        else:
            content += f'<p>{e(claim["state"])}: {e(claim["reason"])}</p>'
        content += '</section>'
    return content
