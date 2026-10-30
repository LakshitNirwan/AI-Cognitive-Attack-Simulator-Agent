# AICAS handoff tranche 3 — locked baseline evaluation — 2026-10-17

## Problem and root cause

The transformer evaluator selected its production threshold on validation data, but also swept thresholds on the final test data and reported the best test operating points. That exposed the final test set to selection-oriented analysis and could encourage test tuning. The prior experiment reports also lacked a direct uncertainty interval and a hash pointer to the exact split manifest.

## Changes

- Removed final-test threshold sweeps and best-test operating-point reporting. Threshold selection and security-oriented diagnostics now use validation only; test metrics use the selected validation threshold once.
- Added 95% Wilson score intervals for precision, recall, and false-positive rate, including successes and denominators so uncertainty is interpretable.
- Added the dataset manifest path and SHA-256, final test row count, and a machine-readable statement that test data was not used for threshold selection to both model reports.
- Corrected stale S-Labs verification wording in the dataset manifest, inventory, and gap matrix. The pinned upstream bytes matched on 2026-10-17 and contain the same conflict; S-Labs remains blocked.
- Executed TF-IDF + logistic regression on the existing locked grouped split. No raw data or split assignments were changed.

## Changed paths

- `ml/evaluate.py`
- `ml/train_tfidf_baseline.py`
- `ml/tests/test_threshold_and_baseline.py`
- `ml/README.md`
- `ml/artifacts/security_detector_v0_1/baseline/config.json`
- `ml/artifacts/security_detector_v0_1/baseline/report.json`
- `ml/artifacts/security_detector_v0_1/baseline/thresholds_validation.json`
- `ml/artifacts/security_detector_v0_1/dataset/manifest.json` (stale S-Labs description corrected; split assignments unchanged)
- `datasets/inventory/DATASET_INVENTORY.md`
- `datasets/audit/DATASET_GAP_MATRIX.md`
- `docs/ProjectReport/AICAS_CURRENT_STATE_AND_ROADMAP.md`
- `docs/ProjectReport/CHANGELOG_HANDOFF_2026-10-17.md`
- `docs/ProjectReport/VERIFICATION_RESULTS_2026-10-17.md`

## Verification

- ML tests: **30 passed, 1 warning**. The warning is the existing scikit-learn float32-to-float64 dtype notice in `test_slabs_near_duplicate_audit.py::test_near_duplicate_candidate_detected`.
- TF-IDF baseline ran successfully. Validation selected threshold 0.43. Locked 40-row test: accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, average precision 0.542, FPR 0.80, FNR 0.10; confusion matrix `[[4,16],[2,18]]`. FPR Wilson 95% interval: 0.584–0.919. These results are too uncertain and show too many benign false positives for deployment claims.
- The baseline report's dataset-manifest SHA-256 matches the current split manifest: `b4728a63d51ff811375cb2f926c0504f3b24ced1283db073b5803aaeca06839a`.
- A direct import check for PyTorch failed with `ModuleNotFoundError: No module named 'torch'`; transformer training/evaluation and model comparison were not run.

## Remaining limitations

The test set has only 20 benign and 20 harmful examples. The TF-IDF result measures JailbreakBench behavior-class classification only. ModernBERT reproduction, calibration, latency, throughput, source slices, larger independent evaluation, and the full-stack security path remain outstanding. S-Labs remains excluded pending authoritative label-quality resolution.


---

# AICAS handoff tranche 4 — P3 gateway prototype — 2026-10-17

## Problem and root cause

The archive's backend and database directories contained no implementation files, so the P3 API → detector → policy → tool control → audit path did not exist. AICAS did have a separate simulation target adapter, but it was not an application security gateway.

## Changes

- Added `backend/security_gateway.py`, a dependency-free in-process reference flow that keeps user input, retrieved content, tool output, and assistant output distinct.
- Added a task-preserving detector contract; any finding and any detector/input error routes to `REVIEW`. Confidence is recorded but is not used as a calibrated policy threshold.
- Added deterministic action allowlisting and verified-approval callbacks. Actions do not run on `REVIEW`/`BLOCK`, without an executor, or if the authorization audit write fails.
- Added JSONL authorization-before-action and execution-outcome records. Raw content, action parameters, and executor results are omitted.
- Added integration-style tests covering allow, review, block, detector failure, approval verification, action execution, and audit failure.
- Documented the trust boundary and production gaps.

## Changed paths

