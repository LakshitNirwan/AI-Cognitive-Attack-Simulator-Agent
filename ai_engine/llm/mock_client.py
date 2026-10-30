from __future__ import annotations

from typing import Any

from ai_engine.llm.client import LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """
    Deterministic LLM substitute used to test the generator pipeline.

    It produces a structured, non-operational test attack.
    """

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:

        return LLMResponse(
            text=(
                "{"
                '"attack_family":"controlled_test",'
                '"objective":"controlled_adaptation",'
                '"strategy":"indirect",'
                '"payload":"CONTROLLED_LLM_GENERATED_TEST",'
                '"target_surface":"input"'
                "}"
            ),
            model="mock-llm",
            metadata={
                "mock": True,
                "temperature": temperature,
            },
        )