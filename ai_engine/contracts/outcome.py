from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True)
class Outcome:
    """
    Research interpretation of an Observation.

    Observation = evidence.
    Outcome = interpretation of that evidence.
    """

    outcome_id: UUID = field(default_factory=uuid4)

    observation_id: UUID | None = None

    classification: str = "unknown"

    success: bool | None = None

    severity: int | None = None

    confidence: float | None = None

    evidence: list[dict[str, Any]] = field(default_factory=list)

    evaluator: str = ""

    evaluator_version: str = ""

    notes: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)