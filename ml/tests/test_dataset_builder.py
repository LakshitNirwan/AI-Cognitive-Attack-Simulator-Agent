from __future__ import annotations

import sys
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.data.build_dataset import (
    LABELS,
    split_data,
    validate_source,
    validate_training_eligibility,
)


def make_valid_frame():
    rows = []
    for index, label in enumerate(["benign", "harmful"]):
        rows.append(
            {
                "record_id": f"R{index}",
                "source_dataset": "JailbreakBench",
                "source_file": "test.csv",
                "behavior_class": label,
                "original_index": index,
                "goal": f"unique goal {index}",
                "target": f"target {index}",
                "behavior": f"behavior {index}",
                "category": "test",
                "source": "Original",
            }
        )
    return pd.DataFrame(rows)


def test_valid_source():
    validate_source(make_valid_frame())


def test_unknown_label_rejected():
    frame = make_valid_frame()
    frame.loc[0, "behavior_class"] = "prompt_injection"
    with pytest.raises(ValueError, match="Unexpected behavior_class"):
        validate_source(frame)


def test_conflicting_labels_for_normalized_goal_rejected():
    frame = make_valid_frame()
    frame.loc[1, "goal"] = frame.loc[0, "goal"]
    with pytest.raises(ValueError, match="conflicting labels"):
        validate_source(frame)


def test_same_label_duplicate_goals_can_be_grouped_without_leakage():
    frame = pd.DataFrame(
        [
            {
                "record_id": f"R{index}",
                "source_dataset": "JailbreakBench",
                "source_file": "test.csv",
                "behavior_class": label,
                "original_index": index,
                "goal": f"unique goal {index // 2}",
                "target": f"target {index}",
                "behavior": f"behavior {index}",
                "category": "test",
                "source": "Original",
            }
            for index in range(40)
            for label in (["benign"] if index < 20 else ["harmful"])
        ]
    )
    # Each duplicated pair has the same label, and is assigned as one group.
    validate_source(frame)
    train, validation, test = split_data(frame, seed=42)
    group_sets = [set(part["group_id"]) for part in (train, validation, test)]
    assert not (group_sets[0] & group_sets[1])
    assert not (group_sets[0] & group_sets[2])
    assert not (group_sets[1] & group_sets[2])
    assert {row for part in (train, validation, test) for row in part["split"]} == {
        "train",
        "validation",
        "test",
    }
    repeated = split_data(frame, seed=42)
    assert [part["record_id"].tolist() for part in (train, validation, test)] == [
        part["record_id"].tolist() for part in repeated
    ]


def test_training_gate_requires_matching_task_path_and_hash(tmp_path):
    source = tmp_path / "jbb.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    component_dir = tmp_path / "datasets" / "jailbreak" / "raw"
    component_dir.mkdir(parents=True)
    (component_dir / "benign-behaviors.csv").write_text("benign", encoding="utf-8")
    (component_dir / "harmful-behaviors.csv").write_text("harmful", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    report_dir = tmp_path / "datasets" / "audit"
    report_dir.mkdir(parents=True)
    report = {
        "datasets": {
            "JailbreakBench": {
                "decision": "CONDITIONAL_TASK_SPECIFIC_USE",
                "local_artifact": {
                    "path": "jbb.csv",
                    "exists": True,
                    "sha256": digest,
                },
            }
        }
    }
    (report_dir / "DATA_READINESS_REPORT.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    components = []
    for name in ("benign-behaviors.csv", "harmful-behaviors.csv"):
        component_path = component_dir / name
        components.append({
            "path": f"datasets/jailbreak/raw/{name}",
            "upstream_url": f"https://example.invalid/{name}",
            "local_sha256": hashlib.sha256(component_path.read_bytes()).hexdigest(),
            "byte_identical": True,
        })
    verification = {
        "status": "PINNED_BYTES_VERIFIED",
        "byte_identical": True,
        "upstream_revision": "a" * 40,
        "license_declared_by_upstream_card": "mit",
        "files": components,
    }
    (report_dir / "JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )
    eligibility = validate_training_eligibility(
        tmp_path, source, "JailbreakBench", "jailbreakbench_behavior_classification"
    )
    assert eligibility["sha256"] == digest
    assert eligibility["source_revision"] == "a" * 40
    assert eligibility["source_revision_status"] == "pinned_upstream_bytes_verified"
    assert len(eligibility["component_files"]) == 2
    with pytest.raises(ValueError, match="not approved"):
        validate_training_eligibility(
            tmp_path, source, "JailbreakBench", "direct_prompt_injection_detection"
        )


def test_training_gate_rejects_blocked_source_and_changed_hash(tmp_path):
    source = tmp_path / "train.csv"
    source.write_text("raw", encoding="utf-8")
    report_dir = tmp_path / "datasets" / "audit"
    report_dir.mkdir(parents=True)
    artifact = {"path": "train.csv", "exists": True, "sha256": "0" * 64}
    report = {
        "datasets": {
            "JailbreakBench": {
                "decision": "BLOCKED",
                "local_artifact": artifact,
            }
        }
    }
    (report_dir / "DATA_READINESS_REPORT.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="not training eligible"):
        validate_training_eligibility(
            tmp_path, source, "JailbreakBench", "jailbreakbench_behavior_classification"
        )
    report["datasets"]["JailbreakBench"]["decision"] = "APPROVED"
    (report_dir / "DATA_READINESS_REPORT.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Source hash changed"):
        validate_training_eligibility(
            tmp_path, source, "JailbreakBench", "jailbreakbench_behavior_classification"
        )


def test_label_mapping_is_explicit():
    assert LABELS == {"benign": 0, "harmful": 1}


def test_training_gate_rejects_unverified_pinned_component_hash(tmp_path):
    source = tmp_path / "jbb.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    component_dir = tmp_path / "datasets" / "jailbreak" / "raw"
    component_dir.mkdir(parents=True)
    for name in ("benign-behaviors.csv", "harmful-behaviors.csv"):
        (component_dir / name).write_text(name, encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    audit_dir = tmp_path / "datasets" / "audit"
    audit_dir.mkdir(parents=True)
    report = {"datasets": {"JailbreakBench": {"decision": "CONDITIONAL_TASK_SPECIFIC_USE", "local_artifact": {"path": "jbb.csv", "exists": True, "sha256": digest}}}}
    (audit_dir / "DATA_READINESS_REPORT.json").write_text(json.dumps(report), encoding="utf-8")
    (audit_dir / "JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json").write_text(json.dumps({"status": "PINNED_BYTES_VERIFIED", "byte_identical": True, "upstream_revision": "a" * 40, "license_declared_by_upstream_card": "mit", "files": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match pinned upstream verification"):
        validate_training_eligibility(tmp_path, source, "JailbreakBench", "jailbreakbench_behavior_classification")
