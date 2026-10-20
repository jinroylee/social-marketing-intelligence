"""Validated operator cost configuration and exact decimal inputs."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

from smi_ingestion.evidence import EvidenceError


def text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise EvidenceError(f'invalid_cost_{field}')
    return value


def decimal(value: str | Decimal | int) -> Decimal:
    """Accept exact finite nonnegative inputs with at most 12 decimal places."""
    if isinstance(value, bool) or not isinstance(value, (str, Decimal, int)):
        raise EvidenceError('invalid_cost_decimal')
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        raise EvidenceError('invalid_cost_decimal') from None
    if (not number.is_finite() or number < 0 or number > Decimal('1000000000000000000')
            or not -12 <= number.as_tuple().exponent <= 18):
        raise EvidenceError('invalid_cost_decimal')
    return number


def amount(value: Decimal) -> str:
    if value == 0:
        return '0'
    result = format(value, 'f')
    return result.rstrip('0').rstrip('.') if '.' in result else result


def timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise EvidenceError('invalid_cost_time') from None
    if parsed.tzinfo is None:
        raise EvidenceError('invalid_cost_time')
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class CostScope:
    """Immutable operator classification for one service/currency/accounting period.

    Default metered configuration preserves synthetic units/rates. Provider
    reports require explicit measurement basis and configured rates; neither
    basis establishes an independently verified invoice. New rates or
    classifications require a new scope identity.
    """

    scope_id: str
    provider: str
    service: str
    classification: str
    currency: str
    period_start: str
    period_end: str
    unit: str | None = None
    rate_version: str | None = None
    unit_rate: str | Decimal | int | None = None
    measurement_basis: str = 'synthetic'

    def document(self) -> dict:
        """Return a canonical persistable configuration or reject invalid inputs."""
        for field in ('scope_id', 'provider', 'service'):
            text(getattr(self, field), field)
        if not isinstance(self.classification, str) or self.classification not in {'metered', 'forecast_only'}:
            raise EvidenceError('invalid_cost_classification')
        if not isinstance(self.currency, str) or re.fullmatch('[A-Z]{3}', self.currency) is None:
            raise EvidenceError('invalid_cost_currency')
        start, end = timestamp(self.period_start), timestamp(self.period_end)
        if start >= end:
            raise EvidenceError('invalid_cost_period')
        if self.classification == 'metered':
            text(self.unit, 'unit')
            text(self.rate_version, 'rate_version')
            rate = amount(decimal(self.unit_rate))
        else:
            if any(v is not None for v in (self.unit, self.rate_version, self.unit_rate)):
                raise EvidenceError('forecast_scope_has_meter')
            rate = None
        if not isinstance(self.measurement_basis, str) or self.measurement_basis not in {'synthetic', 'provider_reported'} or (self.measurement_basis == 'provider_reported' and self.classification != 'metered'):
            raise EvidenceError('invalid_cost_measurement_basis')
        return {**({'measurement_basis': self.measurement_basis} if self.measurement_basis != 'synthetic' else {}), 'scope_id': self.scope_id, 'provider': self.provider, 'service': self.service,
                'classification': self.classification, 'currency': self.currency,
                'period_start': start.isoformat(), 'period_end': end.isoformat(),
                'unit': self.unit, 'rate_version': self.rate_version, 'unit_rate': rate,
                'synthetic': self.classification == 'metered' and self.measurement_basis == 'synthetic'}
