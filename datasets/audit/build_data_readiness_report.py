"""Build a read-only AICAS dataset readiness report from local project artifacts.

This script inventories local data files and summarizes existing audit decisions.
It does not modify or relabel raw benchmark data and does not approve a dataset
solely because it can be read successfully.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

DATASETS = {
    "JailbreakBench": {
        "path": "datasets/jailbreak/processed/jailbreakbench_master.csv",
        "task": "benign-versus-harmful behavior classification; not a generic injection label",
        "decision": "CONDITIONAL_TASK_SPECIFIC_USE",
        "reason": "200 local rows; 9 normalized exact overlaps between harmful goals and HarmBench behaviors; preserve source identity and group overlap before splitting.",
    },
    "HarmBench": {
        "path": "datasets/benchmark/harmbench/processed/harmbench_behaviors_master.csv",
        "task": "harmful-behavior evaluation/classification; not a generic prompt-injection label",
        "decision": "CONDITIONAL_TASK_SPECIFIC_USE",
        "reason": "400 local behaviors; source revision/complete-release pinning remains necessary; missing optional metadata must not be converted into labels.",
    },
    "IndiBias": {
        "path": "datasets/bias/indibias/processed/indibias_master.csv",
        "task": "bias/fairness evaluation",
        "decision": "EVALUATION_FIRST",
        "reason": "561 locally collected sample rows; do not treat this sample as the complete published dataset or collapse paired-context semantics.",
    },
    "DefAn": {
        "path": "datasets/hallucination/defan/processed/defan_aicas_master.csv",
        "task": "reference-grounded factuality/output reliability",
        "decision": "REFERENCE_GROUNDED_SUBSET_ONLY",
        "reason": "1,080 records lack original reference answers; 648 normalized duplicate questions need grouping before splits; do not fabricate answers.",
    },
    "AgentDojo": {
        "path": "datasets/benchmark/agentdojo/raw/agentdojo_v1_2_2_injection_tasks.json",
        "task": "stateful agentic/indirect prompt-injection evaluation",
        "decision": "EVALUATION_FIRST",
        "reason": "35 scenarios are small and environment/state dependent; retain scenario and task semantics rather than flattening to generic text labels.",
    },
    "SLabsPromptInjection": {
        "path": "datasets/raw/external/slabs_prompt_injection/train.csv",
        "task": "direct prompt-injection detection",
        "decision": "BLOCKED_CONFLICTING_LABELS",
        "reason": "One normalized text has both labels 0 and 1. Revision 002a9dd is byte-identical and contains the same conflict; authoritative label-quality resolution is still required.",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        return {"path": relative_path, "exists": False}
    result: dict[str, Any] = {
        "path": relative_path,
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
        result.update({
            "format": "csv",
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "null_cells": int(frame.isna().sum().sum()),
            "duplicate_full_rows": int(frame.duplicated().sum()),
        })
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        result["format"] = "json"
        result["top_level_type"] = type(payload).__name__
        if isinstance(payload, list):
            result["records_or_scenarios"] = len(payload)
        elif isinstance(payload, dict):
            result["top_level_keys"] = sorted(str(key) for key in payload.keys())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root.resolve()
    audit_dir = root / "datasets" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    entries: dict[str, Any] = {}
    for name, meta in DATASETS.items():
        entry = dict(meta)
        entry["local_artifact"] = inspect_file(root, meta["path"])
        entries[name] = entry

    pinned_path = audit_dir / "SLABS_PINNED_UPSTREAM_VERIFICATION.json"
    pinned = None
    if pinned_path.exists():
        try:
            pinned = json.loads(pinned_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pinned = {"status": "UNREADABLE_REPORT", "training_eligible": False}

    manifest_path = root / "datasets/external/slabs_source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    slabs_conflicts_path = audit_dir / "SLABS_CONFLICTING_LABELS.json"
    conflicts = json.loads(slabs_conflicts_path.read_text(encoding="utf-8")) if slabs_conflicts_path.exists() else {}
    pinned_status = (pinned or {}).get("status", "NOT_RUN")
    if pinned_status == "PINNED_SOURCE_HAS_CONFLICTS":
        upstream_decision_reason = "Pinned upstream bytes match the supplied local file and contain the same contradictory labels; keep the source blocked pending authoritative label-quality resolution."
        slabs_decision = "BLOCKED_CONFLICTING_LABELS"
        slabs_reason = "One normalized text has both labels 0 and 1 in both the local and pinned upstream files. Publisher clarification or a corrected revision is required."
        first_release_gate = "Resolve the contradictory S-Labs labels with authoritative publisher documentation or a corrected immutable revision; the pinned bytes are verified but the source remains blocked."
    elif pinned_status == "PINNED_SOURCE_MATCHES_AND_NO_CONFLICTS":
        upstream_decision_reason = "Pinned bytes match and the upstream file has no detected conflicting labels; investigate the discrepancy with the local audit before changing eligibility."
        slabs_decision = "BLOCKED_LOCAL_UPSTREAM_DISCREPANCY"
        slabs_reason = "The current local conflict audit and pinned upstream audit disagree; investigate and preserve both artifacts before any eligibility change."
        first_release_gate = "Investigate the local/upstream S-Labs conflict-audit discrepancy; do not change training eligibility until the difference is explained."
    elif pinned_status == "PINNED_SOURCE_BYTES_DIFFER":
        upstream_decision_reason = "The supplied local S-Labs bytes differ from the pinned upstream revision; provenance is unresolved and the source remains blocked."
        slabs_decision = "BLOCKED_UPSTREAM_BYTES_DIFFER"
        slabs_reason = "The supplied local bytes differ from pinned revision 002a9dd; investigate provenance and the local contradictory labels before training."
        first_release_gate = "Investigate the S-Labs local/pinned byte mismatch and resolve the contradictory labels authoritatively; keep the source blocked."
    else:
        upstream_decision_reason = "Pinned upstream verification has not completed; this is inconclusive and the source remains blocked because contradictory labels are present locally."
        slabs_decision = "BLOCKED_CONFLICTING_LABELS_AND_UPSTREAM_CHECK_PENDING"
        slabs_reason = "One normalized text has both labels 0 and 1. Pinned upstream verification remains inconclusive; byte identity would not itself resolve the contradiction."
        first_release_gate = "Obtain a pinned upstream S-Labs verification result; keep the source blocked regardless until contradictory-label quality is resolved by authoritative documentation."
    entries["SLabsPromptInjection"]["decision"] = slabs_decision
    entries["SLabsPromptInjection"]["reason"] = slabs_reason

    report = {
        "report_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Phase 1 dataset readiness checkpoint; inventory is not blanket training approval.",
        "raw_data_policy": "Read-only inventory. No raw file is rewritten, relabeled, or removed.",
        "datasets": entries,
        "external_source_gate": {
            "name": manifest.get("dataset_name", "S-Labs/prompt-injection-dataset"),
            "pinned_revision": manifest.get("upstream_revision", "002a9dd"),
            "manifest_training_eligible": bool(manifest.get("training_eligible", False)),
            "local_conflicting_text_count": conflicts.get("conflicting_text_count"),
            "pinned_verification_status": (pinned or {}).get("status", "NOT_RUN"),
            "pinned_verification_training_eligible": False,
            "decision": "BLOCKED",
            "decision_reason": upstream_decision_reason,
        },
        "cross_source_findings": {
            "jailbreakbench_harmbench_normalized_exact_overlap": 9,
            "slabs_jailbreakbench_normalized_exact_overlap": 0,
            "slabs_harmbench_normalized_exact_overlap": 0,
            "slabs_near_duplicate_audit_threshold": 0.82,
            "slabs_near_duplicate_candidates_reported": 0,
            "caveat": "The S-Labs cross-source findings are based on the supplied local training split and character n-gram candidate discovery. Zero candidates do not prove absence of semantic overlap or leakage.",
        },
        "release_gates_not_yet_satisfied": [
            first_release_gate,
            "Pin the exact HarmBench source revision and document artifact-specific redistribution terms.",
            "Record artifact-specific licensing/usage decisions for each dataset before redistribution or external release.",
            "Define task-specific target labels and split grouping rules before constructing a unified ML dataset.",
            "Group overlapping JailbreakBench/HarmBench examples and duplicate DefAn questions before splitting.",
            "Keep IndiBias and AgentDojo evaluation-first unless a separately justified task-specific training design is approved.",
            "Build a reproducible, source-aware train/validation/test manifest and verify that raw inputs remain unchanged.",
        ],
    }
    json_path = audit_dir / "DATA_READINESS_REPORT.json"
    md_path = audit_dir / "DATA_READINESS_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# AICAS Data Readiness Report — v1.0", "",
        f"Generated (UTC): {report['generated_utc']}", "",
        "## Decision summary", "",
        "This is a readiness checkpoint, not blanket approval to train. Existing raw data was inspected read-only; no records were relabeled or removed.", "",
        "| Dataset | Local rows/scenarios | Decision |", "|---|---:|---|",
    ]
    for name, entry in entries.items():
        artifact = entry["local_artifact"]
        count = artifact.get("rows", artifact.get("records_or_scenarios", "not available"))
        lines.append(f"| {name} | {count} | `{entry['decision']}` |")
    lines += [
        "", "## S-Labs gate", "",
        f"- Pinned revision: `{report['external_source_gate']['pinned_revision']}`",
        f"- Local contradictory-label texts: `{report['external_source_gate']['local_conflicting_text_count']}`",
        f"- Pinned verification status: `{report['external_source_gate']['pinned_verification_status']}`",
        "- Training eligible: **No**",
        f"- Reason: {report['external_source_gate']['decision_reason']}",
        "", "## Cross-source overlap snapshot", "",
        "- JailbreakBench harmful goals ↔ HarmBench behaviors: 9 normalized exact overlaps.",
        "- S-Labs train ↔ JailbreakBench: 0 normalized exact overlaps in the recorded audit.",
        "- S-Labs train ↔ HarmBench: 0 normalized exact overlaps in the recorded audit.",
        "- S-Labs character n-gram near-duplicate candidates at threshold 0.82: 0 reported.",
        "- These results do not prove absence of semantic overlap or leakage.",
        "", "## Required before training-set construction", "",
    ]
    lines.extend(f"{index}. {item}" for index, item in enumerate(report["release_gates_not_yet_satisfied"], start=1))
    lines += [
        "", "## File integrity inventory", "",
        "The JSON report records relative path, byte size, SHA-256, row/scenario count, columns, null-cell count, and exact duplicate-row count where applicable.",
        "", "## Rebuild", "",
        "```bash", "python datasets/audit/build_data_readiness_report.py --repo-root .", "```", "",
        "The report is generated from current local files and existing audit artifacts. It does not download data, infer missing labels, or grant training approval.", "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"json_report": str(json_path), "markdown_report": str(md_path), "dataset_count": len(entries), "slabs_pinned_status": report["external_source_gate"]["pinned_verification_status"], "slabs_training_eligible": False}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
