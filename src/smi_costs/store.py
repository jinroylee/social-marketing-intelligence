"""PostgreSQL accounting owner; external meters supply explicit synthetic inputs."""

from collections.abc import Callable
from decimal import Context, Decimal, localcontext
from pathlib import Path
import uuid

from psycopg.types.json import Jsonb

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from .contracts import CostScope, amount, decimal, text, timestamp
from .reconciliation import reconcile_usage, recover_meter, resolved_entries, recovered_failures


class UsageAccounting:
    """Persist source-free costs and authoritative bounded synthetic allowance in one workspace.

    Inject the task owner's public attribution resolver when creating task-linked
    operations. Reads need no resolver; immutable attribution remains auditable.
    """

    def __init__(self, db: Database, workspace_id: str = 'local', *, task_attribution: Callable[[str, str, ActorContext], dict[str, str]] | None = None):
        self.db, self.workspace_id, self.task_attribution = db, workspace_id, task_attribution

    def migrate(self) -> None:
        """Install the independent accounting schema idempotently."""
        with self.db.connect() as connection:
            connection.execute(Path(__file__).with_name('schema.sql').read_text())

    def configure_scope(self, scope: CostScope, actor: ActorContext) -> dict:
        """Persist immutable operator configuration; conflicting reuse is rejected."""
        actor.require_workspace(self.workspace_id, importing=True)
        document = scope.document()
        with self.db.connect() as connection:
            connection.execute('INSERT INTO cost_scopes(workspace_id,scope_id,configuration,operator_id) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                               (self.workspace_id, scope.scope_id, Jsonb(document), actor.actor_id))
            prior = connection.execute('SELECT configuration FROM cost_scopes WHERE workspace_id=%s AND scope_id=%s', (self.workspace_id, scope.scope_id)).fetchone()
            if prior['configuration'] != document:
                raise EvidenceError('cost_scope_conflict')
        return document

    def _lock_scope(self, connection, scope_id):
        row = connection.execute('SELECT scope_id FROM cost_scopes WHERE workspace_id=%s AND scope_id=%s FOR UPDATE',
                                 (self.workspace_id, scope_id)).fetchone()
        if row is None:
            raise EvidenceError('cost_scope_not_found')

    def configure_route(self, adapter_id: str, scope_id: str, actor: ActorContext, *, max_units: str | Decimal | int) -> dict:
        """Bind the synthetic worker route immutably to its trusted one-call meter."""
        actor.require_workspace(self.workspace_id, importing=True)
        units = decimal(max_units)
        if adapter_id not in {'fixture-json', 'offline-keyword-json'} or units != 1:
            raise EvidenceError('unsupported_cost_route_contract')
        with self.db.connect() as connection:
            self._lock_scope(connection, scope_id)
            connection.execute('INSERT INTO cost_route_controls(workspace_id,adapter_id,scope_id,max_units,operator_id) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                               (self.workspace_id, adapter_id, scope_id, units, actor.actor_id))
            prior = connection.execute('SELECT * FROM cost_route_controls WHERE workspace_id=%s AND adapter_id=%s',
                                       (self.workspace_id, adapter_id)).fetchone()
            if prior['scope_id'] != scope_id or prior['max_units'] != units:
                raise EvidenceError('cost_route_conflict')
        return {'adapter_id': adapter_id, 'scope_id': scope_id, 'max_units': amount(units)}

    def route_control(self, adapter_id: str, actor: ActorContext) -> dict | None:
        """Read persisted operator binding; callers cannot omit it on recovery."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM cost_route_controls WHERE workspace_id=%s AND adapter_id=%s',
                                     (self.workspace_id, adapter_id)).fetchone()
        return {'adapter_id': adapter_id, 'scope_id': row['scope_id'], 'max_units': amount(row['max_units'])} if row else None

    def configure_ceiling(self, scope_id: str, actor: ActorContext, *, amount: str | Decimal | int,
                          currency: str, period_start: str, period_end: str, paused: bool = False) -> dict:
        """Set trusted metered control for the exact immutable currency and period."""
        actor.require_workspace(self.workspace_id, importing=True)
        value = decimal(amount)
        if type(paused) is not bool:
            raise EvidenceError('invalid_cost_pause')
        with self.db.connect() as connection:
            self._lock_scope(connection, scope_id)
            scope = self._scope(connection, scope_id)
            if scope['classification'] != 'metered':
                raise EvidenceError('cost_scope_not_metered')
            if (currency != scope['currency'] or timestamp(period_start) != timestamp(scope['period_start'])
                    or timestamp(period_end) != timestamp(scope['period_end'])):
                raise EvidenceError('cost_ceiling_scope_mismatch')
            connection.execute('INSERT INTO cost_ceilings(workspace_id,scope_id,amount,paused,operator_id) VALUES (%s,%s,%s,%s,%s) '
                               'ON CONFLICT (workspace_id,scope_id) DO UPDATE SET amount=excluded.amount,paused=excluded.paused,operator_id=excluded.operator_id,updated_at=now()',
                               (self.workspace_id, scope_id, value, paused, actor.actor_id))
            return self._allowance(connection, scope_id)

    def allowance(self, scope_id: str, actor: ActorContext) -> dict:
        """Read authoritative full-scope spend and all unresolved commitments."""
        actor.require_workspace(self.workspace_id)
        with self.db.connect() as connection:
            self._lock_scope(connection, scope_id)
            return self._allowance(connection, scope_id)

    def _allowance(self, connection, scope_id):
        scope = self._scope(connection, scope_id)
        control = connection.execute('SELECT * FROM cost_ceilings WHERE workspace_id=%s AND scope_id=%s',
                                     (self.workspace_id, scope_id)).fetchone()
        entries = connection.execute('SELECT e.measurement_id,e.kind,e.body FROM cost_entries e JOIN cost_operations o ON o.id=e.operation_id '
                                     'WHERE o.workspace_id=%s AND o.scope_id=%s', (self.workspace_id, scope_id)).fetchall()
        reconciliations = connection.execute('SELECT r.body FROM cost_reconciliations r JOIN cost_operations o ON o.id=r.operation_id '
                                            'WHERE o.workspace_id=%s AND o.scope_id=%s', (self.workspace_id, scope_id)).fetchall()
        resolved = resolved_entries(reconciliations)
        recoveries = connection.execute('SELECT r.body FROM cost_meter_recoveries r JOIN cost_operations o ON o.id=r.operation_id '
                                       'WHERE o.workspace_id=%s AND o.scope_id=%s', (self.workspace_id, scope_id)).fetchall()
        recovered = recovered_failures(recoveries)
        pending = connection.execute("SELECT a.reserved_amount FROM cost_admissions a JOIN cost_operations o ON o.id=a.operation_id "
                                     "WHERE o.workspace_id=%s AND o.scope_id=%s AND a.state='dispatched'", (self.workspace_id, scope_id)).fetchall()
        with localcontext(Context(prec=80)):
            actual = sum((Decimal(e['body']['amount']) for e in entries if e['kind'] == 'usage'), Decimal(0))
            declared = sum((Decimal(e['body']['amount']) for e in entries if e['kind'] == 'commitment' and e['measurement_id'] not in resolved), Decimal(0))
            outstanding = declared + sum((Decimal(p['reserved_amount']) for p in pending if p['reserved_amount'] is not None), Decimal(0))
            available = max(Decimal(0), control['amount'] - actual - outstanding) if control else None
            over = max(Decimal(0), actual - control['amount']) if control else None
        metered = scope['classification'] == 'metered'
        reason = ('cost_control_missing' if metered and not control else 'cost_scope_paused' if control and control['paused']
                  else 'cost_coverage_unavailable' if metered and any(
                      (e['kind'] == 'meter_failure' and e['measurement_id'] not in recovered)
                      or (e['kind'] in {'unknown', 'meter_failure'} and e['measurement_id'] not in resolved) for e in entries) else None)
        return {'scope_id': scope_id, 'currency': scope['currency'], 'period_start': scope['period_start'], 'period_end': scope['period_end'],
                'classification': scope['classification'], 'ceiling_amount': amount(control['amount']) if control else None,
                'paused': control['paused'] if control else False,
                'operator_id': control['operator_id'] if control else None,
                'updated_at': control['updated_at'].isoformat() if control else None,
                'actual_amount': amount(actual), 'outstanding_amount': amount(outstanding), 'declared_commitment_amount': amount(declared),
                'available_amount': amount(available) if available is not None else None,
                'over_ceiling_amount': amount(over) if over is not None else None,
                'enforced_monetary_control': metered and control is not None, 'blocked_reason': reason}

    def begin_operation(self, scope_id: str, actor: ActorContext, *, request_id: str, method: str,
                        task_id: str | None = None, attempt_id: str | None = None) -> dict:
        """Bind stable retries to service, actual actor/method and exact optional attempt."""
        actor.require_workspace(self.workspace_id)
        text(scope_id, 'scope_id')
        text(request_id, 'request_id')
        text(method, 'method')
        if (task_id is None) != (attempt_id is None):
            raise EvidenceError('cost_task_attempt_required')
        if task_id is not None:
            if self.task_attribution is None:
                raise EvidenceError('cost_task_resolver_unconfigured')
            attribution = self.task_attribution(task_id, attempt_id, actor)
            task_id, attempt_id = attribution['task_id'], attribution['attempt_id']
        with self.db.connect() as connection:
            self._scope(connection, scope_id)
            connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'cost-operation:{self.workspace_id}:{request_id}',))
            prior = connection.execute('SELECT * FROM cost_operations WHERE workspace_id=%s AND request_id=%s', (self.workspace_id, request_id)).fetchone()
            values = (scope_id, actor.actor_id, actor.kind, method, task_id, attempt_id)
            if prior:
                previous = tuple(str(prior[k]) if prior[k] is not None else None for k in ('scope_id', 'actor_id', 'actor_kind', 'method', 'task_id', 'attempt_id'))
                if previous != values:
                    raise EvidenceError('cost_operation_conflict')
                operation_id = str(prior['id'])
            else:
                operation_id = str(uuid.uuid4())
                connection.execute('INSERT INTO cost_operations(id,workspace_id,request_id,scope_id,actor_id,actor_kind,method,task_id,attempt_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (operation_id, self.workspace_id, request_id, *values))
        return self.read(operation_id, actor)

    def _scope(self, connection, scope_id: str) -> dict:
        row = connection.execute('SELECT configuration,operator_id,created_at FROM cost_scopes WHERE workspace_id=%s AND scope_id=%s', (self.workspace_id, scope_id)).fetchone()
        if row is None:
            raise EvidenceError('cost_scope_not_found')
        return {**row['configuration'], 'operator_id': row['operator_id'], 'configured_at': row['created_at'].isoformat()}

    def record_usage(self, operation_id: str, actor: ActorContext, *, measurement_id: str,
                     units: str | Decimal | int, rate_version: str, measured_at: str, provenance: str) -> dict:
        """Derive one exact synthetic amount from an explicit versioned rate and units."""
        operation = self.read(operation_id, actor)
        if operation['scope'].get('measurement_basis') == 'provider_reported':
            raise EvidenceError('provider_report_required')
        body = self._usage_body(operation['scope'], units, rate_version, measured_at, provenance)
        return self._record(operation['operation_id'], actor, measurement_id, 'usage', body)

    def _usage_body(self, scope, units, rate_version, measured_at, provenance):
        if scope['classification'] != 'metered':
            raise EvidenceError('cost_scope_not_metered')
        if rate_version != scope['rate_version']:
            raise EvidenceError('cost_rate_version_mismatch')
        units = decimal(units)
        at = timestamp(measured_at)
        if not timestamp(scope['period_start']) <= at < timestamp(scope['period_end']):
            raise EvidenceError('cost_measurement_outside_period')
        text(provenance, 'provenance')
        with localcontext(Context(prec=80)):
            charge = units * Decimal(scope['unit_rate'])
        return {'units': amount(units), 'unit': scope['unit'], 'unit_rate': scope['unit_rate'],
                'rate_version': rate_version, 'amount': amount(charge), 'measured_at': at.isoformat(),
                'provenance': provenance, 'synthetic': scope.get('measurement_basis', 'synthetic') == 'synthetic',
                **({'measurement_basis': 'provider_reported', 'report_basis': 'operator_final_attestation'}
                   if scope.get('measurement_basis') == 'provider_reported' else {})}

    def reconcile_usage(self, operation_id: str, actor: ActorContext, *, reconciliation_id: str,
                        measurement_id: str, units: str | Decimal | int, rate_version: str,
                        measured_at: str, provenance: str, reconciled_at: str, evidence_id: str,
                        outcome: str, settle_admission: bool = False,
                        commitment_ids: tuple[str, ...] = (), uncertainty_ids: tuple[str, ...] = (),
                        measurement_basis: str = 'synthetic') -> dict:
        """Record final usage with an explicit matching basis and settle named liabilities.

        A human operator attests the exact final report and outcome, including a
        measured zero for confirmed uncharged failure. Ambiguity is not final
        evidence. Provider reports require explicit provider basis and remain
        operator attestations rather than independently verified invoices. This
        resolves accounting only; it grants no transport retry.
        """
        return reconcile_usage(self, operation_id, actor, reconciliation_id=reconciliation_id,
                               measurement_id=measurement_id, units=units, rate_version=rate_version,
                               measured_at=measured_at, provenance=provenance, reconciled_at=reconciled_at,
                               evidence_id=evidence_id, outcome=outcome, settle_admission=settle_admission,
                               commitment_ids=commitment_ids, uncertainty_ids=uncertainty_ids, measurement_basis=measurement_basis)

    def recover_meter(self, operation_id: str, actor: ActorContext, *, recovery_id: str,
                      failure_ids: tuple[str, ...], recovered_at: str, provenance: str, evidence_id: str,
                      measurement_basis: str = 'synthetic') -> dict:
        """Attest restored expected-meter health after named failures have final accounting.

        This human-only record clears exactly those failures. It neither releases
        liabilities nor changes classification, ceiling, rate or retry authority.
        """
        return recover_meter(self, operation_id, actor, recovery_id=recovery_id, failure_ids=failure_ids,
                             recovered_at=recovered_at, provenance=provenance, evidence_id=evidence_id, measurement_basis=measurement_basis)

    def _context(self, operation_id: str, actor: ActorContext, measured_at: str, provenance: str) -> tuple[dict, dict]:
        operation = self.read(operation_id, actor)
        at = timestamp(measured_at)
        scope = operation['scope']
        if not timestamp(scope['period_start']) <= at < timestamp(scope['period_end']):
            raise EvidenceError('cost_measurement_outside_period')
        text(provenance, 'provenance')
        return operation, {'measured_at': at.isoformat(), 'provenance': provenance}

    def record_forecast(self, operation_id: str, actor: ActorContext, *, measurement_id: str,
                        amount: str | Decimal | int, currency: str, measured_at: str,
                        provenance: str, assumptions: str) -> dict:
        """Retain a separate estimate with explicit assumptions, never actual usage."""
        text(assumptions, 'assumptions')
        return self._estimate(operation_id, actor, measurement_id, 'forecast', amount, currency,
                              measured_at, provenance, {'assumptions': assumptions})

    def record_commitment(self, operation_id: str, actor: ActorContext, *, measurement_id: str,
                          amount: str | Decimal | int, currency: str, measured_at: str, provenance: str) -> dict:
        """Record a declared outstanding synthetic commitment; grants no admission."""
        return self._estimate(operation_id, actor, measurement_id, 'commitment', amount, currency,
                              measured_at, provenance, {})

    def _estimate(self, operation_id, actor, measurement_id, kind, value, currency, measured_at, provenance, extra):
        operation, body = self._context(operation_id, actor, measured_at, provenance)
        if currency != operation['scope']['currency']:
            raise EvidenceError('cost_currency_mismatch')
        if kind == 'commitment' and operation['scope']['classification'] != 'metered':
            raise EvidenceError('cost_scope_not_metered')
        body.update(amount=amount(decimal(value)), currency=currency, **extra)
        return self._record(operation['operation_id'], actor, measurement_id, kind, body)

    def record_uncertainty(self, operation_id: str, actor: ActorContext, *, measurement_id: str,
                           state: str, measured_at: str, provenance: str, reason: str) -> dict:
        """Retain unknown coverage or expected-meter failure without reclassifying scope."""
        if not isinstance(state, str) or state not in {'unknown', 'meter_failure'}:
            raise EvidenceError('invalid_cost_uncertainty')
        text(reason, 'reason')
        operation, body = self._context(operation_id, actor, measured_at, provenance)
        if state == 'meter_failure' and operation['scope']['classification'] != 'metered':
            raise EvidenceError('cost_scope_not_metered')
        return self._record(operation['operation_id'], actor, measurement_id, state, {**body, 'reason': reason})

    def _record(self, operation_id: str, actor: ActorContext, measurement_id: str, kind: str, body: dict) -> dict:
        actor.require_workspace(self.workspace_id)
        text(measurement_id, 'measurement_id')
        with self.db.connect() as connection:
            operation = connection.execute('SELECT scope_id FROM cost_operations WHERE workspace_id=%s AND id=%s',
                                           (self.workspace_id, operation_id)).fetchone()
            self._lock_scope(connection, operation['scope_id'])
            return self._insert_entry(connection, operation_id, actor, measurement_id, kind, body)

    def _insert_entry(self, connection, operation_id, actor, measurement_id, kind, body):
        body = {**body, 'recorder': {'actor_id': actor.actor_id, 'kind': actor.kind}}
        connection.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (f'cost-measurement:{self.workspace_id}:{measurement_id}',))
        prior = connection.execute('SELECT * FROM cost_entries WHERE workspace_id=%s AND measurement_id=%s', (self.workspace_id, measurement_id)).fetchone()
        if prior:
            if str(prior['operation_id']) != operation_id or prior['kind'] != kind or prior['body'] != body:
                raise EvidenceError('cost_measurement_conflict')
            return {'status': 'duplicate', 'measurement_id': measurement_id}
        connection.execute('INSERT INTO cost_entries(workspace_id,measurement_id,operation_id,kind,body) VALUES (%s,%s,%s,%s,%s)',
                           (self.workspace_id, measurement_id, operation_id, kind, Jsonb(body)))
        return {'status': 'recorded', 'measurement_id': measurement_id}

    def list(self, actor: ActorContext, *, task_id: str | None = None) -> list[dict]:
        """Return the newest 100 workspace operations, optionally for one exact task."""
        actor.require_workspace(self.workspace_id)
        if task_id is not None:
            try:
                task_id = str(uuid.UUID(task_id))
            except (ValueError, TypeError, AttributeError):
                raise EvidenceError('cost_task_attribution_not_found') from None
        with self.db.connect() as connection:
            rows = connection.execute('SELECT id FROM cost_operations WHERE workspace_id=%s AND (%s::uuid IS NULL OR task_id=%s::uuid) ORDER BY created_at DESC,id DESC LIMIT 100',
                                      (self.workspace_id, task_id, task_id)).fetchall()
        return [self.read(str(row['id']), actor) for row in rows]

    def read(self, operation_id: str, actor: ActorContext) -> dict:
        """Reopen attributed synthetic actuals separately from nonactual cost states."""
        actor.require_workspace(self.workspace_id)
        try:
            operation_id = str(uuid.UUID(operation_id))
        except (ValueError, TypeError, AttributeError):
            raise EvidenceError('cost_operation_not_found') from None
        with self.db.connect() as connection:
            row = connection.execute('SELECT * FROM cost_operations WHERE workspace_id=%s AND id=%s', (self.workspace_id, operation_id)).fetchone()
            if row is None:
                raise EvidenceError('cost_operation_not_found')
            # Keep the displayed admission and full-scope totals on the same
            # stable ledger frontier as a concurrent reservation settlement.
            self._lock_scope(connection, row['scope_id'])
            scope = self._scope(connection, row['scope_id'])
            admission = connection.execute('SELECT max_units,reserved_amount,state,reason FROM cost_admissions WHERE workspace_id=%s AND operation_id=%s', (self.workspace_id, operation_id)).fetchone()
            allowance = self._allowance(connection, row['scope_id'])
            entries = connection.execute('SELECT * FROM cost_entries WHERE workspace_id=%s AND operation_id=%s ORDER BY recorded_at,measurement_id', (self.workspace_id, operation_id)).fetchall()
            reconciliations = connection.execute('SELECT * FROM cost_reconciliations WHERE workspace_id=%s AND operation_id=%s ORDER BY recorded_at,reconciliation_id', (self.workspace_id, operation_id)).fetchall()
            recoveries = connection.execute('SELECT * FROM cost_meter_recoveries WHERE workspace_id=%s AND operation_id=%s ORDER BY recorded_at,recovery_id', (self.workspace_id, operation_id)).fetchall()
        entries = [{'measurement_id': e['measurement_id'], 'kind': e['kind'], **e['body'], 'recorded_at': e['recorded_at'].isoformat()} for e in entries]
        actual = [Decimal(e['amount']) for e in entries if e['kind'] == 'usage']
        resolved = resolved_entries(reconciliations)
        unresolved = {kind + '_ids': sorted(e['measurement_id'] for e in entries if e['kind'] in kinds and e['measurement_id'] not in resolved)
                      for kind, kinds in (('commitment', {'commitment'}), ('uncertainty', {'unknown', 'meter_failure'}))}
        recovered = recovered_failures(recoveries)
        unresolved['meter_failure_ids'] = sorted(e['measurement_id'] for e in entries if e['kind'] == 'meter_failure' and e['measurement_id'] not in recovered)
        kinds = {e['kind'] for e in entries}
        pending_cost = bool(unresolved['commitment_ids'] or unresolved['uncertainty_ids'] or admission and admission['state'] == 'dispatched')
        final_id = next((r['measurement_id'] for r in reconciliations if r['body']['settle_admission']), f'admission:{operation_id}')
        bounded_usage = next((e for e in entries if e['measurement_id'] == final_id and e['kind'] == 'usage'), None)
        bound_status = ('not_recorded' if not admission else 'violated'
                        if bounded_usage and Decimal(bounded_usage['units']) > admission['max_units'] else 'within_bound'
                        if bounded_usage else 'unverified' if any(e.get('reason') in {'synthetic_service_bound_violated', 'provider_service_bound_or_meter_violated'} for e in entries)
                        else 'declared')
        provider_reported = scope.get('measurement_basis') == 'provider_reported'
        status = ('meter_failure' if unresolved['meter_failure_ids'] else 'unknown'
                  if unresolved['uncertainty_ids'] or scope['classification'] == 'metered' and pending_cost
                  else 'forecast_only' if scope['classification'] == 'forecast_only'
                  else ('provider_reported' if provider_reported else 'synthetic_measured') if actual else 'unmeasured')
        with localcontext(Context(prec=80)):
            total = amount(sum(actual, Decimal(0))) if actual else None
            estimates = {kind + 's': {'amount': amount(sum((Decimal(e['amount']) for e in entries if e['kind'] == kind and e['measurement_id'] not in resolved), Decimal(0)))
                         if kind in kinds else None} for kind in ('forecast', 'commitment')}
        return {'operation_id': operation_id, 'workspace_id': self.workspace_id, 'request_id': row['request_id'],
                'scope': scope, 'actor': {'actor_id': row['actor_id'], 'kind': row['actor_kind']}, 'method': row['method'],
                'task_id': str(row['task_id']) if row['task_id'] else None, 'attempt_id': str(row['attempt_id']) if row['attempt_id'] else None,
                'created_at': row['created_at'].isoformat(), 'entries': entries,
                'reconciliations': [{'reconciliation_id': r['reconciliation_id'], 'measurement_id': r['measurement_id'],
                                     **r['body'], 'recorded_at': r['recorded_at'].isoformat()} for r in reconciliations],
                'unresolved': unresolved,
                'meter_recoveries': [{'recovery_id': r['recovery_id'], **r['body'],
                                     'recorded_at': r['recorded_at'].isoformat()} for r in recoveries],
                'limits': {'known_unit_bound': amount(admission['max_units']) if admission else None,
                           'known_charge_bound': amount(admission['reserved_amount']) if admission and admission['reserved_amount'] is not None else None,
                           'bound_status': bound_status,
                           'billing_lag_bound': None,
                           'billing_state': 'forecast_only' if scope['classification'] == 'forecast_only'
                           else 'awaiting_final_measurement' if pending_cost
                           else 'final_measurement_recorded' if reconciliations or admission and admission['state'] == 'settled'
                           else 'no_final_report_recorded',
                           'meter_health': 'failed' if unresolved['meter_failure_ids'] else 'recovered' if recoveries else 'no_failure_recorded',
                           'enforcement_basis': ('declared_bounded_provider_contract' if provider_reported else 'bounded_synthetic_service_contract_only') if allowance['enforced_monetary_control'] else 'no_enforced_monetary_ceiling',
                           'zero_overshoot_guaranteed': False},
                'actuals': {'amount': total, 'synthetic': not provider_reported, 'commercial_charge': None if provider_reported else False},
                **estimates, 'coverage': {'status': status, 'unknown_cost': status not in {'synthetic_measured', 'provider_reported'}},
                'admission': {k: amount(v) if isinstance(v, Decimal) else v for k, v in admission.items()} if admission else None,
                'allowance': allowance, 'enforced_monetary_control': allowance['enforced_monetary_control']}
