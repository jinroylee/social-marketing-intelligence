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


class UsageAccounting:
    """Persist source-free costs in one workspace, without admitting chargeable work.

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
        scope = operation['scope']
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
        body = {'units': amount(units), 'unit': scope['unit'], 'unit_rate': scope['unit_rate'],
                'rate_version': rate_version, 'amount': amount(charge), 'measured_at': at.isoformat(),
                'provenance': provenance, 'synthetic': True}
        return self._record(operation['operation_id'], actor, measurement_id, 'usage', body)

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
        body = {**body, 'recorder': {'actor_id': actor.actor_id, 'kind': actor.kind}}
        with self.db.connect() as connection:
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
            scope = self._scope(connection, row['scope_id'])
            entries = connection.execute('SELECT * FROM cost_entries WHERE workspace_id=%s AND operation_id=%s ORDER BY recorded_at,measurement_id', (self.workspace_id, operation_id)).fetchall()
        entries = [{'measurement_id': e['measurement_id'], 'kind': e['kind'], **e['body'], 'recorded_at': e['recorded_at'].isoformat()} for e in entries]
        actual = [Decimal(e['amount']) for e in entries if e['kind'] == 'usage']
        kinds = {e['kind'] for e in entries}
        status = ('meter_failure' if 'meter_failure' in kinds else 'unknown' if 'unknown' in kinds
                  else 'forecast_only' if scope['classification'] == 'forecast_only'
                  else 'synthetic_measured' if actual else 'unmeasured')
        with localcontext(Context(prec=80)):
            total = amount(sum(actual, Decimal(0))) if actual else None
            estimates = {kind + 's': {'amount': amount(sum((Decimal(e['amount']) for e in entries if e['kind'] == kind), Decimal(0)))
                         if kind in kinds else None} for kind in ('forecast', 'commitment')}
        return {'operation_id': operation_id, 'workspace_id': self.workspace_id, 'request_id': row['request_id'],
                'scope': scope, 'actor': {'actor_id': row['actor_id'], 'kind': row['actor_kind']}, 'method': row['method'],
                'task_id': str(row['task_id']) if row['task_id'] else None, 'attempt_id': str(row['attempt_id']) if row['attempt_id'] else None,
                'created_at': row['created_at'].isoformat(), 'entries': entries,
                'actuals': {'amount': total, 'synthetic': True, 'commercial_charge': False},
                **estimates, 'coverage': {'status': status, 'unknown_cost': status != 'synthetic_measured'},
                'enforced_monetary_control': False}
