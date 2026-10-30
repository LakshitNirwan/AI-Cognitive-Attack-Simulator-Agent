from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize(text: Any) -> str:
    """Conservative normalization for exact/near duplicate discovery."""
    value = str(text).strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_column(path: Path, candidates: list[str]) -> tuple[list[str], str]:
    frame = pd.read_csv(path)
    lower_to_original = {str(c).strip().lower(): str(c) for c in frame.columns}
    chosen = next((lower_to_original[c.lower()] for c in candidates if c.lower() in lower_to_original), None)
    if chosen is None:
        raise ValueError(
            f"{path}: none of expected text columns found {candidates}; "
            f"available columns={list(frame.columns)}"
        )
    values = [normalize(v) for v in frame[chosen].dropna().tolist()]
    values = [v for v in values if v]
    return values, chosen


def pair_records(left: list[str], right: list[str], threshold: float, top_k: int) -> list[dict[str, Any]]:
    """Return top TF-IDF cosine matches for each left text above threshold."""
    if not left or not right:
        return []
    combined = left + right
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        lowercase=False,
        min_df=1,
        dtype="float32",
    )
    matrix = vectorizer.fit_transform(combined)
    left_matrix = matrix[:len(left)]
    right_matrix = matrix[len(left):]
    # Avoid constructing a dense N x M matrix; process in small row batches.
    output: list[dict[str, Any]] = []
    batch_size = 64
    for start in range(0, len(left), batch_size):
        similarities = cosine_similarity(left_matrix[start:start + batch_size], right_matrix, dense_output=True)
        for offset, row in enumerate(similarities):
            idx = start + offset
            if len(row) == 0:
                continue
            ranked = sorted(range(len(row)), key=lambda j: float(row[j]), reverse=True)
            emitted = 0
            for j in ranked:
                score = float(row[j])
                if score < threshold:
                    break
                if left[idx] == right[j]:
                    # Exact normalized matches are covered by the exact audit.
                    continue
                output.append({
                    "left_index": idx,
                    "right_index": j,
                    "similarity": round(score, 6),
                    "left_text_sha256": sha256_text(left[idx]),
                    "right_text_sha256": sha256_text(right[j]),
                    "left_preview": left[idx][:180],
                    "right_preview": right[j][:180],
                })
                emitted += 1
                if emitted >= top_k:
                    break
    return output


def exact_overlaps(left: list[str], right: list[str]) -> dict[str, Any]:
    left_set = {normalize(x) for x in left}
    right_set = {normalize(x) for x in right}
    shared = sorted(left_set & right_set)
    return {
        "count": len(shared),
        "text_sha256": [sha256_text(x) for x in shared],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AICAS cross-source exact and TF-IDF near-duplicate audit. Does not edit raw data."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--slabs", type=Path, default=Path("datasets/raw/external/slabs_prompt_injection/train.csv"))
    parser.add_argument("--jailbreakbench", type=Path, default=Path("datasets/jailbreak/processed/jailbreakbench_master.csv"))
    parser.add_argument("--harmbench", type=Path, default=Path("datasets/benchmark/harmbench/processed/harmbench_behaviors_master.csv"))
    parser.add_argument("--threshold", type=float, default=0.82)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("datasets/audit/SLABS_NEAR_DUPLICATE_AUDIT.json"))
    args = parser.parse_args()
    if not 0.0 < args.threshold <= 1.0:
        parser.error("--threshold must be in (0, 1]")
    if args.top_k < 1:
        parser.error("--top-k must be >= 1")

    root = args.repo_root.resolve()
    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else root / path

    slabs_path, jb_path, hb_path = map(resolve, (args.slabs, args.jailbreakbench, args.harmbench))
    for path in (slabs_path, jb_path, hb_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Required input missing: {path}\n"
                "Pass the correct path with --slabs, --jailbreakbench, or --harmbench."
            )

    slabs, slabs_col = load_column(slabs_path, ["text"])
    jb, jb_col = load_column(jb_path, ["goal", "behavior", "text", "prompt"])
    hb, hb_col = load_column(hb_path, ["behavior", "goal", "text", "prompt"])

    result = {
        "audit_type": "exact_and_tfidf_char_ngram_near_duplicate_discovery",
        "status": "REVIEW_REQUIRED",
        "training_eligible": False,
        "threshold": args.threshold,
        "method": "character n-gram TF-IDF (3-5) cosine similarity; candidate discovery only",
        "input_files": {
            "slabs": str(slabs_path.relative_to(root)) if slabs_path.is_relative_to(root) else str(slabs_path),
            "jailbreakbench": str(jb_path.relative_to(root)) if jb_path.is_relative_to(root) else str(jb_path),
            "harmbench": str(hb_path.relative_to(root)) if hb_path.is_relative_to(root) else str(hb_path),
        },
        "input_columns": {"slabs": slabs_col, "jailbreakbench": jb_col, "harmbench": hb_col},
        "row_counts_after_empty_removal": {"slabs": len(slabs), "jailbreakbench": len(jb), "harmbench": len(hb)},
        "pairs": {},
        "decision_note": (
            "Similarity scores are candidate signals, not proof of leakage. Review matches manually. "
            "This report does not approve S-Labs for training and does not change any source file."
        ),
    }

    for name, other in (("jailbreakbench", jb), ("harmbench", hb)):
        exact = exact_overlaps(slabs, other)
        near = pair_records(slabs, other, args.threshold, args.top_k)
        result["pairs"][name] = {
            "exact_normalized_overlap": exact,
            "near_duplicate_candidate_count": len(near),
            "near_duplicate_candidates": near,
        }

    output_path = resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "threshold": result["threshold"],
        "row_counts": result["row_counts_after_empty_removal"],
        "results": {
            name: {
                "exact_overlap": details["exact_normalized_overlap"]["count"],
                "near_duplicate_candidates": details["near_duplicate_candidate_count"],
            }
            for name, details in result["pairs"].items()
        },
        "report": str(output_path),
        "note": result["decision_note"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
