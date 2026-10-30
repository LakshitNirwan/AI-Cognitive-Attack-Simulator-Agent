import json
from pathlib import Path

import numpy as np

from ml.evaluate import (
    metric_uncertainty_95,
    metrics_at_threshold,
    select_best,
    threshold_sweep,
    wilson_interval,
)


def test_threshold_metrics_are_consistent():
    labels = np.asarray([0, 0, 1, 1])
    probabilities = np.asarray([0.10, 0.80, 0.70, 0.90])
    result = metrics_at_threshold(labels, probabilities, 0.50)

    assert result["confusion_matrix"] == [[1, 1], [0, 2]]
    assert result["recall"] == 1.0
    assert result["false_negative_rate"] == 0.0


def test_threshold_sweep_contains_requested_range():
    labels = np.asarray([0, 1])
    probabilities = np.asarray([0.2, 0.8])
    results = threshold_sweep(labels, probabilities, 0.10, 0.90, 0.10)

    assert len(results) == 9
    assert results[0]["threshold"] == 0.10
    assert results[-1]["threshold"] == 0.90


def test_best_threshold_uses_f1():
    results = [
        {"threshold": 0.4, "f1": 0.6, "recall": 1.0, "false_positive_rate": 0.5},
        {"threshold": 0.5, "f1": 0.8, "recall": 0.9, "false_positive_rate": 0.2},
    ]
    assert select_best(results, "f1")["threshold"] == 0.5


def test_wilson_interval_reports_small_sample_uncertainty():
    interval = wilson_interval(2, 2)
    assert interval[0] < 1.0
    assert interval[1] == 1.0
    assert wilson_interval(0, 0) is None


def test_metric_uncertainty_uses_fixed_threshold_and_class_denominators():
    labels = np.asarray([0, 0, 1, 1])
    probabilities = np.asarray([0.1, 0.8, 0.7, 0.9])
    result = metric_uncertainty_95(labels, probabilities, 0.5)
    assert result["precision"]["successes"] == 2
    assert result["precision"]["trials"] == 3
    assert result["recall"]["trials"] == 2
    assert result["false_positive_rate"]["successes"] == 1
    assert result["false_positive_rate"]["trials"] == 2


def test_evaluate_uses_local_string_model_path():
    evaluate_path = Path(__file__).resolve().parents[1] / "evaluate.py"
    source = evaluate_path.read_text(encoding="utf-8")
    assert 'model_path = str(model_dir)' in source
    assert 'local_files_only=True' in source


def test_final_test_split_is_not_used_for_threshold_selection():
    evaluate_path = Path(__file__).resolve().parents[1] / "evaluate.py"
    source = evaluate_path.read_text(encoding="utf-8")
    assert "threshold_sweep(test_labels" not in source
    assert '"final_test_used_for_threshold_selection": False' in source
    assert '"test_points"' not in source
