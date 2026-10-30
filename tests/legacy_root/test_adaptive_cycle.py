from ai_engine.contracts import AgentState, Attack
from ai_engine.memory.state_manager import StateManager
from ai_engine.recommendation_engine.strategy_selector import (
    StrategySelector,
)
from ai_engine.response_evaluator import OutcomeEvaluator
from ai_engine.targets import MockTargetAdapter


def execute_cycle(
    target,
    evaluator,
    state_manager,
    state,
    strategy,
):
    attack = Attack(
        attack_family="adaptive_test",
        objective="controlled_adaptation",
        strategy=strategy,
        payload=f"strategy={strategy}",
        target_surface="input",
        generation_method="deterministic_test",
    )

    observation = target.execute(attack)
    outcome = evaluator.evaluate(observation)

    state_manager.update(
        state,
        attack,
        outcome,
    )

    return attack, observation, outcome


def main() -> None:
    print("=" * 80)
    print("AICAS — FIRST ADAPTIVE CYCLE")
    print("=" * 80)

    target = MockTargetAdapter()
    evaluator = OutcomeEvaluator()
    state_manager = StateManager()
    selector = StrategySelector()

    state = AgentState(
        run_id="adaptive-test-001",
        target_id=target.get_target_info().target_id,
        objective="controlled_adaptation",
        unexplored_strategies=[
            "direct",
            "indirect",
        ],
    )

    # --------------------------------------------------------
    # ATTACK 1
    # --------------------------------------------------------

    strategy_1 = selector.select(state)

    attack_1, observation_1, outcome_1 = execute_cycle(
        target,
        evaluator,
        state_manager,
        state,
        strategy_1,
    )

    print()
    print("ATTACK 1")
    print("Strategy:", strategy_1)
    print("Response:", observation_1.response)
    print("Outcome:", outcome_1.classification)
    print("Success:", outcome_1.success)

    # --------------------------------------------------------
    # ATTACK 2
    # --------------------------------------------------------

    strategy_2 = selector.select(state)

    attack_2, observation_2, outcome_2 = execute_cycle(
        target,
        evaluator,
        state_manager,
        state,
        strategy_2,
    )

    print()
    print("ATTACK 2")
    print("Strategy:", strategy_2)
    print("Response:", observation_2.response)
    print("Outcome:", outcome_2.classification)
    print("Success:", outcome_2.success)

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    assert strategy_1 == "direct"
    assert outcome_1.classification == "refusal"

    assert strategy_2 == "indirect"
    assert outcome_2.success is True

    print()
    print("STATE")
    print("Current step:", state.current_step)
    print("Strategy stats:", state.strategy_stats)

    print()
    print("=" * 80)
    print("FIRST ADAPTIVE CYCLE: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()