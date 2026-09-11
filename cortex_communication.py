"""Observable inter-agent communication bus for Cortex.

The bus records real orchestration events so the Command Center can render
agent-to-agent communication without inventing conversations or telemetry.
Secrets and full customer payloads must never be placed in event metadata.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


DEFAULT_PATH = "cortex_communications.json"
MAX_EVENTS = 500
MAX_TEXT = 500


class CortexCommunicationError(RuntimeError):
    """Raised when the communication event store is invalid or unavailable."""


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text[:MAX_TEXT]


def _load(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError, TypeError) as exc:
        raise CortexCommunicationError("communication event store is unreadable") from exc
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise CortexCommunicationError("communication event store has invalid structure")
    return data[-MAX_EVENTS:]


def _save(path: str, events: List[Dict[str, Any]]) -> None:
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".cortex-communications-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(events[-MAX_EVENTS:], handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def record_message(
    sender: str,
    recipient: str,
    message_type: str,
    summary: str,
    *,
    status: str = "sent",
    correlation_id: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    path: str = DEFAULT_PATH,
) -> Dict[str, Any]:
    """Record one real agent communication event and return its safe event view."""
    sender, recipient = _safe_text(sender), _safe_text(recipient)
    message_type, status = _safe_text(message_type), _safe_text(status)
    summary = _safe_text(summary)
    if not sender or not recipient or not message_type or not summary:
        raise ValueError("sender, recipient, message_type, and summary are required")

    clean_metadata: Dict[str, Any] = {}
    if metadata:
        for key, value in metadata.items():
            key_text = _safe_text(key)
            if not key_text or len(clean_metadata) >= 20:
                continue
            if isinstance(value, str):
                clean_metadata[key_text] = _safe_text(value)
            elif isinstance(value, (int, float, bool, type(None))):
                clean_metadata[key_text] = value

    event = {
        "id": "MSG-" + uuid.uuid4().hex[:12].upper(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender": sender,
        "recipient": recipient,
        "message_type": message_type,
        "summary": summary,
        "status": status,
        "correlation_id": _safe_text(correlation_id) if correlation_id else None,
        "metadata": clean_metadata,
    }
    events = _load(path)
    events.append(event)
    _save(path, events)
    return dict(event)


def recent_messages(limit: int = 50, path: str = DEFAULT_PATH) -> List[Dict[str, Any]]:
    """Return newest communication events first, bounded for UI consumption."""
    if not isinstance(limit, int) or not 1 <= limit <= MAX_EVENTS:
        raise ValueError(f"limit must be between 1 and {MAX_EVENTS}")
    return list(reversed(_load(path)[-limit:]))


def clear_messages(path: str = DEFAULT_PATH) -> None:
    """Remove the local event stream; intended for tests/local reset only."""
    try:
        os.remove(path)
    except FileNotFoundError:
        return


def communication_status(path: str = DEFAULT_PATH) -> Dict[str, Any]:
    events = _load(path)
    return {
        "enabled": True,
        "events": len(events),
        "max_events": MAX_EVENTS,
        "storage": path,
        "live_stream_ready": True,
    }
