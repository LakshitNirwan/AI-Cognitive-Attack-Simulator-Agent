from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--transformer-report",
        type=Path,
        default=Path("ml/artifacts/security_detector_v0_1/evaluation/report.json"),
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=Path("ml/artifacts/security_detector_v0_1/baseline/report.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/artifacts/security_detector_v0_1/model_comparison.json"),
    )
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    args = parse_args()
    root = args.repo_root.resolve()
    transformer = load(resolve(root, args.transformer_report))
    baseline = load(resolve(root, args.baseline_report))

    comparison = {
        "experiment": transformer.get("experiment"),
        "test": {
            "tfidf_logistic_regression": baseline["test"],
            "modernbert": transformer["test"],
        },
        "differences_modernbert_minus_tfidf": {},
    }
    for key in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "average_precision",
        "false_positive_rate",
        "false_negative_rate",
    ]:
        comparison["differences_modernbert_minus_tfidf"][key] = (
            transformer["test"][key] - baseline["test"][key]
        )

    output = resolve(root, args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(comparison, handle, indent=2)

    print("AICAS model comparison complete.")
    for model_name, result in comparison["test"].items():
        print(
            f"{model_name}: accuracy={result['accuracy']:.6f} "
            f"precision={result['precision']:.6f} "
            f"recall={result['recall']:.6f} "
            f"f1={result['f1']:.6f} "
            f"average_precision={result['average_precision']:.6f} "
            f"fpr={result['false_positive_rate']:.6f}"
        )
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
