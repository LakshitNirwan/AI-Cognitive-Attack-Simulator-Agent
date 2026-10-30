import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\benchmark\harmbench"
)

RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


ALL_FILE = RAW_DIR / "harmbench_behaviors_text_all.csv"
TEST_FILE = RAW_DIR / "harmbench_behaviors_text_test.csv"
VAL_FILE = RAW_DIR / "harmbench_behaviors_text_val.csv"


# ---------------------------------------------------------
# Load raw files
# ---------------------------------------------------------

all_df = pd.read_csv(ALL_FILE)
test_df = pd.read_csv(TEST_FILE)
val_df = pd.read_csv(VAL_FILE)


# ---------------------------------------------------------
# Build split lookup using BehaviorID
# ---------------------------------------------------------

test_ids = set(
    test_df["BehaviorID"].dropna()
)

val_ids = set(
    val_df["BehaviorID"].dropna()
)


def get_split(behavior_id):

    if behavior_id in test_ids:
        return "test"

    if behavior_id in val_ids:
        return "validation"

    return "unknown"


# ---------------------------------------------------------
# Build canonical processed dataset
# ---------------------------------------------------------

records = []

for _, row in all_df.iterrows():

    behavior_id = row["BehaviorID"]

    record = {
        "record_id":
            f"HARMBENCH_{behavior_id}",

        "source_dataset":
            "HarmBench",

        "source_file":
            "harmbench_behaviors_text_all.csv",

        "benchmark_split":
            get_split(behavior_id),

        "behavior_id":
            behavior_id,

        "behavior":
            row["Behavior"],

        "functional_category":
            row["FunctionalCategory"],

        "semantic_category":
            row["SemanticCategory"],

        "tags":
            row["Tags"],

        "context_string":
            row["ContextString"],
    }

    records.append(record)


master_df = pd.DataFrame(records)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("=" * 80)
print("AICAS — HARMBENCH MASTER DATASET")
print("=" * 80)

print("\nTotal records:", len(master_df))

print(
    "Unique BehaviorIDs:",
    master_df["behavior_id"].nunique()
)

print(
    "Duplicate BehaviorIDs:",
    master_df["behavior_id"].duplicated().sum()
)

print("\nSplit distribution:")

print(
    master_df["benchmark_split"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nFunctional categories:")

print(
    master_df["functional_category"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nSemantic categories:")

print(
    master_df["semantic_category"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nMissing values:")

missing = master_df.isna().sum()

for column, count in missing.items():

    if count > 0:
        print(
            f"{column}: {count}"
        )


# ---------------------------------------------------------
# Save processed dataset
# ---------------------------------------------------------

OUTPUT_FILE = (
    PROCESSED_DIR /
    "harmbench_behaviors_master.csv"
)

master_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------
# Save provenance metadata
# ---------------------------------------------------------

metadata = {

    "dataset":
        "HarmBench",

    "source":
        "HarmBench behavior text benchmark",

    "source_files": [
        "harmbench_behaviors_text_all.csv",
        "harmbench_behaviors_text_test.csv",
        "harmbench_behaviors_text_val.csv"
    ],

    "canonical_source":
        "harmbench_behaviors_text_all.csv",

    "total_records":
        len(master_df),

    "unique_behavior_ids":
        int(master_df["behavior_id"].nunique()),

    "test_records":
        int(
            (master_df["benchmark_split"] == "test")
            .sum()
        ),

    "validation_records":
        int(
            (master_df["benchmark_split"] == "validation")
            .sum()
        ),

    "duplicate_behavior_ids":
        int(
            master_df["behavior_id"]
            .duplicated()
            .sum()
        ),

    "raw_files_modified":
        False,

    "processing_notes": [
        "The all file was used as the canonical 400-record source.",
        "Test and validation membership was reconstructed using BehaviorID.",
        "Test and validation records were not duplicated.",
        "Repeated Behavior text was retained because BehaviorID is unique.",
        "Missing Tags values were preserved as missing.",
        "Missing ContextString values were preserved as missing.",
        "No new semantic or functional labels were generated."
    ]
}


METADATA_FILE = (
    PROCESSED_DIR /
    "harmbench_provenance.json"
)

with open(
    METADATA_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=2,
        ensure_ascii=False
    )


# ---------------------------------------------------------
# Final output
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("FILES CREATED")
print("=" * 80)

print(OUTPUT_FILE)
print(METADATA_FILE)

print("\nRaw HarmBench files were NOT modified.")

print("\nProcessing complete.")
print("=" * 80)