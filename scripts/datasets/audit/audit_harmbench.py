import pandas as pd
from pathlib import Path

ROOT = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\\datasets\\benchmark\\harmbench\\raw"
)

FILES = [
    ROOT / "harmbench_behaviors_text_all.csv",
    ROOT / "harmbench_behaviors_text_test.csv",
    ROOT / "harmbench_behaviors_text_val.csv",
]

print("=" * 80)
print("AICAS — HARM-BENCH DATA QUALITY AUDIT")
print("=" * 80)

datasets = {}

for path in FILES:

    print("\n" + "-" * 80)
    print("FILE:", path.name)

    df = pd.read_csv(path)
    datasets[path.name] = df

    print("Rows:", len(df))
    print("Columns:", list(df.columns))

    print("\nMissing values:")
    missing = df.isna().sum()

    if missing.sum() == 0:
        print("  None")

    else:
        for column, count in missing.items():
            if count > 0:
                print(f"  {column}: {count}")

    print("\nDuplicate rows:", df.duplicated().sum())

    if "BehaviorID" in df.columns:
        print(
            "Unique BehaviorIDs:",
            df["BehaviorID"].nunique()
        )

        print(
            "Duplicate BehaviorIDs:",
            df["BehaviorID"].duplicated().sum()
        )

    if "Behavior" in df.columns:
        print(
            "Unique behaviors:",
            df["Behavior"].nunique()
        )

        print(
            "Duplicate behavior strings:",
            df["Behavior"].duplicated().sum()
        )

    print("\nFunctional categories:")

    if "FunctionalCategory" in df.columns:
        print(
            df["FunctionalCategory"]
            .value_counts(dropna=False)
            .to_string()
        )

    print("\nSemantic categories:")

    if "SemanticCategory" in df.columns:
        print(
            df["SemanticCategory"]
            .value_counts(dropna=False)
            .to_string()
        )


# ----------------------------------------------------------------------
# Cross-file analysis
# ----------------------------------------------------------------------

print("\n" + "=" * 80)
print("CROSS-FILE ANALYSIS")
print("=" * 80)

all_df = datasets["harmbench_behaviors_text_all.csv"]
test_df = datasets["harmbench_behaviors_text_test.csv"]
val_df = datasets["harmbench_behaviors_text_val.csv"]

print("\nRecord counts:")
print("ALL :", len(all_df))
print("TEST:", len(test_df))
print("VAL :", len(val_df))

if "BehaviorID" in all_df.columns:

    all_ids = set(all_df["BehaviorID"].dropna())
    test_ids = set(test_df["BehaviorID"].dropna())
    val_ids = set(val_df["BehaviorID"].dropna())

    print("\nBehaviorID overlap:")

    print("TEST ∩ VAL:", len(test_ids & val_ids))
    print("TEST ∩ ALL:", len(test_ids & all_ids))
    print("VAL ∩ ALL:", len(val_ids & all_ids))

    print("\nUnion:")
    print("TEST ∪ VAL:", len(test_ids | val_ids))
    print("ALL:", len(all_ids))

    print(
        "ALL - (TEST ∪ VAL):",
        len(all_ids - (test_ids | val_ids))
    )

    print(
        "(TEST ∪ VAL) - ALL:",
        len((test_ids | val_ids) - all_ids)
    )

# ----------------------------------------------------------------------
# Behavior overlap
# ----------------------------------------------------------------------

if "Behavior" in all_df.columns:

    all_behaviors = set(all_df["Behavior"].dropna())
    test_behaviors = set(test_df["Behavior"].dropna())
    val_behaviors = set(val_df["Behavior"].dropna())

    print("\nBehavior-string overlap:")

    print(
        "TEST ∩ VAL:",
        len(test_behaviors & val_behaviors)
    )

    print(
        "TEST ∩ ALL:",
        len(test_behaviors & all_behaviors)
    )

    print(
        "VAL ∩ ALL:",
        len(val_behaviors & all_behaviors)
    )

# ----------------------------------------------------------------------
# Missing-value comparison
# ----------------------------------------------------------------------

print("\n" + "=" * 80)
print("MISSING-VALUE COMPARISON")
print("=" * 80)

for name, df in datasets.items():

    print("\n", name)

    for column in df.columns:

        count = int(df[column].isna().sum())

        if count > 0:
            print(
                f"{column}: {count} missing"
            )

print("\n" + "=" * 80)
print("HARM-BENCH AUDIT COMPLETE")
print("=" * 80)