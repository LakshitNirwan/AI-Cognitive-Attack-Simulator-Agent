import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed"
)

DATA_FILE = ROOT / "defan_aicas_master.csv"
PROVENANCE_FILE = ROOT / "defan_answer_provenance.json"


print("=" * 80)
print("AICAS — DEFAN MASTER DATASET VALIDATION")
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
# Source
# ---------------------------------------------------------

print("\n[3] SOURCE")

print(
    df["source"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Domains
# ---------------------------------------------------------

print("\n[4] DOMAINS")

print(
    df["domain"]
    .value_counts(dropna=False)
    .sort_index()
    .to_string()
)


# ---------------------------------------------------------
# Questions
# ---------------------------------------------------------

print("\n[5] QUESTIONS")

print(
    "Missing:",
    df["question"].isna().sum()
)

print(
    "Empty:",
    df["question"]
    .astype(str)
    .str.strip()
    .eq("")
    .sum()
)


# ---------------------------------------------------------
# Reference-answer availability
# ---------------------------------------------------------

print("\n[6] REFERENCE ANSWER AVAILABILITY")

print(
    df["reference_answer_available"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Answer source
# ---------------------------------------------------------

print("\n[7] ANSWER SOURCE")

print(
    df["answer_source"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Verification status
# ---------------------------------------------------------

print("\n[8] VERIFICATION STATUS")

print(
    df["verification_status"]
    .value_counts(dropna=False)
    .to_string()
)


# ---------------------------------------------------------
# Missing-answer consistency
# ---------------------------------------------------------

print("\n[9] MISSING-ANSWER CONSISTENCY")

available = df["reference_answer_available"] == True
unavailable = df["reference_answer_available"] == False

print(
    "Available records:",
    available.sum()
)

print(
    "Unavailable records:",
    unavailable.sum()
)

print(
    "Available + original answer source:",
    (
        available
        & (df["answer_source"] == "DefAn")
    ).sum()
)

print(
    "Unavailable + no answer source:",
    (
        unavailable
        & df["answer_source"].isna()
    ).sum()
)

print(
    "Unavailable + missing verification:",
    (
        unavailable
        & (df["verification_status"] == "missing")
    ).sum()
)


# ---------------------------------------------------------
# Domain 3 missing answers
# ---------------------------------------------------------

print("\n[10] DOMAIN 3 UNANSWERED RECORDS")

domain3 = df["domain"].astype(str) == "3"

domain3_unavailable = (
    domain3
    & (df["reference_answer_available"] == False)
)

print(
    "Domain 3 records:",
    domain3.sum()
)

print(
    "Domain 3 without reference answers:",
    domain3_unavailable.sum()
)


# ---------------------------------------------------------
# Expected counts
# ---------------------------------------------------------

print("\n[11] EXPECTED COUNTS")

checks = {

    "Total records":
        len(df) == 70793,

    "Unique record IDs":
        df["record_id"].nunique() == 70793,

    "No duplicate record IDs":
        df["record_id"].duplicated().sum() == 0,

    "No missing questions":
        df["question"].isna().sum() == 0,

    "Original DefAn answers":
        int(
            (
                df["answer_source"] == "DefAn"
            ).sum()
        ) == 69713,

    "Missing reference answers":
        int(
            (
                df["reference_answer_available"]
                == False
            ).sum()
        ) == 1080,

    "AICAS-generated answers":
        int(
            (
                df["answer_source"]
                == "AICAS"
            ).sum()
        ) == 0,

    "Domain 3 unanswered":
        int(domain3_unavailable.sum()) == 1080,
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
    "Provenance type:",
    type(provenance).__name__
)

if isinstance(provenance, dict):

    print(
        "Provenance keys:",
        list(provenance.keys())
    )

else:

    print(
        "WARNING: provenance is not a JSON object"
    )


# ---------------------------------------------------------
# Final
# ---------------------------------------------------------

all_passed = all(checks.values())


print("\n" + "=" * 80)

if all_passed:
    print("VALIDATION RESULT: PASS")
else:
    print("VALIDATION RESULT: FAIL")

print("=" * 80)