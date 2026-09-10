"""Learning bridge for TJ Cortex: record decisions and observed outcomes safely."""

from cortex_memory import CortexMemory


class CortexLearning:
    """Turn real observations into bounded memory without granting action authority."""

    def __init__(self, memory=None):
        if memory is None:
            memory = CortexMemory()
        if not isinstance(memory, CortexMemory):
            raise TypeError("memory must be a CortexMemory")
        self.memory = memory

    @staticmethod
    def _text(value, field):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        return value.strip()

    def record_decision(self, action, reason, priority, approval_required):
        action = self._text(action, "action")
        reason = self._text(reason, "reason")
        if not isinstance(priority, int) or priority < 0:
            raise ValueError("priority must be a non-negative integer")
        if not isinstance(approval_required, bool):
            raise TypeError("approval_required must be boolean")
        return self.memory.remember(
            "decision",
            f"{action}: {reason}",
            {"priority": priority, "approval_required": approval_required},
        )

    def record_outcome(self, action, outcome, success):
        action = self._text(action, "action")
        outcome = self._text(outcome, "outcome")
        if not isinstance(success, bool):
            raise TypeError("success must be boolean")
        return self.memory.remember(
            "outcome",
            f"{action}: {outcome}",
            {"success": success},
        )

    def context(self, limit=10):
        """Return recent learning context suitable for a CEO prompt."""
        entries = self.memory.recent(limit)
        return [
            {
                "timestamp": entry.get("timestamp"),
                "kind": entry.get("kind"),
                "content": entry.get("content"),
                "metadata": entry.get("metadata", {}),
            }
            for entry in entries
            if isinstance(entry, dict)
        ]
