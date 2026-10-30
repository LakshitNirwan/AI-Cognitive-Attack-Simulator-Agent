from pathlib import Path
import pandas as pd
import sys

# ============================================================
# AICAS — MIGRATION PREFLIGHT
#
# PURPOSE:
#   Inspect the already-validated processed datasets before
#   writing the PostgreSQL migration/importer.
#
# IMPORTANT:
#   - Does NOT modify any files.
#   - Does NOT modify PostgreSQL.
#   - Does NOT migrate data.
# ============================================================

BASE = Path(r"D:\AI-Cognitive-Attack-Simulator-Agent")

DATASETS = {
    "JailbreakBench": {
        "path": BASE / "datasets" / "jailbreak" / "processed"
                    / "jailbreakbench_master.csv",

        "expected_rows": 200,

        "required_columns": [
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
        ],
    },

    "HarmBench": {
        "path": BASE / "datasets" / "benchmark" / "harmbench"
                    / "processed"
                    / "harmbench_behaviors_master.csv",

        "expected_rows": 400,

        "required_columns": [
            "record_id",
            "source_dataset",
            "source_file",
            "benchmark_split",
            "behavior_id",
            "behavior",
            "functional_category",
            "semantic_category",
            "tags",
            "context_string",
        ],
    },

    "IndiBias": {
        "path": BASE / "datasets" / "bias" / "indibias"
                    / "processed"
                    / "indibias_master.csv",

        "expected_rows": 561,

        "required_columns": [
            "record_id",
            "source_dataset",
            "source_file",
            "dataset_scope",
            "source_row_id",
            "original_index",
            "bias_type",
            "stereo_antistereo",
            "english_more",
            "english_less",
            "hindi_more",
            "hindi_less",
        ],
    },

    "DefAn": {
        "path": BASE / "datasets" / "hallucination" / "defan"
                    / "processed"
                    / "defan_aicas_master.csv",

        "expected_rows": 70793,

        "required_columns": [
            "record_id",
            "source",
            "source_file",
            "domain",
            "question",
            "question_type",
            "original_reference_answer",
            "reference_answer",
            "answer_source",
            "reference_answer_available",
            "verification_status",
        ],
    },

    # AgentDojo is intentionally handled separately below because
    # we do not want to guess its filename.
}

print("=" * 80)
print("AICAS — MIGRATION PREFLIGHT")
print("=" * 80)

errors = []
warnings = []

results = []


def inspect_dataset(name, config):
    print()
    print("-" * 80)
    print(f"DATASET: {name}")
    print("-" * 80)

    path = config["path"]

    print(f"Path: {path}")

    if not path.exists():
        print("STATUS: FILE NOT FOUND")
        errors.append(f"{name}: file not found: {path}")
        return

    print("File exists: YES")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"STATUS: FAILED TO READ")
        errors.append(f"{name}: failed to read CSV: {exc}")
        return

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    expected_rows = config["expected_rows"]

    if len(df) == expected_rows:
        print(f"Row count: PASS ({expected_rows})")
    else:
        print(
            f"Row count: FAIL "
            f"(expected {expected_rows}, found {len(df)})"
        )
        errors.append(
            f"{name}: expected {expected_rows} rows, "
            f"found {len(df)}"
        )

    actual_columns = list(df.columns)
    required_columns = config["required_columns"]

    missing_columns = [
        col for col in required_columns
        if col not in actual_columns
    ]

    unexpected_columns = [
        col for col in actual_columns
        if col not in required_columns
    ]

    print()
    print("Required columns:")

    if not missing_columns:
        print("  PASS — all required columns present")
    else:
        print("  FAIL")
        for col in missing_columns:
            print(f"    MISSING: {col}")
            errors.append(
                f"{name}: missing required column: {col}"
            )

    print()
    print("Actual columns:")
    for col in actual_columns:
        print(f"  - {col}")

    if unexpected_columns:
        print()
        print("Additional columns:")
        for col in unexpected_columns:
            print(f"  + {col}")

        warnings.append(
            f"{name}: additional columns found: "
            f"{unexpected_columns}"
        )

    # --------------------------------------------------------
    # Record ID checks
    # --------------------------------------------------------

    if "record_id" in df.columns:
        missing_ids = df["record_id"].isna().sum()
        duplicate_ids = df["record_id"].duplicated().sum()

        print()
        print("record_id:")
        print(f"  Missing:   {missing_ids}")
        print(f"  Duplicate: {duplicate_ids}")

        if missing_ids != 0:
            errors.append(
                f"{name}: {missing_ids} missing record_id values"
            )

        if duplicate_ids != 0:
            errors.append(
                f"{name}: {duplicate_ids} duplicate record_id values"
            )

    # --------------------------------------------------------
    # Missing-value report
    # --------------------------------------------------------

    print()
    print("Missing values:")

    missing = df.isna().sum()
    missing = missing[missing > 0]

    if len(missing) == 0:
        print("  None")
    else:
        for column, count in missing.items():
            print(f"  {column}: {count}")

    # --------------------------------------------------------
    # Dataset-specific identity checks
    # --------------------------------------------------------

    if name == "JailbreakBench":

        if "original_index" in df.columns:
            print()
            print("JailbreakBench original_index:")
            print(
                f"  Unique: "
                f"{df['original_index'].nunique(dropna=True)}"
            )
            print(
                f"  Duplicate rows: "
                f"{df['original_index'].duplicated().sum()}"
            )

        if "behavior_class" in df.columns:
            print()
            print("Behavior class:")
            print(df["behavior_class"].value_counts().to_string())

    elif name == "HarmBench":

        if "behavior_id" in df.columns:
            print()
            print("HarmBench behavior_id:")
            print(
                f"  Unique: "
                f"{df['behavior_id'].nunique(dropna=True)}"
            )
            print(
                f"  Duplicate: "
                f"{df['behavior_id'].duplicated().sum()}"
            )

        if "benchmark_split" in df.columns:
            print()
            print("Benchmark split:")
            print(df["benchmark_split"].value_counts().to_string())

    elif name == "IndiBias":

        if "source_row_id" in df.columns:
            print()
            print("IndiBias source_row_id:")
            print(
                f"  Unique: "
                f"{df['source_row_id'].nunique(dropna=True)}"
            )
            print(
                f"  Duplicate: "
                f"{df['source_row_id'].duplicated().sum()}"
            )

        if "original_index" in df.columns:
            print()
            print("IndiBias original_index:")
            print(
                f"  Unique: "
                f"{df['original_index'].nunique(dropna=True)}"
            )
            print(
                f"  Duplicate: "
                f"{df['original_index'].duplicated().sum()}"
            )

    elif name == "DefAn":

        if "domain" in df.columns:
            print()
            print("DefAn domains:")
            print(df["domain"].value_counts().sort_index().to_string())

        if "reference_answer_available" in df.columns:
            print()
            print("Reference answer availability:")
            print(
                df["reference_answer_available"]
                .value_counts(dropna=False)
                .to_string()
            )

        if "answer_source" in df.columns:
            print()
            print("Answer source:")
            print(
                df["answer_source"]
                .value_counts(dropna=False)
                .to_string()
            )

        if "verification_status" in df.columns:
            print()
            print("Verification status:")
            print(
                df["verification_status"]
                .value_counts(dropna=False)
                .to_string()
            )

    results.append(
        {
            "dataset": name,
            "rows": len(df),
            "columns": len(df.columns),
            "path": str(path),
        }
    )


