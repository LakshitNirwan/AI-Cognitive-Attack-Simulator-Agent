from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True)
class AgentState:
    """
    Working state of one AICAS attack run.

    This is the agent's current working model, not the complete
    historical experiment database.
    """

    agent_state_id: UUID = field(default_factory=uuid4)

    run_id: str = ""

    target_id: str = ""

    objective: str = ""

    current_step: int = 0

    budget: dict[str, Any] = field(default_factory=dict)

    hypotheses: list[dict[str, Any]] = field(default_factory=list)

    strategy_stats: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    successful_patterns: list[dict[str, Any]] = field(
        default_factory=list
    )

    failed_patterns: list[dict[str, Any]] = field(
        default_factory=list
    )

    unexplored_strategies: list[str] = field(
        default_factory=list
    )

    target_profile: dict[str, Any] = field(
        default_factory=dict
    )

    recent_outcomes: list[UUID] = field(
        default_factory=list
    )

    best_known_attack_id: UUID | None = None

    termination_condition: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )