"""Strict explicit human inputs; completion describes recorded review, not truth."""

from datetime import datetime
import math

from .sources import require

LABELS = ('supported', 'unsupported', 'ambiguous', 'not_assessable')


def template(membership):
    """Return an unanswered submission; identities alone are machine supplied."""
    return {'reviewer': None, 'attested': False, 'reviewed_at': None, 'method_version': None,
        'denominator': len(membership), 'items': [{'item_id': identity, 'translation': None,
            'translator': {'actor_id': None, 'kind': None, 'method_version': None, 'model_version': None},
            'label': None, 'ambiguity': None, 'material_error': None, 'error': None, 'correction': None}
            for identity in membership], 'marketer_usefulness': None}


def text(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 16000 and '\x00' not in value


def timestamp(value):
    try:
        return isinstance(value, str) and datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is not None
    except ValueError:
        return False


def validate(body, membership, actor):
    """Validate attribution and exact reviewed IDs without filling human fields."""
    require(isinstance(body, dict) and set(body) == {'reviewer', 'attested', 'reviewed_at', 'method_version',
        'denominator', 'items', 'marketer_usefulness'}, 'invalid_review_record')
    require(body['reviewer'] == actor.actor_id and body['attested'] is True and timestamp(body['reviewed_at'])
        and text(body['method_version']), 'invalid_review_attribution')
    require(type(body['denominator']) is int and body['denominator'] == len(membership), 'invalid_review_denominator')
    items = body['items']
    require(isinstance(items, list) and 1 <= len(items) <= len(membership), 'invalid_review_membership')
    seen, translators = set(), []
    for item in items:
        require(isinstance(item, dict) and set(item) == {'item_id', 'translation', 'translator', 'label',
            'ambiguity', 'material_error', 'error', 'correction'}, 'invalid_review_item')
        identity = item['item_id']
        require(isinstance(identity, str) and identity in membership and identity not in seen, 'invalid_review_membership')
        seen.add(identity)
        require(item['label'] in LABELS and text(item['translation']) and type(item['material_error']) is bool,
            'invalid_review_judgment')
        require(all(item[k] is None or text(item[k]) for k in ('ambiguity', 'error', 'correction'))
            and (not item['material_error'] or text(item['error'])), 'invalid_review_material_error')
        translator = item['translator']
        require(isinstance(translator, dict) and set(translator) == {'actor_id', 'kind', 'method_version', 'model_version'},
            'invalid_review_translator')
        require(text(translator['actor_id']) and translator['kind'] in ('human', 'automation')
            and text(translator['method_version']) and (text(translator['model_version']) if translator['kind'] == 'automation'
                else translator['model_version'] is None), 'invalid_review_translator')
        translators.append(translator)
    usefulness = body['marketer_usefulness']
    if usefulness is not None:
        require(isinstance(usefulness, dict) and set(usefulness) == {'useful', 'rationale', 'task_seconds', 'inspected_posts'},
            'invalid_review_usefulness')
        require(type(usefulness['useful']) is bool and text(usefulness['rationale'])
            and type(usefulness['task_seconds']) in (int, float) and math.isfinite(usefulness['task_seconds'])
            and usefulness['task_seconds'] >= 0 and type(usefulness['inspected_posts']) is int
            and usefulness['inspected_posts'] >= 0, 'invalid_review_usefulness')
    return {'reviewer': actor.actor_id, 'reviewed_at': body['reviewed_at'], 'method_version': body['method_version'],
        'reviewed_item_ids': [i['item_id'] for i in items], 'denominator': body['denominator'], 'translators': translators}


def assessment(body, selected):
    """Report annotation completeness separately from technical/original/usefulness gates."""
    quality = {'technical': 'pending', 'translation_assisted': 'pending',
        'japanese_original': 'not_validated', 'marketer_usefulness': 'pending'}
    counts = dict.fromkeys(LABELS, 0)
    if body:
        for item in body['items']:
            counts[item['label']] += 1
        uncorrected = any(i['material_error'] and i['correction'] is None for i in body['items'])
        quality['translation_assisted'] = 'failed' if uncorrected else 'recorded' if len(body['items']) == selected else 'pending'
        if body['marketer_usefulness'] is not None:
            quality['marketer_usefulness'] = 'recorded' if body['marketer_usefulness']['useful'] and not uncorrected else 'failed'
    return quality, counts
