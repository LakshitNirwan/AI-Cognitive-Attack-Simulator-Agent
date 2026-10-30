from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def norm(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Exact normalized S-Labs/JailbreakBench/HarmBench overlap audit.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--slabs", type=Path)
    parser.add_argument("--jailbreakbench", type=Path)
    parser.add_argument("--harmbench", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()

    slabs_path = (args.slabs or Path("datasets/raw/external/slabs_prompt_injection/train.csv"))
    jb_path = (args.jailbreakbench or Path("datasets/jailbreak/processed/jailbreakbench_master.csv"))
    hb_path = (args.harmbench or Path("datasets/benchmark/harmbench/processed/harmbench_behaviors_master.csv"))
    output_path = args.output or Path("datasets/audit/SLABS_CROSS_SOURCE_AUDIT.json")
    paths = [p if p.is_absolute() else root / p for p in (slabs_path, jb_path, hb_path)]
    slabs_file, jb_file, hb_file = paths

    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Required audit input not found: {path}")

    slabs = pd.read_csv(slabs_file)
    jb = pd.read_csv(jb_file)
    hb = pd.read_csv(hb_file)

    required_slabs = {"text", "label"}
    if not required_slabs.issubset(slabs.columns):
        raise ValueError(f"S-Labs missing columns: {sorted(required_slabs - set(slabs.columns))}")
    if "goal" not in jb.columns:
        raise ValueError("JailbreakBench requires a 'goal' column")
    if "behavior" not in hb.columns:
        raise ValueError("HarmBench requires a 'behavior' column")

    slabs_set = {norm(x) for x in slabs["text"].dropna()}
    jb_set = {norm(x) for x in jb["goal"].dropna()}
    hb_set = {norm(x) for x in hb["behavior"].dropna()}
    jb_overlap = slabs_set & jb_set
    hb_overlap = slabs_set & hb_set

    report = {
        "scope": "S-Labs train split vs JailbreakBench goals and HarmBench behaviors",
        "normalization": "strip, lowercase, collapse internal whitespace",
        "input_files": {
            "slabs": str(slabs_file.relative_to(root)) if slabs_file.is_relative_to(root) else str(slabs_file),
            "jailbreakbench": str(jb_file.relative_to(root)) if jb_file.is_relative_to(root) else str(jb_file),
            "harmbench": str(hb_file.relative_to(root)) if hb_file.is_relative_to(root) else str(hb_file),
        },
        "slabs_rows": int(len(slabs)),
        "jailbreakbench_rows": int(len(jb)),
        "harmbench_rows": int(len(hb)),
        "exact_normalized_overlap": {
            "jailbreakbench": {"count": len(jb_overlap), "text_sha256": sorted(digest(x) for x in jb_overlap)},
            "harmbench": {"count": len(hb_overlap), "text_sha256": sorted(digest(x) for x in hb_overlap)},
        },
        "status": "PASS_EXACT_NORMALIZED_NO_OVERLAP" if not jb_overlap and not hb_overlap else "REVIEW_EXACT_NORMALIZED_OVERLAP",
        "note": "Exact normalized overlap only; this is not a semantic or near-duplicate audit.",
    }

    output_path = output_path if output_path.is_absolute() else root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
