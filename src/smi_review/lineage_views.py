"""Escaped content-free task lineage and current governed navigation."""

import json

from . import cost_views
from .views import e


def detail(trace):
    """Keep recorded completion separate from current support and cost coverage."""
    task_id = trace['task_id']
    content = f'<h1>Task pipeline lineage</h1><p><a href="/tasks/{e(task_id)}">Task {e(task_id)}</a></p>'
    content += '<p>Read-only committed history. Owner reads can observe different committed frontiers while work continues. Source wording stays in governed evidence pages.</p>'
    content += '<p>Queue acceptance does not establish source success or usable knowledge. No update does not establish market absence.</p>'
    synthetic = trace['include_synthetic']
    content += ('<p>Synthetic development support explicitly visible.</p>' if synthetic else
                f'<p>Synthetic support excluded. <a href="/tasks/{e(task_id)}/lineage?include_synthetic=yes">Include synthetic development support</a></p>')
    labels = {'queue': 'Queue acceptance', 'source': 'Source collection', 'ingestion': 'Ingestion',
              'publication': 'Publication', 'completion': 'Historical completion'}
    for key, label in labels.items():
        content += f'<p>{e(label)}: {e(trace["stages"][key])}</p>'
    for label, item in (('Original authority', trace['authority']), ('Submitted', trace['submitted_at']),
                        ('Finished', trace['finished_at']), ('Current execution', trace['execution']),
                        ('Recorded progress', trace['progress']), ('Failure', trace['failure']),
                        ('Historical coverage', trace['historical_coverage']), ('Resource limits', trace['limits'])):
        content += f'<p>{e(label)}: {e(json.dumps(item, ensure_ascii=False))}</p>'
    content += '<h2>Attempts and ingestion runs</h2><p>Recovery reuses actual identities. Recent phase history is bounded to 100 entries; recent recovery actors to 20. The total recovery count is retained.</p>'
    for attempt in trace['attempts']:
        run = attempt['run']
        content += f'<h3>Attempt {e(attempt["number"])} · {e(attempt["attempt_id"])}</h3>'
        for label, item in (('Original producer', attempt['producer']), ('Started', attempt['started_at']),
                            ('Finished', attempt['finished_at']), ('Recovery count', attempt['recovery_count']),
                            ('Resumed by', attempt['resumed_by']), ('Recorded phases', attempt['phases']),
                            ('Prepared exact support', attempt['prepared_support'])):
            content += f'<p>{e(label)}: {e(json.dumps(item, ensure_ascii=False))}</p>'
        content += f'<p>Ingestion run: {e(run["run_id"])} · {e(run["status"])} · input complete: {e(run["input_complete"])}</p>'
        content += f'<p>Created: {e(run["created_at"])} · requests: {e(run["requests_used"])} · bytes: {e(run["bytes_used"])} · records: {e(run["records_used"])} · issue count: {e(run["issue_count"])}</p>'
        content += f'<p>Observation states: {e(json.dumps(run["counts"]))} · Waiting: {e(json.dumps(run["waiting"]))}</p>'
        content += '<p>At most 100 observations and 20 newest derivations per observation. Ingestion time is local persistence time; source capture/as-of dates can be unknown.</p>'
        if run['observations_truncated']:
            content += '<p>Observation history truncated.</p>'
        for observation in run['observations']:
            content += f'<h4>Observation {e(observation["observation_id"])}</h4><p>Status: {e(observation["status"])} · Availability: {e(observation["availability"])} · {e(observation["reason"] or "")}</p>'
            content += f'<p>Source method: {e(json.dumps(observation["source"]))}</p>'
            content += f'<p>Source capture: {e(observation["captured_at"] or "Unknown / withheld")} · Source as-of: {e(observation["source_as_of"] or "Unknown / withheld")} · Ingested: {e(observation["ingested_at"])}</p>'
            for derivation in observation['derivations']:
                content += f'<p>Derivation: {e(derivation["derivation_id"])} · Mapper: {e(derivation["mapper_key"])} · Processing revision: {e(derivation["policy_version"])} · {e(derivation["support_status"])} · Derived: {e(derivation["derived_at"])}</p>'
            if observation['derivations_truncated']:
                content += '<p>Derivation history truncated.</p>'
    if not trace['attempts']:
        content += '<p>No worker attempt or ingestion run recorded.</p>'
    content += '<h2>Receipted publications and current support</h2><p>Historical published counts describe the original outcome. Current usability requires process/display/retention permission and current derivation health.</p>'
    for publication in trace['publications']:
        content += f'<h3>Publication {e(publication["publication_id"])}</h3>'
        content += f'<p>Availability: {e(publication["availability"])} · Currently permitted members: {e(publication["current_support"]["available_members"])} · Unavailable members: {e(publication["current_support"]["unavailable_members"])}</p>'
        for key in ('published_at', 'producer', 'method_version', 'coverage', 'support'):
            if key in publication:
                content += f'<p>{e(key)}: {e(json.dumps(publication[key], ensure_ascii=False))}</p>'
        if publication['href']:
            content += f'<p><a href="{e(publication["href"])}">Open currently permitted publication evidence</a></p>'
    if not trace['publications']:
        content += '<p>No publication receipt recorded for this task.</p>'
    content += '<h2>Attributable usage and costs</h2><p>Newest 100 exact task operations. Recorded attribution does not establish complete billing coverage. Missing costs are unknown; currencies and accounting periods are not combined.</p>'
    if trace['costs']['truncated']:
        content += '<p>Cost operation history truncated; older attribution remains outside this view.</p>'
    if not trace['costs']['operations']:
        content += '<p>No recorded attributable operation. Cost is unknown.</p>'
    for operation in trace['costs']['operations']:
        content += f'<p><a href="/costs/{e(operation["operation_id"])}">Cost operation {e(operation["operation_id"])}</a></p>'
        content += cost_views.detail(operation).replace('<h1>Cost detail</h1>', '<h3>Cost detail</h3>')
    return content
