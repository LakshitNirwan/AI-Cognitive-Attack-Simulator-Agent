import json
from pathlib import Path
import pandas as pd

RAW = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent\datasets\hallucination\defan\raw"
)

CSV_FILE = RAW / "QA_domain_3_public.csv"
JSON_FILE = RAW / "QA_domain_3_public.json"


print("=" * 80)
print("AICAS — DefAn Domain 3 CSV vs JSON COMPARISON")
print("=" * 80)


# ---------------------------------------------------------
# 1. Load CSV
# ---------------------------------------------------------

print("\n[1] Loading CSV...")

csv_df = pd.read_csv(CSV_FILE)

print("CSV records:", len(csv_df))
print("CSV columns:", list(csv_df.columns))

csv_questions = csv_df["questions"].astype(str).str.strip()

missing_csv = csv_df["answer"].isna()

print("CSV missing answers:", int(missing_csv.sum()))


# ---------------------------------------------------------
# 2. Load JSON
# ---------------------------------------------------------

print("\n[2] Loading JSON...")

with open(JSON_FILE, "r", encoding="utf-8") as f:
    json_data = json.load(f)


print("JSON top-level type:", type(json_data).__name__)


# Handle common JSON structures
if isinstance(json_data, list):
    json_records = json_data

elif isinstance(json_data, dict):

    # Try common container names
    for key in ["data", "records", "questions", "examples"]:
        if key in json_data and isinstance(json_data[key], list):
            json_records = json_data[key]
            print("JSON record container:", key)
            break
    else:
        print("\nJSON keys:")
        print(list(json_data.keys()))
        raise ValueError(
            "Could not identify a list of records inside the JSON."
        )

else:
    raise ValueError("Unexpected JSON structure.")


print("JSON records:", len(json_records))


# ---------------------------------------------------------
# 3. Inspect JSON fields
# ---------------------------------------------------------

print("\n[3] JSON fields")

if json_records and isinstance(json_records[0], dict):

    json_fields = list(json_records[0].keys())

    for field in json_fields:
        print(" -", field)

else:
    raise ValueError("JSON records are not dictionaries.")


# ---------------------------------------------------------
# 4. Identify question and answer fields
# ---------------------------------------------------------

question_candidates = [
    "questions",
    "question",
    "Questions",
    "Question"
]

answer_candidates = [
    "answer",
    "answers",
    "Answer",
    "Answers"
]


json_question_field = None
json_answer_field = None

for field in question_candidates:
    if field in json_fields:
        json_question_field = field
        break

for field in answer_candidates:
    if field in json_fields:
        json_answer_field = field
        break


print("\n[4] Detected fields")

print("JSON question field:", json_question_field)
print("JSON answer field:", json_answer_field)


if json_question_field is None:
    raise ValueError("Could not identify question field in JSON.")

if json_answer_field is None:
    raise ValueError("Could not identify answer field in JSON.")


# ---------------------------------------------------------
# 5. Build JSON lookup by question
# ---------------------------------------------------------

json_lookup = {}

for record in json_records:

    question = record.get(json_question_field)

    if question is None:
        continue

    question = str(question).strip()

    if question not in json_lookup:
        json_lookup[question] = record


# ---------------------------------------------------------
# 6. Compare missing CSV answers against JSON
# ---------------------------------------------------------

print("\n[5] Comparing missing CSV answers with JSON")

missing_rows = csv_df[missing_csv].copy()

found_in_json = 0
answer_recovered = 0
still_missing = 0

recovered_records = []
unresolved_records = []


for _, row in missing_rows.iterrows():

    question = str(row["questions"]).strip()

    json_record = json_lookup.get(question)

    if json_record is None:

        unresolved_records.append({
            "question": question,
            "csv_answer": None,
            "json_answer": None,
            "status": "NOT_FOUND_IN_JSON"
        })

        continue

    found_in_json += 1

    json_answer = json_record.get(json_answer_field)

    if (
        json_answer is not None
        and str(json_answer).strip()
        and str(json_answer).strip().lower() != "nan"
    ):

        answer_recovered += 1

        recovered_records.append({
            "question": question,
            "csv_answer": None,
            "json_answer": json_answer,
            "status": "ANSWER_FOUND_IN_JSON"
        })

    else:

        still_missing += 1

        unresolved_records.append({
            "question": question,
            "csv_answer": None,
            "json_answer": None,
            "status": "ANSWER_ALSO_MISSING_IN_JSON"
        })


# ---------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)

print("CSV total records:              ", len(csv_df))
print("CSV missing answers:            ", int(missing_csv.sum()))
print("JSON total records:             ", len(json_records))
print("Missing questions found in JSON:", found_in_json)
print("Answers recovered from JSON:    ", answer_recovered)
print("Still missing answers:          ", still_missing)
print(
    "Not found in JSON:              ",
    len(unresolved_records) - still_missing
)


# ---------------------------------------------------------
# 8. Show recovered answers
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("FIRST 20 RECOVERED ANSWERS")
print("=" * 80)

for i, record in enumerate(recovered_records[:20], start=1):

    print(f"\n{i}. QUESTION:")
    print(record["question"])

    print("ANSWER FROM JSON:")
    print(record["json_answer"])


# ---------------------------------------------------------
# 9. Save comparison results
# ---------------------------------------------------------

OUTPUT_DIR = Path(
    r"D:\AI-Cognitive-Attack-Simulator-Agent"
    r"\datasets\hallucination\defan\processed"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


recovered_file = OUTPUT_DIR / "domain3_answers_recovered_from_json.csv"

unresolved_file = OUTPUT_DIR / "domain3_unresolved_answers.csv"

report_file = OUTPUT_DIR / "domain3_csv_json_comparison.json"


pd.DataFrame(recovered_records).to_csv(
    recovered_file,
    index=False,
    encoding="utf-8"
)

pd.DataFrame(unresolved_records).to_csv(
    unresolved_file,
    index=False,
    encoding="utf-8"
)


report = {
    "csv_file": str(CSV_FILE),
    "json_file": str(JSON_FILE),
    "csv_records": len(csv_df),
    "csv_missing_answers": int(missing_csv.sum()),
    "json_records": len(json_records),
    "missing_questions_found_in_json": found_in_json,
    "answers_recovered_from_json": answer_recovered,
    "answers_also_missing_in_json": still_missing,
    "questions_not_found_in_json": (
        len(unresolved_records) - still_missing
    )
}


with open(report_file, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)


print("\n" + "=" * 80)
print("FILES CREATED")
print("=" * 80)

print(recovered_file)
print(unresolved_file)
print(report_file)

print("\nComparison complete.")