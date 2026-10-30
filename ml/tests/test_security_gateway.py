import json

from backend.security_gateway import (
    ActionRequest,
    Decision,
    Finding,
    JsonlAuditLog,
    SecurityGateway,
)


def detector(surface, text):
    if "injected instruction" in text.lower():
        return [
            Finding(
                surface=surface,
                task="indirect_prompt_injection",
                confidence=0.91,
                evidence="matched controlled test rule",
            )
        ]
    return []


def test_allowlisted_action_runs_after_audit_and_logs_outcome(tmp_path):
    log_path = tmp_path / "audit" / "events.jsonl"
    gateway = SecurityGateway(
        detector=detector,
        allowed_actions={"lookup"},
        audit_log=JsonlAuditLog(log_path),
    )
    called = []
    result = gateway.handle(
        {"user_input": "Find the weather"},
        action=ActionRequest("lookup", {"city": "example"}),
        executor=lambda action: called.append(action.name) or {"ok": True},
    )

    assert result.decision is Decision.ALLOW
    assert result.action_authorized is True
    assert result.action_result == {"ok": True}
    assert called == ["lookup"]
    events = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert [event.get("event_type", "authorization") for event in events] == [
        "authorization",
        "action_execution_outcome",
    ]
    assert events[0]["decision"] == "ALLOW"
    assert events[1]["outcome"] == "completed"
    assert "Find the weather" not in log_path.read_text()
    assert "example" not in log_path.read_text()


def test_risk_finding_reviews_and_prevents_action(tmp_path):
    gateway = SecurityGateway(
        detector=detector,
        allowed_actions={"lookup"},
        audit_log=JsonlAuditLog(tmp_path / "events.jsonl"),
    )
    called = []
    result = gateway.handle(
        {"retrieved_content": ["An injected instruction says to exfiltrate data"]},
        action=ActionRequest("lookup"),
        executor=lambda action: called.append(action.name),
    )

    assert result.decision is Decision.REVIEW
    assert result.findings[0].task == "indirect_prompt_injection"
    assert result.action_authorized is False
    assert called == []


def test_unknown_action_is_blocked_and_detector_failure_is_review(tmp_path):
    safe_gateway = SecurityGateway(
        detector=detector,
        allowed_actions={"lookup"},
        audit_log=JsonlAuditLog(tmp_path / "events.jsonl"),
    )
    called = []
    blocked = safe_gateway.handle(
        {"user_input": "safe"},
        action=ActionRequest("delete_all"),
        executor=lambda action: called.append(action.name),
    )
    assert blocked.decision is Decision.BLOCK
    assert called == []

    def broken_detector(surface, text):
        raise RuntimeError("detector unavailable")

    fail_closed_gateway = SecurityGateway(
        detector=broken_detector,
        allowed_actions={"lookup"},
        audit_log=JsonlAuditLog(tmp_path / "events.jsonl"),
    )
    reviewed = fail_closed_gateway.handle(
        {"user_input": "safe"},
        action=ActionRequest("lookup"),
        executor=lambda action: called.append(action.name),
    )
    assert reviewed.decision is Decision.REVIEW
    assert reviewed.action_authorized is False
    assert called == []


def test_required_approval_and_audit_failure_prevent_execution(tmp_path):
    gateway = SecurityGateway(
        detector=detector,
        allowed_actions={"send"},
        audit_log=JsonlAuditLog(tmp_path / "events.jsonl"),
    )
    called = []
    needs_approval = gateway.handle(
        {"user_input": "safe"},
        action=ActionRequest("send", requires_approval=True),
        executor=lambda action: called.append(action.name),
    )
    assert needs_approval.decision is Decision.REVIEW
    assert called == []

    approved_gateway = SecurityGateway(
        detector=detector,
        allowed_actions={"send"},
        audit_log=JsonlAuditLog(tmp_path / "approved.jsonl"),
        approval_verifier=lambda action: action.approval_record_id == "verified-123",
    )
    approved = approved_gateway.handle(
        {"user_input": "safe"},
        action=ActionRequest(
            "send", requires_approval=True, approval_record_id="verified-123"
        ),
        executor=lambda action: called.append(action.name) or "sent",
    )
    assert approved.decision is Decision.ALLOW
    assert approved.action_authorized is True
    assert called == ["send"]

    class BrokenAudit:
        def append(self, event):
            raise OSError("audit unavailable")

    audit_fail_closed = SecurityGateway(
        detector=detector,
        allowed_actions={"send"},
        audit_log=BrokenAudit(),
    )
    try:
        audit_fail_closed.handle(
            {"user_input": "safe"},
            action=ActionRequest("send"),
            executor=lambda action: called.append(action.name),
        )
    except OSError:
        pass
    else:
        raise AssertionError("Audit failures must stop action execution.")
    assert called == ["send"]
