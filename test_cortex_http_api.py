import json

import cortex_http_api


def test_live_get_delegates_to_read_only_route(monkeypatch):
    expected = (200, {"ok": True, "status": "READY"})

    def fake_dispatch(method, path, *, runtime_snapshot):
        assert method == "GET"
        assert path == "/api/command-center/live?limit=5"
        assert runtime_snapshot == {"runtime": {}}
        return expected

    monkeypatch.setattr(cortex_http_api, "dispatch_live_route", fake_dispatch)
    assert cortex_http_api.dispatch_get(
        "/api/command-center/live?limit=5", runtime_snapshot={"runtime": {}}
    ) == expected


def test_live_get_ignores_other_paths():
    assert cortex_http_api.dispatch_get("/api/status", runtime_snapshot={}) is None


def test_payment_webhook_enforces_body_bounds(monkeypatch):
    called = False

    def fake_process(*_args, **_kwargs):
        nonlocal called
        called = True
        return {"ok": True, "status": 200}

    monkeypatch.setattr(cortex_http_api, "process_webhook", fake_process)
    status, result = cortex_http_api.dispatch_payment_webhook(b"", "sig")
    assert status == 413
    assert result["ok"] is False
    assert called is False


def test_payment_webhook_uses_existing_signature_verifier(monkeypatch):
    raw = b'{"event_id":"evt-1"}'
    seen = {}

    def fake_process(body, signature):
        seen["body"] = body
        seen["signature"] = signature
        return {"ok": True, "status": 200, "event_id": "evt-1"}

    monkeypatch.setattr(cortex_http_api, "process_webhook", fake_process)
    status, result = cortex_http_api.dispatch_payment_webhook(raw, "sha256=test")
    assert status == 200
    assert result["event_id"] == "evt-1"
    assert seen == {"body": raw, "signature": "sha256=test"}


def test_payment_signature_accepts_provider_header_aliases():
    assert cortex_http_api.payment_signature({"X-Payment-Signature": " sig "}) == "sig"
    assert cortex_http_api.payment_signature({"X-Webhook-Signature": "other"}) == "other"
    assert cortex_http_api.payment_signature({}) is None


def test_sandbox_event_builder_is_stable():
    event = cortex_http_api.build_payment_event(
        event_id="evt-1",
        order_id="ord-1",
        transaction_id="txn-1",
        amount="19.99",
        currency="USD",
    )
    assert json.loads(event) == {
        "event_id": "evt-1",
        "type": "payment.succeeded",
        "order_id": "ord-1",
        "transaction_id": "txn-1",
        "amount": "19.99",
        "currency": "USD",
    }
