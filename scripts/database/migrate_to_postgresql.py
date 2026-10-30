from pathlib import Path
import csv
import json
import os
import sys
import uuid



# ============================================================
# AICAS — POSTGRESQL DATA MIGRATION
#
# Version: 1.0.0
#
# PURPOSE
# -------
# Migrate the validated processed datasets into the AICAS
# PostgreSQL relational database.
#
# IMPORTANT
# ---------
# 1. Raw files are NEVER modified.
# 2. Processed master files are NEVER modified.
# 3. Default mode is DRY RUN.
# 4. Use --execute only after the dry run passes.
# 5. Each dataset is migrated inside a transaction.
# 6. Existing conflicting records cause failure rather than
#    silent overwriting.
# ============================================================


BASE = Path(r"D:\AI-Cognitive-Attack-Simulator-Agent")

DB_NAME = "aicas"
DB_SCHEMA_VERSION = "1.0.0"

EXPECTED_COUNTS = {
    "JailbreakBench": 200,
    "HarmBench": 400,
    "IndiBias": 561,
    "DefAn": 70793,
    "AgentDojo": 35,
}


# ------------------------------------------------------------
# Files
# ------------------------------------------------------------

JAILBREAKBENCH_FILE = (
    BASE
    / "datasets"
    / "jailbreak"
    / "processed"
    / "jailbreakbench_master.csv"
)

HARMBENCH_FILE = (
    BASE
    / "datasets"
    / "benchmark"
    / "harmbench"
    / "processed"
    / "harmbench_behaviors_master.csv"
)

INDIBIAS_FILE = (
    BASE
    / "datasets"
    / "bias"
    / "indibias"
    / "processed"
    / "indibias_master.csv"
)

DEFAN_FILE = (
    BASE
    / "datasets"
    / "hallucination"
    / "defan"
    / "processed"
    / "defan_aicas_master.csv"
)

AGENTDOJO_RAW_FILE = (
    BASE
    / "datasets"
    / "benchmark"
    / "agentdojo"
    / "raw"
    / "agentdojo_v1_2_2_injection_tasks.json"
)

AGENTDOJO_META_FILE = (
    BASE
    / "datasets"
    / "benchmark"
    / "agentdojo"
    / "processed"
    / "agentdojo_v1_2_2_security_metadata.json"
)


# ------------------------------------------------------------
# Dataset registry definitions
# ------------------------------------------------------------

DATASETS = {
    "JailbreakBench": {
        "dataset_family": "jailbreak",
        "dataset_version": "validated-master",
        "source_type": "benchmark",
        "description": "Validated JailbreakBench master dataset.",
    },
    "HarmBench": {
        "dataset_family": "harm",
        "dataset_version": "validated-master",
        "source_type": "benchmark",
        "description": "Validated HarmBench master dataset.",
    },
    "IndiBias": {
        "dataset_family": "bias",
        "dataset_version": "sample",
        "source_type": "benchmark",
        "description": "Validated IndiBias sample dataset.",
    },
    "DefAn": {
        "dataset_family": "hallucination",
        "dataset_version": "validated-master",
        "source_type": "benchmark",
        "description": "Validated DefAn master dataset.",
    },
    "AgentDojo": {
        "dataset_family": "agent_security",
        "dataset_version": "v1.2.2",
        "source_type": "benchmark",
        "description": "AgentDojo v1.2.2 injection-task dataset.",
    },
}


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def fail(message):
    raise RuntimeError(message)


def read_csv(path):
    if not path.exists():
        fail(f"Required file does not exist: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    if not path.exists():
        fail(f"Required file does not exist: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def require_columns(rows, required, dataset):
    if not rows:
        fail(f"{dataset}: file contains zero records.")

    actual = set(rows[0].keys())
    missing = [c for c in required if c not in actual]

    if missing:
        fail(
            f"{dataset}: missing required columns: {missing}"
        )


def check_count(rows, dataset):
    expected = EXPECTED_COUNTS[dataset]

    if len(rows) != expected:
        fail(
            f"{dataset}: expected {expected} records, "
            f"found {len(rows)}."
        )


def check_unique_record_ids(rows, dataset):
    ids = [r["record_id"] for r in rows]

    if any(not x for x in ids):
        fail(f"{dataset}: missing record_id.")

    if len(ids) != len(set(ids)):
        fail(f"{dataset}: duplicate record_id detected.")


def uuid_from_record_id(record_id):
    """
    Convert the validated source record ID into a deterministic UUID.

    UUID5 means running the migration twice produces the same
    database identity for the same source record.
    """
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"AICAS:{record_id}",
        )
    )


