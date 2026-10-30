from __future__ import annotations

from ai_engine.contracts import AgentState, Attack, Outcome


class StateManager:
    """
    Updates AICAS working state after an evaluated attack.

    Version 0.1 is deliberately deterministic.
    We will replace the simple strategy rule later with
    a learned/planned policy.
    """

    def update(
        self,
        state: AgentState,
        attack: Attack,
        outcome: Outcome,
    ) -> AgentState:
        state.current_step += 1

        # Store the latest outcome.
        state.recent_outcomes.append(outcome.outcome_id)

        # Keep the recent history bounded.
        state.recent_outcomes = state.recent_outcomes[-10:]

        strategy = attack.strategy

        stats = state.strategy_stats.setdefault(
            strategy,
            {
                "attempts": 0,
                "successes": 0,
                "partial_successes": 0,
                "failures": 0,
            },
        )

        stats["attempts"] += 1

        if outcome.success is True:
            stats["successes"] += 1

        elif outcome.classification == "partial_compliance":
            stats["partial_successes"] += 1

        elif outcome.success is False:
            stats["failures"] += 1

        # Very simple first-version learning signal.
        #
        # This is intentionally NOT an advanced policy yet.
        # It only proves that outcomes can influence state.
        if outcome.success is True:
            state.successful_patterns.append(
                {
                    "attack_id": str(attack.attack_id),
                    "strategy": attack.strategy,
                    "classification": outcome.classification,
                }
            )

            state.best_known_attack_id = attack.attack_id

        elif outcome.success is False:
            state.failed_patterns.append(
                {
                    "attack_id": str(attack.attack_id),
                    "strategy": attack.strategy,
                    "classification": outcome.classification,
                }
            )

        return state