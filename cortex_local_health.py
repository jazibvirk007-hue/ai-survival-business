"""Fail-closed local health checks for the Cortex Windows beta."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


REQUIRED_MODULES = (
    "ai_ceo",
    "cortex_v95_orchestrator",
    "cortex_command_center_routes",
    "cortex_dashboard_live_api",
    "cortex_scheduler_service",
    "cortex_runtime_singleton",
)

REQUIRED_ASSETS = (
    "cortex_dashboard.py",
    "cortex_neural_network.js",
    "Start-Cortex.bat",
)


def build_local_health(root: str | Path | None = None) -> dict[str, Any]:
    """Return a safe installation snapshot without reading secrets."""
    base = Path(root) if root is not None else Path(__file__).resolve().parent
    modules: dict[str, str] = {}
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            modules[name] = "READY"
        except Exception as exc:
            modules[name] = f"FAILED:{type(exc).__name__}"

    assets = {
        name: "READY" if (base / name).is_file() else "MISSING"
        for name in REQUIRED_ASSETS
    }
    module_ok = all(value == "READY" for value in modules.values())
    asset_ok = all(value == "READY" for value in assets.values())
    return {
        "status": "READY" if module_ok and asset_ok else "DEGRADED",
        "engine": "Cortex Local Health",
        "version": "1.0",
        "modules": modules,
        "assets": assets,
        "secrets_checked": False,
        "truth_policy": "health check never reads credentials or financial truth",
    }


def assert_local_health(root: str | Path | None = None) -> dict[str, Any]:
    """Raise when the local beta cannot safely start."""
    result = build_local_health(root)
    if result["status"] != "READY":
        raise RuntimeError("Cortex local health check failed")
    return result
