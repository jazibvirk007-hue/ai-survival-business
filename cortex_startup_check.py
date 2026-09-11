"""Safe local startup validation for the Cortex Command Center."""
from __future__ import annotations

import importlib
import sys
from typing import Any

REQUIRED_MODULES = (
    "cortex_v95_orchestrator",
    "cortex_command_center",
    "cortex_scheduler_service",
    "cortex_neural_network",
)


def run_startup_check() -> dict[str, Any]:
    """Validate the local Python/runtime surface without contacting external services."""
    modules = {}
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            modules[name] = "READY"
        except Exception as exc:
            modules[name] = f"FAILED:{type(exc).__name__}"
    ok = all(value == "READY" for value in modules.values())
    return {
        "ok": ok,
        "python": sys.version.split()[0],
        "modules": modules,
        "external_services_contacted": False,
        "truth_policy": "startup validation only; no customer, payment, outbound, or treasury actions",
    }


if __name__ == "__main__":
    result = run_startup_check()
    print("CORTEX STARTUP CHECK: " + ("READY" if result["ok"] else "FAILED"))
    for name, status in result["modules"].items():
        print(f"- {name}: {status}")
    raise SystemExit(0 if result["ok"] else 1)
