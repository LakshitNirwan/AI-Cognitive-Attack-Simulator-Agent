from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ai_engine.contracts import AgentState


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    """
    Planner output.

    The planner selects WHAT strategy should be attempted next.
    It does not generate the final attack payload.
    """

    strategy: str
    rationale: str
    confidence: float
    metadata: dict[str, Any]


class Planner(ABC):
    """
    Provider/model-independent planner interface.
    """

    @abstractmethod
    def select_strategy(
        self,
        state: AgentState,
    ) -> StrategyDecision:
        raise NotImplementedError