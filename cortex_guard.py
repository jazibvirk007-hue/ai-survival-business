"""Governance and approval queue for TJ Cortex.

The CEO can propose work, but governed actions cannot execute until an explicit
approval is recorded. The queue is local, bounded, atomic, and fail-closed.
"""

import json
import os
import tempfile
import time
import uuid
from typing import Any, Dict, List


DEFAULT_PATH = "cortex_approvals.json"
MAX_ENTRIES = 500
MAX_TEXT_CHARS = 2000


class CortexGuard:
    """Persist and govern explicit human approvals for CEO actions."""

    def __init__(self, path=DEFAULT_PATH, max_entries=MAX_ENTRIES, approval_ttl_seconds=86400):
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path is required")
        if not isinstance(max_entries, int) or max_entries < 1:
            raise ValueError("max_entries must be positive")
        if not isinstance(approval_ttl_seconds, int) or approval_ttl_seconds < 1:
            raise ValueError("approval_ttl_seconds must be positive")
        self.path = path
        self.max_entries = max_entries
        self.approval_ttl_seconds = approval_ttl_seconds

    def _load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ValueError("approval store must be a list of objects")
        return data

    def _save(self, entries: List[Dict[str, Any]]) -> None:
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".cortex-approval-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(entries[-self.max_entries:], handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _text(value, field):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        value = value.strip()
        if len(value) > MAX_TEXT_CHARS:
            raise ValueError(f"{field} is too long")
        return value

    def request(self, action: str, reason: str, priority: int = 0) -> Dict[str, Any]:
        action = self._text(action, "action")
        reason = self._text(reason, "reason")
        if not isinstance(priority, int) or priority < 0:
            raise ValueError("priority must be a non-negative integer")
        now = int(time.time())
        entry = {
            "id": uuid.uuid4().hex,
            "action": action,
            "reason": reason,
            "priority": priority,
            "created_at": now,
            "expires_at": now + self.approval_ttl_seconds,
            "status": "pending",
        }
        entries = self._load()
        entries.append(entry)
        self._save(entries)
        return entry

    def _get(self, approval_id: str) -> Dict[str, Any]:
        approval_id = self._text(approval_id, "approval_id")
        for entry in self._load():
            if entry.get("id") == approval_id:
                return entry
        raise KeyError("approval not found")

    def approve(self, approval_id: str) -> Dict[str, Any]:
        entries = self._load()
        approval_id = self._text(approval_id, "approval_id")
        now = int(time.time())
        for entry in entries:
            if entry.get("id") == approval_id:
                if entry.get("status") != "pending":
                    raise ValueError("approval is not pending")
                if now >= int(entry.get("expires_at", 0)):
                    entry["status"] = "expired"
                    self._save(entries)
                    raise ValueError("approval has expired")
                entry["status"] = "approved"
                entry["approved_at"] = now
                self._save(entries)
                return entry
        raise KeyError("approval not found")

    def reject(self, approval_id: str) -> Dict[str, Any]:
        entries = self._load()
        approval_id = self._text(approval_id, "approval_id")
        for entry in entries:
            if entry.get("id") == approval_id:
                if entry.get("status") != "pending":
                    raise ValueError("approval is not pending")
                entry["status"] = "rejected"
                entry["rejected_at"] = int(time.time())
                self._save(entries)
                return entry
        raise KeyError("approval not found")

    def consume(self, approval_id: str, action: str) -> Dict[str, Any]:
        """Consume one approved request for exactly one matching action."""
        entries = self._load()
        approval_id = self._text(approval_id, "approval_id")
        action = self._text(action, "action")
        now = int(time.time())
        for entry in entries:
            if entry.get("id") == approval_id:
                if entry.get("action") != action:
                    raise ValueError("approval action mismatch")
                if entry.get("status") != "approved":
                    raise ValueError("approval is not executable")
                if now >= int(entry.get("expires_at", 0)):
                    entry["status"] = "expired"
                    self._save(entries)
                    raise ValueError("approval has expired")
                entry["status"] = "consumed"
                entry["consumed_at"] = now
                self._save(entries)
                return entry
        raise KeyError("approval not found")

    def pending(self) -> List[Dict[str, Any]]:
        now = int(time.time())
        entries = self._load()
        changed = False
        for entry in entries:
            if entry.get("status") == "pending" and now >= int(entry.get("expires_at", 0)):
                entry["status"] = "expired"
                changed = True
        if changed:
            self._save(entries)
        return [entry for entry in entries if entry.get("status") == "pending"]

    def status(self) -> Dict[str, Any]:
        entries = self._load()
        return {
            "engine": "Cortex Guard",
            "version": "8.1",
            "pending": sum(1 for entry in entries if entry.get("status") == "pending"),
            "approved": sum(1 for entry in entries if entry.get("status") == "approved"),
            "max_entries": self.max_entries,
            "approval_ttl_seconds": self.approval_ttl_seconds,
        }
