from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

try:
    from ml.evaluate import metrics_at_threshold, metric_uncertainty_95, threshold_sweep, select_best
except ModuleNotFoundError:
    from evaluate import metrics_at_threshold, metric_uncertainty_95, threshold_sweep, select_best


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--config", type=Path, default=Path("ml/configs/security_detector_v0_1.yaml")
    )
    return parser.parse_args()


def load_config(repo_root: Path, config_path: Path) -> dict:
    path = config_path if config_path.is_absolute() else repo_root / config_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config = load_config(repo_root, args.config)
    dataset_dir = repo_root / config["paths"]["dataset_artifacts"]
    output_dir = repo_root / config["paths"].get(
        "baseline_artifacts", "ml/artifacts/security_detector_v0_1/baseline"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    train = load_jsonl(dataset_dir / "train.jsonl")
    validation = load_jsonl(dataset_dir / "validation.jsonl")
    test = load_jsonl(dataset_dir / "test.jsonl")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    x_train = vectorizer.fit_transform([row["text"] for row in train])
    x_val = vectorizer.transform([row["text"] for row in validation])
    x_test = vectorizer.transform([row["text"] for row in test])

    classifier = LogisticRegression(
        max_iter=2000,
        random_state=int(config["experiment"]["seed"]),
        solver="liblinear",
    )
    classifier.fit(x_train, [row["label"] for row in train])

    val_labels = np.asarray([row["label"] for row in validation])
    test_labels = np.asarray([row["label"] for row in test])
    val_probs = classifier.predict_proba(x_val)[:, 1]
    test_probs = classifier.predict_proba(x_test)[:, 1]

    val_results = threshold_sweep(
        val_labels,
        val_probs,
        config["threshold"]["minimum"],
        config["threshold"]["maximum"],
        config["threshold"]["step"],
    )
    best_validation = select_best(
        val_results, config["threshold"].get("selection_metric", "f1")
    )
    test_results = metrics_at_threshold(
        test_labels, test_probs, best_validation["threshold"]
    )
    dataset_manifest_path = dataset_dir / "manifest.json"
    dataset_manifest_sha256 = hashlib.sha256(dataset_manifest_path.read_bytes()).hexdigest()

    report = {
        "experiment": config["experiment"],
        "evaluation_protocol": {
            "threshold_selection_split": "validation",
            "final_test_used_for_threshold_selection": False,
            "dataset_manifest_path": dataset_manifest_path.relative_to(repo_root).as_posix(),
            "dataset_manifest_sha256": dataset_manifest_sha256,
            "final_test_rows": len(test),
        },
        "model": {
            "type": "tfidf_logistic_regression",
            "vectorizer": {
                "ngram_range": [1, 2],
                "sublinear_tf": True,
                "strip_accents": "unicode",
            },
            "classifier": {
                "solver": "liblinear",
                "max_iter": 2000,
                "random_state": int(config["experiment"]["seed"]),
            },
        },
        "split_sizes": {
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "validation_threshold_selection": best_validation,
        "test": test_results,
        "test_metric_uncertainty_95": metric_uncertainty_95(
            test_labels, test_probs, best_validation["threshold"]
        ),
        "feature_count": int(x_train.shape[1]),
        "test_average_precision": float(average_precision_score(test_labels, test_probs)),
    }

    with (output_dir / "report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    with (output_dir / "thresholds_validation.json").open("w", encoding="utf-8") as handle:
        json.dump(val_results, handle, indent=2)

    # Persist only lightweight model metadata by default. The model itself can be
    # reproduced from the deterministic split and these parameters.
    with (output_dir / "config.json").open("w", encoding="utf-8") as handle:
        json.dump(report["model"], handle, indent=2)

    print("AICAS TF-IDF baseline evaluation complete.")
    print(f"features: {x_train.shape[1]}")
    print(f"Selected validation threshold: {best_validation['threshold']:.2f}")
    print("TEST")
    for key in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "average_precision",
        "false_positive_rate",
        "false_negative_rate",
    ]:
        print(f"{key}: {test_results[key]:.6f}")
    print(f"confusion_matrix: {test_results['confusion_matrix']}")
    print(f"Report: {output_dir / 'report.json'}")


if __name__ == "__main__":
    main()
