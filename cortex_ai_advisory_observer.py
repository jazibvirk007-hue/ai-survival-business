"""Bounded observability for AI advisory decisions.

This module deliberately does not execute or mutate business state. It records
only whether an advisory was accepted and which deterministic action was
recommended, allowing the dashboard and Neural Network to show real AI activity.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from cortex_ai_advisor import CortexAIAdvisor, advisory_dict
from cortex_communication import record_message


class CortexAIAdvisoryObserver:
    def __init__(self, advisor: CortexAIAdvisor, *, communication_path: str = "cortex_communications.json") -> None:
        if not isinstance(advisor, CortexAIAdvisor):
            raise TypeError("advisor must be CortexAIAdvisor")
        self.advisor = advisor
        self.communication_path = communication_path

    def evaluate(self, candidates: list[Mapping[str, Any]], *, correlation_id: Optional[str] = None) -> dict[str, Any]:
        advisory = self.advisor.advise(candidates)
        event_id = correlation_id or "AI-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        payload = advisory_dict(advisory)
        payload.update({"timestamp": datetime.now(timezone.utc).isoformat(), "correlation_id": event_id})
        try:
            record_message(
                "Cortex AI Advisor",
                "Cortex CEO",
                "advisory",
                f"AI advisory {'accepted' if advisory.accepted else 'rejected'} for {advisory.action or 'no action'}",
                status="completed" if advisory.accepted else "blocked",
                correlation_id=event_id,
                metadata={"action": advisory.action, "score": advisory.score, "accepted": advisory.accepted},
                path=self.communication_path,
            )
        except Exception:
            pass
        return payload