def dataset_uuid(dataset_name):
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"AICAS:DATASET:{dataset_name}",
        )
    )


def get_connection():
    import psycopg

    return psycopg.connect(
        dbname=os.getenv("PGDATABASE", DB_NAME),
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )

# ------------------------------------------------------------
# Dataset registration
# ------------------------------------------------------------

def ensure_dataset(conn, dataset_name):
    config = DATASETS[dataset_name]

    dataset_id = dataset_uuid(dataset_name)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO core.datasets (
                dataset_id,
                dataset_name,
                dataset_family,
                dataset_version,
                description,
                source_type
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (dataset_name, dataset_version)
            DO UPDATE SET
                dataset_family = EXCLUDED.dataset_family,
                description = EXCLUDED.description,
                source_type = EXCLUDED.source_type
            RETURNING dataset_id
            """,
            (
                dataset_id,
                dataset_name,
                config["dataset_family"],
                config["dataset_version"],
                config["description"],
                config["source_type"],
            ),
        )

        return cur.fetchone()[0]


# ------------------------------------------------------------
# Common record insertion
# ------------------------------------------------------------

def insert_core_record(
    conn,
    dataset_id,
    source_record_id,
    record_type,
    source_file=None,
    source_split=None,
):
    record_id = uuid_from_record_id(
        f"{dataset_id}:{source_record_id}"
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO core.records (
                record_id,
                dataset_id,
                source_record_id,
                record_type,
                record_version,
                schema_version,
                source_file,
                source_split
            )
            VALUES (
                %s, %s, %s, %s, 1, %s, %s, %s
            )
            ON CONFLICT (record_id)
            DO NOTHING
            """,
            (
                record_id,
                dataset_id,
                source_record_id,
                record_type,
                DB_SCHEMA_VERSION,
                source_file,
                source_split,
            ),
        )

        return record_id


