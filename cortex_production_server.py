"""Production HTTP entry point for the governed Cortex dashboard and APIs."""
from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

from cortex_dashboard import CortexHandler, HOST, PORT
from cortex_http_api import MAX_REQUEST_BYTES, dispatch_get, dispatch_payment_webhook, payment_signature
from cortex_runtime_singleton import get_cortex_orchestrator
from cortex_stripe_adapter import process_stripe_webhook
from cortex_stripe_ui import api_delete as stripe_api_delete, api_get as stripe_api_get, api_post as stripe_api_post, page as stripe_page


class CortexProductionHandler(CortexHandler):
    """Dashboard handler with governed live-observability and Stripe boundaries."""

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            return None, 413
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8")), 200
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, 400

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/command-center/live":
            try:
                snapshot = get_cortex_orchestrator().runtime.snapshot()
                status, body = dispatch_get(self.path, runtime_snapshot=snapshot)
            except Exception:
                status, body = 503, {"ok": False, "error": "runtime_snapshot_unavailable"}
            self._send(status, json.dumps(body))
            return
        if path in {"/payments", "/settings/payments", "/settings/stripe"}:
            self._send(200, stripe_page(), "text/html; charset=utf-8")
            return
        if path == "/api/settings/stripe":
            status, body = stripe_api_get()
            self._send(status, json.dumps(body))
            return
        super().do_GET()

    def do_DELETE(self):
        if urlparse(self.path).path != "/api/settings/stripe":
            self._send(404, json.dumps({"ok": False, "error": "route not found"}))
            return
        status, body = stripe_api_delete()
        self._send(status, json.dumps(body))

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/settings/stripe":
            payload, status = self._read_json()
            if status != 200:
                self._send(status, json.dumps({"ok": False, "error": "invalid request body"}))
                return
            status, body = stripe_api_post(payload)
            self._send(status, json.dumps(body))
            return
        if path == "/api/payment/stripe/webhook":
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_REQUEST_BYTES:
                self._send(413, json.dumps({"ok": False, "error": "request too large or empty"}))
                return
            raw = self.rfile.read(length)
            status, body = process_stripe_webhook(raw, self.headers.get("Stripe-Signature"))
            self._send(status, json.dumps(body))
            return
        if path == "/api/payment/webhook":
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_REQUEST_BYTES:
                self._send(413, json.dumps({"ok": False, "error": "request too large or empty"}))
                return
            raw = self.rfile.read(length)
            status, body = dispatch_payment_webhook(raw, payment_signature(self.headers))
            self._send(status, json.dumps(body))
            return
        super().do_POST()


def serve(host: str = HOST, port: int = PORT):
    server = ThreadingHTTPServer((host, port), CortexProductionHandler)
    print(f"TJ Cortex Production Server: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
