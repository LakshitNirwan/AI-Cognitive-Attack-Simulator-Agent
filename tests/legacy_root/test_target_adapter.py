from ai_engine.contracts import Attack
from ai_engine.targets import MockTargetAdapter


def main() -> None:
    target = MockTargetAdapter()

    info = target.get_target_info()

    print("=" * 80)
    print("AICAS — TARGET ADAPTER TEST")
    print("=" * 80)

    print("Target ID:", info.target_id)
    print("Provider:", info.provider)
    print("Model:", info.model)

    attack = Attack(
        attack_family="test",
        objective="verify_target_execution",
        strategy="controlled_trigger",
        payload="trigger_success",
        target_surface="input",
        generation_method="manual_test",
    )

    observation = target.execute(attack)

    print()
    print("Attack ID:", attack.attack_id)
    print("Observation ID:", observation.observation_id)
    print("Response:", observation.response)
    print("Termination:", observation.termination_reason)
    print("Attack IDs match:", observation.attack_id == attack.attack_id)

    assert observation.attack_id == attack.attack_id
    assert observation.response.startswith("MOCK_TARGET_SUCCESS")
    assert observation.termination_reason == "completed"

    print()
    print("TARGET ADAPTER TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()