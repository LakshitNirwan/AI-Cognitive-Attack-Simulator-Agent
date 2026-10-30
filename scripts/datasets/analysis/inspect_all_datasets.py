import json
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\AI-Cognitive-Attack-Simulator-Agent\datasets")

EXTENSIONS = {".csv", ".json", ".jsonl"}


def inspect_csv(path):
    try:
        df = pd.read_csv(path)

        return {
            "format": "csv",
            "records": len(df),
            "columns": list(df.columns),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_values": {
                str(col): int(df[col].isna().sum())
                for col in df.columns
            },
            "sample": df.head(2).to_dict(orient="records"),
        }

    except Exception as e:
        return {
            "format": "csv",
            "error": str(e),
        }


def inspect_json(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            records = len(data)

            if records > 0 and isinstance(data[0], dict):
                fields = list(data[0].keys())
            else:
                fields = []

            sample = data[:2]

        elif isinstance(data, dict):
            records = 1
            fields = list(data.keys())
            sample = data

        else:
            records = 1
            fields = []
            sample = data

        return {
            "format": "json",
            "records": records,
            "fields": fields,
            "sample": sample,
        }

    except Exception as e:
        return {
            "format": "json",
            "error": str(e),
        }


def inspect_jsonl(path):
    try:
        records = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if line:
                    records.append(json.loads(line))

        fields = []

        if records and isinstance(records[0], dict):
            fields = list(records[0].keys())

        return {
            "format": "jsonl",
            "records": len(records),
            "fields": fields,
            "sample": records[:2],
        }

    except Exception as e:
        return {
            "format": "jsonl",
            "error": str(e),
        }


print("=" * 80)
print("AICAS — MASTER DATASET INSPECTION")
print("=" * 80)

files = sorted(
    p for p in ROOT.rglob("*")
    if p.is_file() and p.suffix.lower() in EXTENSIONS
)

print(f"\nFiles found: {len(files)}")

results = []

for path in files:

    relative_path = path.relative_to(ROOT)

    print("\n" + "-" * 80)
    print(f"FILE: {relative_path}")
    print(f"SIZE: {path.stat().st_size:,} bytes")

    if path.suffix.lower() == ".csv":
        result = inspect_csv(path)

    elif path.suffix.lower() == ".json":
        result = inspect_json(path)

    elif path.suffix.lower() == ".jsonl":
        result = inspect_jsonl(path)

    else:
        continue

    result["path"] = str(relative_path)

    results.append(result)

    print(f"FORMAT: {result.get('format')}")

    if "records" in result:
        print(f"RECORDS: {result['records']}")

    if "columns" in result:
        print("COLUMNS:")
        for col in result["columns"]:
            print(f"  - {col}")

    if "fields" in result:
        print("FIELDS:")
        for field in result["fields"]:
            print(f"  - {field}")

    if "duplicate_rows" in result:
        print(f"DUPLICATE ROWS: {result['duplicate_rows']}")

    if "missing_values" in result:
        print("MISSING VALUES:")
        for col, count in result["missing_values"].items():
            if count > 0:
                print(f"  - {col}: {count}")

    if "error" in result:
        print(f"ERROR: {result['error']}")

print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)