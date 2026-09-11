"""V12 Cortex Voice CEO command layer.

Provides the safe bridge between speech-to-text input and the existing Cortex
CEO/runtime. Audio capture and speech synthesis are deliberately adapters at
the edge; this module owns transcript validation, deterministic intent routing,
state observation, and governed-cycle requests.

Voice is never an authorization boundary: customer-facing, financial,
irreversible, or scheduler-control actions require the existing governance
path and are not executed directly from an HTTP/browser voice request.
"""
from __future__ import annotations

from dataclasses import dataclass
import uuid
from typing import Any, Callable, Optional

from cortex_communication import record_message
from cortex_guard import CortexGuard
from cortex_v95_orchestrator import CortexV95Orchestrator

MAX_TRANSCRIPT = 4000
MAX_RESPONSE = 2000
DEFAULT_APPROVAL_PATH = "cortex_approvals.json"


@dataclass(frozen=True)
class VoiceCommand:
    """Normalized voice command with no credentials or hidden payloads."""
    transcript: str
    intent: str
    execute: bool = False


class CortexVoiceCEO:
    """Provider-neutral Voice CEO gateway for the shared Cortex runtime."""

    def __init__(
        self,
        orchestrator: CortexV95Orchestrator,
        *,
        speech_to_text: Optional[Callable[[Any], str]] = None,
        text_to_speech: Optional[Callable[[str], Any]] = None,
        communication_path: str = "cortex_communications.json",
        approval_path: str = DEFAULT_APPROVAL_PATH,
    ) -> None:
        if not isinstance(orchestrator, CortexV95Orchestrator):
            raise TypeError("orchestrator must be CortexV95Orchestrator")
        if speech_to_text is not None and not callable(speech_to_text):
            raise TypeError("speech_to_text must be callable")
        if text_to_speech is not None and not callable(text_to_speech):
            raise TypeError("text_to_speech must be callable")
        if not isinstance(communication_path, str) or not communication_path.strip():
            raise ValueError("communication_path is required")
        if not isinstance(approval_path, str) or not approval_path.strip():
            raise ValueError("approval_path is required")
        self.orchestrator = orchestrator
        self.speech_to_text = speech_to_text
        self.text_to_speech = text_to_speech
        self.communication_path = communication_path
        self.approval_path = approval_path

    @staticmethod
    def normalize_transcript(transcript: str) -> str:
        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("transcript is required")
        transcript = " ".join(transcript.strip().split())
        if len(transcript) > MAX_TRANSCRIPT:
            raise ValueError("transcript is too long")
        return transcript

    @classmethod
    def classify(cls, transcript: str) -> VoiceCommand:
        text = cls.normalize_transcript(transcript)
        lower = text.lower()
        if any(token in lower for token in ("status", "how are we doing", "business update", "what's happening", "whats happening")):
            intent = "status"
        elif any(token in lower for token in ("run one cycle", "run a cycle", "next cycle", "think about the next action", "what should cortex do next")):
            intent = "cycle"
        elif any(token in lower for token in ("pause cortex", "pause scheduler", "stop autonomous", "stop cortex")):
            intent = "pause"
        elif any(token in lower for token in ("resume cortex", "resume scheduler", "start autonomous")):
            intent = "resume"
        else:
            intent = "conversation"
        return VoiceCommand(text, intent, execute=False)

    @staticmethod
    def _status_response(observation: dict[str, Any]) -> str:
        runtime = observation.get("runtime", {}) if isinstance(observation, dict) else {}
        state = runtime.get("state", {}) if isinstance(runtime, dict) else {}
        history = runtime.get("history_count", 0) if isinstance(runtime, dict) else 0
        action = "unknown"
        if isinstance(runtime.get("registered_actions"), list) and runtime.get("registered_actions"):
            action = state.get("current_decision", "ready")
        return f"Cortex is online. The shared runtime has {history} recorded cycles. Current decision state: {action}. Verified financial truth remains authoritative."

    @staticmethod
    def _correlation_id() -> str:
        return "VOICE-" + uuid.uuid4().hex[:12].upper()

    def _record_event(self, event_type: str, summary: str, correlation: str, metadata: dict[str, Any]) -> None:
        """Record safe voice lifecycle telemetry; never persist transcript text."""
        try:
            record_message(
                "Voice CEO",
                "Cortex CEO",
                event_type,
                summary,
                correlation_id=correlation,
                path=self.communication_path,
                metadata=metadata,
            )
        except Exception:
            pass

    def _request_guard_approval(self, action: str, reason: str) -> dict[str, Any]:
        """Create a durable Guard proposal without executing the requested action."""
        try:
            approval = CortexGuard(path=self.approval_path).request(action, reason)
            return {"approval_id": approval["id"], "approval_status": approval["status"]}
        except Exception:
            # A broken approval store must never turn into implicit execution.
            return {"approval_id": None, "approval_status": "unavailable"}

    def handle_transcript(self, transcript: str) -> dict[str, Any]:
        command = self.classify(transcript)
        correlation = self._correlation_id()
        self._record_event(
            "voice_command",
            "Voice CEO command received",
            correlation,
            {"intent": command.intent, "transcript_chars": len(command.transcript)},
        )

        if command.intent == "status":
            observation = self.orchestrator.observe()
            response = self._status_response(observation)
            result = {"ok": True, "command": command.__dict__, "response": response, "executed": False, "observation": observation}
        elif command.intent == "cycle":
            cycle_result = self.orchestrator.tick(execute=False)
            response = "I ran one bounded Cortex decision cycle in observation mode. No external action was executed."
            result = {"ok": True, "command": command.__dict__, "response": response, "executed": False, "cycle": cycle_result["cycle"], "runtime": cycle_result["runtime"]}
        elif command.intent in {"pause", "resume"}:
            action = "pause" if command.intent == "pause" else "resume"
            requested_action = f"scheduler.{action}"
            approval = self._request_guard_approval(
                requested_action,
                f"Voice CEO requested scheduler {action}; execution requires explicit Cortex Guard approval.",
            )
            if approval["approval_id"]:
                response = f"Scheduler {action} was proposed to Cortex Guard. Approval {approval['approval_id']} is required before execution."
            else:
                response = f"Scheduler {action} was not executed. Cortex Guard approval storage is unavailable, so the request remains blocked."
            result = {
                "ok": True,
                "command": command.__dict__,
                "response": response,
                "executed": False,
                "requires_approval": True,
                "requested_action": requested_action,
                "approval_id": approval["approval_id"],
                "approval_status": approval["approval_status"],
                "governance": "Cortex Guard",
            }
        else:
            result = {"ok": True, "command": command.__dict__, "response": "I can report Cortex status or request a bounded decision cycle. Customer-facing, financial, and irreversible actions remain governed by Cortex Guard.", "executed": False}

        self._record_event(
            "voice_response",
            "Voice CEO response generated",
            correlation,
            {"intent": command.intent, "executed": bool(result.get("executed")), "response_chars": len(str(result["response"]))},
        )
        if self.text_to_speech:
            self.text_to_speech(str(result["response"])[:MAX_RESPONSE])
        return result

    def handle_audio(self, audio: Any) -> dict[str, Any]:
        """Convert audio at the edge, then route only the normalized transcript."""
        if self.speech_to_text is None:
            raise RuntimeError("speech_to_text adapter is not configured")
        transcript = self.speech_to_text(audio)
        return self.handle_transcript(transcript)

    def status(self) -> dict[str, Any]:
        return {
            "engine": "Cortex Voice CEO",
            "version": "12.0",
            "status": "READY",
            "speech_to_text": self.speech_to_text is not None,
            "text_to_speech": self.text_to_speech is not None,
            "shared_runtime": True,
            "decision_cycle": "bounded_and_observation_first",
            "execution_authority": "Cortex scheduler + Guard",
            "credential_policy": "voice layer receives no provider credentials",
            "truth_policy": "verified business observations only",
            "control_policy": "voice requests cannot directly mutate scheduler or external state",
        }
