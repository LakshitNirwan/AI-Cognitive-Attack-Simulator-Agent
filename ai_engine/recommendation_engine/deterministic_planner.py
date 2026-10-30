from __future__ import annotations

from ai_engine.contracts import AgentState
from ai_engine.recommendation_engine.planner import (
    Planner,
    StrategyDecision,
)


class DeterministicPlanner(Planner):
    """
    Transparent baseline planner.

    This is intentionally simple. Its purpose is to establish
    a clean planner interface before introducing an LLM-based
    or learned policy.
    """

    def select_strategy(
        self,
        state: AgentState,
    ) -> StrategyDecision:

        # First iteration: choose the first unexplored strategy
        # when available.
        if state.current_step == 0:
            if state.unexplored_strategies:
                strategy = state.unexplored_strategies[0]

                return StrategyDecision(
                    strategy=strategy,
                    rationale="Initial unexplored strategy.",
                    confidence=0.50,
                    metadata={
                        "planner": "deterministic",
                        "mode": "initial_exploration",
                    },
                )

            return StrategyDecision(
                strategy="direct",
                rationale="No unexplored strategy was supplied.",
                confidence=0.25,
                metadata={
                    "planner": "deterministic",
                    "mode": "fallback",
                },
            )

        # Prefer strategies that have not yet been attempted.
        for strategy in state.unexplored_strategies:
            if strategy not in state.strategy_stats:
                return StrategyDecision(
                    strategy=strategy,
                    rationale=(
                        "Explore a strategy with no prior evidence."
                    ),
                    confidence=0.40,
                    metadata={
                        "planner": "deterministic",
                        "mode": "exploration",
                    },
                )

        # If a strategy has already succeeded, prefer the best
        # observed empirical success rate.
        best_strategy = None
        best_rate = -1.0

        for strategy, stats in state.strategy_stats.items():
            attempts = stats.get("attempts", 0)
            successes = stats.get("successes", 0)

            if attempts <= 0:
                continue

            rate = successes / attempts

            if rate > best_rate:
                best_rate = rate
                best_strategy = strategy

        if best_strategy is not None and best_rate > 0.0:
            return StrategyDecision(
                strategy=best_strategy,
                rationale=(
                    "Exploit the strategy with the best observed "
                    "success rate."
                ),
                confidence=min(0.95, best_rate),
                metadata={
                    "planner": "deterministic",
                    "mode": "exploitation",
                    "observed_success_rate": best_rate,
                },
            )

        # If everything tried so far has failed, choose the strategy
        # with the fewest attempts to preserve some exploration.
        if state.strategy_stats:
            least_tested = min(
                state.strategy_stats,
                key=lambda name: state.strategy_stats[name].get(
                    "attempts",
                    0,
                ),
            )

            return StrategyDecision(
                strategy=least_tested,
                rationale=(
                    "No successful strategy exists yet; "
                    "continue exploration."
                ),
                confidence=0.30,
                metadata={
                    "planner": "deterministic",
                    "mode": "fallback_exploration",
                },
            )

        return StrategyDecision(
            strategy="direct",
            rationale="Planner fallback.",
            confidence=0.20,
            metadata={
                "planner": "deterministic",
                "mode": "fallback",
            },
        )