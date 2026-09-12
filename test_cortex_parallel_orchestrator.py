from cortex_parallel_orchestrator import CortexParallelOrchestrator


def test_parallel_observation_is_bounded_and_truthful():
    seen = []

    def growth(state):
        seen.append("growth")
        return {"action": "acquire_next_opportunity"}

    def finance(state):
        seen.append("finance")
        return {"verified_revenue": state.get("verified_revenue", 0)}

    loop = CortexParallelOrchestrator({"growth": growth, "finance": finance})
    result = loop.cycle({"verified_revenue": 12})

    assert seen == ["growth", "finance"]
    assert result["decision"]["transition_budget"] == 1
    assert result["decision"]["action"] == "acquire_next_opportunity"
    assert result["execution"] == "decision_only"
    assert result["observations"]["truth_policy"] == "verified_observations_only"


def test_no_proposal_means_no_transition():
    loop = CortexParallelOrchestrator({"finance": lambda state: {"verified_revenue": 0}})
    result = loop.cycle({})
    assert result["decision"]["action"] is None
    assert result["decision"]["transition_budget"] == 0