def insert_content(
    conn,
    record_id,
    question=None,
    prompt=None,
    goal=None,
    behavior=None,
    target=None,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO core.record_content (
                record_id,
                question,
                prompt,
                goal,
                behavior,
                target
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (record_id)
            DO UPDATE SET
                question = EXCLUDED.question,
                prompt = EXCLUDED.prompt,
                goal = EXCLUDED.goal,
                behavior = EXCLUDED.behavior,
                target = EXCLUDED.target
            """,
            (
                record_id,
                question,
                prompt,
                goal,
                behavior,
                target,
            ),
        )


def insert_provenance(
    conn,
    record_id,
    source_dataset,
    source_file,
    processing_notes,
):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO core.provenance (
                provenance_id,
                record_id,
                source_dataset,
                source_file,
                processing_version,
                raw_data_modified,
                processing_notes
            )
            VALUES (
                %s, %s, %s, %s, %s, FALSE, %s
            )
            """,
            (
                str(uuid.uuid4()),
                record_id,
                source_dataset,
                source_file,
                DB_SCHEMA_VERSION,
                processing_notes,
            ),
        )


# ------------------------------------------------------------
# JailbreakBench
# ------------------------------------------------------------

def migrate_jailbreakbench(conn, rows):
    dataset_id = ensure_dataset(conn, "JailbreakBench")

    source_file = "jailbreakbench_master.csv"

    for row in rows:
        source_record_id = row["record_id"]

        record_id = insert_core_record(
            conn,
            dataset_id,
            source_record_id,
            "jailbreak_behavior",
            source_file,
            None,
        )

        insert_content(
            conn,
            record_id,
            goal=row["goal"],
            behavior=row["behavior"],
            target=row["target"],
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO benchmark.jailbreakbench_records (
                    record_id,
                    behavior_class,
                    original_index,
                    category,
                    source
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (record_id)
                DO NOTHING
                """,
                (
                    record_id,
                    row["behavior_class"],
                    int(row["original_index"]),
                    row["category"],
                    row["source"],
                ),
            )

        insert_provenance(
            conn,
            record_id,
            "JailbreakBench",
            source_file,
            "Migrated from validated JailbreakBench master.",
        )


# ------------------------------------------------------------
# HarmBench
# ------------------------------------------------------------

def migrate_harmbench(conn, rows):
    dataset_id = ensure_dataset(conn, "HarmBench")

    source_file = "harmbench_behaviors_master.csv"

    for row in rows:
        source_record_id = row["record_id"]

        record_id = insert_core_record(
            conn,
            dataset_id,
            source_record_id,
            "harmbench_behavior",
            source_file,
            row["benchmark_split"],
        )

        insert_content(
            conn,
            record_id,
            behavior=row["behavior"],
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO benchmark.harmbench_records (
                    record_id,
                    behavior_id,
                    functional_category,
                    semantic_category,
                    tags,
                    context_string
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (record_id)
                DO NOTHING
                """,
                (
                    record_id,
                    row["behavior_id"],
                    row["functional_category"],
                    row["semantic_category"],
                    row["tags"] or None,
                    row["context_string"] or None,
                ),
            )

        insert_provenance(
            conn,
            record_id,
            "HarmBench",
            source_file,
            "Migrated from validated HarmBench master.",
        )


# ------------------------------------------------------------
# IndiBias
# ------------------------------------------------------------

def migrate_indibias(conn, rows):
    dataset_id = ensure_dataset(conn, "IndiBias")

    source_file = "indibias_master.csv"

    for row in rows:
        source_record_id = row["record_id"]

        record_id = insert_core_record(
            conn,
            dataset_id,
            source_record_id,
            "indibias_record",
            source_file,
            row["dataset_scope"],
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO benchmark.indibias_records (
                    record_id,
                    dataset_scope,
                    source_row_id,
                    original_index,
                    bias_type,
                    stereo_antistereo,
                    english_more,
                    english_less,
                    hindi_more,
                    hindi_less
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (record_id)
                DO NOTHING
                """,
                (
                    record_id,
                    row["dataset_scope"],
                    row["source_row_id"],
                    int(row["original_index"]),
                    row["bias_type"],
                    row["stereo_antistereo"],
                    row["english_more"],
                    row["english_less"],
                    row["hindi_more"],
                    row["hindi_less"],
                ),
            )

        insert_provenance(
            conn,
            record_id,
            "IndiBias",
            source_file,
            "Migrated from validated IndiBias master.",
        )


# ------------------------------------------------------------
# DefAn
# ------------------------------------------------------------

def migrate_defan(conn, rows):
    dataset_id = ensure_dataset(conn, "DefAn")

    source_file = "defan_aicas_master.csv"

    for row in rows:
        source_record_id = row["record_id"]

        record_id = insert_core_record(
            conn,
            dataset_id,
            source_record_id,
            "defan_question",
            source_file,
            None,
        )

        insert_content(
            conn,
            record_id,
            question=row["question"],
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO benchmark.defan_records (
                    record_id,
                    source,
                    domain,
                    question_type,
                    original_reference_answer,
                    reference_answer_available,
                    answer_source,
                    verification_status
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (record_id)
                DO NOTHING
                """,
                (
                    record_id,
                    row["source"],
                    int(row["domain"]),
                    row["question_type"],
                    row["original_reference_answer"] or None,
                    row["reference_answer_available"]
                    in ("True", "true", "1"),
                    row["answer_source"] or None,
                    row["verification_status"],
                ),
            )

        # IMPORTANT:
        # reference_answer is represented as ground truth.
        # Missing DefAn answers remain NULL.
        if row["reference_answer"]:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO core.ground_truth (
                        ground_truth_id,
                        record_id,
                        ground_truth,
                        available,
                        source,
                        status,
                        verification_status
                    )
                    VALUES (
                        %s, %s, %s, TRUE, %s, %s, %s
                    )
                    """,
                    (
                        str(uuid.uuid4()),
                        record_id,
                        row["reference_answer"],
                        row["answer_source"] or "DefAn",
                        "reference_answer",
                        row["verification_status"],
                    ),
                )

        insert_provenance(
            conn,
            record_id,
            "DefAn",
            source_file,
            "Migrated from validated DefAn AICAS master. "
            "Unanswered records were preserved without generated answers.",
        )


# ------------------------------------------------------------
# AgentDojo
# ------------------------------------------------------------

def load_agentdojo():
    raw = read_json(AGENTDOJO_RAW_FILE)
    meta = read_json(AGENTDOJO_META_FILE)

    if not isinstance(raw, list):
        fail("AgentDojo raw file is not a list.")

    if not isinstance(meta, list):
        fail("AgentDojo metadata file is not a list.")

    if len(raw) != 35:
        fail(f"AgentDojo raw count expected 35, found {len(raw)}.")

    if len(meta) != 35:
        fail(
            "AgentDojo metadata count expected 35, "
            f"found {len(meta)}."
        )

    # task_id is NOT globally unique in the source.
    # Therefore we require a unique canonical source row key.
    #
    # The canonical key is:
    # suite + task_id + row occurrence within the source file.
    #
    # This preserves all 35 source records without inventing
    # uniqueness that does not exist in the source.

    grouped = {}

    for row in meta:
        key = (
            row["suite"],
            row["task_id"],
        )
        grouped.setdefault(key, 0)
        grouped[key] += 1

    return raw, meta, grouped


def migrate_agentdojo(conn, raw, meta):
    dataset_id = ensure_dataset(conn, "AgentDojo")

    raw_by_key = {}

    for row in raw:
        key = (
            row["suite"],
            row["task_id"],
        )

        raw_by_key.setdefault(key, []).append(row)

    meta_by_key = {}

    for row in meta:
        key = (
            row["suite"],
            row["task_id"],
        )

        meta_by_key.setdefault(key, []).append(row)

    if set(raw_by_key) != set(meta_by_key):
        fail(
            "AgentDojo raw/processed key sets do not match."
        )

    source_file = "agentdojo_v1_2_2_security_metadata.json"

    # Preserve every processed row.
    # When a suite/task combination occurs more than once,
    # occurrence_index distinguishes the actual source rows.
    occurrence_counter = {}

    for row in meta:
        key = (
            row["suite"],
            row["task_id"],
        )

        occurrence_counter[key] = (
            occurrence_counter.get(key, 0) + 1
        )

        occurrence = occurrence_counter[key]

        source_record_id = (
            f"{row['suite']}::"
            f"{row['task_id']}::"
            f"{occurrence}"
        )

        record_id = insert_core_record(
            conn,
            dataset_id,
            source_record_id,
            "agentdojo_injection_task",
            source_file,
            None,
        )

        insert_content(
            conn,
            record_id,
            goal=row["goal"],
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO benchmark.agentdojo_records (
                    record_id,
                    task_id,
                    suite,
                    task_class,
                    security_source,
                    ground_truth_source
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (record_id)
                DO NOTHING
                """,
                (
                    record_id,
                    row["task_id"],
                    row["suite"],
                    row["task_class"],
                    row.get("security_source"),
                    row.get("ground_truth_source"),
                ),
            )

        insert_provenance(
            conn,
            record_id,
            "AgentDojo",
            source_file,
            "Migrated from AgentDojo v1.2.2 "
            "processed security metadata.",
        )


# ------------------------------------------------------------
# Preflight
# ------------------------------------------------------------

def preflight_files():
    print("=" * 80)
    print("AICAS — POSTGRESQL MIGRATION PREFLIGHT")
    print("=" * 80)

    csv_specs = [
        (
            "JailbreakBench",
            JAILBREAKBENCH_FILE,
            [
                "record_id",
                "source_dataset",
                "source_file",
                "behavior_class",
                "original_index",
                "goal",
                "target",
                "behavior",
                "category",
                "source",
            ],
        ),
        (
            "HarmBench",
            HARMBENCH_FILE,
            [
                "record_id",
                "source_dataset",
                "source_file",
                "benchmark_split",
                "behavior_id",
                "behavior",
                "functional_category",
                "semantic_category",
                "tags",
                "context_string",
            ],
        ),
        (
            "IndiBias",
            INDIBIAS_FILE,
            [
                "record_id",
                "source_dataset",
                "source_file",
                "dataset_scope",
                "source_row_id",
                "original_index",
                "bias_type",
                "stereo_antistereo",
                "english_more",
                "english_less",
                "hindi_more",
                "hindi_less",
            ],
        ),
        (
            "DefAn",
            DEFAN_FILE,
            [
                "record_id",
                "source",
                "source_file",
                "domain",
                "question",
                "question_type",
                "original_reference_answer",
                "reference_answer",
                "answer_source",
                "reference_answer_available",
                "verification_status",
            ],
        ),
    ]

    loaded = {}

    for dataset, path, required in csv_specs:
        rows = read_csv(path)
        require_columns(rows, required, dataset)
        check_count(rows, dataset)
        check_unique_record_ids(rows, dataset)

        loaded[dataset] = rows

        print(
            f"{dataset:<18} PASS — {len(rows)} records"
        )

    raw, meta, grouped = load_agentdojo()

    print(
        f"{'AgentDojo':<18} PASS — "
        f"{len(meta)} processed records"
    )

    print()
    print("AgentDojo unique (suite, task_id) groups:", len(grouped))
    print(
        "AgentDojo source rows preserved:",
        sum(grouped.values()),
    )

    print("=" * 80)
    print("FILE PREFLIGHT: PASS")
    print("=" * 80)

    return loaded, raw, meta


# ------------------------------------------------------------
# Migration
# ------------------------------------------------------------

def migrate(execute):
    loaded, raw_agentdojo, meta_agentdojo = preflight_files()

    if not execute:
        print()
        print("=" * 80)
        print("DRY RUN COMPLETE")
        print("=" * 80)
        print("No PostgreSQL connection was opened.")
        print("No database records were modified.")
        print()
        print("To perform the migration after reviewing the dry run:")
        print("  python migrate_to_postgresql.py --execute")
        print("=" * 80)
        return

    print()
    print("=" * 80)
    print("AICAS — POSTGRESQL DATA MIGRATION")
    print("=" * 80)

    conn = get_connection()

    try:
        # One overall transaction.
        #
        # If any dataset fails, EVERYTHING rolls back.
        # This is intentional for the first migration.
        with conn.transaction():

            migrate_jailbreakbench(
                conn,
                loaded["JailbreakBench"],
            )

            migrate_harmbench(
                conn,
                loaded["HarmBench"],
            )

            migrate_indibias(
                conn,
                loaded["IndiBias"],
            )

            migrate_defan(
                conn,
                loaded["DefAn"],
            )

            migrate_agentdojo(
                conn,
                raw_agentdojo,
                meta_agentdojo,
            )

        print()
        print("Migration transaction committed successfully.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    print()
    print("=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)

    print()
    print("Expected migrated records:")
    for dataset, count in EXPECTED_COUNTS.items():
        print(f"  {dataset:<18} {count:>7}")

    print()
    print("AICAS-generated records: 0")
    print("DefAn unanswered records were NOT answered.")
    print("Raw files were NOT modified.")
    print("=" * 80)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":

    execute = "--execute" in sys.argv

    try:
        migrate(execute)

    except Exception as exc:
        print()
        print("=" * 80)
        print("MIGRATION FAILED")
        print("=" * 80)
        print(str(exc))
        print()
        print("No partial migration should remain because the")
        print("migration runs inside a PostgreSQL transaction.")
        print("=" * 80)
        sys.exit(1)