"""One opt-in HTTPS Responses request with a total deadline, byte limit and no redirects."""

from http.client import HTTPSConnection
import json
from time import monotonic

from smi_ingestion.evidence import EvidenceError


class ResponseBoundExceeded(Exception):
    """The HTTP response exceeded its finite admitted transport contract."""


class ResponsesHTTPTransport:
    """Concrete fixed-endpoint provider adapter, disabled until trusted opt-in.

    ``connection_factory`` is the external HTTP seam used by offline tests. The
    default verifies TLS through HTTPSConnection; there are no redirects, retries,
    proxy/environment credential lookup, polling or secondary provider requests.
    """

    execution_mode = 'provider'

    def __init__(self, *, enabled: bool = False, connection_factory=HTTPSConnection):
        if type(enabled) is not bool:
            raise EvidenceError('model_enablement_invalid')
        self.enabled, self.connection_factory = enabled, connection_factory

    def create(self, request: dict, *, credential: str, timeout_seconds: int, max_response_bytes: int) -> bytes:
        """POST once, read bounded bytes by deadline and close even on uncertainty."""
        if not self.enabled:
            raise EvidenceError('model_live_disabled')
        if (type(timeout_seconds) is not int or not 0 < timeout_seconds <= 30
                or type(max_response_bytes) is not int or not 0 < max_response_bytes <= 1000000):
            raise EvidenceError('model_bounds_invalid')
        body = json.dumps(request, ensure_ascii=False).encode()
        if len(body) > 1000000:
            raise EvidenceError('model_request_bound_exceeded')
        connection = self.connection_factory('api.openai.com', timeout=timeout_seconds)
        deadline = monotonic() + timeout_seconds
        active_socket = None
        def remaining():
            value = deadline - monotonic()
            if value <= 0:
                raise TimeoutError('model_transport_timeout')
            socket = active_socket if active_socket is not None else connection.sock
            if socket is not None:
                socket.settimeout(value)
        try:
            connection.connect()
            active_socket = connection.sock
            remaining()
            connection.request('POST', '/v1/responses', body, {'Authorization': f'Bearer {credential}',
                               'Content-Type': 'application/json', 'Accept': 'application/json', 'Connection': 'close'})
            remaining()
            response = connection.getresponse()
            if response.status != 200:
                # Do not follow redirects or retain provider error bodies/headers.
                raise RuntimeError('model_http_outcome_unavailable')
            result = bytearray()
            while True:
                remaining()
                chunk = response.read1(min(65536, max_response_bytes + 1 - len(result)))
                remaining()
                if not chunk:
                    return bytes(result)
                result.extend(chunk)
                if len(result) > max_response_bytes:
                    raise ResponseBoundExceeded()
        finally:
            connection.close()
