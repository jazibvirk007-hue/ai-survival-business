import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

import cortex_production_server


def _server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_live_route_is_wired_to_real_http_handler(monkeypatch):
    class Runtime:
        def snapshot(self):
            return {"history": []}

    monkeypatch.setattr(
        cortex_production_server,
        "get_cortex_orchestrator",
        lambda: SimpleNamespace(runtime=Runtime()),
    )
    server, thread = _server(cortex_production_server.CortexProductionHandler)
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{server.server_port}/api/command-center/live?limit=5",
            timeout=2,
        ) as response:
            body = json.loads(response.read())
            assert response.status == 200
            assert body["ok"] is True
            assert body["status"] == "READY"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_payment_webhook_is_wired_to_real_http_handler(monkeypatch):
    seen = {}

    def fake_webhook(body, signature):
        seen["body"] = body
        seen["signature"] = signature
        return 200, {"ok": True, "event_id": "evt-test"}

    monkeypatch.setattr(cortex_production_server, "dispatch_payment_webhook", fake_webhook)
    server, thread = _server(cortex_production_server.CortexProductionHandler)
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/payment/webhook",
            data=b'{"event_id":"evt-test"}',
            method="POST",
            headers={"Content-Type": "application/json", "X-Payment-Signature": "sha256=test"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            body = json.loads(response.read())
            assert response.status == 200
            assert body == {"ok": True, "event_id": "evt-test"}
        assert seen == {
            "body": b'{"event_id":"evt-test"}',
            "signature": "sha256=test",
        }
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_payment_webhook_rejects_empty_body_before_processing(monkeypatch):
    called = False

    def fake_webhook(*_args):
        nonlocal called
        called = True
        return 200, {"ok": True}

    monkeypatch.setattr(cortex_production_server, "dispatch_payment_webhook", fake_webhook)
    server, thread = _server(cortex_production_server.CortexProductionHandler)
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/payment/webhook",
            data=b"",
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=2)
            raise AssertionError("expected HTTP 413")
        except urllib.error.HTTPError as error:
            assert error.code == 413
        assert called is False
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
