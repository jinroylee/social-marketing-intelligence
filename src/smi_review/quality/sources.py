"""Explicit projections of public result readers; source values are never cached."""

from smi_ingestion.evidence import EvidenceError


def require(condition, code):
    if not condition:
        raise EvidenceError(code)


def permitted(statuses):
    return all(all(s.get(k, False) for k in ('can_process', 'can_display', 'can_retain', 'current'))
               for s in statuses.values())


def published_at(member, subject_id=None):
    if subject_id is None:
        subjects = {a['subject_id'] for a in member['assertions']}
        if len(subjects) != 1:
            return None
        subject_id = next(iter(subjects))
    dates = [a['value'] for a in member['assertions'] if a['field'] == 'published_at'
             and a['state'] == 'observed' and (subject_id is None or a['subject_id'] == subject_id)]
    return dates[0] if dates and all(d == dates[0] for d in dates) else None


def answer_findings(result):
    """Keep selected values while binding dates to every exact supporting bundle.

    A support ID can occur in multiple publications; never borrow an arbitrary
    duplicate's publication or an observation-wide interpretation date.
    """
    query = result['knowledge_query']
    members = {(m['publication_id'], m['observation_id']): m for m in query['members']}
    output = []
    for fact in result['findings']:
        bindings = []
        field = {'assertion': 'assertion_ids', 'metric': 'metric_ids', 'interpretation': 'interpretation_ids'}[fact['kind']]
        for selected in query['manifest']:
            if fact['support_id'] not in selected[field]:
                continue
            member = members[(selected['publication_id'], selected['observation_id'])]
            bindings.append({key: selected[key] for key in ('publication_id', 'observation_id', 'derivation_id',
                'publication_time', 'publication_method', 'publication_producer')} | {
                'source_subject_id': fact['detail']['subject_id'], 'source_published_at': published_at(member, fact['detail']['subject_id'])})
        output.append({'support_id': fact['support_id'], 'kind': fact['kind'], 'value': fact['value'],
            'detail': {key: value for key, value in fact['detail'].items() if key not in {'published_at', 'source_reference'}},
            'support_bindings': bindings})
    return output


def query_sources(query, statuses):
    """Expose only governed canonical text, exact spans and original source dates."""
    output = []
    manifests = {(m['publication_id'], m['observation_id']): m for m in query['manifest']}
    claims = {c['id']: c for c in query['interpretations'] if c['state'] == 'supported'}
    for member in query['members']:
        oid = member['observation_id']
        selected = manifests[(member['publication_id'], oid)]
        available = permitted({oid: statuses[oid]}) and member['availability'] == 'available'
        item = {key: member.get(key) for key in ('observation_id', 'publication_id', 'derivation_id',
            'assertion_ids', 'metric_ids', 'captured_at', 'source_as_of', 'ingested_at')}
        item.update(available=available, texts=[], spans=[])
        if available:
            item['source_reference'] = member.get('source_reference')
            item['method'] = member.get('method')
            item['publication_context'] = {key: selected[key] for key in ('publication_method', 'publication_time', 'publication_producer')}
            item['texts'] = [{'support_id': a['assertion_id'], 'field': a['field'], 'original_text': a['value'],
                'source_subject_id': a['subject_id'], 'identity': {key: a[key] for key in ('platform', 'namespace', 'kind', 'native_id')},
                'source_published_at': published_at(member, a['subject_id']), 'span': {'start': 0, 'end': len(a['value'])}}
                for a in member['assertions'] if a['state'] == 'observed' and isinstance(a['value'], str)
                and a['assertion_id'] in selected['assertion_ids'] and a['field'] in {'caption', 'text', 'bio', 'display_name', 'handle'}]
            item['published_at'] = published_at(member)
            for claim_id in selected['interpretation_ids']:
                claim = claims.get(claim_id)
                original = next((t for t in item['texts'] if claim and t['support_id'] == claim['source_assertion_id']
                    and t['source_subject_id'] == claim['subject_id']), None)
                if original is None or claim['observation_id'] != oid:
                    continue
                span = claim['span']
                if original['original_text'][span['start']:span['end']] != span['text']:
                    continue
                item['spans'].append({'interpretation_id': claim_id, 'source_assertion_id': claim['source_assertion_id'],
                    'source_subject_id': claim['subject_id'], 'publication_id': member['publication_id'],
                    'span': span, 'method_version': claim['method_version'], 'source_published_at': original['source_published_at']})
        output.append(item)
    return output
