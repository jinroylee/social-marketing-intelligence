"""Shared concrete Responses route, transport bounds and monetary settlement."""

from collections.abc import Callable
from dataclasses import asdict, dataclass
from decimal import Context, Decimal, localcontext
import json
from time import monotonic
from typing import Protocol

from smi_costs import SyntheticOperationAdapter, SyntheticResult, ProviderOperationAdapter, ProviderResult, UsageAccounting
from smi_costs.contracts import amount, decimal
from smi_ingestion.evidence import EvidenceError
from ..contracts import require, text
from .http import ResponsesHTTPTransport, ResponseBoundExceeded

__all__ = ["ResponsesRoute", "ResponsesTransport", "ResponsesHTTPTransport", "decode_json", "generated_document", "execute_request"]

class ResponsesTransport(Protocol):
    """One-call service, bounded in time and bytes with no retries.

    Implementations must enforce the supplied deadline and response-byte limit;
    the HTTP adapter requires explicit enablement and never looks up environment keys.
    A timeout/lost response is uncertain consumption, never a free failure.
    """

    def create(self, request: dict, *, credential: str, timeout_seconds: int, max_response_bytes: int) -> bytes: ...


@dataclass(frozen=True)
class ResponsesRoute:
    """Explicit model identity, token weighting policy and finite bounds.

    The input-token bound is a trusted simulated-service contract, not a text
    tokenization estimate. Provider mode instead pins a verified model input cap.
    Cache-read and cache-write counts partition the input with uncached tokens.
    ``output_tokens`` includes reasoning and nonvisible generated tokens.
    """

    model: str
    model_version: str
    scope_id: str
    rate_version: str
    input_weight: str
    cached_weight: str
    cache_write_weight: str
    output_weight: str
    max_input_tokens: int
    max_output_tokens: int
    max_request_bytes: int
    max_response_bytes: int
    timeout_seconds: int
    measurement_policy: str
    execution_mode: str = 'simulated'
    model_contract_version: str | None = None

    def document(self) -> dict:
        """Validate server configuration without deriving rates or model defaults."""
        for name in ('model', 'model_version', 'scope_id', 'rate_version'):
            value = getattr(self, name)
            require(text(value) and len(value) <= 200, 'model_configuration_invalid')
        require(isinstance(self.execution_mode, str) and self.execution_mode in {'simulated', 'provider'}, 'model_execution_mode_invalid')
        for name, limit in [('max_input_tokens', 1000000), ('max_output_tokens', 10000),
                            ('max_request_bytes', 1000000), ('max_response_bytes', 1000000), ('timeout_seconds', 30)]:
            value = getattr(self, name)
            require(type(value) is int and 0 < value <= limit, 'model_bounds_invalid')
        for name in ('input_weight', 'cached_weight', 'cache_write_weight', 'output_weight'):
            require(0 < decimal(getattr(self, name)) <= 1000, 'model_rates_invalid')
        if self.execution_mode == 'simulated':
            require(self.measurement_policy == 'synthetic-transport-input-bound-v1', 'model_measurement_policy_unavailable')
        else:
            require(self.measurement_policy == 'verified-model-context-v1'
                    and self.model == self.model_version == 'gpt-5.4-mini-2026-03-17'
                    and self.model_contract_version == 'openai-gpt-5.4-mini-2026-03-17:2026-10-20'
                    and self.max_input_tokens == 272000 and 0 < self.max_output_tokens <= 128000
                    and decimal(self.cache_write_weight) == decimal(self.input_weight),
                    'model_verified_bounds_unavailable')
        return {**asdict(self), 'provider': 'openai-responses', 'execution': 'provider_enabled' if self.execution_mode == 'provider' else 'simulated_only'}

    def max_units(self) -> str:
        """Return the conservative weighted-unit bound for the configured contract."""
        with localcontext(Context(prec=80)):
            return amount(self.max_input_tokens * max(Decimal(self.input_weight), Decimal(self.cached_weight), Decimal(self.cache_write_weight))
                          + self.max_output_tokens * Decimal(self.output_weight))


