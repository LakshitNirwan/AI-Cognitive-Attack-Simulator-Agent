import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\bias\indibias\processed"
)

DATA_FILE = ROOT / "indibias_master.csv"
PROVENANCE_FILE = ROOT / "indibias_provenance.json"


print("=" * 80)
print("AICAS — INDIBIAS PROCESSED DATASET VALIDATION")
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
    "dataset_scope",
    "source_row_id",
    "original_index",
    "bias_type",
    "stereo_antistereo",
    "english_more",
    "english_less",
    "hindi_more",
    "hindi_less",
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
# Stop on schema failure
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
    - {"IndiBias"}
)

print(
    "Unexpected source values:",
    unexpected_source
)


# ---------------------------------------------------------
# Dataset scope
# ---------------------------------------------------------

print("\n[4] DATASET SCOPE")

print(
    df["dataset_scope"]
    .value_counts(dropna=False)
    .to_string()
)

unexpected_scope = sorted(
    set(df["dataset_scope"].dropna())
    - {"sample"}
)

print(
    "Unexpected scope values:",
    unexpected_scope
)


# ---------------------------------------------------------
# Source row IDs
# ---------------------------------------------------------

print("\n[5] SOURCE ROW IDs")

print(
    "Unique:",
    df["source_row_id"].nunique()
)

print(
    "Duplicates:",
    df["source_row_id"].duplicated().sum()
)

print(
    "Missing:",
    df["source_row_id"].isna().sum()
)


# ---------------------------------------------------------
# Original indices
# ---------------------------------------------------------

print("\n[6] ORIGINAL INDEX")

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
# Bias labels
# ---------------------------------------------------------

print("\n[7] BIAS TYPES")

print(
    df["bias_type"]
    .value_counts(dropna=False)
    .to_string()
)

print("\n[8] STEREOTYPE LABELS")

print(
    df["stereo_antistereo"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Sentence fields
# ---------------------------------------------------------

print("\n[9] SENTENCE FIELDS")

sentence_columns = [
    "english_more",
    "english_less",
    "hindi_more",
    "hindi_less",
]

for column in sentence_columns:

    missing = df[column].isna().sum()

    empty = (
        df[column]
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        f"{column:20s} | missing: {missing:3d} | empty: {empty:3d}"
    )


# ---------------------------------------------------------
# Duplicates
# ---------------------------------------------------------

print("\n[10] DUPLICATES")

print(
    "Duplicate complete rows:",
    df.duplicated().sum()
)

print(
    "Duplicate record IDs:",
    df["record_id"].duplicated().sum()
)

print(
    "Duplicate source row IDs:",
    df["source_row_id"].duplicated().sum()
)


# ---------------------------------------------------------
# Expected counts
# ---------------------------------------------------------

print("\n[11] EXPECTED COUNTS")

checks = {

    "Total records":
        len(df) == 561,

    "Unique record IDs":
        df["record_id"].nunique() == 561,

    "No duplicate record IDs":
        df["record_id"].duplicated().sum() == 0,

    "Unique source row IDs":
        df["source_row_id"].nunique() == 561,

    "No duplicate source row IDs":
        df["source_row_id"].duplicated().sum() == 0,

    "Unique original indices":
        df["original_index"].nunique() == 561,

    "No missing original indices":
        df["original_index"].isna().sum() == 0,

    "No missing bias types":
        df["bias_type"].isna().sum() == 0,

    "No missing stereotype labels":
        df["stereo_antistereo"].isna().sum() == 0,

    "No missing sentence data":
        df[sentence_columns].isna().sum().sum() == 0,

    "No unexpected source":
        len(unexpected_source) == 0,

    "Correct dataset scope":
        len(unexpected_scope) == 0,
}


for name, passed in checks.items():

    print(
        f"{name:32s}:",
        "PASS" if passed else "FAIL"
    )


# ---------------------------------------------------------
# Provenance
# ---------------------------------------------------------

print("\n[12] PROVENANCE")

print(
    "Dataset:",
    provenance.get("dataset")
)

print(
    "Scope:",
    provenance.get("dataset_scope")
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