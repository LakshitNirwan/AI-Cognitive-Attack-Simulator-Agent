import pandas as pd
from pathlib import Path
import json

RAW_DIR = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\raw"
)

PROCESSED_DIR = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed"
)

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


records = []
record_counter = 1


for domain in range(1, 9):

    file_path = RAW_DIR / f"QA_domain_{domain}_public.csv"

    df = pd.read_csv(file_path)

    for _, row in df.iterrows():

        question = row["questions"]
        answer = row["answer"]
        question_type = row["type"]

        # Preserve whether the original DefAn
        # dataset supplied a reference answer.
        if pd.isna(answer):
            reference_answer = None
            answer_source = "None"
            reference_answer_available = False
            verification_status = "missing"
        else:
            reference_answer = str(answer)
            answer_source = "DefAn"
            reference_answer_available = True
            verification_status = "original"

        record = {
            "record_id": f"DEFAN_D{domain}_{record_counter:06d}",
            "source": "DefAn",
            "source_file": file_path.name,
            "domain": domain,
            "question": str(question),
            "question_type": str(question_type),

            # Original answer from DefAn.
            # NULL means DefAn did not provide one.
            "original_reference_answer": reference_answer,

            # This is the answer AICAS will actually
            # use for evaluation.
            # Initially it is identical to the original
            # DefAn answer where available.
            "reference_answer": reference_answer,

            # DefAn / AICAS / None
            "answer_source": answer_source,

            "reference_answer_available":
                reference_answer_available,

            # original / missing / verified
            "verification_status":
                verification_status,
        }

        records.append(record)

        record_counter += 1


# ---------------------------------------------------------
# Create DataFrame
# ---------------------------------------------------------

master_df = pd.DataFrame(records)


# ---------------------------------------------------------
# Save master dataset
# ---------------------------------------------------------

master_file = PROCESSED_DIR / "defan_aicas_master.csv"

master_df.to_csv(
    master_file,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------
# Create provenance metadata
# ---------------------------------------------------------

metadata = {
    "dataset": "DefAn",
    "source": "DefAn public QA domains",
    "domains": 8,

    "raw_records": len(master_df),

    "records_with_original_defan_answer": int(
        (master_df["answer_source"] == "DefAn").sum()
    ),

    "records_without_original_answer": int(
        (master_df["answer_source"] == "None").sum()
    ),

    "aicas_generated_answers": 0,

    "raw_files_modified": False,

    "processing_notes": [
        "Original raw DefAn files were not modified.",
        "Questions with missing reference answers were retained.",
        "Missing reference answers were not fabricated.",
        "AICAS-generated answers will be added only after independent generation and verification.",
        "The Unnamed: 0 CSV index column was not included in the processed schema.",
        "Paraphrased/repeated questions were retained."
    ]
}


metadata_file = (
    PROCESSED_DIR / "defan_answer_provenance.json"
)

with open(
    metadata_file,
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
# Print summary
# ---------------------------------------------------------

print("=" * 80)
print("AICAS — DEFAN MASTER DATASET CREATED")
print("=" * 80)

print(f"Total records:                 {len(master_df)}")

print(
    "Original DefAn answers:         ",
    int((master_df["answer_source"] == "DefAn").sum())
)

print(
    "Missing original answers:       ",
    int((master_df["answer_source"] == "None").sum())
)

print(
    "AICAS-generated answers:        ",
    int((master_df["answer_source"] == "AICAS").sum())
)

print("\nAnswer-source distribution:")

print(
    master_df["answer_source"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nVerification distribution:")

print(
    master_df["verification_status"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nFiles created:")

print(master_file)
print(metadata_file)

print("\nRaw files were NOT modified.")

print("=" * 80)