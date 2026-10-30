from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


def normalize(text: Any) -> str:
    """Normalize conservatively for exact text/label contradiction detection."""
    value = str(text).strip().lower()
    return re.sub(r"\s+", " ", value)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit_conflicts(csv_path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    frame = pd.read_csv(csv_path)
    required = {"text", "label"}
    if not required.issubset({str(c).strip().lower() for c in frame.columns}):
        raise ValueError(f"Expected columns text,label; found {list(frame.columns)}")
    text_col = next(c for c in frame.columns if str(c).strip().lower() == "text")
    label_col = next(c for c in frame.columns if str(c).strip().lower() == "label")
    groups: dict[str, list[dict[str, Any]]] = {}
    for index, row in frame.iterrows():
        if pd.isna(row[text_col]) or pd.isna(row[label_col]):
            continue
        text = normalize(row[text_col])
        if not text:
            continue
        groups.setdefault(text, []).append({
            "dataframe_index_zero_based": int(index),
            "csv_row_one_based_with_header": int(index) + 2,
            "label": int(row[label_col]),
            "observed_text_sha256": sha256_text(str(row[text_col]).strip()),
        })
    conflicts = []
    for text, occurrences in groups.items():
        labels = sorted({x["label"] for x in occurrences})
        if len(labels) > 1:
            conflicts.append({
                "normalized_text_sha256": sha256_text(text),
                "observed_text_sha256": occurrences[0]["observed_text_sha256"],
                "normalized_text": text,
                "labels": labels,
                "occurrences": occurrences,
            })
    raw_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    input_file = str(csv_path)
    if repo_root is not None:
        try:
            input_file = csv_path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            # Keep external inputs explicit when they are outside the project root.
            input_file = str(csv_path.resolve())
    return {
        "audit_type": "exact_normalized_text_conflicting_label_audit",
        "status": "BLOCKED_CONFLICTS_FOUND" if conflicts else "PASS_NO_CONFLICTS_FOUND",
        "training_eligible": not bool(conflicts),
        "input_file": input_file,
        "input_file_sha256": raw_sha,
        "rows_read": int(len(frame)),
        "conflicting_text_count": len(conflicts),
        "conflicts": conflicts,
        "decision_note": (
            "Any identical normalized text with different labels blocks source approval. "
            "This report is read-only: it does not relabel, delete, or rewrite source rows."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit for contradictory labels on identical text.")
    parser.add_argument("--csv", type=Path, default=Path("datasets/raw/external/slabs_prompt_injection/train.csv"))
    parser.add_argument("--output", type=Path, default=Path("datasets/audit/SLABS_CONFLICTING_LABELS.json"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root.resolve()
    csv_path = args.csv if args.csv.is_absolute() else root / args.csv
    output_path = args.output if args.output.is_absolute() else root / args.output
    result = audit_conflicts(csv_path, repo_root=root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "rows_read": result["rows_read"],
        "conflicting_text_count": result["conflicting_text_count"],
        "training_eligible": result["training_eligible"],
        "output": str(output_path),
    }, indent=2))
    return 0 if not result["conflicts"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
