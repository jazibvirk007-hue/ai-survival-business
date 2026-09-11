"""Cortex Communications: governed customer-channel abstraction.

This layer prepares the business for Gmail/WhatsApp and other channels without
requiring credentials in the AI context. It is intentionally provider-neutral:
actual OAuth/API adapters are added later and all outbound communication is
policy/approval gated.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


CHANNELS = ("gmail", "whatsapp")
MODES = ("disabled", "draft_only", "approved_send", "autonomous_guarded")


@dataclass(frozen=True)
class CommunicationPolicy:
    channel: str
    mode: str = "disabled"
    require_approval: bool = True
    allow_inbound: bool = True
    allow_outbound: bool = False
    daily_send_limit: int = 0

    def __post_init__(self) -> None:
        if self.channel not in CHANNELS:
            raise ValueError("unsupported communication channel")
        if self.mode not in MODES:
            raise ValueError("unsupported communication mode")
        if not isinstance(self.require_approval, bool):
            raise ValueError("require_approval must be boolean")
        if not isinstance(self.allow_inbound, bool) or not isinstance(self.allow_outbound, bool):
            raise ValueError("communication flags must be boolean")
        if not isinstance(self.daily_send_limit, int) or self.daily_send_limit < 0 or self.daily_send_limit > 1000:
            raise ValueError("daily_send_limit must be between 0 and 1000")
        if self.mode == "disabled" and self.allow_outbound:
            raise ValueError("disabled channel cannot allow outbound messages")
        if self.mode == "approved_send" and not self.require_approval:
            raise ValueError("approved_send requires approval")
        if self.mode == "autonomous_guarded" and (self.require_approval or not self.allow_outbound):
            raise ValueError("autonomous_guarded requires guarded outbound policy configuration")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MessageDraft:
    channel: str
    recipient_ref: str
    body: str
    reason: str
    requires_approval: bool = True

    def __post_init__(self) -> None:
        if self.channel not in CHANNELS:
            raise ValueError("unsupported communication channel")
        if not isinstance(self.recipient_ref, str) or not self.recipient_ref.strip():
            raise ValueError("recipient_ref must be non-empty")
        if not isinstance(self.body, str) or not self.body.strip() or len(self.body) > 10000:
            raise ValueError("body must be non-empty and at most 10000 characters")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 2000:
            raise ValueError("reason must be non-empty and at most 2000 characters")
        if not isinstance(self.requires_approval, bool):
            raise ValueError("requires_approval must be boolean")


class CortexCommunications:
    """Manage channel configuration and safe message preparation only."""

    def __init__(self, policies: List[CommunicationPolicy] | None = None):
        self.policies: Dict[str, CommunicationPolicy] = {}
        for policy in policies or []:
            self.set_policy(policy)

    def set_policy(self, policy: CommunicationPolicy) -> None:
        if not isinstance(policy, CommunicationPolicy):
            raise TypeError("policy must be CommunicationPolicy")
        self.policies[policy.channel] = policy

    def policy(self, channel: str) -> CommunicationPolicy:
        if channel not in CHANNELS:
            raise ValueError("unsupported communication channel")
        return self.policies.get(channel, CommunicationPolicy(channel=channel))

    def prepare_draft(self, channel: str, recipient_ref: str, body: str, reason: str) -> MessageDraft:
        policy = self.policy(channel)
        if not policy.allow_outbound:
            raise PermissionError("outbound communication is disabled for this channel")
        return MessageDraft(channel, recipient_ref, body, reason, policy.require_approval)

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Communications",
            "version": "1.0",
            "supported_channels": list(CHANNELS),
            "policies": [self.policy(channel).to_dict() for channel in CHANNELS],
            "credentials_exposed_to_ai": False,
            "outbound_execution": "provider_adapter_and_guard_required",
            "bulk_spam_policy": "prohibited",
        }
