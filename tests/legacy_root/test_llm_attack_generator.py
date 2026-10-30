from ai_engine.attack_generator.llm_generator import LLMAttackGenerator
from ai_engine.contracts import AgentState
from ai_engine.llm import MockLLMClient


def main() -> None:
    generator = LLMAttackGenerator(
        client=MockLLMClient()
    )

    state = AgentState(
        run_id="llm-generator-test-001",
        target_id="mock-target-001",
        objective="controlled_adaptation",
        current_step=2,
        target_profile={
            "interface_type": "chat",
            "supports_tools": False,
        },
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
    print("AICAS — LLM ATTACK GENERATOR TEST")
    print("=" * 80)

    print("Attack ID:", attack.attack_id)
    print("Family:", attack.attack_family)
    print("Objective:", attack.objective)
    print("Strategy:", attack.strategy)
    print("Payload:", attack.payload)
    print("Generation method:", attack.generation_method)
    print("Generation model:", attack.generation_model)

    assert attack.generation_method == "llm"
    assert attack.generation_model == "mock-llm"
    assert attack.strategy == "indirect"
    assert attack.payload == "CONTROLLED_LLM_GENERATED_TEST"

    print()
    print("LLM ATTACK GENERATOR TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()