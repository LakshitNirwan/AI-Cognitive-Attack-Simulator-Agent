import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\jailbreak\processed"
)

DATA_FILE = ROOT / "jailbreakbench_master.csv"
PROVENANCE_FILE = ROOT / "jailbreakbench_provenance.json"


print("=" * 80)
print("AICAS — JAILBREAKBENCH PROCESSED DATASET VALIDATION")
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
    "behavior_class",
    "original_index",
    "goal",
    "target",
    "behavior",
    "category",
    "source",
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
# Record ID validation
# ---------------------------------------------------------

print("\n[2] RECORD IDs")

print(
    "Unique:",
    df["record_id"].nunique()
)

print(
    "Duplicates:",
    df["record_id"].duplicated().sum()
)

print(
    "Missing:",
    df["record_id"].isna().sum()
)


# ---------------------------------------------------------
# Source validation
# ---------------------------------------------------------

print("\n[3] SOURCE DATASET")

print(
    df["source_dataset"]
    .value_counts(dropna=False)
    .to_string()
)

print(
    "Unexpected source values:",
    sorted(
        set(df["source_dataset"].dropna())
        - {"JailbreakBench"}
    )
)


# ---------------------------------------------------------
# Behavior class
# ---------------------------------------------------------

print("\n[4] BEHAVIOR CLASS")

class_counts = (
    df["behavior_class"]
    .value_counts(dropna=False)
)

print(class_counts.to_string())

print(
    "Missing:",
    df["behavior_class"].isna().sum()
)

print(
    "Unexpected:",
    sorted(
        set(df["behavior_class"].dropna())
        - {"benign", "harmful"}
    )
)


# ---------------------------------------------------------
# Original index validation
# ---------------------------------------------------------

print("\n[5] ORIGINAL INDEX")

print(
    "Unique:",
    df["original_index"].nunique()
)

print(
    "Duplicates:",
    df["original_index"].duplicated().sum()
)

print(
    "Missing:",
    df["original_index"].isna().sum()
)


# ---------------------------------------------------------
# Text-field validation
# ---------------------------------------------------------

text_columns = [
    "goal",
    "target",
    "behavior",
    "category",
    "source",
]

print("\n[6] REQUIRED DATA FIELDS")

for column in text_columns:

    missing = df[column].isna().sum()

    empty = (
        df[column]
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        f"{column:10s} | missing: {missing:3d} | empty: {empty:3d}"
    )


# ---------------------------------------------------------
# Duplicate complete records
# ---------------------------------------------------------

print("\n[7] DUPLICATES")

print(
    "Duplicate complete rows:",
    df.duplicated().sum()
)

print(
    "Duplicate behavior text:",
    df["behavior"].duplicated().sum()
)


# ---------------------------------------------------------
# Category distribution
# ---------------------------------------------------------

print("\n[8] CATEGORIES")

print(
    df["category"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Source-file distribution
# ---------------------------------------------------------

print("\n[9] SOURCE FILES")

print(
    df["source_file"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Cross-check expected counts
# ---------------------------------------------------------

print("\n[10] EXPECTED COUNTS")

expected_total = 200
expected_benign = 100
expected_harmful = 100

checks = {
    "Total records":
        len(df) == expected_total,

    "Benign records":
        int(
            (
                df["behavior_class"]
                == "benign"
            ).sum()
        ) == expected_benign,

    "Harmful records":
        int(
            (
                df["behavior_class"]
                == "harmful"
            ).sum()
        ) == expected_harmful,

    "Unique record IDs":
        df["record_id"].nunique()
        == expected_total,

    "No duplicate record IDs":
        df["record_id"].duplicated().sum()
        == 0,

    "No missing values":
        df.isna().sum().sum()
        == 0,
}

for name, passed in checks.items():

    print(
        f"{name:25s}:",
        "PASS" if passed else "FAIL"
    )


# ---------------------------------------------------------
# Provenance validation
# ---------------------------------------------------------

print("\n[11] PROVENANCE")

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
# Final status
# ---------------------------------------------------------

all_passed = all(checks.values())

print("\n" + "=" * 80)

if all_passed:
    print("VALIDATION RESULT: PASS")
else:
    print("VALIDATION RESULT: FAIL")

print("=" * 80)