"""Bounded outcome ledger for Cortex learning and observability."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import os
import tempfile


class CortexOutcomeLedger:
    """Persist only execution outcomes; never derive revenue from outcomes."""

    VERSION = "17.0"
    MAX_RECORDS = 500

    def __init__(self, path: str = "cortex_outcomes.json") -> None:
        self.path = path

    def _load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list) or any(not isinstance(x, dict) for x in data):
            raise RuntimeError("outcome ledger is invalid")
        return data[-self.MAX_RECORDS :]

    def record(self, *, cycle_id: str, action: str, success: bool, outcome: Any, verified: bool = False) -> Dict[str, Any]:
        if not cycle_id or not action:
            raise ValueError("cycle_id and action are required")
        safe_outcome = str(outcome)[:500]
        item = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": cycle_id,
            "action": action,
            "success": bool(success),
            "outcome": safe_outcome,
            "verified": bool(verified),
        }
        records = self._load()
        records.append(item)
        records = records[-self.MAX_RECORDS :]
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=".cortex-outcomes-", dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(records, handle, indent=2)
                handle.write("\n")
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        return dict(item)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        if limit < 1:
            return []
        return self._load()[-min(limit, self.MAX_RECORDS) :]

    def status(self) -> Dict[str, Any]:
        return {"version": self.VERSION, "records": len(self._load()), "max_records": self.MAX_RECORDS, "revenue_policy": "never_derived_from_outcomes"}
