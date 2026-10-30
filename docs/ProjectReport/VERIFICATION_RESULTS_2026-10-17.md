# AICAS verification results — tranche 3 — 2026-10-17

## Commands and outcomes

From the extracted project root, using app-bundled Python 3.12.14 and temporary workspace-only pytest/scikit-learn/PyYAML dependencies:

```powershell
$env:PYTHONPATH='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\test_packages'
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest ml/tests -q -p no:cacheprovider --basetemp='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\pytest_temp_locked_eval'
```

Result: **30 passed, 1 warning**. The warning is scikit-learn's existing float32-to-float64 dtype notice in the near-duplicate audit test.

```powershell
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' ml/train_tfidf_baseline.py --repo-root .
```

Result: exit 0. Same locked split: 120 train / 40 validation / 40 test. Validation-selected threshold: 0.43. Test metrics: accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, average precision 0.542, FPR 0.80, FNR 0.10; confusion matrix `[[4,16],[2,18]]`. Wilson 95% intervals: precision 0.367–0.685 (18/34), recall 0.699–0.972 (18/20), FPR 0.584–0.919 (16/20). The report's manifest hash was checked against the current split manifest and matched exactly.

```powershell
& '<app-bundled-python>' -c "import torch; print(torch.__version__)"
```

Result: failed with `ModuleNotFoundError: No module named 'torch'`. Transformer training/evaluation and model comparison were not run.

## Test-set handling

Code inspection and regression test confirm the transformer evaluator no longer sweeps thresholds on the final test split or reports best test operating points. Test metrics are computed once at the validation-selected threshold.

## Archive

- File: `aicas_full_project_build_v0_1_fix_UPDATED_2026-10-17_TRANCHE3.zip`
- Complete project tree; ephemeral `__pycache__`, `.pytest_cache`, and `.pyc` omitted.
- ZIP 269 files; 3,681,852 bytes. `ZipFile.testzip()` returned `None`. SHA-256: `C477CA50974B6C0266A0664E4C291C5CFED9C00A8D43B559D9FAAC355DE9A64F`.


---

# AICAS verification results — tranche 4 — 2026-10-17

## Test command

From the project root, using app-bundled Python 3.12.14 and temporary workspace-only test packages:

```powershell
$env:PYTHONPATH='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\test_packages'
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest ml/tests -q -p no:cacheprovider --basetemp='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\pytest_temp_gateway_final'
```

Result: **34 passed, 1 warning**. The warning is scikit-learn's existing float32-to-float64 dtype notice in `test_slabs_near_duplicate_audit.py::test_near_duplicate_candidate_detected`.

Gateway coverage includes allowlisted action execution, review on task-specific finding, block on unknown action, review on detector failure, approval verification, and stopping execution when the authorization audit write fails. Tests used temporary audit logs; no user data or secrets were logged.

This document records project verification. The companion tranche 4 verification deliverable records archive integrity and SHA-256.

## Scope limits

The archive contained no existing backend/database implementation. This tranche adds only an in-process reference gateway. It does not prove HTTP/API behavior, authentication, database persistence, concurrency safety, production detector quality, or end-to-end frontend compatibility.


---

# AICAS verification results — tranche 5 — 2026-10-17

## Dataset upstream verification

Official Hugging Face API pinned `JailbreakBench/JBB-Behaviors` revision `886acc352a31533ffbcf4ef22c744658688086fc`, with the card declaring MIT. Local raw benign and harmful CSVs were fetched from that exact revision into workspace scratch space and compared byte-for-byte: both matched. SHA-256 values are in the project audit artifact. No project raw files were changed.

## Dataset build and tests

```powershell
& '<app-bundled-python>' ml/data/build_dataset.py --repo-root .
```

Result: exit 0; all 200 JBB rows split 120 train / 40 validation / 40 test. The model dataset manifest records the pinned source revision and source component hashes.

```powershell
$env:PYTHONPATH='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\test_packages'
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest ml/tests -q -p no:cacheprovider --basetemp='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\pytest_temp_jbb_pin_final'
```

Result: **35 passed, 1 warning**. Warning: existing scikit-learn float32-to-float64 conversion notice.

```powershell
& '<app-bundled-python>' ml/train_tfidf_baseline.py --repo-root .
```

Result: exit 0. Existing locked split; validation threshold 0.43. Test: accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, FPR 0.80, FNR 0.10, confusion matrix `[[4,16],[2,18]]`. Baseline report's dataset-manifest SHA-256 matches the current dataset manifest.

## Transformer environment check

```powershell
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' ml/train_transformer.py --help
```

Result: exit 1 before argument parsing: `ModuleNotFoundError: No module named 'torch'`. Transformers, Accelerate, and Safetensors are also absent. The machine exposes an RTX 2050 with 4 GB VRAM. A CUDA PyTorch wheel advertised 3.46 GB; a CPU-only wheel transfer did not complete, so neither was installed. No fine-tuning or model comparison was run.

## Training scope and S-Labs

S-Labs remains `BLOCKED_CONFLICTING_LABELS` at pinned revision `002a9dd`; its local/upstream bytes match and both retain the contradiction. It is explicitly excluded. JBB-only behavior-class training is the available path and does not relabel JBB examples as prompt injection.

## Archive

- File: `aicas_full_project_build_v0_1_fix_UPDATED_2026-10-17_TRANCHE5.zip`
- Complete project tree; caches and `.pyc` omitted.
- Final member count, size, integrity, and SHA-256 are recorded below.
