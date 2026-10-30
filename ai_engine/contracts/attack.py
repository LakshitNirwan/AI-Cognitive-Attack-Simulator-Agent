from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True)
class Attack:
    """
    Structured representation of one AICAS attack candidate.

    This object describes the intended attack.
    It does not contain target responses or evaluation results.
    """

    attack_id: UUID = field(default_factory=uuid4)

    parent_attack_id: UUID | None = None

    source_record_id: str | None = None

    attack_family: str = "unknown"

    objective: str = ""

    strategy: str = ""

    payload: Any = ""

    context: Any | None = None

    target_surface: str = "input"

    hypotheses: list[dict[str, Any]] = field(default_factory=list)

    generation_method: str = "manual"

    generation_model: str | None = None

    generation_version: str | None = None

    constraints: dict[str, Any] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)