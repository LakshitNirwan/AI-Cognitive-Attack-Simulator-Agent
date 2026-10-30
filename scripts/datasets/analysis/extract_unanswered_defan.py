import pandas as pd
from pathlib import Path

MASTER_FILE = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed\defan_aicas_master.csv"
)

OUTPUT_FILE = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed\unanswered_1080.csv"
)

df = pd.read_csv(MASTER_FILE)

# Select records where the original DefAn answer is unavailable.
unanswered = df[
    df["reference_answer_available"] == False
].copy()

# Add a working status.
unanswered["aicas_answer_status"] = "not_answered"

# Save only the information we need for the answering stage.
columns = [
    "record_id",
    "source_file",
    "domain",
    "question",
    "question_type",
    "original_reference_answer",
    "reference_answer",
    "answer_source",
    "reference_answer_available",
    "verification_status",
    "aicas_answer_status"
]

unanswered[columns].to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

print("=" * 80)
print("AICAS — UNANSWERED DEFAN RECORD EXTRACTION")
print("=" * 80)

print("Master dataset records:", len(df))
print("Unanswered records:    ", len(unanswered))
print("Expected:               1080")

print("\nDomains:")
print(
    unanswered["domain"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nQuestion types:")
print(
    unanswered["question_type"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nExtraction complete.")