from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True)
class Observation:
    """
    Normalized evidence produced by executing an attack.

    This class records what happened.
    It does not decide whether the attack succeeded.
    """

    observation_id: UUID = field(default_factory=uuid4)

    attack_id: UUID | None = None

    target_id: str = ""

    run_id: str = ""

    timestamp: str = ""

    response: Any = None

    tool_events: list[dict[str, Any]] = field(default_factory=list)

    state_changes: list[dict[str, Any]] = field(default_factory=list)

    errors: list[dict[str, Any]] = field(default_factory=list)

    termination_reason: str | None = None

    latency_ms: float | None = None

    token_usage: dict[str, Any] | None = None

    raw_metadata: dict[str, Any] = field(default_factory=dict)