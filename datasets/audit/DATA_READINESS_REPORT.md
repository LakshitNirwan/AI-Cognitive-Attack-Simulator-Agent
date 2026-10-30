# AICAS Data Readiness Report — v1.0

Generated (UTC): 2026-10-17T06:47:57.107036+00:00

## Decision summary

This is a readiness checkpoint, not blanket approval to train. Existing raw data was inspected read-only; no records were relabeled or removed.

| Dataset | Local rows/scenarios | Decision |
|---|---:|---|
| JailbreakBench | 200 | `CONDITIONAL_TASK_SPECIFIC_USE` |
| HarmBench | 400 | `CONDITIONAL_TASK_SPECIFIC_USE` |
| IndiBias | 561 | `EVALUATION_FIRST` |
| DefAn | 70793 | `REFERENCE_GROUNDED_SUBSET_ONLY` |
| AgentDojo | 35 | `EVALUATION_FIRST` |
| SLabsPromptInjection | 11089 | `BLOCKED_CONFLICTING_LABELS` |

## S-Labs gate

- Pinned revision: `002a9dd`
- Local contradictory-label texts: `1`
- Pinned verification status: `PINNED_SOURCE_HAS_CONFLICTS`
- Training eligible: **No**
- Reason: Pinned upstream bytes match the supplied local file and contain the same contradictory labels; keep the source blocked pending authoritative label-quality resolution.

## Cross-source overlap snapshot

- JailbreakBench harmful goals ↔ HarmBench behaviors: 9 normalized exact overlaps.
- S-Labs train ↔ JailbreakBench: 0 normalized exact overlaps in the recorded audit.
- S-Labs train ↔ HarmBench: 0 normalized exact overlaps in the recorded audit.
- S-Labs character n-gram near-duplicate candidates at threshold 0.82: 0 reported.
- These results do not prove absence of semantic overlap or leakage.

## Required before training-set construction

1. Resolve the contradictory S-Labs labels with authoritative publisher documentation or a corrected immutable revision; the pinned bytes are verified but the source remains blocked.
2. Pin the exact HarmBench source revision and document artifact-specific redistribution terms.
3. Record artifact-specific licensing/usage decisions for each dataset before redistribution or external release.
4. Define task-specific target labels and split grouping rules before constructing a unified ML dataset.
5. Group overlapping JailbreakBench/HarmBench examples and duplicate DefAn questions before splitting.
6. Keep IndiBias and AgentDojo evaluation-first unless a separately justified task-specific training design is approved.
7. Build a reproducible, source-aware train/validation/test manifest and verify that raw inputs remain unchanged.

## File integrity inventory

The JSON report records relative path, byte size, SHA-256, row/scenario count, columns, null-cell count, and exact duplicate-row count where applicable.

## Rebuild

```bash
python datasets/audit/build_data_readiness_report.py --repo-root .
```

The report is generated from current local files and existing audit artifacts. It does not download data, infer missing labels, or grant training approval.
