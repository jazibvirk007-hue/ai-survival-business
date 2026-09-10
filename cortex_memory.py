"""Persistent, bounded, secret-safe memory for TJ Cortex."""

import json
import os
import tempfile
import time


DEFAULT_PATH = "cortex_memory.json"
MAX_ENTRIES = 500
MAX_TEXT_CHARS = 4000


class CortexMemory:
    """Store useful observations without turning memory into an unsafe secret vault."""

    def __init__(self, path=DEFAULT_PATH, max_entries=MAX_ENTRIES):
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path is required")
        if not isinstance(max_entries, int) or max_entries < 1:
            raise ValueError("max_entries must be positive")
        self.path = path
        self.max_entries = max_entries

    def _load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError("memory store must be a list")
        return data

    def _save(self, entries):
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".cortex-memory-", suffix=".tmp", dir=directory)
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

    @staticmethod
    def _safe_metadata(metadata):
        if metadata is None:
            return {}
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")
        safe = {}
        for key, value in metadata.items():
            if not isinstance(key, str) or len(key) > 100:
                continue
            if any(secret in key.lower() for secret in ("key", "token", "secret", "password", "private")):
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe[key] = value
        return safe

    def remember(self, kind, content, metadata=None):
        """Append one safe memory entry and return its persisted representation."""
        kind = self._text(kind, "kind")
        content = self._text(content, "content")
        entry = {
            "timestamp": int(time.time()),
            "kind": kind,
            "content": content,
            "metadata": self._safe_metadata(metadata),
        }
        entries = self._load()
        entries.append(entry)
        self._save(entries)
        return entry

    def recent(self, limit=20):
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be positive")
        return self._load()[-min(limit, self.max_entries):]

    def clear(self):
        """Remove memory only when an explicit local maintenance operation requests it."""
        if os.path.exists(self.path):
            os.unlink(self.path)
