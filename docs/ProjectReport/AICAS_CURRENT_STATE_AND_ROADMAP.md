# AICAS — Current Project State, Blockers, and Roadmap

**Assessment date:** 2026-10-17  
**Basis:** inspection of the v1.0 Data Readiness project archive, its existing audit artifacts, and a fresh run of `python -m pytest ml/tests -q` in the review environment.  
**Evidence limit:** this is not a full production deployment, database migration, frontend build, or end-to-end integration audit. Findings below distinguish confirmed facts from items that still need verification.

## 1. Executive assessment

AICAS has a broad repository structure and an initial ML training/evaluation path, but it is **not yet a validated end-to-end AI security product**. The current bottleneck is not model size. It is data eligibility and reproducibility, clear task definitions, end-to-end integration evidence, and measurable security effectiveness.

The inherited v1.0 review recorded 22 passing ML tests. After approved handoff updates, the current ML-focused test suite passes **35 tests** with one existing scikit-learn dtype warning. This is useful but only establishes the behavior covered by those tests; it does not prove the backend, frontend, PostgreSQL migration, agent tools, and ML pipeline work together.

The S-Labs dataset is **still blocked**. A fresh check on 2026-10-17 verified that the local `train.csv` is byte-identical to the file at pinned revision `002a9dd` (SHA-256 `bab012fec95d4214599b18777fd6efc5cc5e9545354df581880aeca5c1d487d7`). The pinned file contains the same normalized text with labels 0 and 1. Upstream identity is now verified; label quality is not resolved. Keep this source out of training until the publisher or authoritative documentation explains the conflict or provides a corrected revision.

## 2. Current state by workstream

| Workstream | Evidence-backed status | What is holding it back |
|---|---|---|
| Dataset inventory | Six source collections are inventoried in `datasets/audit/DATA_READINESS_REPORT.*` | Inventory and hashes are not the same as provenance, license, or training approval |
| S-Labs external source | Blocked | Pinned bytes verified; one contradictory-label text is present locally and upstream |
| JailbreakBench/HarmBench | Conditional, task-specific use | Nine normalized exact overlaps; source versions and grouping rules must be pinned before splitting |
| DefAn factuality | Reference-grounded subset only | 1,080 records lack original reference answers; 648 normalized duplicate questions need grouping |
| IndiBias | Evaluation-first | 561 local sample rows; paired-context/fairness semantics must be preserved |
| AgentDojo | Evaluation-first | 35 stateful scenarios; not a standalone generic text-classification dataset |
| ML baseline | Initial working path documented | Small 40-example held-out test in prior experiment; reported metrics are too uncertain to claim generalization |
| ML tests | 35 passed on 2026-10-17 | Test scope is concentrated in `ml/tests`; broader integration checks remain unverified |
| Backend/API, frontend, PostgreSQL, agent loop | Present in repository | No fresh end-to-end acceptance result is established by this review |
| Release/reproducibility | Incomplete | Dataset revisions, license/usage decisions, split grouping, environment and experiment manifests need to be release gates |

## 3. Confirmed data issues and risks

### 3.1 S-Labs prompt-injection dataset — hard blocker

Evidence in `datasets/audit/SLABS_CONFLICTING_LABELS.json`, `datasets/audit/SLABS_PINNED_UPSTREAM_VERIFICATION.json`, `datasets/audit/SLABS_UPSTREAM_CONFLICT_INVESTIGATION.md`, and `datasets/audit/DATA_READINESS_REPORT.json`:

- Pinned revision recorded: `002a9dd`.
- Local `train.csv`: 11,089 rows, columns `text`,`label`, 37 duplicate full rows.
- One normalized text appears with both labels 0 and 1. The conflict was recorded at CSV row numbers 2857 and 4626 (header included) in the earlier source audit.
- Local file SHA-256 recorded by the audit: `bab012fec95d4214599b18777fd6efc5cc5e9545354df581880aeca5c1d487d7`.
- Pinned verification status: `PINNED_SOURCE_HAS_CONFLICTS`; local and upstream bytes match at revision `002a9dd`, and both contain the same conflict.
- Exact-overlap and character n-gram audits reported no candidates against the recorded JailbreakBench/HarmBench data, but those limited checks do not rule out semantic leakage.

