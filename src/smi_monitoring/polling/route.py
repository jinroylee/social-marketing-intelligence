"""One fixed-host, bounded X recent-search request, with no automatic retries."""

from dataclasses import dataclass, field
from datetime import timedelta
import hashlib
import json
import math
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from smi_ingestion.adapters.http import open_no_redirect
from smi_ingestion.evidence import EvidenceError
from smi_monitoring.contracts import require
from smi_monitoring.recent.route import instant, validate_records

ROUTE = 'x-recent-search'
MAX_BYTES = 65536
MAX_RECORDS = 10
TIMEOUT = 15
MAX_SECONDS = 20
BOUNDS = {'max_requests': 1, 'max_records': MAX_RECORDS, 'max_response_bytes': MAX_BYTES, 'max_request_bytes': 2048,
          'minimum_interval_seconds': 2, 'max_elapsed_seconds': MAX_SECONDS, 'socket_timeout_seconds': TIMEOUT}


class XCollectionError(EvidenceError):
    """Sanitized source failure with bounded source-free acquisition evidence."""

    def __init__(self, reason, receipt):
        super().__init__(reason)
        self.receipt = receipt


@dataclass(frozen=True)
class LiveXConfig:
    """Explicit trusted runtime gates; credentials are transient and never represented."""

    enabled: bool = False
    operation_authorized: bool = False
    source_use_authorized: bool = False
    bearer_token: str | None = field(default=None, repr=False)

    def __post_init__(self):
        require(all(type(getattr(self, k)) is bool for k in ('enabled', 'operation_authorized', 'source_use_authorized')), 'invalid_live_x_gate')

    def unavailable_reason(self):
        for gate, reason in (('enabled', 'live_x_disabled'), ('operation_authorized', 'live_x_operation_authorization_required'),
                              ('source_use_authorized', 'live_x_source_use_authorization_required'), ('bearer_token', 'live_x_credentials_required')):
            if not getattr(self, gate):
                return reason
        require(isinstance(self.bearer_token, str) and len(self.bearer_token) <= 4096 and all(33 <= ord(c) <= 126 for c in self.bearer_token), 'invalid_live_x_credential')
        return None


def response_cooldown(status, headers, now):
    """Return a bounded conservative delay from source quota metadata, never a retry grant."""
    headers = headers or {}
    delay = 900 if status == 429 else 0
    try:
        remaining = int(headers.get('x-rate-limit-remaining', '-1'))
        reset = int(headers.get('x-rate-limit-reset', '0')) - int(now.timestamp())
        retry_after = int(headers.get('retry-after', '0'))
        if remaining >= 0 and 0 < reset <= 86400:
            delay = max(delay, reset if remaining == 0 else math.ceil(reset / (remaining + 1)))
        if status == 429 and 0 < retry_after <= 86400:
            delay = max(delay, retry_after)
    except (ValueError, TypeError, OverflowError):
        pass
    return delay


