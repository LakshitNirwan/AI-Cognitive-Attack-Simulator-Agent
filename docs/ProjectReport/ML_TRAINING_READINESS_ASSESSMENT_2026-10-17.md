# AICAS ML training readiness assessment — 2026-10-17

## Decision

**Do not expand or relabel the current training corpus in this tranche. Do not claim that the current classifier is an injection detector.** Keep the existing JailbreakBench (JBB) behavior-class task and its raw inputs unchanged. It has 200 examples (100 benign, 100 harmful behavior requests), split 120/40/40. Its test set has only 20 benign examples, and the measured 80% false-positive rate is 16/20. That is a serious signal, but too small a denominator to estimate deployment performance precisely (Wilson 95% interval recorded by the project: 0.584–0.919).

The current ML baseline has already been trained: TF-IDF + logistic regression on JBB `goal` text. It achieved test accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, FPR 0.80 and FNR 0.10 at the validation-selected threshold. These are poor and uncertain results, not a production-ready detector. No transformer fine-tuning has run. The available Python environment lacks PyTorch, Transformers, Accelerate and Safetensors; the machine has an RTX 2050 with 4 GB VRAM.

## Task and candidate-source review

| Source/model | Verified evidence | Training decision |
|---|---|---|
| JBB-Behaviors | Official dataset card and repository; pinned revision `886acc352a31533ffbcf4ef22c744658688086fc`; local raw benign/harmful components were byte-compared to that revision in the prior tranche. 200 examples, 100 per source-defined behavior class. | Keep as the existing JBB behavior-classification task. Do not interpret it as prompt injection, indirect injection, or tool abuse. A larger independent held-out evaluation set is required before making quality claims. |
| S-Labs | Local bytes match pinned upstream revision `002a9dd`; a normalized text has both labels 0 and 1 in both copies. | Remains excluded. Upstream identity verification succeeded; authoritative label-quality resolution did not. This source is not needed for the JBB-only task. Do not delete, relabel, or bypass the conflict. |
| deepset `prompt-injections` | Official Hub card shows 546 train and 116 test records. The card’s displayed license is Apache-2.0 while embedded dataset metadata declares CC-BY-4.0. | Not admitted until the publisher resolves the license discrepancy, the exact pinned artifacts and label semantics are audited, and duplicates are checked. Its size alone would not establish generalization. |
| Lakera `mosscap_prompt_injection` | Official card describes 278,945 rows (223,533 train, 27,683 validation, 27,729 test) and MIT. Its author explicitly says every submitted prompt is included, whether or not it is actually an injection, and that many prompts are not injections. | Do not use raw rows as binary labels. It is a large source of unadjudicated prompts, not a labeled injection corpus. Any future use would need a documented annotation protocol, label provenance and quality review; that work would create new labels and cannot be represented as publisher ground truth. |
| Lakera PINT | Official benchmark repository describes 4,314 inputs, including public and proprietary data, with injections, jailbreaks, hard negatives, chats and documents. It is intended as an independent detector benchmark. | Evaluation-only. Do not train on it or attempt to reconstruct proprietary rows. Use only data expressly published for permitted use; the repository’s code license does not grant rights to proprietary benchmark inputs. |
| Microsoft BIPIA | Official repository covers five task contexts (Web QA, Email QA, Table QA, Summarization, Code QA) for indirect-injection robustness; it explicitly calls out source-data licensing restrictions for Web QA and Summarization. Its evaluation is agent/context behavior, not a flat binary label for JBB request goals. | Evaluation-first, per task. Do not flatten its scenarios into JBB labels. Resolve source terms and pin the data before any acquisition or task-specific training. |
| ModernBERT-base | Official Answer.AI model card lists Apache-2.0, 149M parameters, and use as a pretrained encoder requiring downstream fine-tuning for classification. Project config pins revision `8949b909ec900327062f0ebf497f51aef5e6f0c8`. | Model identity/license are pinned, but this is not a security certification or proof of task performance. Keep as a candidate for a controlled comparison after task data and runtime gates pass. Current hardware/runtime makes the configured batch 8 / length 512 setup unverified. |

“Certified” is not a universal certification status attached to these datasets or models. For AICAS, use the term only to mean that the publisher, exact revision, license/terms, intended task, schema, hashes and transformations have been independently recorded and checked. Even that source-verification bar does not certify label correctness, representativeness, security effectiveness or suitability for deployment.

## Why not enlarge the current set immediately