def decode_json(raw):
    """Decode one JSON value while rejecting duplicate object keys."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'model_response_invalid')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)

def _usage(response: dict, route: ResponsesRoute) -> tuple[dict, str]:
    try:
        usage = response['usage']
        counts = {key: usage[key] for key in ('input_tokens', 'output_tokens', 'total_tokens')}
        counts.update({key: usage['input_tokens_details'][key] for key in ('cached_tokens', 'cache_write_tokens')})
        counts['reasoning_tokens'] = usage['output_tokens_details']['reasoning_tokens']
        require(all(type(value) is int and value >= 0 for value in counts.values()), 'model_usage_invalid')
        require(counts['input_tokens'] <= route.max_input_tokens and counts['output_tokens'] <= route.max_output_tokens
                and counts['cached_tokens'] + counts['cache_write_tokens'] <= counts['input_tokens']
                and counts['reasoning_tokens'] <= counts['output_tokens']
                and counts['total_tokens'] == counts['input_tokens'] + counts['output_tokens'], 'model_usage_invalid')
        with localcontext(Context(prec=80)):
            units = amount((counts['input_tokens'] - counts['cached_tokens'] - counts['cache_write_tokens']) * Decimal(route.input_weight)
                           + counts['cached_tokens'] * Decimal(route.cached_weight)
                           + counts['cache_write_tokens'] * Decimal(route.cache_write_weight)
                           + counts['output_tokens'] * Decimal(route.output_weight))
        return counts, units
    except (KeyError, TypeError, EvidenceError):
        raise EvidenceError('model_usage_invalid') from None


def generated_document(response: dict):
    """Read one completed assistant JSON text, rejecting tools, refusals and duplicate keys."""
    output = response['output']
    require(isinstance(output, list) and bool(output), 'model_output_invalid')
    contents = []
    for item in output:
        require(isinstance(item, dict) and item.get('type') in {'message', 'reasoning'}, 'model_output_unsupported')
        if item['type'] == 'message':
            require(item.get('role') == 'assistant' and item.get('status') == 'completed', 'model_output_invalid')
            require(isinstance(item.get('content'), list), 'model_output_invalid')
            contents.extend(item['content'])
    if any(isinstance(item, dict) and item.get('type') == 'refusal' for item in contents):
        raise EvidenceError('model_refusal')
    require(len(contents) == 1 and isinstance(contents[0], dict) and contents[0].get('type') == 'output_text', 'model_output_unsupported')
    return decode_json(contents[0]['text'])


def execute_request(route: ResponsesRoute, transport: ResponsesTransport, credential: str, accounting: UsageAccounting,
            actor, *, operation_request: str, method_version: str, request: dict,
                    validate: Callable[[dict], dict], attach_operation: Callable[[str], None]) -> dict:
    """Admit one bounded call; retain liability on missing/invalid metering."""
    require(len(json.dumps(request, ensure_ascii=False).encode()) <= route.max_request_bytes, 'model_request_bound_exceeded')
    operation = accounting.begin_operation(route.scope_id, actor, request_id=operation_request, method=method_version)
    attach_operation(operation['operation_id'])
    scope = operation['scope']
    require(scope['classification'] == 'metered' and scope['unit'] == 'weighted_token'
            and scope['rate_version'] == route.rate_version
            and scope.get('measurement_basis', 'synthetic') == ('provider_reported' if route.execution_mode == 'provider' else 'synthetic'), 'model_rate_classification_unavailable')
    require(route.execution_mode != 'provider' or (scope['provider'] == 'openai' and scope['service'] == 'responses'),
            'model_rate_classification_unavailable')
    result_type = ProviderResult if route.execution_mode == 'provider' else SyntheticResult

    def call(bound):
        started = monotonic()
        try:
            raw = transport.create(request, credential=credential, timeout_seconds=route.timeout_seconds, max_response_bytes=route.max_response_bytes)
        except ResponseBoundExceeded:
            return result_type({'status': 'invalid', 'reason': 'model_response_bound_exceeded'}, None)
        except Exception:
            raise RuntimeError('model_transport_outcome_unknown') from None
        if monotonic() - started > route.timeout_seconds:
            raise TimeoutError('model_transport_timeout')
        if not isinstance(raw, bytes) or len(raw) > route.max_response_bytes:
            return result_type({'status': 'invalid', 'reason': 'model_response_bound_exceeded'}, None)
        try:
            response = decode_json(raw)
            require(isinstance(response, dict), 'model_response_invalid')
            require(response.get('model') == route.model and response.get('status') in {'completed', 'incomplete'},
                    'model_final_usage_contract_unverified')
            if route.execution_mode == 'provider':
                require(response.get('service_tier') == 'default', 'model_rate_classification_unavailable')
            usage, units = _usage(response, route)
        except (ValueError, TypeError, EvidenceError):
            return result_type({'status': 'invalid', 'reason': 'model_usage_invalid'}, None)
        value = validate(response)
        return (ProviderResult({**value, 'usage': usage}, units, usage) if route.execution_mode == 'provider'
                else SyntheticResult({**value, 'usage': usage}, units))

    adapter = ProviderOperationAdapter if route.execution_mode == 'provider' else SyntheticOperationAdapter
    result = adapter(accounting, route.scope_id, max_units=route.max_units()).execute(
        actor, request_id=operation_request, method=method_version, call=call)
    if result['status'] != 'executed':
        return {'status': 'blocked', 'reason': result['reason']}
    return result['value']
