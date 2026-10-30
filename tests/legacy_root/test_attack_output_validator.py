from ai_engine.attack_generator.validator import (
    AttackOutputValidator,
)


def main() -> None:
    validator = AttackOutputValidator()

    print("=" * 80)
    print("AICAS — ATTACK OUTPUT VALIDATOR TEST")
    print("=" * 80)

    # --------------------------------------------------
    # VALID
    # --------------------------------------------------

    valid = validator.validate(
        """
        {
            "attack_family": "controlled_test",
            "objective": "controlled_adaptation",
            "strategy": "indirect",
            "payload": "CONTROLLED_VALID_TEST",
            "target_surface": "input"
        }
        """,
        expected_strategy="indirect",
    )

    print()
    print("VALID CASE")
    print("Valid:", valid.valid)
    print("Errors:", valid.errors)

    assert valid.valid is True
    assert valid.errors == []

    # --------------------------------------------------
    # MALFORMED JSON
    # --------------------------------------------------

    malformed = validator.validate(
        "{this is not valid JSON}",
        expected_strategy="indirect",
    )

    print()
    print("MALFORMED JSON")
    print("Valid:", malformed.valid)
    print("Errors:", malformed.errors)

    assert malformed.valid is False

    # --------------------------------------------------
    # MISSING FIELD
    # --------------------------------------------------

    missing = validator.validate(
        """
        {
            "attack_family": "controlled_test",
            "objective": "controlled_adaptation",
            "strategy": "indirect",
            "payload": "CONTROLLED_TEST"
        }
        """,
        expected_strategy="indirect",
    )

    print()
    print("MISSING FIELD")
    print("Valid:", missing.valid)
    print("Errors:", missing.errors)

    assert missing.valid is False
    assert any(
        "target_surface" in error
        for error in missing.errors
    )

    # --------------------------------------------------
    # WRONG TYPE
    # --------------------------------------------------

    wrong_type = validator.validate(
        """
        {
            "attack_family": "controlled_test",
            "objective": "controlled_adaptation",
            "strategy": 123,
            "payload": "CONTROLLED_TEST",
            "target_surface": "input"
        }
        """,
        expected_strategy="indirect",
    )

    print()
    print("WRONG TYPE")
    print("Valid:", wrong_type.valid)
    print("Errors:", wrong_type.errors)

    assert wrong_type.valid is False

    # --------------------------------------------------
    # STRATEGY MISMATCH
    # --------------------------------------------------

    mismatch = validator.validate(
        """
        {
            "attack_family": "controlled_test",
            "objective": "controlled_adaptation",
            "strategy": "direct",
            "payload": "CONTROLLED_TEST",
            "target_surface": "input"
        }
        """,
        expected_strategy="indirect",
    )

    print()
    print("STRATEGY MISMATCH")
    print("Valid:", mismatch.valid)
    print("Errors:", mismatch.errors)

    assert mismatch.valid is False
    assert any(
        "strategy" in error.lower()
        for error in mismatch.errors
    )

    # --------------------------------------------------
    # UNSUPPORTED TARGET SURFACE
    # --------------------------------------------------

    bad_surface = validator.validate(
        """
        {
            "attack_family": "controlled_test",
            "objective": "controlled_adaptation",
            "strategy": "indirect",
            "payload": "CONTROLLED_TEST",
            "target_surface": "unknown_surface"
        }
        """,
        expected_strategy="indirect",
    )

    print()
    print("UNSUPPORTED TARGET SURFACE")
    print("Valid:", bad_surface.valid)
    print("Errors:", bad_surface.errors)

    assert bad_surface.valid is False

    print()
    print("=" * 80)
    print("ATTACK OUTPUT VALIDATOR TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()