Adding examples is useful only when they teach the same clearly defined target and come with defensible labels and provenance. The currently reviewed larger sources fail at least one of these conditions: Mosscap contains unadjudicated prompts; PINT includes proprietary evaluation data and must remain held out; BIPIA tests contextual agent tasks; deepset has a licensing inconsistency and only 662 total rows. Mixing these sources into the JBB behavior-class task would change its semantics or introduce uncertain labels. Keeping them out is a quality-preserving decision, not a claim that 200 rows are enough.

The 80% FPR does not prove that TF-IDF alone caused the problem, nor does it prove a transformer will fix it. The next comparison must retain the same locked task and split for debugging, but a credible generalization claim also needs a larger, source-diverse, leakage-audited test set that stays untouched during tuning. With only 20 benign test examples, each error changes FPR by five percentage points.

## Mandatory gates before a credible training run

1. **Choose the claim and task.** Decide whether the next model is JBB harmful-behavior classification or direct/indirect prompt-injection detection. Keep separate label definitions, datasets, reports and model identities. Do not treat all harmful behavior as injection.
2. **Admit only task-matched data.** For every source, record the official publisher URL, immutable revision, retrieval date, file hashes, license/terms, label definition, source lineage, transformation and intended use. Resolve the deepset card conflict before using it. Do not use S-Labs until an authoritative correction resolves the conflict.
3. **Audit labels and leakage before split.** Preserve raw bytes. Detect exact and normalized duplicates, near-duplicates and known source overlaps; group related records before splitting. Keep original labels, exclusions and reasons in the manifest. Do not generate labels or references and call them upstream ground truth.
4. **Make a larger evaluation set before training for a quality claim.** Obtain independently sourced, task-matched benign and positive examples under explicit terms. Use a locked source-separated test set with enough benign examples to report meaningful FPR intervals; choose sample size from the desired interval width and class prevalence, not an arbitrary total. Keep PINT or equivalent blind evaluation data untouched.
5. **Freeze experiment design.** Record seed, split-manifest hash, tokenizer/model pin, package versions, max length, precision mode, batch size, gradient accumulation, stopping/checkpoint selection rule and threshold selection rule. Validation can select checkpoints/thresholds; test is used once for final evaluation.
6. **Make the runtime usable.** Install compatible pinned ML dependencies in the intended runtime, verify model download hash/revision and available memory, then run a one-batch forward/backward smoke test. On 4 GB VRAM, start with a memory-safe configuration (small per-device batch, gradient accumulation, shorter sequence length and mixed precision only if supported); record actual peak memory. If that fails, use a controlled CPU/cloud environment with its provenance recorded.
7. **Run and compare.** Compare TF-IDF and a pinned pretrained encoder on identical train/validation/test membership. Perform error analysis on benign false positives and false negatives. Report confusion matrix, precision, recall, F1, PR-AUC, FPR/FNR with confidence intervals, calibration, throughput/latency, per-source/category slices and legitimate-task preservation. Do not tune on test results.
8. **Keep enforcement independent.** Until the detector meets predeclared acceptance criteria on held-out and adversarial evaluation, treat it as advisory. Tool authorization, allowlists, approval checks and sandboxing remain deterministic controls; model scores do not authorize consequential actions.

## Immediate execution order and stop conditions

1. Preserve the current JBB artifact and baseline as the reproducible reference. The JBB-only path already avoids S-Labs.
2. Select and document one near-term model claim. If it is direct injection detection, stop using JBB as its training label source and complete source admission for a dedicated injection dataset first. If it is JBB behavior classification, keep its label/task name unchanged and obtain additional eligible JBB-like data or limit the result to a small research baseline.
3. Establish a separately locked, source-diverse test set and freeze the acceptance metrics before model comparison.
4. Resolve runtime/hardware fit and execute the smoke test.
5. Train only after gates 1–4 pass. Stop or report “not ready” if source terms, labels, split leakage, runtime or acceptance criteria fail.

There is no defensible date-based promise for a good model before the data and runtime gates pass. Technically, the project has already started model work with the TF-IDF baseline. Transformer fine-tuning can start after the runtime smoke test, but a credible security-quality claim also depends on obtaining eligible task-matched training data and a sufficiently informative independent evaluation set. The S-Labs issue does not block the JBB-only workstream and is not to be bypassed.

## Source links

- JBB repository and task documentation: <https://github.com/JailbreakBench/jailbreakbench>
- deepset prompt-injections dataset card: <https://huggingface.co/datasets/deepset/prompt-injections>
- Lakera Mosscap dataset card: <https://huggingface.co/datasets/Lakera/mosscap_prompt_injection>
- Lakera PINT benchmark: <https://github.com/lakeraai/pint-benchmark>
- Microsoft BIPIA benchmark: <https://github.com/microsoft/BIPIA>
- ModernBERT-base model card: <https://huggingface.co/answerdotai/ModernBERT-base>

