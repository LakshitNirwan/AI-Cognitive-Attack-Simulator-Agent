# AICAS ML Foundation v0.1 — Security Detector

This directory contains the first real transformer-training pipeline for AICAS.

## Current task

This version trains on the source-defined `behavior_class` field from JailbreakBench:

- `benign`
- `harmful`

It does not redefine these labels as "jailbreak" or "prompt injection".

The model input is the JailbreakBench `goal` field only. The `target` field is retained in source data/provenance but is not used as model input in this first classifier.

## Files

- `data/build_dataset.py` — checks the dataset readiness decision and source hash, then creates deterministic, grouped train/validation/test JSONL files and a manifest.
- `train_transformer.py` — trains a transformer sequence classifier.
- `evaluate.py` — evaluates ModernBERT, selects a threshold on validation data, and reports only the final test metrics at that locked threshold.
- `train_tfidf_baseline.py` — trains/evaluates a TF-IDF + Logistic Regression baseline using the exact same split.
- `compare_models.py` — compares the saved ModernBERT and TF-IDF reports on the same held-out test set.
- `tests/test_dataset_builder.py` — dataset integrity tests.
- `tests/test_threshold_and_baseline.py` — threshold metric/sweep tests.
- `configs/security_detector_v0_1.yaml` — experiment configuration.
- `requirements.txt` — ML dependencies.

## Evaluation policy

The validation set is used for threshold selection. The test set is used only for final reporting at the selected validation threshold. The raw JailbreakBench source is not modified.

The dataset builder only permits the configured JailbreakBench behavior-classification task when its readiness report and processed CSV hash match, and the raw component hashes match the pinned upstream verification artifact. The local component files were verified byte-identical to JailbreakBench/JBB-Behaviors revision `886acc352a31533ffbcf4ef22c744658688086fc`; its dataset card declares MIT. Preserve attribution and review constituent-source terms before redistributing combined or derived artifacts. S-Labs, HarmBench, IndiBias, DefAn, and AgentDojo are outside this training task and are recorded as excluded. S-Labs remains blocked and is not used for this task; it is not a prerequisite for JailbreakBench behavior-classification training.

Exact normalized goal duplicates with the same label stay in the dataset and are assigned to one split by a stable group ID. Conflicting labels for the same normalized goal stop the build. Current grouping catches exact normalized duplicates; it does not claim to resolve semantic similarity.

Threshold analysis also records two security-oriented operating points:

1. The best validation operating point among thresholds with zero false-negative rate.
2. The best-recall validation operating point among thresholds with false-positive rate at or below 20%, when such a point exists.

Security-oriented threshold diagnostics are calculated on validation only. The final test split is evaluated once at the locked validation threshold. Reports include Wilson 95% intervals for precision, recall, and false-positive rate.

## Expected repository layout

```text
AI-Cognitive-Attack-Simulator-Agent/
├── datasets/
│   └── jailbreak/
│       └── processed/
│           └── jailbreakbench_master.csv
└── ml/
    ├── configs/
    ├── data/
    ├── tests/
    ├── compare_models.py
    ├── evaluate.py
    ├── requirements.txt
    ├── train_tfidf_baseline.py
    └── train_transformer.py
```

## Run from repository root

```bash
python -m pip install -r ml/requirements.txt
python ml/data/build_dataset.py --repo-root .
python -m pytest -q
python ml/train_tfidf_baseline.py --repo-root .
python ml/train_transformer.py --repo-root .
python ml/evaluate.py --repo-root .
python ml/compare_models.py --repo-root .
```

The default transformer is `answerdotai/ModernBERT-base`.

The first transformer run requires internet access to download the model/tokenizer unless they are already cached locally.

Generated experiment artifacts go under:

```text
ml/artifacts/security_detector_v0_1/
```

Do not commit large model weights to Git unless the project later adopts a deliberate artifact-storage strategy.


## Defensive gateway prototype

`backend/security_gateway.py` is an in-process policy/action-control reference path. It requires an injected detector and approval verifier; findings stay tied to their input surface and task. Any finding or detector failure requires review, and actions run only after allowlist and approval checks. Authorization is logged before execution, and outcome is logged afterward without raw content or action parameters. It is not yet an HTTP service and does not provide authentication, database persistence, or concurrent audit guarantees.

## Transformer training preflight

Before starting a full fine-tuning run, rebuild the prepared split and validate the
configured inputs:

```bash
python ml/data/build_dataset.py --repo-root .
python ml/training_preflight.py --repo-root . --check-only
```

The check-only report is written to
`ml/artifacts/security_detector_v0_1/preflight_report.json`. It validates the
configured task/model revision and the prepared training JSONL; it does not load a
model or train anything.

After installing `ml/requirements.txt`, run the one-batch forward/backward smoke
test:

```bash
python ml/training_preflight.py --repo-root .
```

This loads the configured pinned model/tokenizer, runs one optimizer step on one
training example, and writes the result to the same report path. The first run may
need network access to fetch the pinned model. To require a local model cache, add
`--local-files-only`. A blocked report is written on dependency, model-download,
configuration, or runtime failure; it is not evidence that training succeeded.

The smoke test is not a full training run. S-Labs remains excluded from this
experiment; the configured task is JailbreakBench behavior classification only.
