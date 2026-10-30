from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable
from uuid import uuid4


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


ALLOWED_SURFACES = {
    "user_input",
    "retrieved_content",
    "tool_output",
    "assistant_output",
}


@dataclass(frozen=True)
class Finding:
    """Task-specific detector output; different security tasks stay distinct."""

    surface: str
    task: str
    confidence: float
    evidence: str = ""

    def __post_init__(self) -> None:
        if self.surface not in ALLOWED_SURFACES:
            raise ValueError(f"Unsupported content surface: {self.surface!r}")
        if not self.task.strip():
            raise ValueError("Finding task must be a non-empty task identifier.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Finding confidence must be between 0 and 1.")


@dataclass(frozen=True)
class ActionRequest:
    name: str
    parameters: dict[str, object] = field(default_factory=dict)
    requires_approval: bool = False
    approval_record_id: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Action name must be non-empty.")


@dataclass(frozen=True)
class GatewayResult:
    request_id: str
    decision: Decision
    reasons: tuple[str, ...]
    findings: tuple[Finding, ...]
    action_authorized: bool
    action_result: object | None
    audit_event_id: str


class JsonlAuditLog:
    """Append-only event log that records hashes and metadata, never content."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, event: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")


Detector = Callable[[str, str], Iterable[Finding]]
ActionExecutor = Callable[[ActionRequest], object]
ApprovalVerifier = Callable[[ActionRequest], bool]


def _hash_content(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SecurityGateway:
    """In-process reference flow for detection, policy, action control and audit.

    The detector and approval record must come from a trusted caller. This class
    is not an HTTP server, authentication layer, or production credential store.
    """

    POLICY_VERSION = "aicas-gateway-policy-v0.1"

    def __init__(
        self,
        *,
        detector: Detector,
        allowed_actions: set[str],
        audit_log: JsonlAuditLog,
        approval_verifier: ApprovalVerifier | None = None,
    ) -> None:
        if not callable(detector):
            raise TypeError("A detector callback is required; no implicit allow mode exists.")
        self.detector = detector
        self.allowed_actions = frozenset(allowed_actions)
        self.audit_log = audit_log
        self.approval_verifier = approval_verifier

    def handle(
        self,
        content: dict[str, str | list[str]],
        *,
        action: ActionRequest | None = None,
        executor: ActionExecutor | None = None,
    ) -> GatewayResult:
        request_id = str(uuid4())
        findings: list[Finding] = []
        reasons: list[str] = []
        hashes: dict[str, list[str]] = {}
        decision = Decision.ALLOW
        action_result = None
        action_authorized = False

        try:
            for surface, values in content.items():
                if surface not in ALLOWED_SURFACES:
                    raise ValueError(f"Unsupported content surface: {surface!r}")
                parts = [values] if isinstance(values, str) else values
                if not all(isinstance(value, str) for value in parts):
                    raise TypeError("Content values must be strings or lists of strings.")
                hashes[surface] = [_hash_content(value) for value in parts]
                for value in parts:
                    detected = list(self.detector(surface, value))
                    if any(
                        not isinstance(finding, Finding) or finding.surface != surface
                        for finding in detected
                    ):
                        raise TypeError("Detector must return Finding objects for the current surface.")
                    findings.extend(detected)
            if findings:
                decision = Decision.REVIEW
                reasons.append("task_specific_risk_finding_requires_review")
        except Exception as exc:
            # A detector or input validation failure cannot authorize an action.
            decision = Decision.REVIEW
            reasons.append(f"detector_or_input_failure:{type(exc).__name__}")

        if action is not None and decision is Decision.ALLOW:
            if action.name not in self.allowed_actions:
                decision = Decision.BLOCK
                reasons.append("action_not_allowlisted")
            elif action.requires_approval:
                approved = False
                if action.approval_record_id and self.approval_verifier is not None:
                    try:
                        approved = bool(self.approval_verifier(action))
                    except Exception:
                        approved = False
                if not approved:
                    decision = Decision.REVIEW
                    reasons.append("action_requires_verified_approval")
            if decision is Decision.ALLOW and executor is None:
                decision = Decision.REVIEW
                reasons.append("action_executor_unavailable")
            if decision is Decision.ALLOW and executor is not None:
                action_authorized = True

        audit_event_id = str(uuid4())
        event: dict[str, object] = {
            "event_id": audit_event_id,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_version": self.POLICY_VERSION,
            "decision": decision.value,
            "reasons": reasons,
            "content_sha256": hashes,
            "findings": [
                {
                    "surface": finding.surface,
                    "task": finding.task,
                    "confidence": finding.confidence,
                    "evidence_sha256": _hash_content(finding.evidence)
                    if finding.evidence
                    else None,
                }
                for finding in findings
            ],
            "action": {
                "name": action.name,
                "authorized": action_authorized,
                "approval_record_id": action.approval_record_id,
            }
            if action is not None
            else None,
        }
        self.audit_log.append(event)
        # Persist authorization before any external action is attempted.
        if action_authorized and action is not None and executor is not None:
            try:
                action_result = executor(action)
                outcome = "completed"
            except Exception as exc:
                decision = Decision.REVIEW
                reasons.append(f"action_execution_failure:{type(exc).__name__}")
                outcome = f"failed:{type(exc).__name__}"
            self.audit_log.append(
                {
                    "event_id": str(uuid4()),
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "policy_version": self.POLICY_VERSION,
                    "event_type": "action_execution_outcome",
                    "action_name": action.name,
                    "outcome": outcome,
                }
            )
        return GatewayResult(
            request_id=request_id,
            decision=decision,
            reasons=tuple(reasons),
            findings=tuple(findings),
            action_authorized=action_authorized,
            action_result=action_result,
            audit_event_id=audit_event_id,
        )
