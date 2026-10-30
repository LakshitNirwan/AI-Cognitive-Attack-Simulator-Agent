from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ai_engine.contracts.attack import Attack
from ai_engine.contracts.observation import Observation


@dataclass(slots=True)
class TargetInfo:
    """
    Stable metadata describing a target system.
    """

    target_id: str
    provider: str
    model: str
    model_version: str | None = None

    interface_type: str = "chat"

    supports_tools: bool = False
    supports_multiturn: bool = True
    supports_system_prompt: bool = False
    supports_streaming: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)


class TargetAdapter(ABC):
    """
    Provider-independent interface between AICAS and a target.

    The adapter is responsible for execution mechanics.
    It does not decide attack strategy or attack success.
    """

    @abstractmethod
    def execute(self, attack: Attack) -> Observation:
        """
        Execute exactly one attack and return normalized evidence.
        """
        raise NotImplementedError

    @abstractmethod
    def get_target_info(self) -> TargetInfo:
        """
        Return stable metadata about the target.
        """
        raise NotImplementedError