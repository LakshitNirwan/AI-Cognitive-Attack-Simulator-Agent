from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

from ai_engine.contracts.attack import Attack
from ai_engine.contracts.observation import Observation
from ai_engine.targets.base import TargetAdapter, TargetInfo


class MockTargetAdapter(TargetAdapter):
    """
    Deterministic target for validating the AICAS execution pipeline.

    This is an infrastructure test target, not a simulation of a
    real model's safety behavior.
    """

    def __init__(self) -> None:
        self._info = TargetInfo(
            target_id="mock-target-001",
            provider="AICAS",
            model="mock-model",
            model_version="0.1",
            interface_type="chat",
            supports_tools=False,
            supports_multiturn=True,
            supports_system_prompt=True,
            supports_streaming=False,
        )

    def get_target_info(self) -> TargetInfo:
        return self._info

    def execute(self, attack: Attack) -> Observation:
        start = perf_counter()

        strategy = attack.strategy.lower()

        if strategy == "direct":
            response = "MOCK_TARGET_REFUSAL: direct strategy blocked."
            termination_reason = "refused"

        elif strategy == "indirect":
            response = (
                "MOCK_TARGET_SUCCESS: indirect strategy accepted "
                "in controlled test."
            )
            termination_reason = "completed"

        elif strategy == "controlled_trigger":
            trigger_responses = {
                "trigger_success": (
                    "MOCK_TARGET_SUCCESS: explicit test trigger accepted."
                ),
                "trigger_partial": (
                    "MOCK_TARGET_PARTIAL: explicit test trigger partially accepted."
                ),
                "trigger_refusal": (
                    "MOCK_TARGET_REFUSAL: explicit test trigger refused."
                ),
            }
            response = trigger_responses.get(
                str(attack.payload), "MOCK_TARGET_REFUSAL: unknown test trigger."
            )
            termination_reason = (
                "completed" if "MOCK_TARGET_SUCCESS" in response else "refused"
            )

        else:
            response = "MOCK_TARGET_REFUSAL: unknown strategy."
            termination_reason = "refused"

        latency_ms = (perf_counter() - start) * 1000

        return Observation(
            attack_id=attack.attack_id,
            target_id=self._info.target_id,
            run_id="mock-run-001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            response=response,
            termination_reason=termination_reason,
            latency_ms=latency_ms,
            raw_metadata={
                "mock": True,
                "attack_family": attack.attack_family,
                "strategy": attack.strategy,
            },
        )
