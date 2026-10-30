from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_engine.attack_generator import AttackGenerator
from ai_engine.contracts import AgentState, Outcome
from ai_engine.recommendation_engine import Planner
from ai_engine.response_evaluator import OutcomeEvaluator
from ai_engine.targets import TargetAdapter
from ai_engine.memory.state_manager import StateManager


@dataclass
class RunResult:
    run_id: str
    outcomes: list[Outcome] = field(default_factory=list)
    final_state: AgentState | None = None
    attacks_generated: int = 0


class AdaptiveRunner:
    """
    Connects the AICAS planner, generator, target, evaluator,
    and state manager into one adaptive execution loop.
    """

    def __init__(
        self,
        planner: Planner,
        generator: AttackGenerator,
        target: TargetAdapter,
        evaluator: OutcomeEvaluator,
        state_manager: StateManager,
    ) -> None:
        self.planner = planner
        self.generator = generator
        self.target = target
        self.evaluator = evaluator
        self.state_manager = state_manager

    def run(
        self,
        state: AgentState,
        max_steps: int = 3,
    ) -> RunResult:
        outcomes: list[Outcome] = []
        attacks_generated = 0

        for _ in range(max_steps):
            if self._should_stop(state):
                break

            decision = self.planner.select_strategy(state)

            attack = self.generator.generate(
                state=state,
                strategy=decision.strategy,
            )

            observation = self.target.execute(attack)

            outcome = self.evaluator.evaluate(observation)

            self.state_manager.update(
                state,
                attack,
                outcome,
            )

            outcomes.append(outcome)
            attacks_generated += 1

            # Controlled prototype termination:
            # stop after the first successful objective.
            if outcome.success is True:
                break

        return RunResult(
            run_id=state.run_id,
            outcomes=outcomes,
            final_state=state,
            attacks_generated=attacks_generated,
        )

    @staticmethod
    def _should_stop(state: AgentState) -> bool:
        max_steps = state.budget.get("max_steps")

        if max_steps is not None:
            if state.current_step >= int(max_steps):
                return True

        return False