"""Crash-safe persistence for Cortex autonomous scheduler state."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

STATE_PATH = "cortex_scheduler_state.json"
MAX_KEYS = 30
MAX_TEXT = 500


def _validate(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or len(state) > MAX_KEYS:
        raise ValueError("invalid scheduler state")
    for key, value in state.items():
        if not isinstance(key, str) or len(key) > 100:
            raise ValueError("invalid scheduler state key")
        if isinstance(value, str) and len(value) > MAX_TEXT:
            raise ValueError("scheduler state text too large")
    return dict(state)


def load_scheduler_state(path: str = STATE_PATH) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    if os.path.getsize(path) == 0:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return _validate(json.load(handle))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid persisted scheduler state") from exc


def save_scheduler_state(state: dict[str, Any], path: str = STATE_PATH) -> None:
    state = _validate(state)
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, temp_path = tempfile.mkstemp(prefix=".cortex-scheduler-", suffix=".tmp", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
