# AICAS verification results — tranche 6 — 2026-10-17

## Scope

Documentation-only training-readiness update. No source code, dataset, split, model, dependency, or audit record was changed. Raw benchmark files and the existing baseline artifact were preserved.

## Evidence reviewed

- Latest project archive: tranche 5, 274 files, 3,694,451 bytes, SHA-256 `1A8EA914423C3AF8B7E27F4DBCA6DBA4785884CB400EACF701EDEC7DE31DBC97`; ZIP integrity check returned `None`.
- Existing JBB data verification: pinned revision `886acc352a31533ffbcf4ef22c744658688086fc`; both local raw CSV component hashes match the recorded official pinned upstream hashes.
- Existing model experiment: 200 rows, split 120/40/40; TF-IDF test accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, FPR 0.80 (16/20 benign), FNR 0.10. The reported Wilson 95% FPR interval is 0.584–0.919.
- Existing environment record: Python 3.12.14 lacks PyTorch, Transformers, Accelerate and Safetensors; RTX 2050 has 4 GB VRAM. No transformer fine-tuning was run.
- Official dataset/model cards and source repositories were reviewed for task scope, reported size, source statement, license/terms metadata and intended evaluation/training role. Candidate source limits and exact links are in the readiness assessment.

## Commands and outcomes

```powershell
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' --version
```

Result: **Python 3.12.14**.

```powershell
$env:PYTHONPATH='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\test_packages'
& 'C:\Users\VICTUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest ml/tests -q -p no:cacheprovider --basetemp='C:\Users\VICTUS\Documents\Codex\2026-10-17\aicas-project-handoff-preserve-existing-work\work\pytest_temp_tranche6'
```

Result: **35 passed, 1 warning, 20.49 seconds**. The warning is the existing scikit-learn float32-to-float64 dtype conversion notice in `test_slabs_near_duplicate_audit.py::test_near_duplicate_candidate_detected`.

The updated archive was checked with Python `zipfile.ZipFile.testzip()` and its SHA-256/file count/size are recorded in the companion delivery verification file.

## Unresolved

- Transformer runtime installation and GPU memory smoke test.
- A larger task-matched, source-diverse training/evaluation plan with verified labels, rights and leakage controls.
- S-Labs label conflict; data remains excluded.
- Independent performance evidence sufficient for any deployment/security-effectiveness claim.