**Required resolution:** preserve the verified pinned artifact and both conflicting rows; seek an authoritative publisher clarification or corrected upstream revision; document any new revision as a new immutable source artifact; rerun conflict, duplicate, and cross-source audits. If the conflict remains unexplained, keep S-Labs excluded. Do not silently deduplicate, relabel, or drop the conflicting records to make the gate pass.

### 3.2 JailbreakBench and HarmBench overlap

The readiness report records nine normalized exact overlaps between JailbreakBench harmful goals and HarmBench behaviors. These datasets represent related but non-identical concepts. Treating them as independent random rows risks leakage across splits and overstates test performance.

**Required resolution:** preserve source and task identity; group overlapping examples before splitting; pin exact source revisions and artifacts; define labels for each task independently. A `harmful` behavior label must not be renamed to `jailbreak` or `prompt injection` without evidence.

### 3.3 DefAn reference-answer gaps and duplicate questions

The readiness report identifies 70,793 local records, 1,080 without original reference answers, and 648 normalized duplicate questions requiring grouping before splits.

**Required resolution:** use only examples with an auditable reference for reference-grounded factuality tasks; maintain a distinct unavailable-reference state; group duplicate/related questions before splitting. Do not generate synthetic references and present them as source ground truth.

### 3.4 IndiBias and AgentDojo task semantics

IndiBias is a local sample of 561 rows, not proven to be the complete published dataset. Its paired-context comparisons should remain paired for evaluation. AgentDojo has 35 scenarios and depends on agent state and tool interactions. Flattening either into generic prompt labels would discard the property being evaluated.

**Required resolution:** retain them as evaluation-first until a separate task-specific training/evaluation design, provenance record, and split plan are reviewed.

### 3.5 License and provenance gates

The readiness report explicitly says artifact-specific licensing/usage decisions are still required and HarmBench's exact source revision/release pin is incomplete. Dataset availability or a repository-level license does not automatically grant redistribution rights for every included artifact.

**Required resolution:** record source URL, exact commit/release, retrieval date, artifact hashes, license/terms evidence, intended-use decision, transformations, and responsible review for every dataset. Block external redistribution until rights are confirmed.

## 4. ML performance: what can and cannot be concluded

Prior project notes record an initial ModernBERT result on 40 examples, but that result has not been reproduced in this environment. The current TF-IDF baseline was executed on the locked 40-row test split at a threshold selected from validation: accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, average precision 0.542, false-positive rate 0.80, false-negative rate 0.10. Its 95% Wilson interval for FPR is 0.584–0.919. This small test set indicates substantial uncertainty and a high benign false-positive rate; it does not establish deployment performance.

The initial task predicts the source-defined JailbreakBench `behavior_class` from `goal`, excluding `target` to avoid obvious target leakage. This is a behavior classification baseline, not a validated prompt-injection detector. Do not use the results to claim that AICAS detects indirect injection, tool abuse, hallucination, bias, or all jailbreaks.

**Required resolution:** establish reproducible splits with source-aware grouping; run multiple seeds where appropriate; preserve a final untouched test set; report confusion matrix, precision/recall/F1, PR-AUC, FPR/FNR, calibration, latency, throughput, and slices by source/category/transformation. Include a legitimate-task preservation measure. Compare TF-IDF and transformer on the same locked split. Document confidence intervals or uncertainty where sample sizes support them.

## 5. What is dragging the project forward slowly

