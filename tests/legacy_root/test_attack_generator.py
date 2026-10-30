from ai_engine.attack_generator import DeterministicAttackGenerator
from ai_engine.contracts import AgentState


def main() -> None:
    generator = DeterministicAttackGenerator()

    state = AgentState(
        run_id="generator-test-001",
        target_id="mock-target-001",
        objective="controlled_adaptation",
        current_step=1,
        hypotheses=[
            {
                "statement": "Direct strategy was blocked.",
                "confidence": 0.9,
            }
        ],
    )

    attack = generator.generate(
        state=state,
        strategy="indirect",
    )

    print("=" * 80)
    print("AICAS — ATTACK GENERATOR TEST")
    print("=" * 80)

    print()
    print("Attack ID:", attack.attack_id)
    print("Family:", attack.attack_family)
    print("Objective:", attack.objective)
    print("Strategy:", attack.strategy)
    print("Payload:", attack.payload)
    print("Generation method:", attack.generation_method)
    print("State step:", attack.metadata["state_step"])

    assert attack.strategy == "indirect"
    assert attack.objective == state.objective
    assert attack.payload == "CONTROLLED_INDIRECT_ATTACK"
    assert attack.generation_method == "deterministic_generator"

    print()
    print("=" * 80)
    print("ATTACK GENERATOR TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()