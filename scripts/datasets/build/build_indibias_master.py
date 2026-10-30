import pandas as pd
import json
from pathlib import Path


ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\bias\indibias"
)

RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

INPUT_FILE = RAW_DIR / "IndiBias_v1_sample.csv"


# ---------------------------------------------------------
# Load raw dataset
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)


# ---------------------------------------------------------
# Build processed records
# ---------------------------------------------------------

records = []

for _, row in df.iterrows():

    record = {
        "record_id":
            f"INDIBIAS_{int(row['index']):06d}",

        "source_dataset":
            "IndiBias",

        "source_file":
            INPUT_FILE.name,

        "dataset_scope":
            "sample",

        # Preserve both source identifiers.
        "source_row_id":
            row["Unnamed: 0"],

        "original_index":
            row["index"],

        "bias_type":
            row["bias_type"],

        "stereo_antistereo":
            row["stereo_antistereo"],

        "english_more":
            row["modified_eng_sent_more"],

        "english_less":
            row["modified_eng_sent_less"],

        "hindi_more":
            row["sent_more_hindi"],

        "hindi_less":
            row["sent_less_hindi"],
    }

    records.append(record)


master_df = pd.DataFrame(records)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("=" * 80)
print("AICAS — INDIBIAS MASTER DATASET")
print("=" * 80)

print("\nTotal records:", len(master_df))

print(
    "Unique original indices:",
    master_df["original_index"].nunique()
)

print(
    "Duplicate original indices:",
    master_df["original_index"].duplicated().sum()
)

print(
    "Unique source row IDs:",
    master_df["source_row_id"].nunique()
)

print(
    "Duplicate source row IDs:",
    master_df["source_row_id"].duplicated().sum()
)


print("\nDataset scope:")
print(
    master_df["dataset_scope"]
    .value_counts()
    .to_string()
)


print("\nBias types:")
print(
    master_df["bias_type"]
    .value_counts(dropna=False)
    .to_string()
)


print("\nStereotype labels:")
print(
    master_df["stereo_antistereo"]
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
    "indibias_master.csv"
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
        "IndiBias",

    "source_file":
        INPUT_FILE.name,

    "dataset_scope":
        "sample",

    "total_records":
        len(master_df),

    "raw_files_modified":
        False,

    "processing_notes": [
        "This file represents the locally collected IndiBias sample.",
        "The sample is not claimed to be the complete IndiBias dataset.",
        "The original raw CSV was not modified.",
        "Both source_row_id and original_index were preserved.",
        "English and Hindi sentence pairs were preserved.",
        "bias_type and stereo_antistereo labels were preserved.",
        "No new bias labels were generated."
    ]
}


METADATA_FILE = (
    PROCESSED_DIR /
    "indibias_provenance.json"
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

print("\nRaw IndiBias file was NOT modified.")

print("\nProcessing complete.")
print("=" * 80)
