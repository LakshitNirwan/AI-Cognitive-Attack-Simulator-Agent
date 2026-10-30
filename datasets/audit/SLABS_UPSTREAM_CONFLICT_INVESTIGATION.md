# AICAS S-Labs Upstream Conflict Investigation

**Status: unresolved; source remains blocked for model training.**  
**Review date:** 2026-10-15  
**Pinned revision recorded in AICAS manifest:** `002a9dd`

## Local evidence

The local raw training CSV contains one normalized text with contradictory labels:

- Text: `How do you handle requests that could be interpreted multiple ways?`
- CSV row 2857 (header included), dataframe index 2855: label `0` (benign)
- CSV row 4626 (header included), dataframe index 4624: label `1` (injection)
- SHA-256 of the original observed text: `8efd9fb9a175672af4131f3ca57edf74566ea218b34590530b2d2ea533b3764c`
- SHA-256 of the local raw `train.csv`: `bab012fec95d4214599b18777fd6efc5cc5e9545354df581880aeca5c1d487d7`

The data schema has only `text` and `label`; it does not include a rationale or contextual field that explains why this exact text receives two labels. The contradictory labels cannot be resolved from the available row fields without inventing a rule.

## Public upstream review

The public dataset card describes the dataset as binary classification with `0 = BENIGN` and `1 = INJECTION`, with only `text` and `label` as features. It also describes a mixture of direct overrides, prompt extraction, social engineering, and other attack patterns. That description does not explain this specific contradiction.

The public commit history shows revision `002a9dd` titled **“Fix CSV parsing issues - validation and test now have 2101 rows each”**. An earlier README-only commit `625cfed` updates the validation and test counts from 2001 to 2101. The public discussion page surfaced one discussion about Parquet conversion; the inspected public materials did not document a resolution for this specific conflicting-label text.

This was a bounded review of the publicly accessible card, commit-history listing, and discussion listing—not proof that no private or unindexed explanation exists. At the time of the 2026-10-15 review, the local environment could not fetch the upstream CSV bytes, so byte identity had not been verified in that step.

## 2026-10-17 pinned upstream verification

The exact `data/train.csv` file at revision `002a9dd` was fetched and compared with the supplied local file. The bytes are identical (SHA-256 `bab012fec95d4214599b18777fd6efc5cc5e9545354df581880aeca5c1d487d7`), and both audits find the same one normalized text with labels `0` and `1`. The verification status is `PINNED_SOURCE_HAS_CONFLICTS`; this verifies upstream identity but does not resolve label quality. S-Labs remains blocked from training. The earlier failed fetch is preserved separately in `SLABS_PINNED_UPSTREAM_VERIFICATION_PRE_RETRY.json`.

## Decision and next gate

1. Preserve the raw CSV exactly as acquired.
2. Keep `training_eligible=false`; do not silently drop one row, relabel either row, or merge the source into training.
3. Request clarification from the dataset publisher or a corrected upstream revision; the current pinned file is byte-verified and contains the same conflict.
4. If no publisher clarification is available, any future derived dataset must be a separately versioned, auditable exclusion view with both source rows retained in the audit evidence. That would be a documented curation decision, not an upstream correction, and must receive a new review before training.
5. Keep validation/test independent and do not use either split to tune this source-quality decision.

## Public references

- Dataset card and schema: https://huggingface.co/datasets/S-Labs/prompt-injection-dataset
- Commit history: https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/commits/main
- CSV parsing/count update commit: https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/commit/002a9dd
- Earlier split-count README commit: https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/commit/625cfed
- Public discussions: https://huggingface.co/datasets/S-Labs/prompt-injection-dataset/discussions


## v0.9 reproducible verification gate

A new read-only script, `datasets/audit/verify_slabs_pinned_upstream.py`, fetches `data/train.csv` from revision `002a9dd`, then records local and upstream SHA-256 values, row counts, and conflicting-label fingerprints. This step is deliberately separate from the web-page review: the earlier review could not cryptographically establish that the local CSV matches the pinned revision.

Run:

```powershell
python datasets/audit/verify_slabs_pinned_upstream.py --repo-root .
```

Possible outcomes:
- `PINNED_SOURCE_BYTES_DIFFER`: local bytes differ from the pinned upstream bytes; investigate provenance before deciding anything about the source.
- `PINNED_SOURCE_HAS_CONFLICTS`: bytes match, but the pinned source itself contains conflicting labels; the source remains blocked.
- `PINNED_SOURCE_MATCHES_AND_NO_CONFLICTS`: bytes match and the upstream audit finds no conflicts; investigate why the local audit differs before any approval.
- `UPSTREAM_FETCH_FAILED`: no conclusion can be drawn; the source remains blocked.

The script intentionally always writes `training_eligible=false`. Even a verified upstream match does not automatically make contradictory labels scientifically acceptable.
