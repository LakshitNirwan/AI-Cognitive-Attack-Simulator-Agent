BEGIN;

-- ============================================================
-- AICAS PostgreSQL Schema
-- Schema version: 1.0.0
--
-- IMPORTANT:
--   This creates structure only.
--   No benchmark data is imported here.
--   Raw/processed source files are not modified.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS benchmark;
CREATE SCHEMA IF NOT EXISTS aicas;

-- ============================================================
-- 1. DATASET REGISTRY
-- ============================================================

CREATE TABLE IF NOT EXISTS core.datasets (
    dataset_id       UUID PRIMARY KEY,
    dataset_name     TEXT NOT NULL,
    dataset_family   TEXT NOT NULL,
    dataset_version  TEXT NOT NULL,
    description      TEXT,
    source_type      TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_dataset_name_version
        UNIQUE (dataset_name, dataset_version)
);

-- ============================================================
-- 2. MASTER RECORD IDENTITY
-- ============================================================

CREATE TABLE IF NOT EXISTS core.records (
    record_id         UUID PRIMARY KEY,

    dataset_id        UUID NOT NULL
                      REFERENCES core.datasets(dataset_id),

    source_record_id  TEXT NOT NULL,

    record_type       TEXT NOT NULL,

    record_version    INTEGER NOT NULL DEFAULT 1,

    schema_version    TEXT NOT NULL DEFAULT '1.0.0',

    source_file       TEXT,

    source_split      TEXT,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_record_version_positive
        CHECK (record_version >= 1)
);

CREATE INDEX IF NOT EXISTS idx_records_dataset
    ON core.records(dataset_id);

CREATE INDEX IF NOT EXISTS idx_records_source_record
    ON core.records(dataset_id, source_record_id);

CREATE INDEX IF NOT EXISTS idx_records_record_type
    ON core.records(record_type);

-- ============================================================
-- 3. COMMON RECORD CONTENT
-- ============================================================

CREATE TABLE IF NOT EXISTS core.record_content (
    record_id   UUID PRIMARY KEY
                REFERENCES core.records(record_id)
                ON DELETE CASCADE,

    question    TEXT,
    prompt      TEXT,
    goal        TEXT,
    behavior    TEXT,
    target      TEXT
);

-- ============================================================
-- 4. GROUND TRUTH
-- ============================================================

CREATE TABLE IF NOT EXISTS core.ground_truth (
    ground_truth_id       UUID PRIMARY KEY,

    record_id             UUID NOT NULL
                          REFERENCES core.records(record_id)
                          ON DELETE CASCADE,

    ground_truth          TEXT,

    available             BOOLEAN NOT NULL,

    source                TEXT NOT NULL,

    status                TEXT NOT NULL,

    verification_status   TEXT,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_ground_truth_available
        CHECK (
            (available = TRUE)
            OR
            (available = FALSE)
        )
);

CREATE INDEX IF NOT EXISTS idx_ground_truth_record
    ON core.ground_truth(record_id);

CREATE INDEX IF NOT EXISTS idx_ground_truth_source
    ON core.ground_truth(source);

-- ============================================================
-- 5. PROVENANCE
-- ============================================================

