from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai_engine.contracts import AgentState, Attack


class AttackGenerator(ABC):
    """
    Converts a planner decision into a concrete Attack object.

    The generator constructs the attack.
    It does not decide whether the strategy should be selected.
    """

    @abstractmethod
    def generate(
        self,
        state: AgentState,
        strategy: str,
    ) -> Attack:
        raise NotImplementedError