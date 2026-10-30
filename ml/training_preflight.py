"""Validate the configured training inputs and optionally run one transformer update.

This utility never modifies raw datasets. The full smoke test may download the
pinned model revision unless --local-files-only is supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REQUIRED_RUNTIME_MODULES = ("torch", "transformers", "accelerate", "safetensors", "numpy")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            rows.append(row)
    return rows


def validate_inputs(repo_root: Path, config_path: Path) -> dict[str, Any]:
    config_file = config_path if config_path.is_absolute() else repo_root / config_path
    if not config_file.is_file():
        raise FileNotFoundError(f"Training config not found: {config_file}")
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Training config must be a YAML mapping")

    required = ("experiment", "data", "model", "training", "paths")
    missing = [key for key in required if not isinstance(config.get(key), dict)]
    if missing:
        raise ValueError(f"Missing configuration sections: {missing}")
    model = config["model"]
    for key in ("name", "revision", "max_length", "num_labels"):
        if model.get(key) in (None, ""):
            raise ValueError(f"Missing model configuration: model.{key}")
    if int(model["num_labels"]) != 2:
        raise ValueError("This preflight currently expects the configured binary classifier")
    if int(model["max_length"]) < 8:
        raise ValueError("model.max_length must be at least 8")

    dataset_dir = repo_root / config["paths"]["dataset_artifacts"]
    train_path = dataset_dir / "train.jsonl"
    manifest_path = dataset_dir / "manifest.json"
    if not train_path.is_file():
        raise FileNotFoundError(f"Prepared training split not found: {train_path}. Run ml/data/build_dataset.py first.")
    rows = read_jsonl(train_path)
    if not rows:
        raise ValueError("Prepared training split is empty")
    for index, row in enumerate(rows):
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError(f"Training row {index} has missing/empty text")
        if row.get("label") not in (0, 1):
            raise ValueError(f"Training row {index} has label outside binary classes 0/1")
    label_counts = {str(label): sum(row["label"] == label for row in rows) for label in (0, 1)}
    if any(count == 0 for count in label_counts.values()):
        raise ValueError(f"Training split must contain both labels; counts={label_counts}")

    manifest_info: dict[str, Any] = {"exists": manifest_path.is_file()}
    if manifest_path.is_file():
        manifest_info["sha256"] = sha256_file(manifest_path)
    source = repo_root / config["data"]["source"]
    return {
        "config_path": str(config_file),
        "config_sha256": sha256_file(config_file),
        "task": config["experiment"].get("task"),
        "model_name": model["name"],
        "model_revision": str(model["revision"]),
        "max_length_configured": int(model["max_length"]),
        "num_labels": int(model["num_labels"]),
        "train_path": str(train_path),
        "train_sha256": sha256_file(train_path),
        "train_rows": len(rows),
        "train_label_counts": label_counts,
        "dataset_manifest": manifest_info,
        "source_path": str(source),
        "source_exists": source.is_file(),
        "raw_source_unchanged_by_this_check": True,
    }


def run_smoke(repo_root: Path, config_path: Path, local_files_only: bool) -> dict[str, Any]:
    # Dependency presence is checked before importing optional runtime packages.
    missing = [name for name in REQUIRED_RUNTIME_MODULES if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError(f"Missing transformer runtime dependencies: {missing}. Install ml/requirements.txt.")

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    config_file = config_path if config_path.is_absolute() else repo_root / config_path
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    model_cfg = config["model"]
    dataset_path = repo_root / config["paths"]["dataset_artifacts"] / "train.jsonl"
    rows = read_jsonl(dataset_path)
    sample = next((row for row in rows if str(row.get("text", "")).strip()), None)
    if sample is None:
        raise ValueError("No non-empty training text is available for smoke test")

    load_kwargs: dict[str, Any] = {"revision": str(model_cfg["revision"])}
    if local_files_only:
        load_kwargs["local_files_only"] = True
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["name"], **load_kwargs)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_cfg["name"],
        num_labels=int(model_cfg["num_labels"]),
        id2label={0: "benign", 1: "harmful"},
        label2id={"benign": 0, "harmful": 1},
        **load_kwargs,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.train()
    encoded = tokenizer(
        [sample["text"]],
        truncation=True,
        max_length=min(int(model_cfg["max_length"]), 128),
        padding=True,
        return_tensors="pt",
    )
    encoded = {key: value.to(device) for key, value in encoded.items()}
    encoded["labels"] = torch.tensor([int(sample["label"])], dtype=torch.long, device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config["training"]["learning_rate"]))
    optimizer.zero_grad(set_to_none=True)
    outputs = model(**encoded)
    if outputs.loss is None or not torch.isfinite(outputs.loss):
        raise RuntimeError("Model returned a missing or non-finite loss")
    outputs.loss.backward()
    grad_count = sum(1 for param in model.parameters() if param.grad is not None)
    if grad_count == 0:
        raise RuntimeError("Backward pass produced no parameter gradients")
    torch.nn.utils.clip_grad_norm_(model.parameters(), float(config["training"]["gradient_clip_norm"]))
    optimizer.step()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return {
        "status": "PASSED",
        "device": str(device),
        "torch_version": torch.__version__,
        "transformers_version": __import__("transformers").__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "sample_label": int(sample["label"]),
        "sample_token_count": int(encoded["input_ids"].shape[1]),
        "loss": float(outputs.loss.detach().cpu()),
        "parameters_with_gradients": grad_count,
        "optimizer_step_completed": True,
        "model_name": model_cfg["name"],
        "model_revision": str(model_cfg["revision"]),
        "local_files_only": local_files_only,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("ml/configs/security_detector_v0_1.yaml"))
    parser.add_argument("--check-only", action="store_true", help="Validate config and prepared data without loading the model")
    parser.add_argument("--local-files-only", action="store_true", help="Do not download model files; require pinned revision in local cache")
    parser.add_argument("--report", type=Path, default=Path("ml/artifacts/security_detector_v0_1/preflight_report.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report_path = args.report if args.report.is_absolute() else repo_root / args.report
    report: dict[str, Any] = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "mode": "check_only" if args.check_only else "forward_backward_smoke_test",
        "training_completed": False,
        "s_labs_used": False,
    }
    exit_code = 0
    try:
        report["inputs"] = validate_inputs(repo_root, args.config)
        report["input_validation_status"] = "PASSED"
        if args.check_only:
            report["status"] = "INPUTS_VALIDATED_MODEL_NOT_TESTED"
        else:
            report["runtime_smoke_test"] = run_smoke(repo_root, args.config, args.local_files_only)
            report["status"] = "PASSED"
    except Exception as exc:
        report["status"] = "BLOCKED"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        exit_code = 2
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report.get(key) for key in ("status", "input_validation_status", "error_type", "error", "training_completed", "s_labs_used")}, indent=2))
    print(f"Report: {report_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
