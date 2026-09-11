"""Cortex Agent Factory: design and package customer-demand AI agents.

This module creates bounded, reviewable agent specifications. It does not
silently deploy agents, contact customers, access secrets, or execute tools.
Those actions belong to later Commerce/Guard integrations.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


AGENT_CATEGORIES = (
    "customer_support",
    "sales",
    "marketing",
    "research",
    "operations",
    "finance",
    "content",
    "coding",
    "data_analysis",
    "workflow_automation",
    "custom",
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


class CortexAgentFactory:
    """Turns a real customer requirement into a sellable agent specification."""

    @staticmethod
    def from_customer_demand(
        problem: str,
        customer: str,
        category: str,
        capabilities: List[str],
        inputs: List[str],
        outputs: List[str],
        integrations: List[str],
        price: float,
        name: str = "Custom Cortex Agent",
    ) -> AgentProductSpec:
        return AgentProductSpec(name, category, problem, customer, capabilities, inputs, outputs, integrations, price, True)

    @staticmethod
    def build_package(spec: AgentProductSpec) -> Dict[str, Any]:
        """Return a deterministic package manifest for later artifact generation."""
        if not isinstance(spec, AgentProductSpec):
            raise TypeError("spec must be AgentProductSpec")
        return {
            "product_type": "ai_agent",
            "version": "1.0",
            "manifest": spec.to_dict(),
            "artifacts": [
                "agent_definition.json",
                "system_instructions.txt",
                "setup_guide.md",
                "usage_guide.md",
                "integration_guide.md",
                "safety_and_limits.md",
            ],
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

    def status(self) -> Dict[str, Any]:
        return {
            "engine": "Cortex Agent Factory",
            "version": "1.0",
            "product_type": "customer_demand_ai_agents",
            "deployment_policy": "authorized_and_guarded",
        }
