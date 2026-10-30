# AICAS dataset-integrity changes

## v0.7 — Near-duplicate discovery

- Added `audit_slabs_near_duplicates.py` for exact normalized overlap and TF-IDF character n-gram near-duplicate candidate discovery.
- Added regression tests for normalization, hash-only exact match reporting, and near-duplicate candidate detection.
- Reports remain review-only; no automated relabeling, deletion, or training approval.
- Existing S-Labs conflict quarantine remains in effect.


## v0.8 — Upstream conflict investigation and reproducible conflict audit

- Added `audit_slabs_conflicting_labels.py`, a read-only, reproducible exact-normalized-text/label conflict audit.
- Added `SLABS_CONFLICTING_LABELS.json` with row locations, observed-text hashes, and raw-file SHA-256.
- Added `SLABS_UPSTREAM_CONFLICT_INVESTIGATION.md` summarizing the bounded public source review and its limitations.
- Corrected the CSV row references to 2857 and 4626 (header included); zero-based dataframe indices are 2855 and 4624.
- S-Labs remains blocked; no source row was changed, deleted, or relabeled.

## v0.9 — Pinned upstream byte verification

- Added `verify_slabs_pinned_upstream.py` to fetch the exact manifest revision, compare local/upstream SHA-256, and compare conflicting-label fingerprints.
- Added offline unit tests for byte identity, mismatch handling, and conflict retention.
- Verification fails closed: network errors and conflicting labels never grant training approval.
- Corrected any stale absolute workspace paths in the near-duplicate report to project-relative paths.
