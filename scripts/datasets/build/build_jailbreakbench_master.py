import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\jailbreak"
)

RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

FILES = {
    "benign": RAW_DIR / "benign-behaviors.csv",
    "harmful": RAW_DIR / "harmful-behaviors.csv",
}


# ---------------------------------------------------------
# Load and process both source files
# ---------------------------------------------------------

records = []

for behavior_class, input_file in FILES.items():

    df = pd.read_csv(input_file)

    for _, row in df.iterrows():

        record = {
            "record_id":
                f"JAILBREAKBENCH_{behavior_class.upper()}_{int(row['Index']):03d}",

            "source_dataset":
                "JailbreakBench",

            "source_file":
                input_file.name,

            "behavior_class":
                behavior_class,

            "original_index":
                row["Index"],

            "goal":
                row["Goal"],

            "target":
                row["Target"],

            "behavior":
                row["Behavior"],

            "category":
                row["Category"],

            "source":
                row["Source"],
        }

        records.append(record)


master_df = pd.DataFrame(records)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("=" * 80)
print("AICAS — JAILBREAKBENCH MASTER DATASET")
print("=" * 80)

print("\nTotal records:", len(master_df))

print(
    "Unique record IDs:",
    master_df["record_id"].nunique()
)

print(
    "Duplicate record IDs:",
    master_df["record_id"].duplicated().sum()
)

print("\nBehavior class distribution:")

print(
    master_df["behavior_class"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nSource file distribution:")

print(
    master_df["source_file"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nCategory distribution:")

print(
    master_df["category"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nMissing values:")

missing = master_df.isna().sum()

if missing.sum() == 0:

    print("None")

else:

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
    "jailbreakbench_master.csv"
)

master_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------
# Save provenance
# ---------------------------------------------------------

metadata = {

    "dataset":
        "JailbreakBench",

    "source_files": [
        "benign-behaviors.csv",
        "harmful-behaviors.csv"
    ],

    "total_records":
        len(master_df),

    "benign_records":
        int(
            (
                master_df["behavior_class"]
                == "benign"
            ).sum()
        ),

    "harmful_records":
        int(
            (
                master_df["behavior_class"]
                == "harmful"
            ).sum()
        ),

    "unique_record_ids":
        int(
            master_df["record_id"].nunique()
        ),

    "duplicate_record_ids":
        int(
            master_df["record_id"].duplicated().sum()
        ),

    "raw_files_modified":
        False,

    "processing_notes": [
        "Benign and harmful source files were combined into one processed dataset.",
        "The original behavior class was preserved.",
        "Original source indices were preserved.",
        "Goal, Target, Behavior, Category, and Source were preserved.",
        "No new attack labels were generated.",
        "Raw source files were not modified."
    ]
}


METADATA_FILE = (
    PROCESSED_DIR /
    "jailbreakbench_provenance.json"
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

print("\nRaw JailbreakBench files were NOT modified.")

print("\nProcessing complete.")
print("=" * 80)