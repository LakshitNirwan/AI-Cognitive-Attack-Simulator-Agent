from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


REQUIRED_FIELDS = {
    "attack_family",
    "objective",
    "strategy",
    "payload",
    "target_surface",
}

ALLOWED_TARGET_SURFACES = {
    "input",
    "system_prompt",
    "user_message",
    "tool_input",
    "context",
}

MAX_STRING_LENGTHS = {
    "attack_family": 200,
    "objective": 2000,
    "strategy": 200,
    "payload": 10000,
    "target_surface": 100,
}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    data: dict[str, Any] | None
    errors: list[str]


class AttackOutputValidator:
    """
    Validates untrusted model output before it becomes an Attack.

    This validator performs:
      1. JSON parsing
      2. required-field validation
      3. type validation
      4. length validation
      5. controlled-value validation
      6. strategy consistency validation
    """

    def validate(
        self,
        raw_text: str,
        *,
        expected_strategy: str | None = None,
    ) -> ValidationResult:

        errors: list[str] = []

        # --------------------------------------------------
        # JSON parsing
        # --------------------------------------------------

        try:
            data = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError) as exc:
            return ValidationResult(
                valid=False,
                data=None,
                errors=[
                    f"Invalid JSON: {exc}",
                ],
            )

        # --------------------------------------------------
        # Top-level object
        # --------------------------------------------------

        if not isinstance(data, dict):
            return ValidationResult(
                valid=False,
                data=None,
                errors=[
                    "Model output must be a JSON object.",
                ],
            )

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------

        missing = REQUIRED_FIELDS - data.keys()

        for field in sorted(missing):
            errors.append(
                f"Missing required field: {field}"
            )

        if errors:
            return ValidationResult(
                valid=False,
                data=None,
                errors=errors,
            )

        # --------------------------------------------------
        # Reject unexpected fields for now
        # --------------------------------------------------

        unexpected = set(data.keys()) - REQUIRED_FIELDS

        for field in sorted(unexpected):
            errors.append(
                f"Unexpected field: {field}"
            )

        # --------------------------------------------------
        # Type validation
        # --------------------------------------------------

        for field in REQUIRED_FIELDS:
            if not isinstance(data[field], str):
                errors.append(
                    f"Field '{field}' must be a string."
                )

        # --------------------------------------------------
        # Empty-string validation
        # --------------------------------------------------

        for field in REQUIRED_FIELDS:
            value = data[field]

            if isinstance(value, str) and not value.strip():
                errors.append(
                    f"Field '{field}' cannot be empty."
                )

        # --------------------------------------------------
        # Length validation
        # --------------------------------------------------

        for field, maximum in MAX_STRING_LENGTHS.items():
            value = data.get(field)

            if isinstance(value, str) and len(value) > maximum:
                errors.append(
                    f"Field '{field}' exceeds maximum length "
                    f"of {maximum}."
                )

        # --------------------------------------------------
        # Target surface validation
        # --------------------------------------------------

        target_surface = data.get("target_surface")

        if (
            isinstance(target_surface, str)
            and target_surface not in ALLOWED_TARGET_SURFACES
        ):
            errors.append(
                "Unsupported target_surface: "
                f"{target_surface}"
            )

        # --------------------------------------------------
        # Planner/generator consistency
        # --------------------------------------------------

        strategy = data.get("strategy")

        if (
            expected_strategy is not None
            and isinstance(strategy, str)
            and strategy != expected_strategy
        ):
            errors.append(
                "Generated strategy does not match the "
                f"planner-selected strategy. "
                f"Expected '{expected_strategy}', "
                f"received '{strategy}'."
            )

        if errors:
            return ValidationResult(
                valid=False,
                data=None,
                errors=errors,
            )

        return ValidationResult(
            valid=True,
            data=data,
            errors=[],
        )