# ============================================================
# Inspect known processed datasets
# ============================================================

for dataset_name, config in DATASETS.items():
    inspect_dataset(dataset_name, config)


# ============================================================
# AgentDojo discovery
#
# We deliberately do NOT guess its filename.
# Search only inside datasets/agentdojo/processed.
# ============================================================

print()
print("-" * 80)
print("DATASET: AgentDojo")
print("-" * 80)

agentdojo_processed = (
    BASE / "datasets" / "agentdojo" / "processed"
)

print(f"Expected processed directory: {agentdojo_processed}")

if not agentdojo_processed.exists():
    print("STATUS: PROCESSED DIRECTORY NOT FOUND")
    errors.append(
        f"AgentDojo: processed directory not found: "
        f"{agentdojo_processed}"
    )
else:
    candidates = sorted(agentdojo_processed.glob("*.csv"))

    print(f"CSV files found: {len(candidates)}")

    if not candidates:
        print("STATUS: NO CSV FILE FOUND")
        errors.append(
            "AgentDojo: no processed CSV file found"
        )

    elif len(candidates) == 1:
        print("Candidate:")
        print(f"  {candidates[0]}")

        try:
            df = pd.read_csv(candidates[0])

            print(f"Rows: {len(df)}")
            print("Columns:")
            for col in df.columns:
                print(f"  - {col}")

            print()
            print("AgentDojo candidate identified.")
            print(
                "IMPORTANT: We will verify its exact schema "
                "against the validated AgentDojo structure "
                "before migration."
            )

            results.append(
                {
                    "dataset": "AgentDojo",
                    "rows": len(df),
                    "columns": len(df.columns),
                    "path": str(candidates[0]),
                }
            )

        except Exception as exc:
            errors.append(
                f"AgentDojo: failed to read candidate: {exc}"
            )

    else:
        print("STATUS: MULTIPLE CSV FILES FOUND")
        print("Candidates:")

        for candidate in candidates:
            print(f"  - {candidate}")

        errors.append(
            "AgentDojo: multiple processed CSV files found; "
            "migration must not guess which one to use."
        )


# ============================================================
# Summary
# ============================================================

print()
print("=" * 80)
print("PREFLIGHT SUMMARY")
print("=" * 80)

print()
print("Datasets inspected:")
for result in results:
    print(
        f"  {result['dataset']:<18} "
        f"{result['rows']:>7} rows | "
        f"{result['columns']:>3} columns"
    )

print()
print("Errors:", len(errors))
for error in errors:
    print(f"  ERROR: {error}")

print()
print("Warnings:", len(warnings))
for warning in warnings:
    print(f"  WARNING: {warning}")

print()
print("=" * 80)

if errors:
    print("PREFLIGHT RESULT: FAIL")
    print("Migration must NOT proceed.")
    print("=" * 80)
    sys.exit(1)

print("PREFLIGHT RESULT: PASS")
print("No migration was performed.")
print("The database was not modified.")
print("=" * 80)