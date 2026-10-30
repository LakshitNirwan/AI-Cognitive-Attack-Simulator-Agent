import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "datasets" / "external" / "acquire_slabs_prompt_injection.py"


def load_module():
    spec = importlib.util.spec_from_file_location("aicas_slabs_acquire", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conflicting_duplicate_is_reported_with_hash_and_rows(tmp_path):
    module = load_module()
    path = tmp_path / "train.csv"
    path.write_text(
        'text,label\n"same text",0\n"same text",1\n"other",0\n',
        encoding="utf-8",
    )
    audit = module.audit_split(path)
    assert audit["conflicting_label_texts"] == 1
    assert audit["conflicts"][0]["labels"] == [0, 1]
    assert audit["conflicts"][0]["row_numbers"] == [2, 3]
    assert len(audit["conflicts"][0]["text_sha256"]) == 64
