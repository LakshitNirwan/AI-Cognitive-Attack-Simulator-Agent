import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_slabs_manifest_is_explicit_and_blocked_until_source_quality_resolved():
    path = ROOT / "datasets" / "external" / "slabs_source_manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["license"] == "MIT"
    assert data["expected_splits"] == {"train": 11089, "validation": 2101, "test": 2101}
    assert data["status"] == "blocked_conflicting_labels_pinned_upstream_verified"
    assert data["training_eligible"] is False


def test_slabs_acquisition_script_contains_hash_and_overlap_checks():
    path = ROOT / "datasets" / "external" / "acquire_slabs_prompt_injection.py"
    source = path.read_text(encoding="utf-8")
    assert "sha256" in source
    assert "cross_split_exact_text_overlap" in source
    assert "PASS_LOCAL_SOURCE_AUDIT" in source
    assert "conflicting_label_texts" in source
    assert "Within-split duplicate texts are reported" in source
