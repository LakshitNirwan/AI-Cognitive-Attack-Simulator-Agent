import csv
import json
import os
import sys
from pathlib import Path

import psycopg


BASE = Path(r"D:\AI-Cognitive-Attack-Simulator-Agent")

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5433"),
    "dbname": os.getenv("PGDATABASE", "aicas"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD"),
}


FILES = {
    "JailbreakBench": BASE / "datasets" / "jailbreak" / "processed"
    / "jailbreakbench_master.csv",

    "HarmBench": BASE / "datasets" / "benchmark" / "harmbench"
    / "processed" / "harmbench_behaviors_master.csv",

    "IndiBias": BASE / "datasets" / "bias" / "indibias"
    / "processed" / "indibias_master.csv",

    "DefAn": BASE / "datasets" / "hallucination" / "defan"
    / "processed" / "defan_aicas_master.csv",

    "AgentDojoRaw": BASE / "datasets" / "benchmark" / "agentdojo"
    / "raw" / "agentdojo_v1_2_2_injection_tasks.json",

    "AgentDojoMeta": BASE / "datasets" / "benchmark" / "agentdojo"
    / "processed" / "agentdojo_v1_2_2_security_metadata.json",
}


def norm(value):
    if value is None:
        return None
    return str(value)


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dataset_id(cur, name):
    cur.execute(
        """
        SELECT dataset_id
        FROM core.datasets
        WHERE dataset_name = %s
        """,
        (name,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Dataset not found in PostgreSQL: {name}")
    return row[0]


def load_db_maps(cur):
    maps = {}

    for dataset in [
        "JailbreakBench",
        "HarmBench",
        "IndiBias",
        "DefAn",
        "AgentDojo",
    ]:
        did = dataset_id(cur, dataset)

        cur.execute(
            """
            SELECT
                record_id,
                source_record_id
            FROM core.records
            WHERE dataset_id = %s
            """,
            (did,),
        )

        maps[dataset] = {
            row[1]: row[0]
            for row in cur.fetchall()
        }

    return maps


def audit_jailbreakbench(cur, db_maps):
    print("\n" + "-" * 80)
    print("JAILBREAKBENCH VALUE INTEGRITY")
    print("-" * 80)

    rows = read_csv(FILES["JailbreakBench"])
    missing = 0
    mismatches = 0

    for row in rows:
        source_id = row["record_id"]
        pg_record_id = db_maps["JailbreakBench"].get(source_id)

        if pg_record_id is None:
            missing += 1
            continue

        cur.execute(
            """
            SELECT
                rc.goal,
                rc.behavior,
                rc.target,
                jb.behavior_class,
                jb.original_index,
                jb.category,
                jb.source
            FROM core.record_content rc
            JOIN benchmark.jailbreakbench_records jb
              ON jb.record_id = rc.record_id
            WHERE rc.record_id = %s
            """,
            (pg_record_id,),
        )

        db = cur.fetchone()

        expected = (
            row["goal"],
            row["behavior"],
            row["target"],
            row["behavior_class"],
            int(row["original_index"]),
            row["category"],
            row["source"],
        )

        if db != expected:
            mismatches += 1

    print("Source records:", len(rows))
    print("Missing in DB:", missing)
    print("Value mismatches:", mismatches)

    return missing == 0 and mismatches == 0


def audit_harmbench(cur, db_maps):
    print("\n" + "-" * 80)
    print("HARMBENCH VALUE INTEGRITY")
    print("-" * 80)

    rows = read_csv(FILES["HarmBench"])
    missing = 0
    mismatches = 0

    for row in rows:
        source_id = row["record_id"]
        pg_record_id = db_maps["HarmBench"].get(source_id)

        if pg_record_id is None:
            missing += 1
            continue

        cur.execute(
            """
            SELECT
                rc.behavior,
                hb.behavior_id,
                hb.functional_category,
                hb.semantic_category,
                hb.tags,
                hb.context_string
            FROM core.record_content rc
            JOIN benchmark.harmbench_records hb
              ON hb.record_id = rc.record_id
            WHERE rc.record_id = %s
            """,
            (pg_record_id,),
        )

        db = cur.fetchone()

        expected = (
            row["behavior"],
            row["behavior_id"],
            row["functional_category"],
            row["semantic_category"],
            row["tags"] or None,
            row["context_string"] or None,
        )

        if db != expected:
            mismatches += 1

    print("Source records:", len(rows))
    print("Missing in DB:", missing)
    print("Value mismatches:", mismatches)

    return missing == 0 and mismatches == 0


def audit_indibias(cur, db_maps):
    print("\n" + "-" * 80)
    print("INDIBIAS VALUE INTEGRITY")
    print("-" * 80)

    rows = read_csv(FILES["IndiBias"])
    missing = 0
    mismatches = 0

    for row in rows:
        source_id = row["record_id"]
        pg_record_id = db_maps["IndiBias"].get(source_id)

        if pg_record_id is None:
            missing += 1
            continue

        cur.execute(
            """
            SELECT
                dataset_scope,
                source_row_id,
                original_index,
                bias_type,
                stereo_antistereo,
                english_more,
                english_less,
                hindi_more,
                hindi_less
            FROM benchmark.indibias_records
            WHERE record_id = %s
            """,
            (pg_record_id,),
        )

        db = cur.fetchone()

        expected = (
            row["dataset_scope"],
            row["source_row_id"],
            int(row["original_index"]),
            row["bias_type"],
            row["stereo_antistereo"],
            row["english_more"],
            row["english_less"],
            row["hindi_more"],
            row["hindi_less"],
        )

        if db != expected:
            mismatches += 1

    print("Source records:", len(rows))
    print("Missing in DB:", missing)
    print("Value mismatches:", mismatches)

    return missing == 0 and mismatches == 0


def audit_defan(cur, db_maps):
    print("\n" + "-" * 80)
    print("DEFAN VALUE INTEGRITY")
    print("-" * 80)

    rows = read_csv(FILES["DefAn"])
    missing = 0
    mismatches = 0

    for row in rows:
        source_id = row["record_id"]
        pg_record_id = db_maps["DefAn"].get(source_id)

        if pg_record_id is None:
            missing += 1
            continue

        cur.execute(
            """
            SELECT
                rc.question,
                d.source,
                d.domain,
                d.question_type,
                d.original_reference_answer,
                d.reference_answer_available,
                d.answer_source,
                d.verification_status
            FROM core.record_content rc
            JOIN benchmark.defan_records d
              ON d.record_id = rc.record_id
            WHERE rc.record_id = %s
            """,
            (pg_record_id,),
        )

        db = cur.fetchone()

        expected_available = row["reference_answer_available"] in (
            "True",
            "true",
            "1",
        )

        expected = (
            row["question"],
            row["source"],
            int(row["domain"]),
            row["question_type"],
            row["original_reference_answer"] or None,
            expected_available,
            row["answer_source"] or None,
            row["verification_status"],
        )

        if db != expected:
            mismatches += 1

    print("Source records:", len(rows))
    print("Missing in DB:", missing)
    print("Value mismatches:", mismatches)

    return missing == 0 and mismatches == 0


def audit_agentdojo(cur, db_maps):
    print("\n" + "-" * 80)
    print("AGENTDOJO VALUE INTEGRITY")
    print("-" * 80)

    raw = read_json(FILES["AgentDojoRaw"])
    meta = read_json(FILES["AgentDojoMeta"])

    if len(raw) != 35 or len(meta) != 35:
        raise RuntimeError("AgentDojo source count is not 35.")

    # Use the same source-row identity rule as migration:
    # suite::task_id::occurrence
    occurrence = {}
    expected_rows = []

    for row in meta:
        key = (row["suite"], row["task_id"])
        occurrence[key] = occurrence.get(key, 0) + 1

        source_id = (
            f"{row['suite']}::"
            f"{row['task_id']}::"
            f"{occurrence[key]}"
        )

        expected_rows.append(
            (
                source_id,
                row,
            )
        )

    missing = 0
    mismatches = 0

    for source_id, row in expected_rows:
        pg_record_id = db_maps["AgentDojo"].get(source_id)

        if pg_record_id is None:
            missing += 1
            continue

        cur.execute(
            """
            SELECT
                rc.goal,
                a.task_id,
                a.suite,
                a.task_class,
                a.security_source,
                a.ground_truth_source
            FROM core.record_content rc
            JOIN benchmark.agentdojo_records a
              ON a.record_id = rc.record_id
            WHERE rc.record_id = %s
            """,
            (pg_record_id,),
        )

        db = cur.fetchone()

        expected = (
            row["goal"],
            row["task_id"],
            row["suite"],
            row["task_class"],
            row.get("security_source"),
            row.get("ground_truth_source"),
        )

        if db != expected:
            mismatches += 1

    print("Processed source records:", len(meta))
    print("Missing in DB:", missing)
    print("Value mismatches:", mismatches)

    return missing == 0 and mismatches == 0


def run():
    print("=" * 80)
    print("AICAS — POSTGRESQL SOURCE VALUE INTEGRITY AUDIT")
    print("=" * 80)

    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "PGPASSWORD is not set in the current PowerShell session."
        )

    conn = psycopg.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:
            db_maps = load_db_maps(cur)

            results = {
                "JailbreakBench": audit_jailbreakbench(cur, db_maps),
                "HarmBench": audit_harmbench(cur, db_maps),
                "IndiBias": audit_indibias(cur, db_maps),
                "DefAn": audit_defan(cur, db_maps),
                "AgentDojo": audit_agentdojo(cur, db_maps),
            }

        print("\n" + "=" * 80)
        print("FINAL RESULT")
        print("=" * 80)

        for dataset, passed in results.items():
            print(
                f"{dataset:<18}:",
                "PASS" if passed else "FAIL",
            )

        overall = all(results.values())

        print("\n" + "=" * 80)

        if overall:
            print("VALUE INTEGRITY RESULT: PASS")
        else:
            print("VALUE INTEGRITY RESULT: FAIL")

        print("=" * 80)

        if not overall:
            sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    run()