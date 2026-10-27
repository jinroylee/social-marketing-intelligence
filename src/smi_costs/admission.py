"""One-use bounded synthetic dispatch; uncertainty retains its reservation."""

from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Context, Decimal, localcontext
from typing import Any, TYPE_CHECKING

from psycopg.types.json import Jsonb

from smi_ingestion.evidence import EvidenceError
from smi_ingestion.evidence_sets import ActorContext

from .contracts import amount, decimal, timestamp

if TYPE_CHECKING:
    from .store import UsageAccounting


@dataclass(frozen=True)
class SyntheticResult:
    """Trusted fake service result and its finite measured units within the bound."""

    value: Any
    units: str | Decimal | int


@dataclass(frozen=True)
class ProviderResult(SyntheticResult):
    """Provider-reported units and source-free validated token counts, never a final invoice."""

    token_usage: dict | None = None


@dataclass(frozen=True)
class DeferredProviderResult:
    """Returned source work with no final billing measurement; retain its admission."""

    value: Any


class SyntheticOperationAdapter:
    """Run one simulated call at most once for a stable operation identity.

    The trusted service contract accepts a unit bound and returns measured units
    no greater than it. No retries occur here. Exceptions or lost responses retain
    the full reservation; repeated execution pauses for later reconciliation.
    ``transaction`` joins a task's actual ownership session for dispatch/settlement.
    I/O occurs after the dispatch commit and outside database transactions.
    """

    measurement_basis = 'synthetic'
    provenance = 'bounded-synthetic-adapter-v1'
    failure_reason = 'synthetic_service_bound_violated'

    def __init__(self, accounting: 'UsageAccounting', scope_id: str, *, max_units: str | Decimal | int):
        self.accounting, self.scope_id = accounting, scope_id
        self.max_units = amount(decimal(max_units))

    def execute(self, actor: ActorContext, *, request_id: str, method: str, call: Callable[[str], SyntheticResult | DeferredProviderResult],
                task_id: str | None = None, attempt_id: str | None = None,
                transaction: Callable[[str], AbstractContextManager] | None = None,
                operation_actor: ActorContext | None = None,
                dispatch_guard: Callable[[Any], str | None] | None = None) -> dict:
        """Return executed/refused/paused metadata; only executed contains a value.

        Trusted task composition can retain the initial ``operation_actor`` while
        recording the actual dispatcher/settler as ``actor`` on recovery. A trusted
        ``dispatch_guard(connection)`` may refuse with a source-free reason after
        the allowance decision; its policy locks persist through admission commit.
        Guard refusal records no dispatch or monetary liability. I/O follows commit.
        """
        costs = self.accounting
        actor.require_workspace(costs.workspace_id)
        operation = costs.begin_operation(self.scope_id, operation_actor or actor, request_id=request_id,
                                          method=method, task_id=task_id, attempt_id=attempt_id)
        oid = operation['operation_id']
        scope = operation['scope']
        if scope.get('measurement_basis', 'synthetic') != self.measurement_basis:
            raise EvidenceError('cost_measurement_basis_mismatch')
        metered = scope['classification'] == 'metered'
        with localcontext(Context(prec=80)):
            reserved = Decimal(self.max_units) * Decimal(scope['unit_rate']) if metered else None
        with transaction('cost_dispatch') if transaction else nullcontext() as owned:
            with nullcontext(owned) if owned is not None else costs.db.connect() as connection:
                costs._lock_scope(connection, self.scope_id)
                prior = connection.execute('SELECT * FROM cost_admissions WHERE workspace_id=%s AND operation_id=%s',
                                           (costs.workspace_id, oid)).fetchone()
                if prior and Decimal(prior['max_units']) != Decimal(self.max_units):
                    raise EvidenceError('cost_admission_conflict')
                allowance = costs._allowance(connection, self.scope_id)
                if prior and prior['state'] != 'refused':
                    reason = 'cost_operation_already_executed' if prior['state'] == 'settled' else 'cost_operation_in_flight_or_uncertain'
                    return {'status': 'paused', 'reason': reason, 'operation_id': oid, 'allowance': allowance}
                now = datetime.now(timezone.utc)
                reason = (None if timestamp(scope['period_start']) <= now < timestamp(scope['period_end'])
                          else 'cost_accounting_period_inactive')
                if metered and reason is None:
                    reason = allowance['blocked_reason']
                    with localcontext(Context(prec=80)):
                        if reason is None and reserved > Decimal(allowance['available_amount']):
                            reason = 'cost_allowance_exhausted'
                state = 'refused' if reason else 'dispatched'
                connection.execute('INSERT INTO cost_admissions(workspace_id,operation_id,max_units,reserved_amount,state,reason,dispatched_by) VALUES (%s,%s,%s,%s,%s,%s,%s) '
                                   'ON CONFLICT (workspace_id,operation_id) DO UPDATE SET state=excluded.state,reason=excluded.reason,dispatched_by=excluded.dispatched_by,updated_at=now()',
                                   (costs.workspace_id, oid, Decimal(self.max_units), reserved, state, reason,
                                    Jsonb({'actor_id': actor.actor_id, 'kind': actor.kind})))
                if reason is None and dispatch_guard is not None:
                    reason = dispatch_guard(connection)
                    if reason is not None:
                        if not isinstance(reason, str) or not reason or len(reason) > 200:
                            raise EvidenceError('invalid_dispatch_guard_reason')
                        connection.execute("UPDATE cost_admissions SET state='refused',reason=%s WHERE workspace_id=%s AND operation_id=%s",
                                           (reason, costs.workspace_id, oid))
        if reason:
            return {'status': 'refused', 'reason': reason, 'operation_id': oid, 'allowance': allowance}
        result = call(self.max_units)
        if isinstance(result, DeferredProviderResult) and isinstance(self, DeferredProviderOperationAdapter):
            # A response/record count is not a final provider bill. Keep this
            # exact reservation available for explicit final reconciliation.
            return {'status': 'executed', 'reason': 'awaiting_final_measurement',
                    'operation_id': oid, 'allowance': costs.allowance(self.scope_id, actor), 'value': result.value}
        try:
            valid = isinstance(result, SyntheticResult) and decimal(result.units) <= Decimal(self.max_units)
            if self.measurement_basis == 'provider_reported':
                keys = {'input_tokens', 'output_tokens', 'total_tokens', 'cached_tokens', 'cache_write_tokens', 'reasoning_tokens'}
                valid = (valid and isinstance(result, ProviderResult) and isinstance(result.token_usage, dict)
                         and set(result.token_usage) == keys and all(type(v) is int and v >= 0 for v in result.token_usage.values()))
                if valid:
                    usage = result.token_usage
                    valid = (usage['total_tokens'] == usage['input_tokens'] + usage['output_tokens']
                             and usage['cached_tokens'] + usage['cache_write_tokens'] <= usage['input_tokens']
                             and usage['reasoning_tokens'] <= usage['output_tokens'])
        except EvidenceError:
            valid = False
        if not valid:
            # A broken meter no longer establishes the advertised finite bound.
            # Preserve its reservation and block metered scope dispatch as well.
            with transaction('cost_meter_failure') if transaction else nullcontext() as owned:
                with nullcontext(owned) if owned is not None else costs.db.connect() as connection:
                    costs._lock_scope(connection, self.scope_id)
                    costs._insert_entry(connection, oid, actor, f'admission-meter:{oid}',
                                        'meter_failure' if metered else 'unknown',
                                        {'measured_at': now.isoformat(), 'provenance': self.provenance,
                                         'reason': self.failure_reason})
            raise EvidenceError(self.failure_reason)
        with transaction('cost_settlement') if transaction else nullcontext() as owned:
            with nullcontext(owned) if owned is not None else costs.db.connect() as connection:
                costs._lock_scope(connection, self.scope_id)
                if metered:
                    units = decimal(result.units)
                    with localcontext(Context(prec=80)):
                        charge = units * Decimal(scope['unit_rate'])
                    body = {'units': amount(units), 'unit': scope['unit'], 'unit_rate': scope['unit_rate'],
                            'rate_version': scope['rate_version'], 'amount': amount(charge),
                            'measured_at': now.isoformat(), 'provenance': self.provenance, 'synthetic': self.measurement_basis == 'synthetic'}
                    if self.measurement_basis == 'provider_reported':
                        body.update(measurement_basis='provider_reported', token_usage=result.token_usage)
                    prior = connection.execute('SELECT state FROM cost_admissions WHERE workspace_id=%s AND operation_id=%s',
                                               (costs.workspace_id, oid)).fetchone()
                    if prior['state'] == 'settled':
                        # A trusted final report can arrive while this original
                        # call is still returning. It already owns the charge;
                        # a different response cannot add a second final bill.
                        final = connection.execute("SELECT e.body FROM cost_reconciliations r JOIN cost_entries e "
                                                   "ON e.workspace_id=r.workspace_id AND e.measurement_id=r.measurement_id "
                                                   "WHERE r.workspace_id=%s AND r.operation_id=%s AND r.body->>'settle_admission'='true'",
                                                   (costs.workspace_id, oid)).fetchone()
                        if not final or Decimal(final['body']['units']) != units:
                            raise EvidenceError('cost_measurement_conflict')
                    else:
                        costs._insert_entry(connection, oid, actor, f'admission:{oid}', 'usage', body)
                connection.execute("UPDATE cost_admissions SET state='settled',reason=NULL,updated_at=now() WHERE workspace_id=%s AND operation_id=%s",
                                   (costs.workspace_id, oid))
                allowance = costs._allowance(connection, self.scope_id)
        return {'status': 'executed', 'reason': None, 'operation_id': oid, 'allowance': allowance, 'value': result.value}


class ProviderOperationAdapter(SyntheticOperationAdapter):
    """Share one-use admission/settlement for a verified bounded provider contract.

    The provider integration supplies defensible finite unit bounds and reports
    validated usage. This records configured-rate usage, not an audited invoice;
    uncertainty still retains the reservation without automatic release/retry.
    """

    measurement_basis = 'provider_reported'
    provenance = 'openai-responses-reported-usage-v1'
    failure_reason = 'provider_service_bound_or_meter_violated'


class DeferredProviderOperationAdapter(SyntheticOperationAdapter):
    """Admit one provider attempt without manufacturing a final usage measurement.

    The configured maximum is a declared commitment, not a verified invoice cap.
    A returned response retains it; explicit provider-basis final reconciliation
    owns settlement. Same-operation replay never obtains another dispatch grant.
    """

    measurement_basis = 'provider_reported'
