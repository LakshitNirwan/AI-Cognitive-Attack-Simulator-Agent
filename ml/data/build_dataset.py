from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import StratifiedGroupKFold

REQUIRED_COLUMNS = [
    "record_id",
    "source_dataset",
    "source_file",
    "behavior_class",
    "original_index",
    "goal",
    "target",
    "behavior",
    "category",
    "source",
]

LABELS = {"benign": 0, "harmful": 1}
TASK_DATASETS = {"jailbreakbench_behavior_classification": "JailbreakBench"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("ml/configs/security_detector_v0_1.yaml"),
    )
    return parser.parse_args()


def stable_text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalized_group_id(value: str) -> str:
    normalized = " ".join(str(value).strip().lower().split())
    return stable_text_hash(normalized)


def load_config(repo_root: Path, config_path: Path) -> dict:
    path = config_path if config_path.is_absolute() else repo_root / config_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_source(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required JailbreakBench columns: {missing}")

    if df.empty:
        raise ValueError("JailbreakBench source is empty.")

    if df["record_id"].isna().any():
        raise ValueError("record_id contains missing values.")

    if df["record_id"].duplicated().any():
        raise ValueError("record_id contains duplicates.")

    if df["goal"].isna().any():
        raise ValueError("goal contains missing values.")

    if df["goal"].astype(str).str.strip().eq("").any():
        raise ValueError("goal contains empty strings.")

    unknown = sorted(set(df["behavior_class"].astype(str)) - set(LABELS))
    if unknown:
        raise ValueError(f"Unexpected behavior_class values: {unknown}")

    normalized_goal = df["goal"].astype(str).map(
        lambda value: " ".join(value.strip().lower().split())
    )
    label_counts = df.assign(_normalized_goal=normalized_goal).groupby(
        "_normalized_goal", dropna=False
    )["behavior_class"].nunique()
    conflicts = label_counts[label_counts > 1]
    if not conflicts.empty:
        fingerprints = [stable_text_hash(text) for text in conflicts.index.tolist()]
        raise ValueError(
            "Normalized goal groups have conflicting labels; preserve and resolve "
            f"the source examples before training: {fingerprints[:10]}"
        )


def validate_training_eligibility(
    repo_root: Path,
    source_path: Path,
    source_dataset: str,
    task: str,
) -> dict:
    """Require a matching machine-readable readiness decision before training."""
    expected_dataset = TASK_DATASETS.get(task)
    if expected_dataset is None or source_dataset != expected_dataset:
        raise ValueError(
            f"Task {task!r} is not approved for source {source_dataset!r}."
        )

    report_path = repo_root / "datasets/audit/DATA_READINESS_REPORT.json"
    if not report_path.is_file():
        raise ValueError(f"Dataset readiness report is missing: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dataset = report.get("datasets", {}).get(source_dataset)
    if not dataset:
        raise ValueError(f"No readiness entry exists for {source_dataset}.")

    decision = dataset.get("decision")
    if decision not in {"APPROVED", "CONDITIONAL_TASK_SPECIFIC_USE"}:
        raise ValueError(
            f"Dataset {source_dataset} is not training eligible: {decision!r}."
        )

    artifact = dataset.get("local_artifact", {})
    expected_path = (repo_root / artifact.get("path", "")).resolve()
    actual_path = source_path.resolve()
    if not artifact.get("exists") or actual_path != expected_path:
        raise ValueError(
            f"Configured source {actual_path} does not match the readiness artifact."
        )
    actual_hash = hashlib.sha256(actual_path.read_bytes()).hexdigest()
    if actual_hash != artifact.get("sha256"):
        raise ValueError(
            f"Source hash changed since the readiness report for {source_dataset}."
        )

    component_files = []
    if source_dataset == "JailbreakBench":
        for filename in sorted({"benign-behaviors.csv", "harmful-behaviors.csv"}):
            component_path = repo_root / "datasets/jailbreak/raw" / filename
            if not component_path.is_file():
                raise ValueError(f"JailbreakBench source component is missing: {component_path}")
            component_files.append(
                {
                    "path": str(component_path.relative_to(repo_root.resolve())),
                    "sha256": hashlib.sha256(component_path.read_bytes()).hexdigest(),
                }
            )

    if source_dataset == "JailbreakBench":
        verification_path = repo_root / "datasets/audit/JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json"
        if not verification_path.is_file():
            raise ValueError(f"Pinned JailbreakBench verification is missing: {verification_path}")
        verification = json.loads(verification_path.read_text(encoding="utf-8"))
        if verification.get("status") != "PINNED_BYTES_VERIFIED" or not verification.get("byte_identical"):
            raise ValueError("JailbreakBench pinned upstream bytes are not verified.")
        upstream_components = {
            str(item.get("path", "")).replace("\\", "/"): item.get("local_sha256")
            for item in verification.get("files", [])
            if item.get("byte_identical") is True
        }
        for component in component_files:
            if upstream_components.get(component["path"].replace("\\", "/")) != component["sha256"]:
                raise ValueError("JailbreakBench component hash does not match pinned upstream verification.")
        if len(upstream_components) != len(component_files):
            raise ValueError("JailbreakBench pinned verification does not cover every raw component.")
        upstream_revision = verification.get("upstream_revision")
        if not upstream_revision or verification.get("license_declared_by_upstream_card", "").lower() != "mit":
            raise ValueError("Pinned JailbreakBench revision/license evidence is incomplete.")
    else:
        upstream_revision = None
        verification = {}

    return {
        "dataset": source_dataset,
        "decision": decision,
        "task_scope": task,
        "path": str(actual_path.relative_to(repo_root.resolve())),
        "sha256": actual_hash,
        "component_files": component_files,
        "source_revision": upstream_revision,
        "source_revision_status": "pinned_upstream_bytes_verified" if upstream_revision else "not_recorded_in_provenance",
        "upstream_license_declared": verification.get("license_declared_by_upstream_card"),
        "license_usage_status": "MIT_declared_by_upstream; retain source attribution and review before redistribution" if upstream_revision else "artifact_specific_decision_not_recorded",
    }


def split_data(
    df: pd.DataFrame, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    working = df.copy()
    working["_group_id"] = working["goal"].map(normalized_group_id)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    folds = list(
        splitter.split(
            working,
            working["behavior_class"],
            groups=working["_group_id"],
        )
    )
    test_indices = folds[0][1]
    validation_indices = folds[1][1]
    train_indices = np.concatenate([fold[1] for fold in folds[2:]])

    result = []
    for name, indices in (("train", train_indices), ("validation", validation_indices), ("test", test_indices)):
        part = working.iloc[indices].copy()
        part["group_id"] = part["_group_id"]
        part["split"] = name
        part = part.drop(columns=["_group_id"])
        result.append(part.sort_values("record_id").reset_index(drop=True))

    group_sets = [set(part["group_id"]) for part in result]
    if any(group_sets[i] & group_sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise RuntimeError("Normalized goal group overlap detected between splits.")
    return tuple(result)


def serialize(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "record_id": str(row["record_id"]),
                "source_dataset": str(row["source_dataset"]),
                "source_file": str(row["source_file"]),
                "original_index": int(row["original_index"]),
                "text": str(row["goal"]),
                "label_name": str(row["behavior_class"]),
                "label": LABELS[str(row["behavior_class"])],
                "category": str(row["category"]),
                "group_id": str(row["group_id"]),
                "split": str(row["split"]),
            }
        )
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config = load_config(repo_root, args.config)

    random.seed(config["experiment"]["seed"])
    np.random.seed(config["experiment"]["seed"])

    source_path = repo_root / config["data"]["source"]
    if not source_path.exists():
        raise FileNotFoundError(f"Source dataset not found: {source_path}")

    df = pd.read_csv(source_path)
    validate_source(df)
    source_names = set(df["source_dataset"].astype(str))
    if len(source_names) != 1:
        raise ValueError(f"Expected exactly one source dataset, found {sorted(source_names)}")
    eligibility = validate_training_eligibility(
        repo_root,
        source_path,
        source_dataset=next(iter(source_names)),
        task=str(config["experiment"]["task"]),
    )

    if config["data"]["max_rows"] is not None:
        raise ValueError(
            "max_rows is intentionally unsupported for this first reproducible "
            "dataset build; use the complete validated source."
        )

    expected_fractions = (0.60, 0.20, 0.20)
    configured_fractions = tuple(
        float(config["data"][key])
        for key in ("train_fraction", "validation_fraction", "test_fraction")
    )
    if not all(
        math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9)
        for actual, expected in zip(configured_fractions, expected_fractions)
    ):
        raise ValueError(
            "The grouped 5-fold splitter supports train/validation/test fractions "
            "of 0.60/0.20/0.20 only. Update the splitter before changing these values."
        )

    train, validation, test = split_data(
        df,
        seed=int(config["experiment"]["seed"]),
    )

    train_ids = set(train["record_id"])
    validation_ids = set(validation["record_id"])
    test_ids = set(test["record_id"])

    if train_ids & validation_ids or train_ids & test_ids or validation_ids & test_ids:
        raise RuntimeError("Record overlap detected between splits.")

    artifact_dir = repo_root / config["paths"]["dataset_artifacts"]
    artifact_dir.mkdir(parents=True, exist_ok=True)

    split_rows = {
        "train": serialize(train),
        "validation": serialize(validation),
        "test": serialize(test),
    }

    for split_name, rows in split_rows.items():
        write_jsonl(artifact_dir / f"{split_name}.jsonl", rows)

    manifest = {
        "schema_version": "1.0.0",
        "experiment": config["experiment"],
        "source": {
            **eligibility,
            "rows": int(len(df)),
        },
        "transformation": {
            "input_column": "goal",
            "label_column": "behavior_class",
            "normalization_for_grouping": "strip, lowercase, collapse internal whitespace",
            "group_id": "sha256 of normalized goal",
            "raw_source_modified": False,
            "pinned_upstream_verification": "datasets/audit/JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json",
            "license_usage_limitation": "Upstream card declares MIT for JBB-Behaviors; preserve source attribution and review constituent-source terms before redistribution.",
            "excluded_sources": {
                "S-Labs/prompt-injection-dataset": "Blocked because the byte-verified pinned upstream revision contains conflicting labels; never included in this task.",
                "HarmBench": "Not included in this task; known exact overlaps require grouped handling before any combined-source evaluation.",
                "IndiBias": "Evaluation-first; not included in this task.",
                "DefAn": "Different reference-grounded task; not included in this task.",
                "AgentDojo": "Stateful agentic evaluation; not included in this text-classification task.",
            },
        },
        "splits": {
            name: {
                "rows": len(rows),
                "label_counts": {
                    label: sum(1 for row in rows if row["label_name"] == label)
                    for label in LABELS
                },
                "record_ids_sha256": stable_text_hash(
                    "\n".join(row["record_id"] for row in rows)
                ),
                "group_ids_sha256": stable_text_hash(
                    "\n".join(sorted({row["group_id"] for row in rows}))
                ),
            }
            for name, rows in split_rows.items()
        },
        "input_policy": {
            "model_input": "goal",
            "target_used_as_input": False,
            "label_source": "JailbreakBench.behavior_class",
            "split_method": "StratifiedGroupKFold: 5 folds; 3 train, 1 validation, 1 test",
        },
    }

    with (artifact_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    print("AICAS dataset build completed.")
    print(f"Source rows: {len(df)}")
    for name, rows in split_rows.items():
        print(f"{name}: {len(rows)} rows")
        print(
            "  labels:",
            {
                label: sum(1 for row in rows if row["label_name"] == label)
                for label in LABELS
            },
        )
    print(f"Artifacts: {artifact_dir}")


if __name__ == "__main__":
    main()
