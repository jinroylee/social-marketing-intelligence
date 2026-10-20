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


class SyntheticOperationAdapter:
    """Run one simulated call at most once for a stable operation identity.

    The trusted service contract accepts a unit bound and returns measured units
    no greater than it. No retries occur here. Exceptions or lost responses retain
    the full reservation; repeated execution pauses for later reconciliation.
    ``transaction`` joins a task's actual ownership session for dispatch/settlement.
    I/O occurs after the dispatch commit and outside database transactions.
    """

    def __init__(self, accounting: 'UsageAccounting', scope_id: str, *, max_units: str | Decimal | int):
        self.accounting, self.scope_id = accounting, scope_id
        self.max_units = amount(decimal(max_units))

    def execute(self, actor: ActorContext, *, request_id: str, method: str, call: Callable[[str], SyntheticResult],
                task_id: str | None = None, attempt_id: str | None = None,
                transaction: Callable[[str], AbstractContextManager] | None = None,
                operation_actor: ActorContext | None = None) -> dict:
        """Return executed/refused/paused metadata; only executed contains a value.

        Trusted task composition can retain the initial ``operation_actor`` while
        recording the actual dispatcher/settler as ``actor`` on recovery.
        """
        costs = self.accounting
        actor.require_workspace(costs.workspace_id)
        operation = costs.begin_operation(self.scope_id, operation_actor or actor, request_id=request_id,
                                          method=method, task_id=task_id, attempt_id=attempt_id)
        oid = operation['operation_id']
        scope = operation['scope']
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
        if reason:
            return {'status': 'refused', 'reason': reason, 'operation_id': oid, 'allowance': allowance}
        result = call(self.max_units)
        try:
            valid = isinstance(result, SyntheticResult) and decimal(result.units) <= Decimal(self.max_units)
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
                                        {'measured_at': now.isoformat(), 'provenance': 'bounded-synthetic-adapter-v1',
                                         'reason': 'synthetic_service_bound_violated'})
            raise EvidenceError('synthetic_service_bound_violated')
        with transaction('cost_settlement') if transaction else nullcontext() as owned:
            with nullcontext(owned) if owned is not None else costs.db.connect() as connection:
                costs._lock_scope(connection, self.scope_id)
                if metered:
                    units = decimal(result.units)
                    with localcontext(Context(prec=80)):
                        charge = units * Decimal(scope['unit_rate'])
                    body = {'units': amount(units), 'unit': scope['unit'], 'unit_rate': scope['unit_rate'],
                            'rate_version': scope['rate_version'], 'amount': amount(charge),
                            'measured_at': now.isoformat(), 'provenance': 'bounded-synthetic-adapter-v1', 'synthetic': True}
                    costs._insert_entry(connection, oid, actor, f'admission:{oid}', 'usage', body)
                connection.execute("UPDATE cost_admissions SET state='settled',reason=NULL,updated_at=now() WHERE workspace_id=%s AND operation_id=%s",
                                   (costs.workspace_id, oid))
                allowance = costs._allowance(connection, self.scope_id)
        return {'status': 'executed', 'reason': None, 'operation_id': oid, 'allowance': allowance, 'value': result.value}
