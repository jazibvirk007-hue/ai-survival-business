"""Production HTTP entry point that extends the existing Cortex dashboard handler.

The dashboard remains the UI; this adapter adds governed live-observability and
payment-webhook routes without duplicating runtime or commerce logic.
"""
from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

from cortex_dashboard import CortexHandler, HOST, PORT
from cortex_http_api import (
    MAX_REQUEST_BYTES,
    dispatch_get,
    dispatch_lemonsqueezy_webhook,
    dispatch_payment_webhook,
    lemonsqueezy_signature,
    payment_signature,
)
from cortex_runtime_singleton import get_cortex_orchestrator


class CortexProductionHandler(CortexHandler):
    """Dashboard handler with the production API boundaries enabled."""

    def do_GET(self):
        if urlparse(self.path).path == "/api/command-center/live":
            try:
                snapshot = get_cortex_orchestrator().runtime.snapshot()
                status, body = dispatch_get(self.path, runtime_snapshot=snapshot)
            except Exception:
                status, body = 503, {"ok": False, "error": "runtime_snapshot_unavailable"}
            self._send(status, json.dumps(body))
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in {"/api/payment/webhook", "/api/payment/lemonsqueezy/webhook"}:
            super().do_POST()
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._send(413, json.dumps({"ok": False, "error": "request too large or empty"}))
            return
        raw = self.rfile.read(length)
        if path == "/api/payment/lemonsqueezy/webhook":
            status, body = dispatch_lemonsqueezy_webhook(raw, lemonsqueezy_signature(self.headers))
        else:
            status, body = dispatch_payment_webhook(raw, payment_signature(self.headers))
        self._send(status, json.dumps(body))


def serve(host: str = HOST, port: int = PORT):
    server = ThreadingHTTPServer((host, port), CortexProductionHandler)
    print(f"TJ Cortex Production Server: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
