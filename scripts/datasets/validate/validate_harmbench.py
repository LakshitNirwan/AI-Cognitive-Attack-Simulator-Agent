import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\benchmark\harmbench\processed"
)

DATA_FILE = ROOT / "harmbench_behaviors_master.csv"
PROVENANCE_FILE = ROOT / "harmbench_provenance.json"


print("=" * 80)
print("AICAS — HARMBENCH PROCESSED DATASET VALIDATION")
print("=" * 80)


# ---------------------------------------------------------
# Load
# ---------------------------------------------------------

df = pd.read_csv(DATA_FILE)

with open(
    PROVENANCE_FILE,
    "r",
    encoding="utf-8"
) as f:
    provenance = json.load(f)


# ---------------------------------------------------------
# Basic structure
# ---------------------------------------------------------

print("\n[1] FILE")

print("Records:", len(df))
print("Columns:", list(df.columns))


required_columns = [
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
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

print(
    "Missing required columns:",
    len(missing_columns)
)

if missing_columns:
    for column in missing_columns:
        print(" -", column)


# ---------------------------------------------------------
# Stop if schema is broken
# ---------------------------------------------------------

if missing_columns:
    print("\nVALIDATION RESULT: FAIL — SCHEMA ERROR")
    print("=" * 80)
    raise SystemExit(1)


# ---------------------------------------------------------
# Record IDs
# ---------------------------------------------------------

print("\n[2] RECORD IDs")

print("Unique:", df["record_id"].nunique())
print(
    "Duplicates:",
    df["record_id"].duplicated().sum()
)
print("Missing:", df["record_id"].isna().sum())


# ---------------------------------------------------------
# Source dataset
# ---------------------------------------------------------

print("\n[3] SOURCE DATASET")

print(
    df["source_dataset"]
    .value_counts(dropna=False)
    .to_string()
)

unexpected_source = sorted(
    set(df["source_dataset"].dropna())
    - {"HarmBench"}
)

print("Unexpected source values:", unexpected_source)


# ---------------------------------------------------------
# Source files
# ---------------------------------------------------------

print("\n[4] SOURCE FILES")

print(
    df["source_file"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Benchmark split
# ---------------------------------------------------------

print("\n[5] BENCHMARK SPLIT")

print(
    df["benchmark_split"]
    .value_counts(dropna=False)
    .to_string()
)

print(
    "Missing:",
    df["benchmark_split"].isna().sum()
)

unexpected_splits = sorted(
    set(df["benchmark_split"].dropna())
    - {"test", "validation"}
)

print("Unexpected split values:", unexpected_splits)


# ---------------------------------------------------------
# Behavior IDs
# ---------------------------------------------------------

print("\n[6] BEHAVIOR IDs")

print("Unique:", df["behavior_id"].nunique())
print(
    "Duplicates:",
    df["behavior_id"].duplicated().sum()
)
print("Missing:", df["behavior_id"].isna().sum())


# ---------------------------------------------------------
# Required data fields
# ---------------------------------------------------------

print("\n[7] REQUIRED DATA FIELDS")

required_data_columns = [
    "behavior",
    "functional_category",
    "semantic_category",
]

for column in required_data_columns:

    missing = df[column].isna().sum()

    empty = (
        df[column]
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        f"{column:22s} | missing: {missing:3d} | empty: {empty:3d}"
    )


# ---------------------------------------------------------
# Optional fields
# ---------------------------------------------------------

print("\n[8] OPTIONAL FIELDS")

for column in ["tags", "context_string"]:

    missing = df[column].isna().sum()

    print(
        f"{column:22s} | missing: {missing:3d}"
    )


# ---------------------------------------------------------
# Duplicates
# ---------------------------------------------------------

print("\n[9] DUPLICATES")

print(
    "Duplicate complete rows:",
    df.duplicated().sum()
)

print(
    "Duplicate BehaviorIDs:",
    df["behavior_id"].duplicated().sum()
)

print(
    "Duplicate behavior strings:",
    df["behavior"].duplicated().sum()
)


# ---------------------------------------------------------
# Functional categories
# ---------------------------------------------------------

print("\n[10] FUNCTIONAL CATEGORIES")

print(
    df["functional_category"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Semantic categories
# ---------------------------------------------------------

print("\n[11] SEMANTIC CATEGORIES")

print(
    df["semantic_category"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Expected counts
# ---------------------------------------------------------

print("\n[12] EXPECTED COUNTS")

checks = {

    "Total records":
        len(df) == 400,

    "Unique record IDs":
        df["record_id"].nunique() == 400,

    "No duplicate record IDs":
        df["record_id"].duplicated().sum() == 0,

    "Unique BehaviorIDs":
        df["behavior_id"].nunique() == 400,

    "No duplicate BehaviorIDs":
        df["behavior_id"].duplicated().sum() == 0,

    "Test records":
        int(
            (
                df["benchmark_split"]
                == "test"
            ).sum()
        ) == 320,

    "Validation records":
        int(
            (
                df["benchmark_split"]
                == "validation"
            ).sum()
        ) == 80,

    "No missing required data":
        df[
            [
                "behavior",
                "functional_category",
                "semantic_category",
            ]
        ].isna().sum().sum() == 0,

    "No unexpected source":
        len(unexpected_source) == 0,

    "No unexpected splits":
        len(unexpected_splits) == 0,
}


for name, passed in checks.items():

    print(
        f"{name:30s}:",
        "PASS" if passed else "FAIL"
    )


# ---------------------------------------------------------
# Provenance
# ---------------------------------------------------------

print("\n[13] PROVENANCE")

print(
    "Dataset:",
    provenance.get("dataset")
)

print(
    "Total in provenance:",
    provenance.get("total_records")
)

print(
    "Raw files modified:",
    provenance.get("raw_files_modified")
)

print(
    "Provenance total matches:",
    provenance.get("total_records")
    == len(df)
)


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

all_passed = (
    all(checks.values())
    and provenance.get("total_records") == len(df)
    and provenance.get("raw_files_modified") is False
)


print("\n" + "=" * 80)

if all_passed:
    print("VALIDATION RESULT: PASS")
else:
    print("VALIDATION RESULT: FAIL")

print("=" * 80)