class XRecentRoute:
    """Read one page, never follow pagination, redirects, pending responses or errors."""

    def __init__(self, config, *, monotonic=time.monotonic):
        self.config, self.monotonic = config, monotonic

    def validate(self, prepared, now, *, activation=False):
        """Reject unsupported query/time bounds before any chargeable dispatch."""
        query = prepared['settings']['query'].strip()
        require(all(c.isalnum() or c in ' _-' for c in query), 'live_x_literal_query_required')
        require(instant(prepared['window_start']) >= now - timedelta(days=7), 'live_x_recent_time_limit')
        require(activation or instant(prepared['window_end']) <= now - timedelta(seconds=30), 'live_x_indexing_delay')
        params = {'query': '"' + query + '"', 'start_time': prepared['window_start'], 'end_time': prepared['window_end'],
                  'max_results': MAX_RECORDS, 'sort_order': 'recency', 'post.fields': 'created_at,public_metrics'}
        url = 'https://api.x.com/2/tweets/search/recent?' + urlencode(params)
        require(len(url.encode()) <= 2048, 'live_x_request_byte_limit')
        return url

    def collect(self, prepared, response_id, now):
        """Return validated captures and source-free receipt; unsuccessful calls stay uncertain."""
        receipt = {'route': ROUTE, 'bounds': dict(BOUNDS), 'requests': None, 'bytes_read': None, 'response_status': None}
        try:
            return self._collect(prepared, response_id, now, receipt)
        except EvidenceError as error:
            raise XCollectionError(str(error), receipt) from None

    def _collect(self, prepared, response_id, now, receipt):
        require(self.config.unavailable_reason() is None, 'live_x_unavailable')
        url = self.validate(prepared, now)
        request = Request(url, headers={'Authorization': 'Bearer ' + self.config.bearer_token, 'Accept': 'application/json', 'User-Agent': 'smi-recent-monitoring/1'})
        began = self.monotonic()
        receipt.update(requests=1, request_bytes=len(url.encode()))
        try:
            with open_no_redirect(request, TIMEOUT) as reply:
                status = reply.status
                receipt.update(response_status=status, bytes_read=0, cooldown_seconds=response_cooldown(status, reply.headers, now))
                chunks = []
                while receipt['bytes_read'] < MAX_BYTES:
                    receipt['elapsed_seconds'] = self.monotonic() - began
                    require(receipt['elapsed_seconds'] <= MAX_SECONDS, 'live_x_elapsed_limit')
                    chunk = reply.read1(min(4096, MAX_BYTES - receipt['bytes_read']))
                    require(isinstance(chunk, bytes), 'live_x_invalid_body')
                    receipt['bytes_read'] += len(chunk)
                    chunks.append(chunk)
                    receipt['elapsed_seconds'] = self.monotonic() - began
                    require(receipt['elapsed_seconds'] <= MAX_SECONDS, 'live_x_elapsed_limit')
                    if not chunk:
                        break
                raw = b''.join(chunks)
        except HTTPError as error:
            receipt.update(response_status=error.code, cooldown_seconds=response_cooldown(error.code, error.headers, now))
            raise EvidenceError('live_x_transport_uncertain') from None
        except (URLError, OSError, TimeoutError):
            raise EvidenceError('live_x_transport_uncertain') from None
        receipt.update(bytes_read=len(raw), response_status=status, elapsed_seconds=self.monotonic() - began)
        require(receipt['elapsed_seconds'] <= MAX_SECONDS, 'live_x_elapsed_limit')
        require(len(raw) < MAX_BYTES, 'live_x_response_byte_limit')
        require(status == 200, 'live_x_pending_or_http_uncertain')
        try:
            document = json.loads(raw)
        except (ValueError, UnicodeError):
            raise EvidenceError('live_x_invalid_json') from None
        require(isinstance(document, dict) and not document.get('errors'), 'live_x_partial_error')
        records, meta = document.get('data', []), document.get('meta')
        require(isinstance(records, list) and len(records) <= MAX_RECORDS and isinstance(meta, dict)
                and type(meta.get('result_count')) is int and meta['result_count'] == len(records), 'live_x_response_record_limit')
        next_token = meta.get('next_token')
        require(next_token is None or isinstance(next_token, str) and 1 <= len(next_token) <= 2048, 'live_x_invalid_pagination')
        mapped = []
        for record in records:
            require(isinstance(record, dict) and isinstance(record.get('id'), str) and re.fullmatch(r'[0-9]{1,19}', record['id']), 'live_x_invalid_identity')
            metrics = record.get('public_metrics', {})
            require(isinstance(metrics, dict), 'live_x_invalid_metrics')
            if record.get('withheld'):
                continue
            mapped.append({'capture_id': response_id + ':' + record['id'], 'native_id': record['id'], 'text': record.get('text'),
                'published_at': record.get('created_at'), 'captured_at': None, 'metric_measured_at': None,
                'metrics': {target: metrics[source] for source, target in [('like_count', 'like_count'), ('repost_count', 'repost_count'), ('reply_count', 'reply_count')] if source in metrics}})
        mapped = validate_records(mapped)
        return mapped, {**receipt, 'route': ROUTE, 'version': 'x-recent-search-v1', 'synthetic': False,
            'response_id': response_id, 'response_sha256': hashlib.sha256(raw).hexdigest(), 'bytes_read': len(raw),
            'request_bytes': len(url.encode()), 'requests': 1, 'returned_records': len(records), 'pagination_remaining': next_token is not None,
            'retrieved_at': now.isoformat(), 'declared_coverage': 'partial',
            'sampling': {'method': 'literal-query-recent-page-v1', 'record_schema': 'x-api-v2-recent-v1',
                         'file_record_limit': MAX_RECORDS, 'file_byte_limit': MAX_BYTES, 'max_seconds': MAX_SECONDS}}
