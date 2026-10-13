"""HTTP dispatch shared by bounded source transports."""

from urllib.request import HTTPRedirectHandler, Request, build_opener


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        # Each transport call accounts for one request; redirect hops would
        # escape that budget and could forward credentials to another host.
        return None


def open_no_redirect(request: Request, timeout: int):
    """Dispatch one HTTP request; return redirect responses as HTTPError."""
    return build_opener(_RejectRedirects()).open(request, timeout=timeout)
