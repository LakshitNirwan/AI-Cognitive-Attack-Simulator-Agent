from ai_engine.contracts import AgentState
from ai_engine.recommendation_engine import DeterministicPlanner


def main() -> None:
    planner = DeterministicPlanner()

    state = AgentState(
        run_id="planner-test-001",
        target_id="mock-target-001",
        objective="controlled_adaptation",
        unexplored_strategies=[
            "direct",
            "indirect",
        ],
    )

    decision_1 = planner.select_strategy(state)

    print("=" * 80)
    print("AICAS — PLANNER TEST")
    print("=" * 80)

    print()
    print("Decision 1")
    print("Strategy:", decision_1.strategy)
    print("Rationale:", decision_1.rationale)
    print("Confidence:", decision_1.confidence)

    assert decision_1.strategy == "direct"

    # Simulate a failed direct attempt.
    state.current_step = 1
    state.strategy_stats["direct"] = {
        "attempts": 1,
        "successes": 0,
        "partial_successes": 0,
        "failures": 1,
    }

    decision_2 = planner.select_strategy(state)

    print()
    print("Decision 2")
    print("Strategy:", decision_2.strategy)
    print("Rationale:", decision_2.rationale)
    print("Confidence:", decision_2.confidence)

    assert decision_2.strategy == "indirect"

    print()
    print("=" * 80)
    print("PLANNER TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()