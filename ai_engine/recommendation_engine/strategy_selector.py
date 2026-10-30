from __future__ import annotations

from ai_engine.contracts import AgentState


class StrategySelector:
    """
    Deterministic strategy selector for the first adaptive prototype.

    This is intentionally simple. The goal is to prove the control
    loop before introducing an LLM planner or learned policy.
    """

    def select(self, state: AgentState) -> str:
        # First attempt.
        if state.current_step == 0:
            return "direct"

        # If direct has failed, try indirect.
        direct_stats = state.strategy_stats.get("direct", {})

        if direct_stats.get("failures", 0) > 0:
            return "indirect"

        # Otherwise keep the current simple strategy.
        return "direct"