"""Cortex Agent Factory: design, package, and staff bounded AI agents.

The factory can design sellable agent products and staff missing specialists.
Persisted workforce records are metadata only: a restart never restores a
callable handler or execution authority. Hiring never creates payment
authority, Guard authority, customer identities, or arbitrary tool access.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import json
import os
import re

from cortex_specialist_registry import CortexSpecialistRegistry

AGENT_CATEGORIES = (
    "customer_support", "sales", "marketing", "research", "operations",
    "finance", "content", "coding", "data_analysis", "workflow_automation", "custom",
)

@dataclass(frozen=True)
class AgentProductSpec:
    name: str
    category: str
    customer_problem: str
    target_customer: str
    capabilities: List[str]
    inputs: List[str]
    outputs: List[str]
    integrations: List[str]
    price: float
    requires_approval: bool = True

    def __post_init__(self) -> None:
        for field in ("name", "customer_problem", "target_customer"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be non-empty")
        if self.category not in AGENT_CATEGORIES:
            raise ValueError("unsupported agent category")
        for field in ("capabilities", "inputs", "outputs", "integrations"):
            value = getattr(self, field)
            if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
                raise ValueError(f"{field} must be a non-empty list of strings")
        if not isinstance(self.price, (int, float)) or self.price < 0:
            raise ValueError("price must be non-negative")
        if not isinstance(self.requires_approval, bool):
            raise ValueError("requires_approval must be boolean")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class HireRequest:
    """A bounded hiring proposal; it is not itself permission to execute code."""
    action: str
    workload: int
    reason: str
    proposed_name: str
    purpose: str
    created_at: str
    status: str = "proposed"

@dataclass(frozen=True)
class HiredAgent:
    name: str
    action: str
    purpose: str
    created_at: str
    reason: str
    status: str = "active"

class CortexAgentFactory:
    """Turns demand into agent products and staffs missing bounded specialists."""
    VERSION = "20.4"
    MAX_HIRED_AGENTS = 32
    MAX_HIRE_REQUESTS = 64
    MAX_TEXT = 240

    def __init__(self, registry: Optional[CortexSpecialistRegistry] = None, path: Optional[str] = None) -> None:
        self.registry = registry if registry is not None else CortexSpecialistRegistry()
        self.path = path
        self._hired: Dict[str, HiredAgent] = {}
        self._hire_requests: List[HireRequest] = []
        self._load_state()

    @staticmethod
    def from_customer_demand(problem: str, customer: str, category: str, capabilities: List[str], inputs: List[str], outputs: List[str], integrations: List[str], price: float, name: str = "Custom Cortex Agent") -> AgentProductSpec:
        return AgentProductSpec(name, category, problem, customer, capabilities, inputs, outputs, integrations, price, True)

    @staticmethod
    def build_package(spec: AgentProductSpec) -> Dict[str, Any]:
        if not isinstance(spec, AgentProductSpec):
            raise TypeError("spec must be AgentProductSpec")
        return {
            "product_type": "ai_agent", "version": "1.0", "manifest": spec.to_dict(),
            "artifacts": ["agent_definition.json", "system_instructions.txt", "setup_guide.md", "usage_guide.md", "integration_guide.md", "safety_and_limits.md"],
            "deployment": "customer-controlled_or_authorized_platform",
            "external_actions": "approval_gated",
        }

    @staticmethod
    def quality_gate(spec: AgentProductSpec) -> Dict[str, Any]:
        checks = {
            "customer_problem_defined": bool(spec.customer_problem.strip()),
            "target_customer_defined": bool(spec.target_customer.strip()),
            "capabilities_defined": len(spec.capabilities) > 0,
            "inputs_defined": len(spec.inputs) > 0,
            "outputs_defined": len(spec.outputs) > 0,
            "integrations_declared": len(spec.integrations) > 0,
            "price_valid": spec.price >= 0,
            "external_actions_guarded": spec.requires_approval,
        }
        return {"passed": all(checks.values()), "checks": checks}

    def should_hire(self, action: str, workload: int) -> bool:
        """Use observed workload to justify one unstaffed action."""
        return (
            self.registry.get(action) is None
            and action not in self._hired
            and action in self.registry.status()["allowed_actions"]
            and isinstance(workload, int)
            and workload > 0
        )

    def propose_hire(self, *, action: str, workload: int, reason: str, proposed_name: str, purpose: str) -> HireRequest:
        """Create an auditable, non-executing hiring proposal from observed workload."""
        if not self.should_hire(action, workload):
            raise ValueError("agent hiring is not justified or action is already staffed")
        reason = self._bounded_text(reason, "hire reason")
        proposed_name = self._safe_name(proposed_name)
        purpose = self._bounded_text(purpose, "agent purpose")
        if len(self._hire_requests) >= self.MAX_HIRE_REQUESTS:
            self._hire_requests = self._hire_requests[-(self.MAX_HIRE_REQUESTS - 1):]
        request = HireRequest(action, workload, reason, proposed_name, purpose, datetime.now(timezone.utc).isoformat())
        self._hire_requests.append(request)
        self._save_state()
        return request

    @staticmethod
    def _bounded_text(value: str, label: str) -> str:
        text = str(value or "").strip()
        if not text or len(text) > CortexAgentFactory.MAX_TEXT:
            raise ValueError(f"{label} must be non-empty and <= {CortexAgentFactory.MAX_TEXT} characters")
        return text

    @staticmethod
    def _safe_name(value: str) -> str:
        name = CortexAgentFactory._bounded_text(value, "agent name")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]*", name):
            raise ValueError("agent name contains unsupported characters")
        return name

    @staticmethod
    def _restore_agent(item: Dict[str, Any], allowed_actions: set[str]) -> Optional[HiredAgent]:
        required = ("name", "action", "purpose", "created_at", "reason", "status")
        if any(key not in item for key in required):
            return None
        action = item["action"]
        if not isinstance(action, str) or action not in allowed_actions:
            return None
        if item["status"] != "active":
            return None
        try:
            name = CortexAgentFactory._safe_name(item["name"])
            purpose = CortexAgentFactory._bounded_text(item["purpose"], "agent purpose")
            reason = CortexAgentFactory._bounded_text(item["reason"], "hire reason")
            created_at = CortexAgentFactory._bounded_text(item["created_at"], "created_at")
        except ValueError:
            return None
        # Persisted records are explicitly unbound until a trusted caller
        # supplies the concrete handler again. They never restore execution.
        return HiredAgent(name, action, purpose, created_at, reason, "persisted_unbound")

    def hire(self, *, name: str, action: str, purpose: str, handler: Callable[[Dict[str, Any]], Any], reason: str) -> HiredAgent:
        """Hire/register one specialist after a concrete observed need is supplied."""
        name, purpose, reason = self._safe_name(name), self._bounded_text(purpose, "agent purpose"), self._bounded_text(reason, "hire reason")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if len(self._hired) >= self.MAX_HIRED_AGENTS:
            raise RuntimeError("agent hiring capacity reached")
        if action not in self.registry.status()["allowed_actions"]:
            raise ValueError(f"unsupported specialist action: {action}")
        if self.registry.get(action) is not None or action in self._hired:
            raise ValueError(f"specialist action already staffed: {action}")
        self.registry.register(action, handler)
        hired = HiredAgent(name, action, purpose, datetime.now(timezone.utc).isoformat(), reason)
        self._hired[action] = hired
        self._save_state()
        return hired

    def bind_handler(self, *, action: str, handler: Callable[[Dict[str, Any]], Any]) -> HiredAgent:
        """Explicitly re-bind execution for persisted workforce metadata."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        hired = self._hired.get(action)
        if hired is None:
            raise ValueError("no persisted specialist exists for action")
        if self.registry.get(action) is not None:
            raise ValueError(f"specialist action already staffed: {action}")
        if action not in self.registry.status()["allowed_actions"]:
            raise ValueError(f"unsupported specialist action: {action}")
        self.registry.register(action, handler)
        rebound = HiredAgent(hired.name, hired.action, hired.purpose, hired.created_at, hired.reason, "active")
        self._hired[action] = rebound
        self._save_state()
        return rebound

    def _load_state(self) -> None:
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                return
            allowed = set(self.registry.status().get("allowed_actions", []))
            hired = payload.get("hired_agents", [])
            requests = payload.get("hire_requests", [])
            if isinstance(hired, list):
                for item in hired[-self.MAX_HIRED_AGENTS:]:
                    if isinstance(item, dict):
                        restored = self._restore_agent(item, allowed)
                        if restored is not None and restored.action not in self._hired:
                            self._hired[restored.action] = restored
            if isinstance(requests, list):
                for item in requests[-self.MAX_HIRE_REQUESTS:]:
                    if not isinstance(item, dict):
                        continue
                    required = ("action", "workload", "reason", "proposed_name", "purpose", "created_at", "status")
                    if any(key not in item for key in required) or item["action"] not in allowed or item["status"] != "proposed":
                        continue
                    try:
                        workload = int(item["workload"])
                        if workload <= 0 or workload > 1000000:
                            continue
                        self._hire_requests.append(HireRequest(
                            item["action"], workload,
                            self._bounded_text(item["reason"], "hire reason"),
                            self._safe_name(item["proposed_name"]),
                            self._bounded_text(item["purpose"], "agent purpose"),
                            self._bounded_text(item["created_at"], "created_at"),
                            "proposed",
                        ))
                    except (TypeError, ValueError):
                        continue
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self._hired, self._hire_requests = {}, []

    def _save_state(self) -> None:
        if not self.path:
            return
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        payload = {
            "version": self.VERSION,
            "hired_agents": self.roster(),
            "hire_requests": self.hire_requests()[-self.MAX_HIRE_REQUESTS:],
        }
        temp = self.path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)

    def roster(self) -> List[Dict[str, Any]]:
        return [asdict(agent) for agent in self._hired.values()]

    def hire_requests(self) -> List[Dict[str, Any]]:
        return [asdict(request) for request in self._hire_requests]

    def status(self) -> Dict[str, Any]:
        active = sum(1 for agent in self._hired.values() if agent.status == "active" and self.registry.get(agent.action) is not None)
        return {
            "engine": "Cortex Agent Factory", "version": self.VERSION,
            "product_type": "customer_demand_ai_agents", "deployment_policy": "authorized_and_guarded",
            "hiring_capacity": self.MAX_HIRED_AGENTS, "hired_agents": len(self._hired),
            "active_handlers": active, "unbound_persisted_agents": len(self._hired) - active,
            "roster": self.roster(), "hire_requests": len(self._hire_requests),
            "pending_hire_requests": self.hire_requests()[-10:], "persistence": bool(self.path),
            "authority_boundary": "no_payment_or_guard_authority; persisted workforce metadata never restores execution",
        }
