"""Escaped source-free synthetic accounting details."""

import json

from .views import e


def control_summary(operation):
    """Show known contract bounds separately from delayed billing/control limits."""
    limits = operation['limits']
    bound = limits['known_charge_bound']
    bound = 'Unknown' if bound is None else f'{bound} {operation["scope"]["currency"]}'
    return (f'<p>Known charge bound: {e(bound)}</p><p>Bound status: {e(limits["bound_status"])}</p><p>Billing state: {e(limits["billing_state"])} · '
            f'Meter health: {e(limits["meter_health"])}</p><p>Enforcement basis: {e(limits["enforcement_basis"])}</p>'
            '<p>Billing lag bound: Unknown. Unresolved charges have no automatic expiry.</p>'
            '<p>No zero-overshoot guarantee for delayed or unbounded charges.</p>')


def task_summary(operations):
    """Reopen current accounting control independently of saved task progress."""
    if not operations:
        return ''
    content = '<h2>Current cost control</h2>'
    for operation in operations:
        content += f'<p><a href="/costs/{e(operation["operation_id"])}">Exact cost operation</a> · {e(operation["coverage"]["status"])}</p>'
        content += control_summary(operation)
    return content


def index(operations):
    """List at most 100 retained operations; missing records establish no zero cost."""
    content = '<h1>Usage and costs</h1><p>Newest 100 operations. Coverage beyond configured records is unknown. Open an operation for its authoritative scope allowance.</p>'
    for operation in operations:
        content += f'<p><a href="/costs/{e(operation["operation_id"])}">{e(operation["scope"]["service"])}</a> · {e(operation["method"])} · {e(operation["coverage"]["status"])}</p>'
    return content if operations else content + '<p>No recorded operations. Cost is unknown.</p>'


def detail(operation):
    """Separate measured, declared and unknown amounts without commercial claims."""
    scope = operation['scope']
    def value(section):
        amount = operation[section]['amount']
        return 'Unknown' if amount is None else f'{amount} {scope["currency"]}'
    content = f'<h1>Cost detail</h1><p>{e(scope["provider"])} / {e(scope["service"])} · {e(scope["classification"])}</p>'
    control = operation['enforced_monetary_control']
    content += '<p>No commercial charge. Measured units and rates are synthetic development inputs.</p>'
    content += '<p>Enforced synthetic monetary ceiling.</p>' if control else '<p>No enforced monetary ceiling.</p>'
    if control:
        content += f'<p>Scope ceiling: {e(operation["allowance"]["ceiling_amount"])} {e(scope["currency"])}</p>'
    content += f'<p>Admission: {e(json.dumps(operation["admission"]))}</p><p>Authoritative scope allowance: {e(json.dumps(operation["allowance"]))}</p>'
    content += control_summary(operation)
    content += f'<p>Synthetic measured amount: {e(value("actuals"))}</p><p>Forecasts: {e(value("forecasts"))}</p><p>Outstanding commitments: {e(value("commitments"))}</p>'
    content += f'<p>Coverage: {e(operation["coverage"]["status"])} · Unknown cost: {e(operation["coverage"]["unknown_cost"])}</p>'
    content += '<p>Declared commitments do not authorize work or reserve a ceiling. Missing amounts are unknown; amounts from different currencies or periods are not combined.</p>'
    if operation['task_id']:
        content += f'<p><a href="/tasks/{e(operation["task_id"])}">Exact task</a> · Attempt {e(operation["attempt_id"])}</p>'
    for label, item in (('Operation', operation['operation_id']), ('Workspace', operation['workspace_id']),
                        ('Actor', operation['actor']), ('Method', operation['method']), ('Configuration', scope),
                        ('Entries and provenance', operation['entries']), ('Final reconciliations', operation['reconciliations']),
                        ('Meter recoveries', operation['meter_recoveries']), ('Unresolved identities', operation['unresolved'])):
        content += f'<p>{e(label)}: {e(json.dumps(item, ensure_ascii=False))}</p>'
    return content
