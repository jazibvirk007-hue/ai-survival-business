"""Atomic persistence for the bounded Cortex autonomy runtime state."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict

STATE_PATH = "cortex_runtime_state.json"
MAX_STATE_KEYS = 40
MAX_HISTORY = 200
MAX_TEXT = 2000


def _validate(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict) or len(state) > MAX_STATE_KEYS:
        raise ValueError("invalid runtime state")
    for key, value in state.items():
        if not isinstance(key, str) or len(key) > 100:
            raise ValueError("invalid runtime state key")
        if isinstance(value, str) and len(value) > MAX_TEXT:
            raise ValueError("runtime state text too large")
        if key == "history" and (not isinstance(value, list) or len(value) > MAX_HISTORY):
            raise ValueError("runtime history too large")
    return state


def load_runtime_state(path: str = STATE_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return _validate(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError("invalid persisted runtime state") from exc


def save_runtime_state(state: Dict[str, Any], path: str = STATE_PATH) -> None:
    data = _validate(dict(state))
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, temporary = tempfile.mkstemp(prefix=".cortex-runtime-", suffix=".tmp", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
