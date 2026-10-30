import pandas as pd
from pathlib import Path

FILE = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\bias\indibias\raw\IndiBias_v1_sample.csv"
)

print("=" * 80)
print("AICAS — INDIBIAS DATA QUALITY AUDIT")
print("=" * 80)

df = pd.read_csv(FILE)

print("\nFile:")
print(FILE)

print("\nRows:", len(df))

print("\nColumns:")
for column in df.columns:
    print(" -", column)

print("\nMissing values:")
missing = df.isna().sum()

if missing.sum() == 0:
    print("None")
else:
    print(missing[missing > 0].to_string())

print("\nDuplicate rows:")
print(df.duplicated().sum())

print("\nDuplicate index values:")

if "index" in df.columns:
    print(df["index"].duplicated().sum())

    print(
        "Unique index values:",
        df["index"].nunique()
    )

print("\nUnnamed: 0 analysis:")

if "Unnamed: 0" in df.columns:

    print(
        "Unique values:",
        df["Unnamed: 0"].nunique()
    )

    print(
        "Missing values:",
        df["Unnamed: 0"].isna().sum()
    )

    if "index" in df.columns:

        print(
            "Same as index:",
            df["Unnamed: 0"].equals(df["index"])
        )

print("\nBias type distribution:")

if "bias_type" in df.columns:
    print(
        df["bias_type"]
        .value_counts(dropna=False)
        .to_string()
    )

print("\nStereotype / anti-stereotype distribution:")

if "stereo_antistereo" in df.columns:
    print(
        df["stereo_antistereo"]
        .value_counts(dropna=False)
        .to_string()
    )

print("\nEnglish sentence columns:")

for column in [
    "modified_eng_sent_more",
    "modified_eng_sent_less"
]:

    if column in df.columns:

        print(
            f"\n{column}:"
        )

        print(
            "Non-empty:",
            df[column].notna().sum()
        )

        print(
            "Unique:",
            df[column].nunique()
        )

print("\nHindi sentence columns:")

for column in [
    "sent_more_hindi",
    "sent_less_hindi"
]:

    if column in df.columns:

        print(
            f"\n{column}:"
        )

        print(
            "Non-empty:",
            df[column].notna().sum()
        )

        print(
            "Unique:",
            df[column].nunique()
        )

print("\nFirst 10 records:")
print(
    df.head(10).to_string(index=False)
)

print("\n" + "=" * 80)
print("INDIBIAS AUDIT COMPLETE")
print("=" * 80)