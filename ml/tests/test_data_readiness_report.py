import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "datasets/audit/DATA_READINESS_REPORT.json"


def test_readiness_report_records_all_current_sources():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert set(report["datasets"]) == {
        "JailbreakBench", "HarmBench", "IndiBias", "DefAn", "AgentDojo", "SLabsPromptInjection"
    }
    for dataset in report["datasets"].values():
        assert dataset["local_artifact"]["exists"] is True
        assert len(dataset["local_artifact"]["sha256"]) == 64


def test_slabs_remains_blocked_when_upstream_bytes_match_but_labels_conflict():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    gate = report["external_source_gate"]
    assert gate["decision"] == "BLOCKED"
    assert gate["manifest_training_eligible"] is False
    assert gate["pinned_verification_status"] == "PINNED_SOURCE_HAS_CONFLICTS"
    assert gate["pinned_verification_training_eligible"] is False


def test_slabs_pinned_conflict_verification_is_audited():
    path = ROOT / "datasets/audit/SLABS_PINNED_UPSTREAM_VERIFICATION.json"
    verification = json.loads(path.read_text(encoding="utf-8"))
    assert verification["revision"] == "002a9dd"
    assert verification["byte_identical"] is True
    assert verification["status"] == "PINNED_SOURCE_HAS_CONFLICTS"
    assert verification["training_eligible"] is False
    earlier_path = ROOT / "datasets/audit/SLABS_PINNED_UPSTREAM_VERIFICATION_PRE_RETRY.json"
    earlier = json.loads(earlier_path.read_text(encoding="utf-8"))
    assert earlier["status"] == "UPSTREAM_FETCH_FAILED"


def test_task_semantics_and_missing_reference_guardrails_are_explicit():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["datasets"]["JailbreakBench"]["decision"] == "CONDITIONAL_TASK_SPECIFIC_USE"
    assert report["datasets"]["HarmBench"]["decision"] == "CONDITIONAL_TASK_SPECIFIC_USE"
    assert report["datasets"]["IndiBias"]["decision"] == "EVALUATION_FIRST"
    assert report["datasets"]["AgentDojo"]["decision"] == "EVALUATION_FIRST"
    assert "1,080" in report["datasets"]["DefAn"]["reason"]
