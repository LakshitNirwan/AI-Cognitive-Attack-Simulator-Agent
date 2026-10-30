# AICAS S-Labs Integrity Stage v0.8

This update is integrated into the full AICAS project archive.

## Decision

The supplied S-Labs `train.csv` contains one identical text with conflicting labels:
- CSV rows (including header): 2857 and 4626
- labels: 0 and 1
- text SHA-256: `8efd9fb9a175672af4131f3ca57edf74566ea218b34590530b2d2ea533b3764c`

The source remains **blocked for training**. The bounded public upstream review did not find a resolution for this contradiction; see `datasets/audit/SLABS_UPSTREAM_CONFLICT_INVESTIGATION.md`. Raw data is preserved and must not be relabeled or silently cleaned.

## Run tests

From the project root:

```powershell
python -m pytest ml/tests -q
```

## Exact normalized cross-source overlap audit

From the project root:

```powershell
python datasets/audit/audit_slabs_cross_source.py --repo-root .
```

The report is written to `datasets/audit/SLABS_CROSS_SOURCE_AUDIT.json`. This checks exact normalized text overlap only, not paraphrases or semantic near-duplicates.

## Acquisition behavior

The acquisition script downloads upstream splits and audits schema, row counts, duplicate texts, conflicting labels, cross-split overlap, and SHA-256. A source that fails an integrity check remains blocked. The local supplied train CSV is retained as evidence; do not hand-edit it.


## Near-duplicate discovery (v0.7)

Run from the project root:

```powershell
python datasets/audit/audit_slabs_near_duplicates.py --repo-root . --threshold 0.82
```

The tool uses character n-gram TF-IDF cosine similarity to propose candidates for human review. It reports exact normalized overlap and near-duplicate candidates with similarity scores and text hashes. Candidate matches are not automatically treated as confirmed leakage. It never edits source CSVs, and the report remains `REVIEW_REQUIRED`; this audit alone cannot approve S-Labs for training.

If a dataset's columns or file paths differ, pass `--jailbreakbench`, `--harmbench`, and/or `--slabs` with the correct paths. The default threshold is a review threshold, not a scientifically universal cutoff.


## Conflicting-label audit (v0.8)

Run from the project root:

```powershell
python datasets/audit/audit_slabs_conflicting_labels.py --repo-root .
```

Expected for the currently supplied raw file: exit code `2`, status `BLOCKED_CONFLICTS_FOUND`, and one conflicting normalized text in `datasets/audit/SLABS_CONFLICTING_LABELS.json`. Exit code 2 is intentional: it signals that this source fails the gate. The audit is read-only and records both CSV row numbers and hashes.

The CSV row numbers include the header row: **2857** and **4626**. The dataframe indices are zero-based: **2855** and **4624**.


## Pinned upstream byte verification (v0.9)

Run with network access from the project root:

```powershell
python datasets/audit/verify_slabs_pinned_upstream.py --repo-root .
```

This fetches `data/train.csv` from the exact revision recorded in the manifest (`002a9dd`), computes SHA-256 for both the local and remote files, and compares conflicting-label fingerprints. It does not modify either file. A network failure produces `UPSTREAM_FETCH_FAILED`; different bytes produce `PINNED_SOURCE_BYTES_DIFFER`; matching bytes that still contain conflicts produce `PINNED_SOURCE_HAS_CONFLICTS`. All outcomes keep `training_eligible=false`. A byte match alone cannot clear a label-quality issue.
