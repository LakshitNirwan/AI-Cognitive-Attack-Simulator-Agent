from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
try:
    import torch
    from torch.utils.data import DataLoader, Dataset
except ModuleNotFoundError:  # Metric helpers are usable without transformer extras.
    torch = None
    DataLoader = None
    Dataset = object

_no_grad = torch.no_grad if torch is not None else (lambda function: function)


class JsonlTextDataset(Dataset):
    def __init__(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            self.rows = [json.loads(line) for line in handle if line.strip()]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("ml/configs/security_detector_v0_1.yaml"),
    )
    return parser.parse_args()


def load_config(repo_root, config_path):
    path = config_path if config_path.is_absolute() else repo_root / config_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@_no_grad
def predict(model, tokenizer, dataset, batch_size, max_length, device):
    if torch is None:
        raise RuntimeError("Transformer prediction requires the optional PyTorch dependency.")
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    labels = []
    probabilities = []

    model.eval()

    for rows in loader:
        texts = rows["text"]
        encoded = tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        logits = model(**encoded).logits
        probs = torch.softmax(logits, dim=-1)[:, 1]

        labels.extend(rows["label"].numpy().tolist())
        probabilities.extend(probs.cpu().numpy().tolist())

    return np.asarray(labels), np.asarray(probabilities)


def metrics_at_threshold(labels, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(
        labels, predictions, labels=[0, 1]
    ).ravel()

    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "average_precision": float(average_precision_score(labels, probabilities)),
        "false_positive_rate": float(fp / max(fp + tn, 1)),
        "false_negative_rate": float(fn / max(fn + tp, 1)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def wilson_interval(successes, trials, z=1.959963984540054):
    """Return a two-sided Wilson score interval for a binomial proportion."""
    successes = int(successes)
    trials = int(trials)
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("Expected 0 <= successes <= trials.")
    if trials == 0:
        return None
    proportion = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (proportion + z2 / (2.0 * trials)) / denominator
    margin = (
        z
        * np.sqrt(proportion * (1.0 - proportion) / trials + z2 / (4.0 * trials * trials))
        / denominator
    )
    return [float(max(0.0, center - margin)), float(min(1.0, center + margin))]


def metric_uncertainty_95(labels, probabilities, threshold):
    """Wilson intervals for precision, recall and FPR at one fixed threshold."""
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "method": "95% Wilson score interval",
        "precision": {"successes": int(tp), "trials": int(tp + fp), "interval": wilson_interval(tp, tp + fp)},
        "recall": {"successes": int(tp), "trials": int(tp + fn), "interval": wilson_interval(tp, tp + fn)},
        "false_positive_rate": {"successes": int(fp), "trials": int(fp + tn), "interval": wilson_interval(fp, fp + tn)},
    }


def threshold_sweep(labels, probabilities, minimum, maximum, step):
    thresholds = np.arange(float(minimum), float(maximum) + 0.0001, float(step))
    return [
        metrics_at_threshold(labels, probabilities, float(threshold))
        for threshold in thresholds
    ]


def select_best(results, metric):
    return max(results, key=lambda result: (result[metric], result["recall"], -result["false_positive_rate"]))


def select_security_points(results):
    zero_fn = [result for result in results if result["false_negative_rate"] == 0.0]
    zero_fn_best = max(
        zero_fn,
        key=lambda result: (
            -result["false_positive_rate"],
            result["precision"],
            result["threshold"],
        ),
    ) if zero_fn else None

    low_fpr_candidates = [
        result for result in results if result["false_positive_rate"] <= 0.20
    ]
    low_fpr_best = max(
        low_fpr_candidates,
        key=lambda result: (result["recall"], result["f1"], -result["false_positive_rate"]),
    ) if low_fpr_candidates else None

    return {
        "zero_false_negative_rate_best": zero_fn_best,
        "fpr_at_or_below_0_20_best_recall": low_fpr_best,
    }


def main():
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config = load_config(repo_root, args.config)

    dataset_dir = repo_root / config["paths"]["dataset_artifacts"]
    model_dir = repo_root / config["paths"]["model_artifacts"]
    evaluation_dir = repo_root / config["paths"]["evaluation_artifacts"]
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    # Pass an explicit string path and force local loading. On some Windows
    # Transformers/Hugging Face Hub combinations, a pathlib.Path containing
    # a drive letter can be misinterpreted as a Hub repo ID.
    model_path = str(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_path,
        local_files_only=True,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    batch_size = int(config["training"]["batch_size"])
    max_length = int(config["model"]["max_length"])

    validation = JsonlTextDataset(dataset_dir / "validation.jsonl")
    test = JsonlTextDataset(dataset_dir / "test.jsonl")

    val_labels, val_probs = predict(
        model, tokenizer, validation, batch_size, max_length, device
    )
    test_labels, test_probs = predict(
        model, tokenizer, test, batch_size, max_length, device
    )

    validation_results = threshold_sweep(
        val_labels,
        val_probs,
        config["threshold"]["minimum"],
        config["threshold"]["maximum"],
        config["threshold"]["step"],
    )
    selection_metric = config["threshold"].get("selection_metric", "f1")
    best_validation = select_best(validation_results, selection_metric)
    test_results = metrics_at_threshold(
        test_labels,
        test_probs,
        best_validation["threshold"],
    )

    dataset_manifest_path = dataset_dir / "manifest.json"
    dataset_manifest_sha256 = hashlib.sha256(dataset_manifest_path.read_bytes()).hexdigest()
    report = {
        "experiment": config["experiment"],
        "model": config["model"],
        "evaluation_protocol": {
            "threshold_selection_split": "validation",
            "final_test_used_for_threshold_selection": False,
            "dataset_manifest_path": dataset_manifest_path.relative_to(repo_root).as_posix(),
            "dataset_manifest_sha256": dataset_manifest_sha256,
            "final_test_rows": len(test),
        },
        "validation_threshold_selection": best_validation,
        "test": test_results,
        "test_metric_uncertainty_95": metric_uncertainty_95(
            test_labels, test_probs, best_validation["threshold"]
        ),
        "device": str(device),
        "threshold_analysis": {
            "selection_metric": selection_metric,
            "validation_points": select_security_points(validation_results),
            "tested_minimum": float(config["threshold"]["minimum"]),
            "tested_maximum": float(config["threshold"]["maximum"]),
            "tested_step": float(config["threshold"]["step"]),
        },
    }

    with (evaluation_dir / "report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    with (evaluation_dir / "thresholds_validation.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(validation_results, handle, indent=2)

    print("AICAS transformer evaluation complete.")
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
    print("THRESHOLD ANALYSIS")
    print(
        "validation_zero_fnr_best:",
        report["threshold_analysis"]["validation_points"]["zero_false_negative_rate_best"],
    )
    print(
        "validation_fpr_le_0.20_best_recall:",
        report["threshold_analysis"]["validation_points"]["fpr_at_or_below_0_20_best_recall"],
    )
    print(f"Report: {evaluation_dir / 'report.json'}")


if __name__ == "__main__":
    main()
