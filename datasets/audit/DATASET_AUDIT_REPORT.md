# AICAS Dataset Audit — Initial Baseline

Generated: 2026-10-08T16:53:22.430725+00:00

## Purpose

This audit is a gate before dataset expansion. It checks local structural integrity and records source/provenance findings. It does **not** invent labels and does not modify raw benchmark files.

## Initial verdict

- **No raw files were modified.**
- JailbreakBench: structurally clean locally; suitable for a specialist behavior task, with cross-source overlap controls.
- HarmBench: structurally clean locally, but the local 400-record acquisition must be version/commit pinned before treating it as a complete/current source.
- IndiBias: valid local sample, **not the complete published dataset**.
- DefAn: large and valuable for output reliability; **1,080 records have no original reference answer and remain unsuitable for supervised factuality labels**.
- AgentDojo: valid evaluation source, but 35 scenarios are too small for sole supervised training.
- A normalized exact overlap check found **9 harmful JailbreakBench goals matching HarmBench behavior text**. This is consistent with known source relationships and means the two datasets must not be randomly merged without provenance-aware grouping.

## Dataset status

| Dataset | Local rows/scenarios | Training status | Evaluation status | Main issue |
|---|---:|---|---|---|
| JailbreakBench | 200 | Eligible for specialist task | Yes | Cross-source overlap with HarmBench |
| HarmBench | 400 | Eligible for specialist task | Yes | Local subset/version needs pinning |
| IndiBias | 561 | Evaluation-first | Yes | Local file is a sample |
| DefAn | 70,793 | Reference-answer subset only | Yes | 1,080 missing references; duplicate questions need grouping |
| AgentDojo v1.2.2 | 35 | Evaluation-first | Yes | Too small and stateful for flat supervised training |

## Local integrity findings

### JailbreakBench
- 200 rows: 100 benign + 100 harmful.
- 0 duplicate full rows.
- 0 duplicate record IDs.
- 0 duplicate normalized goals.
- All required fields are populated locally.

### HarmBench
- 400 rows.
- 0 duplicate full rows.
- 400 unique BehaviorID values.
- 320 test + 80 validation records.
- Missing `Tags` and `ContextString` values are preserved rather than fabricated.

### IndiBias
- 561 rows in the locally collected sample.
- 0 duplicate full rows.
- 561 unique source row IDs.
- 454 `stereo`, 107 `antistereo`.
- No missing cells locally.

### DefAn
- 70,793 rows.
- 0 duplicate full rows and 70,793 unique record IDs.
- 69,713 records have original reference answers.
- 1,080 records have no original reference answer.
- 648 duplicate normalized questions are present and must be grouped/deduplicated for supervised splits.

### AgentDojo
- 35 injection scenarios.
- 35 unique task IDs.
- Ground-truth/security metadata is preserved in the processed project representation.
- This remains an evaluation benchmark, not a large flat text-training corpus.

## Expansion gate

No external dataset should enter AICAS training until it has:

1. an identified official/research source;
2. a recorded version or immutable source commit where possible;
3. a SHA-256 hash of the raw file;
4. documented license/usage terms;
5. schema and label validation;
6. duplicate and leakage checks;
7. task-specific label semantics;
8. a declared train/validation/test eligibility;
9. an explanation of why the dataset fills a measured gap.

## Source verification

- JailbreakBench: official project repository and NeurIPS benchmark documentation.
- HarmBench: official Center for AI Safety repository.
- IndiBias: author repository plus NAACL 2024 paper.
- DefAn: author repository plus published paper.
- AgentDojo: official ETH Zurich/SPY Lab repository, local version v1.2.2.

See `SOURCE_VERIFICATION.md` for source links and verification notes.
