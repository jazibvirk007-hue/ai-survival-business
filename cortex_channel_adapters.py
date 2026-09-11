"""Provider-neutral customer communication channel adapters for Cortex.

The adapters validate outbound envelopes and delegate actual transport to an
injected connector. They never contain credentials, discover private contacts,
or bypass Cortex Guard. A host may later inject an official Gmail or WhatsApp
connector after the user authorizes that integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

MAX_TEXT = 10000
SUPPORTED_CHANNELS = ("gmail", "whatsapp")


@dataclass(frozen=True)
class OutboundEnvelope:
    channel: str
    recipient: str
    subject: str
    body: str
    approval_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.channel not in SUPPORTED_CHANNELS:
            raise ValueError("unsupported channel")
        for field in ("recipient", "body"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} is required")
            if len(value) > MAX_TEXT:
                raise ValueError(f"{field} is too long")
        if not isinstance(self.subject, str):
            raise ValueError("subject must be a string")
        if len(self.subject) > 500:
            raise ValueError("subject is too long")
        if self.approval_id is not None and (not isinstance(self.approval_id, str) or not self.approval_id.strip()):
            raise ValueError("approval_id must be non-empty when supplied")

    def safe_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "body_chars": len(self.body),
            "approval_id": self.approval_id,
        }


class CortexChannelAdapter:
    """Common governed boundary for customer-facing channel transports."""

    channel = ""

    def __init__(self, sender: Optional[Callable[[OutboundEnvelope], Any]] = None) -> None:
        if sender is not None and not callable(sender):
            raise TypeError("sender must be callable")
        self.sender = sender

    def prepare(self, recipient: str, body: str, *, subject: str = "", approval_id: Optional[str] = None) -> Dict[str, Any]:
        envelope = OutboundEnvelope(self.channel, recipient, subject, body, approval_id)
        return {
            "ok": True,
            "prepared": True,
            "requires_guard": True,
            "envelope": envelope.safe_dict(),
        }

    def send(self, envelope: OutboundEnvelope) -> Dict[str, Any]:
        if not isinstance(envelope, OutboundEnvelope) or envelope.channel != self.channel:
            raise ValueError("envelope does not match adapter")
        if not envelope.approval_id:
            return {"ok": False, "executed": False, "error": "approval_required"}
        if self.sender is None:
            return {"ok": False, "executed": False, "error": "transport_not_configured"}
        result = self.sender(envelope)
        return {"ok": True, "executed": True, "result": result, "envelope": envelope.safe_dict()}

    def status(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "transport": "configured" if self.sender is not None else "not_configured",
            "credentials": "host_managed",
            "execution": "approval_gated",
            "policy": "authorized_connector_required",
        }


class GmailChannelAdapter(CortexChannelAdapter):
    channel = "gmail"


class WhatsAppChannelAdapter(CortexChannelAdapter):
    channel = "whatsapp"


def channel_status() -> Dict[str, Any]:
    return {
        "engine": "Cortex Communications Channels",
        "version": "1.0",
        "channels": {
            "gmail": GmailChannelAdapter().status(),
            "whatsapp": WhatsAppChannelAdapter().status(),
        },
        "policy": "Cortex Guard approval plus authorized provider connector",
        "credential_policy": "credentials remain outside Cortex channel envelopes",
    }
