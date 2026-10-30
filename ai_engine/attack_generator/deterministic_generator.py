from __future__ import annotations

from ai_engine.contracts import AgentState, Attack
from ai_engine.attack_generator.generator import AttackGenerator


class DeterministicAttackGenerator(AttackGenerator):
    """
    Transparent baseline attack generator.

    This is intentionally simple. It proves the generator
    interface before we introduce an LLM-based generator.
    """

    def generate(
        self,
        state: AgentState,
        strategy: str,
    ) -> Attack:

        payloads = {
            "direct": (
                "CONTROLLED_DIRECT_ATTACK"
            ),
            "indirect": (
                "CONTROLLED_INDIRECT_ATTACK"
            ),
        }

        payload = payloads.get(
            strategy,
            f"CONTROLLED_{strategy.upper()}_ATTACK",
        )

        return Attack(
            source_record_id=None,
            attack_family="controlled_test",
            objective=state.objective,
            strategy=strategy,
            payload=payload,
            target_surface="input",
            hypotheses=list(state.hypotheses),
            generation_method="deterministic_generator",
            generation_model=None,
            generation_version="0.1.0",
            metadata={
                "generator": "deterministic",
                "state_step": state.current_step,
            },
        )