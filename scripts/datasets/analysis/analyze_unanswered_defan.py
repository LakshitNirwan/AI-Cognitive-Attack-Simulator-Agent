import pandas as pd
from pathlib import Path
from collections import Counter

INPUT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed\unanswered_1080.csv"
)

OUTPUT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed\unanswered_question_analysis.csv"
)

df = pd.read_csv(INPUT)

# Normalize only for analysis.
# The original question text is preserved.
df["normalized_question"] = (
    df["question"]
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
)

# Exact duplicate groups after normalization.
counts = Counter(df["normalized_question"])

df["exact_duplicate_count"] = (
    df["normalized_question"].map(counts)
)

df["exact_duplicate"] = (
    df["exact_duplicate_count"] > 1
)

# Give each exact-question group an ID.
group_map = {
    question: f"QG_{i:04d}"
    for i, question in enumerate(
        sorted(counts.keys()),
        start=1
    )
}

df["exact_question_group"] = (
    df["normalized_question"].map(group_map)
)

# Save analysis.
df.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

print("=" * 80)
print("AICAS — UNANSWERED DEFAN QUESTION ANALYSIS")
print("=" * 80)

print("Total records:", len(df))

print(
    "Unique questions after normalization:",
    df["normalized_question"].nunique()
)

print(
    "Records belonging to repeated exact-question groups:",
    int(df["exact_duplicate"].sum())
)

print(
    "Number of exact-question groups:",
    df.loc[
        df["exact_duplicate"],
        "exact_question_group"
    ].nunique()
)

print("\nMost repeated exact questions:")

repeated = (
    df[df["exact_duplicate"]]
    [["exact_question_group", "question", "exact_duplicate_count"]]
    .drop_duplicates()
    .sort_values(
        "exact_duplicate_count",
        ascending=False
    )
)

if len(repeated) == 0:
    print("None")

else:
    print(
        repeated.head(20).to_string(index=False)
    )

print("\nQuestion type distribution:")
print(df["question_type"].value_counts().to_string())

print("\nOutput:")
print(OUTPUT)

print("\nAnalysis complete.")