from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

PINNED_REVISION = "002a9dd"
UPSTREAM_URL = (
    "https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/"
    f"resolve/{PINNED_REVISION}/data/train.csv"
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def audit_csv_bytes(payload: bytes) -> dict:
    frame = pd.read_csv(__import__("io").BytesIO(payload))
    if not {"text", "label"}.issubset(frame.columns):
        raise ValueError(f"Expected text,label columns; found {list(frame.columns)}")
    groups: dict[str, set[int]] = {}
    for text, label in zip(frame["text"], frame["label"]):
        if pd.isna(text) or pd.isna(label):
            continue
        normalized = " ".join(str(text).strip().lower().split())
        if normalized:
            groups.setdefault(normalized, set()).add(int(label))
    conflicts = [
        {"normalized_text_sha256": hashlib.sha256(t.encode("utf-8")).hexdigest(),
         "labels": sorted(labels)}
        for t, labels in groups.items() if len(labels) > 1
    ]
    return {
        "sha256": sha256_bytes(payload),
        "rows": int(len(frame)),
        "conflicting_normalized_text_count": len(conflicts),
        "conflicts": conflicts,
    }


def compare_pinned_source(local_bytes: bytes, upstream_bytes: bytes) -> dict:
    local = audit_csv_bytes(local_bytes)
    upstream = audit_csv_bytes(upstream_bytes)
    same_bytes = local["sha256"] == upstream["sha256"]
    same_conflict_fingerprints = sorted(
        (x["normalized_text_sha256"], tuple(x["labels"])) for x in local["conflicts"]
    ) == sorted(
        (x["normalized_text_sha256"], tuple(x["labels"])) for x in upstream["conflicts"]
    )
    if not same_bytes:
        status = "PINNED_SOURCE_BYTES_DIFFER"
    elif upstream["conflicting_normalized_text_count"]:
        status = "PINNED_SOURCE_HAS_CONFLICTS"
    else:
        status = "PINNED_SOURCE_MATCHES_AND_NO_CONFLICTS"
    return {
        "audit_type": "pinned_upstream_bytes_and_conflict_verification",
        "revision": PINNED_REVISION,
        "upstream_url": UPSTREAM_URL,
        "status": status,
        "training_eligible": False,
        "byte_identical": same_bytes,
        "same_conflict_fingerprints": same_conflict_fingerprints,
        "local": local,
        "upstream": upstream,
        "decision_note": (
            "This check verifies byte identity and contradiction fingerprints only. "
            "Even if upstream bytes match, a conflicting-label source remains blocked. "
            "This script never modifies either source file."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare local S-Labs train.csv with the exact pinned upstream revision."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--local", type=Path, default=Path(
        "datasets/raw/external/slabs_prompt_injection/train.csv"
    ))
    parser.add_argument("--output", type=Path, default=Path(
        "datasets/audit/SLABS_PINNED_UPSTREAM_VERIFICATION.json"
    ))
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    local_path = args.local if args.local.is_absolute() else root / args.local
    output_path = args.output if args.output.is_absolute() else root / args.output

    request = Request(UPSTREAM_URL, headers={"User-Agent": "AICAS-dataset-audit/0.9"})
    try:
        with urlopen(request, timeout=args.timeout) as response:
            upstream_bytes = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        result = {
            "audit_type": "pinned_upstream_bytes_and_conflict_verification",
            "revision": PINNED_REVISION,
            "upstream_url": UPSTREAM_URL,
            "status": "UPSTREAM_FETCH_FAILED",
            "training_eligible": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "decision_note": "Network or upstream failure is not evidence of source integrity; source remains blocked.",
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 3

    result = compare_pinned_source(local_path.read_bytes(), upstream_bytes)
    result["local_file"] = str(local_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "byte_identical": result["byte_identical"],
        "local_sha256": result["local"]["sha256"],
        "upstream_sha256": result["upstream"]["sha256"],
        "local_conflicts": result["local"]["conflicting_normalized_text_count"],
        "upstream_conflicts": result["upstream"]["conflicting_normalized_text_count"],
        "training_eligible": False,
        "output": str(output_path),
    }, indent=2))
    return 0 if result["byte_identical"] and result["upstream"]["conflicting_normalized_text_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