- `backend/__init__.py`
- `backend/security_gateway.py`
- `ml/tests/test_security_gateway.py`
- `ml/README.md`
- `docs/ProjectReport/SECURITY_GATEWAY_V0_1.md`
- `docs/ProjectReport/AICAS_CURRENT_STATE_AND_ROADMAP.md`
- `docs/ProjectReport/CHANGELOG_HANDOFF_2026-10-17.md`
- `docs/ProjectReport/VERIFICATION_RESULTS_2026-10-17.md`

No raw benchmark or dataset files were changed.

## Verification

- `python -m pytest ml/tests -q -p no:cacheprovider --basetemp <workspace temp>`: **34 passed, 1 warning**. The warning is the existing scikit-learn float32-to-float64 dtype notice in the near-duplicate audit test.
- ZIP integrity and SHA-256 are recorded in the verification results.

## Remaining limitations

This is not an HTTP API and supplies no authentication, human review workflow, database durability, concurrency/tamper guarantees, or ML detector. Detector and approval verification must be provided by a trusted caller. The prototype is not production-ready.


---

# AICAS handoff tranche 5 — training readiness and source pin — 2026-10-17

## Findings from the latest archive

The tranche 4 ZIP passed integrity verification. It already contained a trained TF-IDF + logistic-regression baseline, but no ModernBERT model weights. The baseline is task-specific JailbreakBench behavior-classification from `goal`, not prompt-injection classification. The latest ZIP also had stale manifest wording that described S-Labs upstream verification as unsuccessful even though its audit record says pinned bytes matched and labels conflict.

## Changes and evidence

- Queried the official Hugging Face dataset API and downloaded the two JBB raw source components at pinned revision `886acc352a31533ffbcf4ef22c744658688086fc` into workspace scratch space for read-only comparison. Both local files are byte-identical to those pinned upstream files; their SHA-256 hashes are recorded in `datasets/audit/JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json`. Raw project files were not changed.
- The upstream dataset card declares MIT. The verification/provenance notes retain attribution and flag review of constituent-source terms before redistribution of combined/derived data.
- Updated the training gate to require the pinned verification artifact and matching component hashes; the generated manifest now records JBB revision and declared license. The JBB-only training task continues to exclude S-Labs.
- Pinned ModernBERT to Hub revision `8949b909ec900327062f0ebf497f51aef5e6f0c8`; training metadata records model revision and split-manifest SHA-256. Model weights were not downloaded.
- Corrected stale S-Labs verification wording and updated current-state/readme documentation.
- Rebuilt deterministic JBB splits and reran the TF-IDF baseline. Membership and metrics were unchanged.

## Changed paths

- `datasets/audit/JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json`
- `datasets/jailbreak/processed/jailbreakbench_provenance.json`
- `ml/data/build_dataset.py`
- `ml/tests/test_dataset_builder.py`
- `ml/configs/security_detector_v0_1.yaml`
- `ml/train_transformer.py`
- `ml/artifacts/security_detector_v0_1/dataset/{train,validation,test}.jsonl` (same membership; deterministically rebuilt)
- `ml/artifacts/security_detector_v0_1/dataset/manifest.json`
- `ml/artifacts/security_detector_v0_1/baseline/{config,report,thresholds_validation}.json`
- `ml/README.md`
- `docs/ProjectReport/AICAS_CURRENT_STATE_AND_ROADMAP.md`
- `docs/ProjectReport/CHANGELOG_HANDOFF_2026-10-17.md`
- `docs/ProjectReport/VERIFICATION_RESULTS_2026-10-17.md`

No S-Labs records were changed, dropped, relabeled, or used.

## Verification

- `python ml/data/build_dataset.py --repo-root .`: exit 0; 200 rows produced 120/40/40 grouped splits.
- `python -m pytest ml/tests -q -p no:cacheprovider --basetemp <workspace temp>`: **35 passed, 1 warning** (existing scikit-learn float dtype notice).
- `python ml/train_tfidf_baseline.py --repo-root .`: exit 0; validation threshold 0.43; test accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, FPR 0.80, FNR 0.10. The baseline report manifest hash matches the generated dataset manifest.
- `python ml/train_transformer.py --help`: exit 1, `ModuleNotFoundError: No module named 'torch'`. No ModernBERT training has been run. PyTorch CUDA wheel is 3.46 GB; the smaller CPU wheel download did not complete in this environment.
- ZIP file count, integrity, and SHA-256 are recorded in the companion verification report.

## What remains before transformer fine-tuning

Install a compatible, pinned PyTorch/Transformers runtime and download the pinned ModernBERT snapshot; set a memory-safe training mode for the 4 GB RTX 2050 or use CPU; then run a first training smoke run, validation checkpoint selection, and one locked test evaluation. S-Labs publisher resolution is not part of this critical path. The 40-row test remains too small and the false-positive rate too high for deployment or broad security claims.