CREATE TABLE IF NOT EXISTS core.provenance (
    provenance_id       UUID PRIMARY KEY,

    record_id           UUID NOT NULL
                        REFERENCES core.records(record_id)
                        ON DELETE CASCADE,

    source_dataset      TEXT NOT NULL,

    source_file         TEXT,

    processing_version  TEXT NOT NULL,

    raw_data_modified   BOOLEAN NOT NULL,

    processing_notes    TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_provenance_record
    ON core.provenance(record_id);

-- ============================================================
-- 6. RELATIONSHIPS
-- ============================================================

CREATE TABLE IF NOT EXISTS core.relationships (
    relationship_id     UUID PRIMARY KEY,

    from_record_id      UUID NOT NULL
                        REFERENCES core.records(record_id)
                        ON DELETE CASCADE,

    to_record_id        UUID NOT NULL
                        REFERENCES core.records(record_id)
                        ON DELETE CASCADE,

    relationship_type   TEXT NOT NULL,

    relationship_source TEXT NOT NULL,

    confidence          NUMERIC(6,5),

    method_version      TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_relationship_not_self
        CHECK (from_record_id <> to_record_id),

    CONSTRAINT chk_relationship_confidence
        CHECK (
            confidence IS NULL
            OR (
                confidence >= 0
                AND confidence <= 1
            )
        ),

    CONSTRAINT uq_relationship
        UNIQUE (
            from_record_id,
            to_record_id,
            relationship_type,
            method_version
        )
);

CREATE INDEX IF NOT EXISTS idx_relationships_from
    ON core.relationships(from_record_id);

CREATE INDEX IF NOT EXISTS idx_relationships_to
    ON core.relationships(to_record_id);

CREATE INDEX IF NOT EXISTS idx_relationships_type
    ON core.relationships(relationship_type);

-- ============================================================
-- 7. EVALUATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS core.evaluations (
    evaluation_id       UUID PRIMARY KEY,

    record_id           UUID NOT NULL
                        REFERENCES core.records(record_id)
                        ON DELETE CASCADE,

    model_id            TEXT NOT NULL,

    model_version       TEXT,

    run_id              TEXT,

    response            TEXT,

    result              TEXT,

    score               NUMERIC,

    evaluator           TEXT,

    evaluation_version  TEXT NOT NULL DEFAULT '1.0.0',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluations_record
    ON core.evaluations(record_id);

CREATE INDEX IF NOT EXISTS idx_evaluations_model
    ON core.evaluations(model_id);

CREATE INDEX IF NOT EXISTS idx_evaluations_run
    ON core.evaluations(run_id);

-- ============================================================
-- 8. JAILBREAKBENCH
-- ============================================================

CREATE TABLE IF NOT EXISTS benchmark.jailbreakbench_records (
    record_id       UUID PRIMARY KEY
                    REFERENCES core.records(record_id)
                    ON DELETE CASCADE,

    behavior_class  TEXT NOT NULL,

    original_index  INTEGER NOT NULL,

    category        TEXT NOT NULL,

    source          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jbb_category
    ON benchmark.jailbreakbench_records(category);

CREATE INDEX IF NOT EXISTS idx_jbb_behavior_class
    ON benchmark.jailbreakbench_records(behavior_class);

-- ============================================================
-- 9. HARMBENCH
-- ============================================================

CREATE TABLE IF NOT EXISTS benchmark.harmbench_records (
    record_id              UUID PRIMARY KEY
                           REFERENCES core.records(record_id)
                           ON DELETE CASCADE,

    behavior_id            TEXT NOT NULL UNIQUE,

    functional_category    TEXT NOT NULL,

    semantic_category      TEXT NOT NULL,

    tags                   TEXT,

    context_string         TEXT
);

CREATE INDEX IF NOT EXISTS idx_hb_functional_category
    ON benchmark.harmbench_records(functional_category);

CREATE INDEX IF NOT EXISTS idx_hb_semantic_category
    ON benchmark.harmbench_records(semantic_category);

-- ============================================================
-- 10. AGENTDOJO
-- ============================================================

CREATE TABLE IF NOT EXISTS benchmark.agentdojo_records (
    record_id          UUID PRIMARY KEY
                       REFERENCES core.records(record_id)
                       ON DELETE CASCADE,

    task_id            TEXT NOT NULL,

    suite              TEXT NOT NULL,

    task_class         TEXT NOT NULL,

    security_source    TEXT,

    UNIQUE (task_id)
);

CREATE INDEX IF NOT EXISTS idx_agentdojo_suite
    ON benchmark.agentdojo_records(suite);

CREATE INDEX IF NOT EXISTS idx_agentdojo_task_class
    ON benchmark.agentdojo_records(task_class);

-- ============================================================
-- 11. INDIBIAS
-- ============================================================

CREATE TABLE IF NOT EXISTS benchmark.indibias_records (
    record_id              UUID PRIMARY KEY
                           REFERENCES core.records(record_id)
                           ON DELETE CASCADE,

    dataset_scope          TEXT NOT NULL,

    source_row_id          TEXT NOT NULL UNIQUE,

    original_index         INTEGER NOT NULL UNIQUE,

    bias_type              TEXT NOT NULL,

    stereo_antistereo      TEXT NOT NULL,

    english_more           TEXT NOT NULL,

    english_less           TEXT NOT NULL,

    hindi_more             TEXT NOT NULL,

    hindi_less             TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_indibias_bias_type
    ON benchmark.indibias_records(bias_type);

CREATE INDEX IF NOT EXISTS idx_indibias_stereo
    ON benchmark.indibias_records(stereo_antistereo);

-- ============================================================
-- 12. DEFAN
-- ============================================================

CREATE TABLE IF NOT EXISTS benchmark.defan_records (
    record_id                    UUID PRIMARY KEY
                                 REFERENCES core.records(record_id)
                                 ON DELETE CASCADE,

    source                       TEXT NOT NULL,

    domain                       INTEGER NOT NULL,

    question_type                TEXT NOT NULL,

    original_reference_answer    TEXT,

    reference_answer_available   BOOLEAN NOT NULL,

    answer_source                TEXT,

    verification_status          TEXT
);

CREATE INDEX IF NOT EXISTS idx_defan_domain
    ON benchmark.defan_records(domain);

CREATE INDEX IF NOT EXISTS idx_defan_question_type
    ON benchmark.defan_records(question_type);

CREATE INDEX IF NOT EXISTS idx_defan_answer_available
    ON benchmark.defan_records(reference_answer_available);

-- ============================================================
-- 13. FUTURE AICAS-GENERATED RECORDS
-- ============================================================

CREATE TABLE IF NOT EXISTS aicas.generated_records (
    record_id                    UUID PRIMARY KEY
                                 REFERENCES core.records(record_id)
                                 ON DELETE CASCADE,

    generation_method             TEXT,

    generation_model              TEXT,

    generation_model_version      TEXT,

    generation_prompt_version     TEXT,

    attack_strategy               TEXT,

    mutation_operator             TEXT,

    generation_parameters         JSONB
);

CREATE INDEX IF NOT EXISTS idx_aicas_generation_model
    ON aicas.generated_records(generation_model);

CREATE INDEX IF NOT EXISTS idx_aicas_attack_strategy
    ON aicas.generated_records(attack_strategy);

-- ============================================================
-- 14. SCHEMA METADATA
-- ============================================================

CREATE TABLE IF NOT EXISTS core.schema_metadata (
    schema_name       TEXT PRIMARY KEY,
    schema_version    TEXT NOT NULL,
    description       TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO core.schema_metadata (
    schema_name,
    schema_version,
    description
)
VALUES (
    'AICAS',
    '1.0.0',
    'Authoritative relational schema for the AICAS unified dataset system.'
)
ON CONFLICT (schema_name)
DO UPDATE SET
    schema_version = EXCLUDED.schema_version,
    description = EXCLUDED.description;

COMMIT;