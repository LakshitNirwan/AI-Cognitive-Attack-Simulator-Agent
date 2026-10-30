import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


INPUT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed\unanswered_1080.csv"
)

OUTPUT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed\unanswered_semantic_analysis.csv"
)

# ---------------------------------------------------------
# Load questions
# ---------------------------------------------------------

df = pd.read_csv(INPUT)

questions = df["question"].astype(str).tolist()

print("=" * 80)
print("AICAS — DEFAN SEMANTIC QUESTION ANALYSIS")
print("=" * 80)

print("Questions:", len(questions))

# ---------------------------------------------------------
# Load embedding model
# ---------------------------------------------------------

print("\nLoading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Model loaded.")

# ---------------------------------------------------------
# Generate embeddings
# ---------------------------------------------------------

print("\nGenerating embeddings...")

embeddings = model.encode(
    questions,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("Embedding shape:", embeddings.shape)

# ---------------------------------------------------------
# Similarity matrix
# ---------------------------------------------------------

print("\nCalculating semantic similarity...")

similarities = cosine_similarity(embeddings)

# ---------------------------------------------------------
# Find strongest semantic match for each question
# ---------------------------------------------------------

best_match_index = []
best_match_score = []

for i in range(len(questions)):

    scores = similarities[i].copy()

    # Ignore the question itself
    scores[i] = -1

    j = int(np.argmax(scores))

    best_match_index.append(j)
    best_match_score.append(float(scores[j]))


df["best_match_record_id"] = [
    df.iloc[i]["record_id"]
    for i in best_match_index
]

df["best_match_question"] = [
    questions[i]
    for i in best_match_index
]

df["semantic_similarity"] = best_match_score


# ---------------------------------------------------------
# Candidate grouping thresholds
# ---------------------------------------------------------

df["candidate_very_high"] = (
    df["semantic_similarity"] >= 0.90
)

df["candidate_high"] = (
    df["semantic_similarity"] >= 0.85
)

df["candidate_possible"] = (
    df["semantic_similarity"] >= 0.80
)


# ---------------------------------------------------------
# Save analysis
# ---------------------------------------------------------

df.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("SEMANTIC ANALYSIS SUMMARY")
print("=" * 80)

print("Total questions:", len(df))

print(
    "Very high similarity (>= 0.90):",
    int(df["candidate_very_high"].sum())
)

print(
    "High similarity (>= 0.85):",
    int(df["candidate_high"].sum())
)

print(
    "Possible similarity (>= 0.80):",
    int(df["candidate_possible"].sum())
)


# ---------------------------------------------------------
# Display strongest candidate pairs
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("TOP 30 STRONGEST CANDIDATE PAIRS")
print("=" * 80)

top = (
    df[
        [
            "record_id",
            "question",
            "best_match_record_id",
            "best_match_question",
            "semantic_similarity"
        ]
    ]
    .sort_values(
        "semantic_similarity",
        ascending=False
    )
    .head(30)
)

for _, row in top.iterrows():

    print("\nSimilarity:",
          round(row["semantic_similarity"], 4))

    print("QUESTION A:")
    print(row["question"])

    print("QUESTION B:")
    print(row["best_match_question"])

    print("-" * 80)


print("\nOutput:")
print(OUTPUT)

print("\nSemantic analysis complete.")