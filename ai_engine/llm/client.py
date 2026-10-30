from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    metadata: dict[str, Any]


class LLMClient(ABC):
    """
    Provider-independent interface for the model used by AICAS.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        raise NotImplementedError