1. **Too many tracks are being built in parallel.** The repository contains attack generation/evolution, bias, hallucination, leakage, graph, frontend, backend, database, and ML components. Without a single vertical slice with acceptance criteria, integration risk grows faster than verified capability.
2. **Dataset readiness is not yet a reproducible training contract.** Inventory reports exist, but eligibility, task label definitions, source revisions, grouped splits, and immutable manifests must all be enforced by the pipeline.
3. **External-source uncertainty is consuming cycles.** S-Labs cannot be approved based on a failed network fetch; a publisher response or verified clean revision is needed, otherwise the project should proceed without it.
4. **Evaluation evidence is too narrow for broad claims.** A 40-example test is useful for debugging, not for deployment claims. Cross-dataset generalization and legitimate-task false positives remain unproven.
5. **Test coverage does not equal system integration.** The current 22 passing ML tests do not demonstrate the complete API → detector → policy → tool control → outcome logging path or database/frontend compatibility.
6. **Provenance and license decisions are not release-ready.** Missing source pins or rights review can invalidate reproducibility or distribution later.
7. **The product objective is not yet expressed as one measurable acceptance target.** Detection scores alone are insufficient; the system must reduce successful attacks while preserving legitimate user goals and maintaining acceptable latency.

## 6. Recommended target architecture

Build a narrow, auditable gateway before expanding the attack simulator:

1. **Input risk:** distinguish benign, direct prompt injection, jailbreak attempts, and harmful requests using task-appropriate labels (potentially multi-label rather than one forced class).
2. **Context/retrieval risk:** inspect retrieved documents, quoted content, and tool outputs separately from the user's request.
3. **Tool/action risk:** enforce deterministic permission checks and least privilege before consequential tool calls.
4. **Policy aggregator:** produce `ALLOW`, `REVIEW`, or `BLOCK` with reasons, evidence, and calibrated confidence; define fail-safe behavior explicitly.
5. **Output reliability:** check supported/unsupported/contradictory/uncertain answers only when evidence or reference material is available.
6. **Telemetry and audit:** record model/policy versions, source IDs, decision, latency, tool action, and outcome without leaking secrets.
7. **Red-team harness:** run fixed baseline attacks against protected and unprotected target agents; only add adaptive attack evolution after baseline measurements are stable.

Machine-learning scores should not replace deterministic authorization or tool sandboxing.

## 7. Prioritized roadmap and completion gates

### P0 — Close the data-integrity loop

- Preserve the successful pinned S-Labs byte verification and the earlier failed-fetch audit as separate records; seek authoritative resolution of the remaining label conflict.
- Resolve the label conflict authoritatively or permanently exclude this revision from training.
- Pin HarmBench and all other training/evaluation artifacts; document license/usage decisions.
- Re-run exact duplicate, near-duplicate, source-overlap, schema, missingness, and hash checks.
- Gate: every source is `APPROVED`, `CONDITIONAL`, `EVALUATION_ONLY`, or `BLOCKED` with machine-readable reasons; no blocked source can enter a training dataset.

### P1 — Make dataset construction reproducible

- Define separate task specifications and label mappings for each specialist detector.
- Add stable example IDs, source revision/hash, transformation lineage, group IDs, and split assignment to manifests.
- Group duplicate/overlapping examples before train/validation/test split.
- Keep final test data untouched and prevent test data from threshold/model selection.
- Gate: two clean runs from the same pinned inputs produce identical manifests and split membership; raw source hashes remain unchanged.

### P2 — Establish defensible baselines

- Reproduce TF-IDF and transformer results on the locked dataset.
- Inspect false positives/negatives manually by category; prioritize reducing benign false positives without hiding attack misses.
- Evaluate per-source and cross-source generalization; include calibration and operational metrics.
- Gate: predeclared metrics, sample-size caveats, reproducible configs, and error analysis are published; no broad security claim based on a tiny test split.

### P3 — Deliver one end-to-end defensive vertical slice

- Wire input detector → deterministic policy → simulated or sandboxed target/tool action → decision log.
- Add API contract tests, failure handling, authentication/authorization checks where applicable, and database persistence tests.
- Verify frontend against the actual API contract.
- Gate: end-to-end tests cover allow/review/block, tool denial, malformed inputs, timeouts, and audit records.

### P4 — Build evaluation-first attack simulation

