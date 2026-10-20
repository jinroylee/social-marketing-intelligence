"""Explicit final-evidence resolution within the accounting owner's scope lock."""

from decimal import Decimal

from psycopg.types.json import Jsonb

from smi_ingestion.evidence import EvidenceError

from .contracts import text, timestamp


def target_ids(values):
    if not isinstance(values, (tuple, list)) or len(values) > 200:
        raise EvidenceError('invalid_cost_reconciliation_targets')
    for value in values:
        text(value, 'measurement_id')
    if len(set(values)) != len(values):
        raise EvidenceError('invalid_cost_reconciliation_targets')
    return sorted(values)


def resolved_entries(reconciliations):
    """Return explicitly resolved entry identities without changing their audit rows."""
    return {mid for r in reconciliations for key in ('commitment_ids', 'uncertainty_ids') for mid in r['body'][key]}


def recovered_failures(recoveries):
    return {mid for r in recoveries for mid in r['body']['failure_ids']}


def recover_meter(costs, operation_id, actor, *, recovery_id, failure_ids, recovered_at, provenance, evidence_id, measurement_basis='synthetic'):
    actor.require_workspace(costs.workspace_id, importing=True)
    for value, name in ((recovery_id, 'recovery_id'), (provenance, 'provenance'), (evidence_id, 'evidence_id')):
        text(value, name)
    failure_ids = target_ids(failure_ids)
    if not failure_ids:
        raise EvidenceError('invalid_cost_recovery_targets')
    operation = costs.read(operation_id, actor)
    oid = operation['operation_id']
    if measurement_basis not in {'synthetic', 'provider_reported'} or operation['scope'].get('measurement_basis', 'synthetic') != measurement_basis:
        raise EvidenceError('cost_measurement_basis_mismatch')
    if operation['scope']['classification'] != 'metered':
        raise EvidenceError('cost_scope_not_metered')
    at = timestamp(recovered_at)
    body = {'failure_ids': failure_ids, 'recovered_at': at.isoformat(), 'provenance': provenance,
            'evidence_id': evidence_id, 'operator': {'actor_id': actor.actor_id, 'kind': actor.kind},
            **({'measurement_basis': measurement_basis} if measurement_basis == 'provider_reported' else {})}
    with costs.db.connect() as connection:
        costs._lock_scope(connection, operation['scope']['scope_id'])
        connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',
                           (f'cost-recovery:{costs.workspace_id}:{recovery_id}',))
        prior = connection.execute('SELECT * FROM cost_meter_recoveries WHERE workspace_id=%s AND recovery_id=%s',
                                   (costs.workspace_id, recovery_id)).fetchone()
        if prior:
            if str(prior['operation_id']) != oid or prior['body'] != body:
                raise EvidenceError('cost_meter_recovery_conflict')
            return {'status': 'duplicate', 'recovery_id': recovery_id}
        reconciliations = connection.execute('SELECT body FROM cost_reconciliations WHERE workspace_id=%s AND operation_id=%s',
                                            (costs.workspace_id, oid)).fetchall()
        recoveries = connection.execute('SELECT body FROM cost_meter_recoveries WHERE workspace_id=%s AND operation_id=%s',
                                       (costs.workspace_id, oid)).fetchall()
        resolved, recovered = resolved_entries(reconciliations), recovered_failures(recoveries)
        for mid in failure_ids:
            entry = connection.execute('SELECT operation_id,kind,body FROM cost_entries WHERE workspace_id=%s AND measurement_id=%s',
                                       (costs.workspace_id, mid)).fetchone()
            if not entry or str(entry['operation_id']) != oid or entry['kind'] != 'meter_failure':
                raise EvidenceError('invalid_cost_recovery_targets')
            if mid not in resolved:
                raise EvidenceError('cost_meter_failure_unreconciled')
            if mid in recovered:
                raise EvidenceError('cost_meter_failure_already_recovered')
            final = next(r for r in reconciliations if mid in r['body']['uncertainty_ids'])
            if at < timestamp(final['body']['reconciled_at']) or at < timestamp(entry['body']['measured_at']):
                raise EvidenceError('invalid_cost_recovery_time')
        connection.execute('INSERT INTO cost_meter_recoveries(workspace_id,recovery_id,operation_id,body) VALUES (%s,%s,%s,%s)',
                           (costs.workspace_id, recovery_id, oid, Jsonb(body)))
    return {'status': 'recorded', 'recovery_id': recovery_id}


