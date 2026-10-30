import json
from pathlib import Path

import pytest

from ml.training_preflight import validate_inputs, main


ROOT = Path(__file__).resolve().parents[2]


def test_preflight_validates_prepared_training_data():
    result = validate_inputs(ROOT, Path("ml/configs/security_detector_v0_1.yaml"))
    assert result["task"] == "jailbreakbench_behavior_classification"
    assert result["train_rows"] == 120
    assert result["train_label_counts"] == {"0": 60, "1": 60}
    assert result["model_revision"] == "8949b909ec900327062f0ebf497f51aef5e6f0c8"
    assert result["raw_source_unchanged_by_this_check"] is True


def test_preflight_rejects_missing_config(tmp_path):
    with pytest.raises(FileNotFoundError, match="Training config not found"):
        validate_inputs(tmp_path, Path("missing.yaml"))


def test_check_only_writes_report_without_training(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sys.argv",
        ["training_preflight.py", "--repo-root", str(ROOT), "--check-only", "--report", str(tmp_path / "report.json")],
    )
    assert main() == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "INPUTS_VALIDATED_MODEL_NOT_TESTED"
    assert report["training_completed"] is False
    assert report["s_labs_used"] is False


def test_smoke_reports_missing_transformer_dependencies(monkeypatch, tmp_path):
    # The test should be deterministic even on machines that happen to have Transformers.
    import ml.training_preflight as preflight
    original = preflight.importlib.util.find_spec
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda name: None if name == "transformers" else original(name))
    with pytest.raises(RuntimeError, match="Missing transformer runtime dependencies"):
        preflight.run_smoke(ROOT, Path("ml/configs/security_detector_v0_1.yaml"), True)
