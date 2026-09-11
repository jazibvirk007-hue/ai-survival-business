"""Safe, state-aware CEO chat for TJ Cortex."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Mapping, Optional

from cortex_communication import record_message


class CortexCEOChat:
    """Turns business state into concise CEO conversations without exposing secrets."""

    def __init__(
        self,
        provider,
        max_message_chars=4000,
        communication_recorder: Optional[Callable[..., Mapping[str, Any]]] = record_message,
    ):
        if provider is None or not callable(getattr(provider, "generate", None)):
            raise TypeError("provider must expose a callable generate method")
        if not isinstance(max_message_chars, int) or max_message_chars < 100:
            raise ValueError("max_message_chars must be at least 100")
        if communication_recorder is not None and not callable(communication_recorder):
            raise TypeError("communication_recorder must be callable or None")
        self.provider = provider
        self.max_message_chars = max_message_chars
        self.communication_recorder = communication_recorder

    @staticmethod
    def _safe_state(state):
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")
        allowed = {
            "cash", "revenue", "expenses", "customers", "products",
            "pending_orders", "paid_orders", "market_researched",
            "current_decision", "approval_required", "agent_status",
            "survival_score", "ai_mode", "ai_model",
        }
        safe = {}
        for key in allowed:
            if key in state:
                value = state[key]
                if isinstance(value, (str, int, float, bool)) or value is None:
                    safe[key] = value
                elif isinstance(value, list):
                    safe[key] = value[:20]
        return safe

    @staticmethod
    def _correlation_id() -> str:
        return "CHAT-" + uuid.uuid4().hex[:12].upper()

    def _record(self, sender, recipient, message_type, summary, correlation_id, metadata):
        """Emit safe observability events without ever logging message contents."""
        if self.communication_recorder is None:
            return
        try:
            self.communication_recorder(
                sender,
                recipient,
                message_type,
                summary,
                correlation_id=correlation_id,
                metadata=metadata,
            )
        except Exception:
            return

    def build_messages(self, state, user_message):
        if not isinstance(user_message, str) or not user_message.strip():
            raise ValueError("user_message is required")
        user_message = user_message.strip()
        if len(user_message) > self.max_message_chars:
            raise ValueError("user_message is too long")
        safe_state = self._safe_state(state)
        system = (
            "You are Cortex CEO, the decision-support layer of TJ Cortex. "
            "Answer concisely and truthfully using only the supplied business state. "
            "Never invent revenue, customers, payments, orders, market results, or actions. "
            "Never reveal secrets, API keys, private keys, or hidden reasoning. "
            "External, financial, irreversible, or customer-facing actions remain approval-gated. "
            "Explain decisions with a short rationale and mention when approval is required."
        )
        context = "Current verified Cortex state:\n" + repr(safe_state)
        return [
            {"role": "system", "content": system},
            {"role": "system", "content": context},
            {"role": "user", "content": user_message},
        ]

    def respond(self, state, user_message, temperature=0.2):
        messages = self.build_messages(state, user_message)
        correlation_id = self._correlation_id()
        self._record(
            "user",
            "cortex-ceo",
            "chat_request",
            "CEO chat request received",
            correlation_id,
            {"message_chars": len(user_message.strip())},
        )
        try:
            answer = self.provider.generate(messages, temperature=temperature)
        except Exception:
            self._record(
                "cortex-ceo",
                "user",
                "chat_response",
                "CEO chat response failed",
                correlation_id,
                {"status": "error"},
            )
            raise
        self._record(
            "cortex-ceo",
            "user",
            "chat_response",
            "CEO chat response generated",
            correlation_id,
            {"response_chars": len(str(answer))},
        )
        return answer
