import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "datasets" / "audit" / "audit_slabs_conflicting_labels.py"


def load_module():
    spec = importlib.util.spec_from_file_location("aicas_conflicting_labels", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conflicting_labels_are_reported_without_cleaning(tmp_path):
    import pandas as pd

    source = tmp_path / "tiny.csv"
    pd.DataFrame([
        {"text": " Same   prompt ", "label": 0},
        {"text": "same prompt", "label": 1},
        {"text": "different prompt", "label": 0},
    ]).to_csv(source, index=False)
    before = source.read_bytes()
    result = load_module().audit_conflicts(source)
    assert result["status"] == "BLOCKED_CONFLICTS_FOUND"
    assert result["training_eligible"] is False
    assert result["conflicting_text_count"] == 1
    assert result["conflicts"][0]["labels"] == [0, 1]
    assert [x["csv_row_one_based_with_header"] for x in result["conflicts"][0]["occurrences"]] == [2, 3]
    assert source.read_bytes() == before


def test_no_conflicts_passes(tmp_path):
    import pandas as pd

    source = tmp_path / "clean.csv"
    pd.DataFrame([
        {"text": "first", "label": 0},
        {"text": "second", "label": 1},
    ]).to_csv(source, index=False)
    result = load_module().audit_conflicts(source)
    assert result["status"] == "PASS_NO_CONFLICTS_FOUND"
    assert result["training_eligible"] is True


def test_repo_input_path_is_portable_and_hash_is_preserved(tmp_path):
    import pandas as pd

    root = tmp_path / "project"
    source = root / "datasets" / "raw" / "sample.csv"
    source.parent.mkdir(parents=True)
    pd.DataFrame([{"text": "prompt", "label": 0}]).to_csv(source, index=False)
    before = source.read_bytes()
    result = load_module().audit_conflicts(source, repo_root=root)
    import hashlib

    assert result["input_file"] == "datasets/raw/sample.csv"
    assert result["input_file_sha256"] == hashlib.sha256(before).hexdigest()
    assert source.read_bytes() == before
