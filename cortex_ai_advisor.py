"""Governed AI advisory layer for Cortex CEO decisions.

The model may rank deterministic CEO candidates, but it cannot invent actions or
execute them. Deterministic CEO logic remains authoritative; this module only
returns a validated advisory signal for observability and bounded ranking.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Sequence

from cortex_ai_policy import advisory_prompt, validate_advisory
from cortex_ai_runtime import AIRuntimeError, AISelection, CortexAIRuntime


@dataclass(frozen=True)
class AIAdvisory:
    action: str
    score: int
    reason: str
    accepted: bool
    provider_id: str
    model: str


class CortexAIAdvisor:
    """Ask a configured provider for bounded advice without granting authority."""

    def __init__(self, runtime: CortexAIRuntime, selection: AISelection) -> None:
        if not isinstance(runtime, CortexAIRuntime):
            raise TypeError("runtime must be a CortexAIRuntime")
        if not isinstance(selection, AISelection):
            raise TypeError("selection must be an AISelection")
        self.runtime = runtime
        self.selection = selection

    @staticmethod
    def _parse(text: str) -> Mapping[str, Any]:
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError("AI advisory response must be a JSON object")
        return value

    def advise(self, candidates: Sequence[Mapping[str, Any]]) -> AIAdvisory:
        """Return a safe advisory; provider failures become rejected advice."""
        candidate_actions = [str(item.get("action", "")) for item in candidates if isinstance(item, Mapping)]
        prompt = advisory_prompt(candidates)
        try:
            text = self.runtime.generate(
                self.selection,
                [
                    {"role": "system", "content": "You are Cortex advisory intelligence. You rank only supplied candidates. Never execute actions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            result = validate_advisory(self._parse(text), candidate_actions)
            return AIAdvisory(result.action, result.score, result.reason, result.accepted, self.selection.provider_id, self.selection.model)
        except (AIRuntimeError, ValueError, TypeError, json.JSONDecodeError) as error:
            return AIAdvisory("", 0, f"AI advisory unavailable: {type(error).__name__}", False, self.selection.provider_id, self.selection.model)

    def safe_status(self) -> dict[str, Any]:
        status = dict(self.runtime.status(self.selection))
        status.pop("credential_env", None)
        return status


def advisory_dict(advisory: AIAdvisory) -> dict[str, Any]:
    """Serialize only bounded, non-secret advisory state."""
    return asdict(advisory)
