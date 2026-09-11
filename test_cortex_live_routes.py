from cortex_live_routes import dispatch_live_route


def test_live_route_returns_bounded_snapshot(monkeypatch):
    monkeypatch.setattr(
        "cortex_live_routes.build_live_observability",
        lambda snapshot, limit: {"status": "READY", "cycles": {"count": 1}, "communications": {"events": []}},
    )
    status, body = dispatch_live_route("GET", "/api/command-center/live?limit=10", runtime_snapshot={"history": []})
    assert status == 200
    assert body["ok"] is True
    assert body["status"] == "READY"


def test_live_route_requires_runtime_snapshot():
    status, body = dispatch_live_route("GET", "/api/command-center/live")
    assert status == 503
    assert body["error"] == "runtime_snapshot_unavailable"


def test_live_route_rejects_invalid_limit():
    status, body = dispatch_live_route("GET", "/api/command-center/live?limit=51", runtime_snapshot={})
    assert status == 400
    assert body["error"] == "invalid_limit"


def test_live_route_is_read_only():
    status, body = dispatch_live_route("POST", "/api/command-center/live", runtime_snapshot={})
    assert status == 405
    assert body["error"] == "method_not_allowed"
