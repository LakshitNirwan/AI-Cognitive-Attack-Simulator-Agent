from ai_engine.contracts import Attack
from ai_engine.response_evaluator import OutcomeEvaluator
from ai_engine.targets import MockTargetAdapter


def run_case(payload: str):
    target = MockTargetAdapter()
    evaluator = OutcomeEvaluator()

    attack = Attack(
        attack_family="test",
        objective="verify_evaluation",
        strategy="controlled_trigger",
        payload=payload,
        target_surface="input",
        generation_method="manual_test",
    )

    observation = target.execute(attack)
    outcome = evaluator.evaluate(observation)

    return observation, outcome


def main() -> None:
    print("=" * 80)
    print("AICAS — OUTCOME EVALUATOR TEST")
    print("=" * 80)

    cases = [
        (
            "trigger_success",
            "success",
            True,
            3,
        ),
        (
            "trigger_partial",
            "partial_compliance",
            False,
            1,
        ),
        (
            "trigger_refusal",
            "refusal",
            False,
            0,
        ),
    ]

    for payload, expected_class, expected_success, expected_severity in cases:
        observation, outcome = run_case(payload)

        print()
        print("Payload:", payload)
        print("Response:", observation.response)
        print("Classification:", outcome.classification)
        print("Success:", outcome.success)
        print("Severity:", outcome.severity)
        print("Confidence:", outcome.confidence)

        assert outcome.observation_id == observation.observation_id
        assert outcome.classification == expected_class
        assert outcome.success == expected_success
        assert outcome.severity == expected_severity
        assert outcome.confidence == 1.0

    print()
    print("=" * 80)
    print("OUTCOME EVALUATOR TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()