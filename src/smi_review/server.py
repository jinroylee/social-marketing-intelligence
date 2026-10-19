"""Loopback HTTP boundary for the trusted local review application."""

from __future__ import annotations

import argparse
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from smi_ingestion.db import Database
from smi_ingestion.evidence import EvidenceError

from .app import Response, ReviewApp
from .views import request_error


class ReviewServer(ThreadingHTTPServer):
    """A loopback server with a single configured local reviewer."""

    daemon_threads = True

    def __init__(self, app: ReviewApp, port: int):
        self.app = app
        super().__init__(("127.0.0.1", port), ReviewHandler)
        self.url = f"http://127.0.0.1:{self.server_port}"


class ReviewHandler(BaseHTTPRequestHandler):
    """Enforce local Host, same-origin writes, bounded forms and no-store responses."""

    server: ReviewServer
    server_version = "SMIReview"

    def log_message(self, format, *args):
        # Form data and record URLs stay out of the local console log.
        pass

    def _send(self, response: Response):
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'self'; script-src 'self'; "
                         "form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        # Keep form POST origins intact while withholding referrers from external sites.
        self.send_header("Referrer-Policy", "same-origin")
        if response.location:
            self.send_header("Location", response.location)
        self.end_headers()
        self.wfile.write(response.body)

    def _reject(self, status: int, message: str):
        content = request_error(message, self.server.url)
        self._send(self.server.app.page("Request unavailable", content, status))

    def _allowed(self) -> bool:
        hosts = self.headers.get_all("Host", [])
        allowed_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if len(hosts) != 1 or hosts[0] not in allowed_hosts:
            self._reject(403, "Use the local review address")
            return False
        if self.command == "POST" and (self.headers.get_all("Origin", []) != ["http://" + hosts[0]]
                                       or self.headers.get("Sec-Fetch-Site") == "cross-site"):
            self._reject(403, "Reopen the local review form before saving")
            return False
        return True

    def do_GET(self):
        if self._allowed():
            self._send(self.server.app.handle("GET", self.path))

    def do_POST(self):
        if not self._allowed():
            return
        try:
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or self.headers.get("Transfer-Encoding"):
                raise ValueError("invalid length")
            length = int(lengths[0])
            if not 0 < length <= 1_048_576:
                self._reject(413, "The form is too large or empty")
                return
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/x-www-form-urlencoded":
                self._reject(415, "Submit the browser form")
                return
            self.connection.settimeout(10)
            payload = self.rfile.read(length)
            if len(payload) != length:
                raise ValueError("incomplete form")
            form = parse_qs(payload.decode("utf-8"), keep_blank_values=True, max_num_fields=5000, errors="strict")
        except (ValueError, UnicodeError, TimeoutError):
            self._reject(400, "The form could not be read")
            return
        self._send(self.server.app.handle("POST", self.path, form))


def make_server(app: ReviewApp, port: int = 8765) -> ReviewServer:
    """Create a loopback-only server; port zero allocates a test/demo port."""
    return ReviewServer(app, port)


def main(argv: list[str] | None = None) -> int:
    """Serve existing local persistence; setup/import remain explicit operator actions."""
    parser = argparse.ArgumentParser(prog="smi-review")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--actor", default="local-marketer")
    parser.add_argument("--dsn", default=os.environ.get("SMI_DATABASE_URL", "postgresql://smi:local_only_change_me@127.0.0.1:6543/smi"))
    parser.add_argument("--schema", default=os.environ.get("SMI_DATABASE_SCHEMA"))
    args = parser.parse_args(argv)
    try:
        app = ReviewApp(Database(args.dsn, args.schema), args.actor)
        with make_server(app, args.port) as server:
            print(f"Local campaign review: {server.url} · reviewer: {app.actor.actor_id}", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, EvidenceError):
        print("Could not start local review. Check the port and reviewer name.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