- Standardize a target-agent adapter and scenario schema.
- Establish fixed direct and indirect injection suites, baseline success metrics, and repeatable seeds.
- Evaluate protected versus unprotected target behavior and legitimate-task completion.
- Gate: all runs produce versioned reports and are reproducible from scenario/model/policy versions.

### P5 — Add adaptive attacks and broader specialists

- Only after P0–P4 are stable, add mutation/evolution loops with budgets and safety boundaries.
- Add context/tool detector, output reliability, and bias evaluator as separate tasks with their own datasets and metrics.
- Gate: each specialist has independent data approval, held-out tests, failure analysis, and integration acceptance.

### P6 — Release engineering

- Pin Python/package versions and model revisions; capture hardware/runtime details and random seeds.
- Add CI for unit, integration, data-integrity, and smoke tests.
- Establish model/policy rollback, threshold versioning, monitoring, privacy-aware logs, and regression gates.
- Gate: a clean checkout can reproduce the documented checks and produce a signed/versioned evaluation report.

## 8. Immediate next actions

1. Keep S-Labs blocked; do not train on it while the conflict is unresolved.
2. Obtain an authoritative publisher clarification or corrected upstream revision. The pinned bytes now match, but the label conflict remains in both local and upstream data.
3. Pin HarmBench provenance and document artifact-specific terms.
4. Implement source-aware grouped split manifests and a hard training eligibility gate.
5. Reproduce baseline metrics with a larger, locked, leakage-aware evaluation design.
6. Test the end-to-end gateway path before expanding attack-generation features.

## 9. Verification commands

Run from the repository root:

```bash
python -m pytest ml/tests -q
python datasets/audit/build_data_readiness_report.py --repo-root .
python datasets/audit/verify_slabs_pinned_upstream.py --repo-root .
```

Interpretation:

- `ml/tests`: validates only the covered ML/data-audit behaviors; not full-system acceptance.
- readiness report: summarizes local files and existing audit artifacts; it does not approve a dataset by itself.
- S-Labs verification: `PINNED_SOURCE_HAS_CONFLICTS` means bytes match but the source remains ineligible; byte identity does not resolve contradictory labels.

## 10. Final status statement

**AICAS is at an early research/prototype stage with a partially working ML foundation and meaningful data-audit safeguards. It is not yet ready to claim robust end-to-end AI-agent attack detection.** For the current JailbreakBench behavior-classification experiment, S-Labs is not a blocker and stays excluded. Remaining blockers are the missing transformer runtime/model download, the small evaluation set and high false-positive rate, unresolved provenance for other sources (including HarmBench), and unverified full-stack integration. Resolve these in order rather than adding more model complexity or parallel features.


## 11. Approved progress update — locked baseline evaluation

On 2026-10-17, the transformer evaluator was changed so threshold selection and security operating-point analysis use validation data only. The final test split is evaluated once at the selected validation threshold; test-threshold sweeps and best-test operating points are no longer generated. Both baseline and transformer reports now record the dataset-manifest SHA-256 and final test row count, plus 95% Wilson intervals for precision, recall, and false-positive rate.

The TF-IDF baseline was actually run using seed 42 and the current grouped JailbreakBench split (120 train, 40 validation, 40 test). It selected threshold 0.43 on validation and produced the metrics stated in section 4. The test set contains only 20 benign and 20 harmful examples, so interval widths are large. This remains a task-specific research baseline; no prompt-injection, agentic-attack, or deployment claim follows from it.

The transformer evaluator and model comparison were not run in this tranche because PyTorch/model runtime availability was not established here. The TF-IDF report is in `ml/artifacts/security_detector_v0_1/baseline/report.json`.


## 12. Approved progress update — in-process gateway prototype

The repository archive had no backend/database implementation files to connect. A small dependency-free gateway prototype now demonstrates the defensive decision path in `backend/security_gateway.py`: it keeps user input, retrieved content, tool output, and assistant output as distinct surfaces; accepts task-specific detector findings without merging task labels; routes any finding or detector/input failure to `REVIEW`; blocks actions outside an explicit allowlist; requires an injected verifier for approval-gated actions; records a privacy-conscious JSONL authorization event before invoking an action; and records the action outcome separately. Raw text and action parameters are not written to the log.

