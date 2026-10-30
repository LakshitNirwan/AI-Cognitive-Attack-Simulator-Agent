from ai_engine.attack_generator import DeterministicAttackGenerator
from ai_engine.attack_orchestrator import AdaptiveRunner
from ai_engine.contracts import AgentState
from ai_engine.memory.state_manager import StateManager
from ai_engine.recommendation_engine import DeterministicPlanner
from ai_engine.response_evaluator import OutcomeEvaluator
from ai_engine.targets import MockTargetAdapter


def main() -> None:
    print("=" * 80)
    print("AICAS — CLOSED-LOOP TEST")
    print("=" * 80)

    planner = DeterministicPlanner()
    generator = DeterministicAttackGenerator()
    target = MockTargetAdapter()
    evaluator = OutcomeEvaluator()
    state_manager = StateManager()

    state = AgentState(
        run_id="closed-loop-test-001",
        target_id=target.get_target_info().target_id,
        objective="controlled_adaptation",
        unexplored_strategies=[
            "direct",
            "indirect",
        ],
        budget={
            "max_steps": 3,
        },
    )

    runner = AdaptiveRunner(
        planner=planner,
        generator=generator,
        target=target,
        evaluator=evaluator,
        state_manager=state_manager,
    )

    result = runner.run(
        state=state,
        max_steps=3,
    )

    print()
    print("RUN ID:", result.run_id)
    print("ATTACKS GENERATED:", result.attacks_generated)

    print()
    print("OUTCOMES")

    for index, outcome in enumerate(result.outcomes, start=1):
        print(
            f"  {index}. "
            f"classification={outcome.classification}, "
            f"success={outcome.success}, "
            f"severity={outcome.severity}"
        )

    print()
    print("FINAL STATE STEP:", result.final_state.current_step)
    print("STRATEGY STATS:", result.final_state.strategy_stats)

    # Expected first step:
    # direct → refusal
    #
    # Expected second step:
    # indirect → success
    assert result.attacks_generated == 2
    assert len(result.outcomes) == 2
    assert result.outcomes[0].classification == "refusal"
    assert result.outcomes[1].success is True

    print()
    print("=" * 80)
    print("CLOSED-LOOP TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()