def reconcile_usage(costs, operation_id, actor, *, reconciliation_id, measurement_id, units,
                    rate_version, measured_at, provenance, reconciled_at, evidence_id, outcome,
                    settle_admission, commitment_ids, uncertainty_ids, measurement_basis='synthetic'):
    actor.require_workspace(costs.workspace_id, importing=True)
    for value, name in ((reconciliation_id, 'reconciliation_id'), (measurement_id, 'measurement_id'),
                        (evidence_id, 'evidence_id')):
        text(value, name)
    if not isinstance(outcome, str) or outcome not in {'succeeded', 'failed'}:
        raise EvidenceError('invalid_cost_final_outcome')
    commitment_ids, uncertainty_ids = target_ids(commitment_ids), target_ids(uncertainty_ids)
    if type(settle_admission) is not bool or not (settle_admission or commitment_ids or uncertainty_ids):
        raise EvidenceError('invalid_cost_reconciliation_targets')
    operation = costs.read(operation_id, actor)
    oid = operation['operation_id']
    if measurement_basis not in {'synthetic', 'provider_reported'} or operation['scope'].get('measurement_basis', 'synthetic') != measurement_basis:
        raise EvidenceError('cost_measurement_basis_mismatch')
    usage = costs._usage_body(operation['scope'], units, rate_version, measured_at, provenance)
    admission = operation['admission']
    bound_failure = (f'reconciliation-meter:{oid}' if settle_admission and admission
                     and Decimal(usage['units']) > Decimal(admission['max_units']) else None)
    if bound_failure:
        uncertainty_ids = sorted(set(uncertainty_ids) | {bound_failure})
    at = timestamp(reconciled_at)
    if at < timestamp(measured_at):
        raise EvidenceError('invalid_cost_reconciliation_time')
    body = {'settle_admission': settle_admission, 'commitment_ids': commitment_ids, 'uncertainty_ids': uncertainty_ids,
            'evidence_id': evidence_id, 'outcome': outcome, 'reconciled_at': at.isoformat(),
            'provenance': provenance, 'operator': {'actor_id': actor.actor_id, 'kind': actor.kind},
            **({'measurement_basis': measurement_basis, 'commercial_invoice_verified': False} if measurement_basis == 'provider_reported' else {})}
    with costs.db.connect() as connection:
        costs._lock_scope(connection, operation['scope']['scope_id'])
        connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',
                           (f'cost-reconciliation:{costs.workspace_id}:{reconciliation_id}',))
        prior = connection.execute('SELECT * FROM cost_reconciliations WHERE workspace_id=%s AND reconciliation_id=%s',
                                   (costs.workspace_id, reconciliation_id)).fetchone()
        if prior:
            if str(prior['operation_id']) != oid or prior['measurement_id'] != measurement_id or prior['body'] != body:
                raise EvidenceError('cost_reconciliation_conflict')
            saved = connection.execute('SELECT body FROM cost_entries WHERE workspace_id=%s AND measurement_id=%s',
                                       (costs.workspace_id, measurement_id)).fetchone()
            if {k: v for k, v in saved['body'].items() if k != 'recorder'} != usage:
                raise EvidenceError('cost_measurement_conflict')
            return {'status': 'duplicate', 'reconciliation_id': reconciliation_id}
        if settle_admission:
            admission = connection.execute('SELECT state FROM cost_admissions WHERE workspace_id=%s AND operation_id=%s',
                                           (costs.workspace_id, oid)).fetchone()
            if not admission or admission['state'] != 'dispatched':
                raise EvidenceError('cost_reconciliation_target_not_outstanding')
        if bound_failure:
            # The final bill itself disproves the expected finite bound. Its
            # cost is known, but future dispatch still needs meter recovery.
            costs._insert_entry(connection, oid, actor, bound_failure, 'meter_failure',
                                {'measured_at': usage['measured_at'], 'provenance': provenance,
                                 'reason': 'provider_service_bound_or_meter_violated' if measurement_basis == 'provider_reported' else 'synthetic_service_bound_violated'})
        previous = connection.execute('SELECT body FROM cost_reconciliations WHERE workspace_id=%s AND operation_id=%s',
                                      (costs.workspace_id, oid)).fetchall()
        resolved = resolved_entries(previous)
        for ids, kinds in ((commitment_ids, {'commitment'}), (uncertainty_ids, {'unknown', 'meter_failure'})):
            for mid in ids:
                entry = connection.execute('SELECT operation_id,kind,body FROM cost_entries WHERE workspace_id=%s AND measurement_id=%s',
                                           (costs.workspace_id, mid)).fetchone()
                if not entry or str(entry['operation_id']) != oid or entry['kind'] not in kinds:
                    raise EvidenceError('invalid_cost_reconciliation_targets')
                if mid in resolved:
                    raise EvidenceError('cost_reconciliation_target_not_outstanding')
                if at < timestamp(entry['body']['measured_at']):
                    raise EvidenceError('invalid_cost_reconciliation_time')
        # A final bill may cover a named group of liabilities exactly once. Its
        # identity cannot be allocated again to free another unrelated portion.
        connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',
                           (f'cost-measurement:{costs.workspace_id}:{measurement_id}',))
        used = connection.execute('SELECT reconciliation_id FROM cost_reconciliations WHERE workspace_id=%s AND measurement_id=%s',
                                  (costs.workspace_id, measurement_id)).fetchone()
        if used:
            raise EvidenceError('cost_reconciliation_conflict')
        saved = connection.execute('SELECT operation_id,kind,body FROM cost_entries WHERE workspace_id=%s AND measurement_id=%s',
                                   (costs.workspace_id, measurement_id)).fetchone()
        if saved:
            if (str(saved['operation_id']) != oid or saved['kind'] != 'usage'
                    or {k: v for k, v in saved['body'].items() if k != 'recorder'} != usage):
                raise EvidenceError('cost_measurement_conflict')
        else:
            costs._insert_entry(connection, oid, actor, measurement_id, 'usage', usage)
        connection.execute('INSERT INTO cost_reconciliations(workspace_id,reconciliation_id,operation_id,measurement_id,body) VALUES (%s,%s,%s,%s,%s)',
                           (costs.workspace_id, reconciliation_id, oid, measurement_id, Jsonb(body)))
        if settle_admission:
            connection.execute("UPDATE cost_admissions SET state='settled',reason=NULL,updated_at=now() WHERE workspace_id=%s AND operation_id=%s",
                               (costs.workspace_id, oid))
    return {'status': 'recorded', 'reconciliation_id': reconciliation_id}