The prototype is covered by integration-style unit tests for allow, review, block, detector failure, approval verification, action execution, and audit-write failure. The ML test suite now passes 35 tests. This does not establish an HTTP API, authentication, database durability, concurrent audit safety, or production-grade detector quality. Those remain P3/P6 work; only a trusted caller should provide detector findings and approval verification.


## 13. Approved progress update — S-Labs-independent training path

On 2026-10-17, the official Hugging Face dataset API identified JailbreakBench/JBB-Behaviors revision `886acc352a31533ffbcf4ef22c744658688086fc` and declared an MIT license. Both local raw component CSVs were downloaded from that exact revision for comparison and found byte-identical: benign SHA-256 `3cda234d21a991fa309bbfea4b6d9dae31ccdf8e9d452424b6a983e4fdc33468`; harmful SHA-256 `4a8ec6832056b631eb092dccc60d37a61c3d441268268888b3d006288afeffa1`. The verification is recorded in `datasets/audit/JAILBREAKBENCH_PINNED_UPSTREAM_VERIFICATION.json`. The dataset builder now requires that pinned component verification and records its revision in the training manifest.

The ModernBERT model is also pinned to Hub revision `8949b909ec900327062f0ebf497f51aef5e6f0c8`; training metadata will record that revision and the dataset-manifest hash. The model weights are not in the project archive. This pin allows a task-specific JBB training run without S-Labs. The resulting model would classify JBB `behavior_class` from `goal`; it would not be a direct or indirect prompt-injection detector.

Environment check on the available machine: NVIDIA GeForce RTX 2050 with 4 GB VRAM; app Python 3.12.14 has no PyTorch, Transformers, Accelerate, or Safetensors. CUDA PyTorch's Windows wheel was 3.46 GB; the CPU-only wheel download also stalled before installation. No ModernBERT training was started. The already executed TF-IDF baseline is the only classifier trained to date.


## 14. Training readiness and source-size assessment — 2026-10-17

The current trained classifier is a TF-IDF + logistic-regression model for JailbreakBench `behavior_class` prediction from `goal`; it is not a prompt-injection detector. On the 40-row test split it scored accuracy 0.55, precision 0.529, recall 0.90, F1 0.667, FPR 0.80 and FNR 0.10. The FPR is 16/20 benign examples and has a wide Wilson 95% interval (0.584–0.919). No transformer fine-tuning has run because the active Python runtime lacks the required ML packages; hardware is an RTX 2050 with 4 GB VRAM.

The source review did not find a safe, task-matched larger corpus to merge into JBB: Lakera Mosscap contains many unadjudicated prompts and explicitly says not every row is an injection; Lakera PINT combines public/proprietary data and is intended as independent evaluation; Microsoft BIPIA measures contextual indirect-injection robustness across distinct tasks; and deepset `prompt-injections` has only 662 rows plus conflicting Apache-2.0 and CC-BY-4.0 license metadata. Accordingly, the current 200 JBB rows and raw artifacts remain unchanged. This avoids treating row count as quality or collapsing behavior labels into injection labels.

“Certified dataset/model” is not a universal status these sources expose. AICAS requires verified publisher, exact revision, terms, task/label definition, hashes and transformation lineage; this source verification still does not certify label quality or deployment performance. S-Labs remains excluded because its contradictory label exists in both pinned local and upstream bytes. Its unresolved conflict does not block JBB-only work.

The full candidate review and mandatory pre-training gates are in `docs/ProjectReport/ML_TRAINING_READINESS_ASSESSMENT_2026-10-17.md`. In short: select the model claim/task; admit only sources with verified terms and labels; audit duplicates/related examples and freeze source-grouped splits; create a larger independent source-diverse test set before quality claims; install and pin the ML runtime; pass a memory-aware training smoke test; then compare TF-IDF and the pinned ModernBERT on identical splits with threshold selection on validation and one final test evaluation. Until predeclared quality gates pass, the model is advisory and deterministic tool controls remain authoritative.
