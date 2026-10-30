from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from pathlib import Path

EXPECTED = {"train": 11089, "validation": 2101, "test": 2101}
URLS = {
    "train": "https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/resolve/main/data/train.csv",
    "validation": "https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/resolve/main/data/validation.csv",
    "test": "https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/resolve/main/data/test.csv",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "AICAS-dataset-acquisition/0.6"})
    with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def audit_split(path: Path) -> dict:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["text", "label"]:
            raise ValueError(f"{path}: expected columns ['text', 'label'], got {reader.fieldnames}")
        for row_number, row in enumerate(reader, start=2):
            text = row["text"]
            label = row["label"]
            if not text or not text.strip():
                raise ValueError(f"{path}: empty text found at CSV row {row_number}")
            if label not in {"0", "1"}:
                raise ValueError(f"{path}: invalid label {label!r} at CSV row {row_number}")
            rows.append((text.strip(), int(label), row_number))

    label_by_text = {}
    locations_by_text = {}
    for text, label, row_number in rows:
        label_by_text.setdefault(text, set()).add(label)
        locations_by_text.setdefault(text, []).append((row_number, label))

    conflicts = []
    for text, label_set in label_by_text.items():
        if len(label_set) > 1:
            conflicts.append(
                {
                    "text_sha256": text_hash(text),
                    "labels": sorted(label_set),
                    "row_numbers": [r for r, _ in locations_by_text[text]],
                    "occurrences": len(locations_by_text[text]),
                }
            )

    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]
    return {
        "rows": len(rows),
        "label_counts": {
            "benign": sum(x == 0 for x in labels),
            "injection": sum(x == 1 for x in labels),
        },
        "duplicate_texts": len(texts) - len(set(texts)),
        "unique_texts": len(set(texts)),
        "conflicting_label_texts": len(conflicts),
        "conflicts": conflicts,
        "texts": texts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root.resolve()

    raw = root / "datasets" / "raw" / "external" / "slabs_prompt_injection"
    raw.mkdir(parents=True, exist_ok=True)
    report_path = raw / "provenance_manifest.json"

    report = {
        "dataset": "S-Labs/prompt-injection-dataset",
        "upstream_revision": "002a9dd",
        "source_url": "https://huggingface.co/datasets/S-Labs/prompt-injection-dataset",
        "license": "MIT",
        "training_eligible": False,
        "status": "ACQUISITION_AUDIT_BLOCKED",
        "splits": {},
        "cross_split_exact_text_overlap": None,
        "duplicate_policy": (
            "Within-split duplicate texts are reported but not automatically rejected. "
            "Conflicting labels for identical text are rejected. Exact text overlap across "
            "train/validation/test is rejected as leakage."
        ),
        "raw_data_policy": "Raw downloaded source files are never modified by the audit.",
    }

    split_audits = {}
    try:
        for split, url in URLS.items():
            path = raw / f"{split}.csv"
            print(f"Downloading {split}: {url}")
            download(url, path)
            audit = audit_split(path)
            split_audits[split] = audit

            report["splits"][split] = {
                "rows": audit["rows"],
                "expected_rows": EXPECTED[split],
                "unique_texts": audit["unique_texts"],
                "duplicate_texts": audit["duplicate_texts"],
                "conflicting_label_texts": audit["conflicting_label_texts"],
                "conflicts": audit["conflicts"],
                "label_counts": audit["label_counts"],
                "sha256": sha256(path),
                "filename": str(path.relative_to(root)),
            }

            if audit["rows"] != EXPECTED[split]:
                raise ValueError(
                    f"{split}: expected {EXPECTED[split]} rows, received {audit['rows']}"
                )

            if audit["conflicting_label_texts"]:
                raise ValueError(
                    f"{split}: identical text appears with conflicting labels "
                    f"({audit['conflicting_label_texts']} texts)"
                )

        for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
            overlap = set(split_audits[a]["texts"]) & set(split_audits[b]["texts"])
            if overlap:
                report["cross_split_exact_text_overlap"] = {
                    "status": "BLOCKED",
                    "pairs": {f"{a}:{b}": len(overlap)},
                }
                raise ValueError(f"Exact text overlap between {a} and {b}: {len(overlap)}")

        report["cross_split_exact_text_overlap"] = {"status": "PASS", "count": 0}
        report["training_eligible"] = True
        report["status"] = "PASS_LOCAL_SOURCE_AUDIT"

    except Exception as exc:
        report["status"] = "ACQUISITION_AUDIT_BLOCKED"
        report["training_eligible"] = False
        report["failure"] = str(exc)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("AICAS S-Labs acquisition/audit BLOCKED.")
        print(f"Reason: {exc}")
        print(f"Audit manifest: {report_path}")
        return 2

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AICAS S-Labs acquisition/audit completed.")
    print("Status: PASS_LOCAL_SOURCE_AUDIT")
    print(f"Manifest: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
