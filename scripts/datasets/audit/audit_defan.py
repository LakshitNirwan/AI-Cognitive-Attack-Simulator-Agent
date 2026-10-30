import pandas as pd
from pathlib import Path

ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent\datasets\hallucination\defan\raw"
)

FILES = sorted(ROOT.glob("QA_domain_*_public.csv"))


print("=" * 80)
print("AICAS — DEFAN DATA QUALITY AUDIT")
print("=" * 80)


for path in FILES:

    print("\n" + "-" * 80)
    print(f"FILE: {path.name}")

    df = pd.read_csv(path)

    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # --------------------------------------------------
    # Index-column inspection
    # --------------------------------------------------

    if "Unnamed: 0" in df.columns:

        values = df["Unnamed: 0"]

        print("\n[INDEX COLUMN]")
        print("Unnamed: 0 present: YES")
        print("Unique values:", values.nunique(dropna=False))
        print("Missing values:", values.isna().sum())

        numeric = pd.to_numeric(values, errors="coerce")

        if numeric.notna().all():

            expected = pd.Series(
                range(len(df)),
                index=df.index,
                dtype="float64"
            )

            matches = (numeric.reset_index(drop=True) == expected).all()

            print("Matches sequential CSV index:", matches)

        print("First 10 values:")
        print(values.head(10).tolist())

    else:
        print("\n[INDEX COLUMN]")
        print("Unnamed: 0 present: NO")

    # --------------------------------------------------
    # Exact duplicate inspection
    # --------------------------------------------------

    duplicate_mask = df.duplicated(keep=False)
    duplicate_rows = df[duplicate_mask]

    print("\n[DUPLICATES]")
    print("Duplicate rows:", duplicate_mask.sum())

    if len(duplicate_rows) > 0:

        print("Unique duplicated records:",
              duplicate_rows.drop_duplicates().shape[0])

        print("\nFirst duplicated records:")

        print(
            duplicate_rows
            .drop_duplicates()
            .head(10)
            .to_string(index=False)
        )

    # --------------------------------------------------
    # Missing-answer inspection
    # --------------------------------------------------

    if "answer" in df.columns:

        missing_answer = df["answer"].isna()

        print("\n[MISSING ANSWERS]")
        print("Missing answer rows:", missing_answer.sum())

        if missing_answer.sum() > 0:

            missing = df[missing_answer]

            print("\nFirst 10 questions with missing answers:")

            print(
                missing.head(10)
                .to_string(index=False)
            )

            print("\nMissing-answer question duplicates:",
                  missing["questions"].duplicated().sum())

    # --------------------------------------------------
    # Question duplicates
    # --------------------------------------------------

    if "questions" in df.columns:

        print("\n[QUESTION DUPLICATES]")

        print(
            "Duplicate question values:",
            df["questions"].duplicated().sum()
        )

print("\n" + "=" * 80)
print("DEFAN AUDIT COMPLETE")
print("=" * 80)