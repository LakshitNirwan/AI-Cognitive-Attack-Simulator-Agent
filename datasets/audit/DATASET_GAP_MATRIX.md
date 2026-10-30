# AICAS Dataset Gap Matrix — v0.3

## Purpose

This document defines what the current AICAS datasets cover, what they do not cover,
and which external benchmark sources are candidates for filling measured gaps.

**Policy:** no candidate dataset is automatically approved for training. A candidate must
pass provenance, license, schema, label, duplication, leakage, and reproducibility checks
before acquisition into `datasets/raw/`.

## Current coverage

| Capability | Existing source(s) | Current evidence | Gap | Decision |
|---|---|---|---|---|
| Harmful/jailbreak behavior | JailbreakBench, HarmBench | 200 + 400 local records | Small supervised pool; overlap exists | Expand carefully; keep source identity |
| Direct prompt injection | No dedicated large local benchmark | Existing sources do not cleanly represent this task | **High** | Highest-priority gap |
| Indirect prompt injection | AgentDojo | 35 local scenarios | Too small for supervised training | Evaluation-first; add dedicated benchmark(s) |
| Agent/tool abuse | AgentDojo | 35 scenarios | Small | Evaluation-first |
| Output factuality/reliability | DefAn | 70,793 local records; some lack references | Reference-grounded subset needs isolation | Use only records with valid original evidence/reference |
| Bias/fairness | IndiBias | 561 local records; local sample | Incomplete local coverage | Evaluation-first; obtain official full release only after provenance/license audit |
| Multilingual security | Limited coverage across existing sources | No dedicated balanced multilingual security training set | **High** | Add only after source audit |
| Cross-dataset generalization | Multiple sources | Potential source overlap | Leakage risk | Build source-separated external test sets |

## Candidate external sources

### 1. InjecAgent — high-priority indirect-injection evaluation

- Official repository: `https://github.com/uiuc-kang-lab/InjecAgent`
- Reported size: 1,054 test cases.
- Coverage: tool-integrated agents; 17 user tools and 62 attacker tools.
- Intended role: **evaluation first**, not immediate training.
- Reason: it directly tests indirect prompt injection in tool-integrated agents.
- Status: `candidate_evaluation`.
- Required before acquisition: verify license, exact release/version, file hashes, schema,
  and whether any records overlap AgentDojo or other sources.

### 2. BIPIA — indirect-injection benchmark

- Official repository: `https://github.com/microsoft/BIPIA`
- Coverage: Web QA, Email QA, Table QA, Summarization, Code QA.
- Intended role: **evaluation first** and potentially task-specific research training only
  after licensing/provenance review.
- Important limitation: the repository states that Web QA and Summarization require
  users to obtain source data under their respective terms.
- Status: `candidate_evaluation`.
- Required before acquisition: resolve source-data licensing and reproduce the dataset
  from the documented sources where required.

### 3. PINT Benchmark — direct prompt-injection evaluation

- Repository: `https://github.com/lakeraai/pint-benchmark`
- Reported size: 4,314 inputs, including 3,016 English and 1,298 non-English.
- Categories include prompt injections, jailbreaks, hard negatives, chats, and documents.
- Important limitation: the repository says the dataset contains a blend of public and
  proprietary data. Its code repository is MIT-licensed, which does not grant rights to
  proprietary benchmark records. The benchmark README describes the set as an independent
  evaluation and states evaluated solutions are not trained on its inputs.
- Intended role: **held-out evaluation candidate**, not training by default.
- Status: `evaluation_only_pending_license_review`.
- Reason: using benchmark data for training could undermine its role as an independent
  evaluation set, and proprietary components require additional rights review.

### 5. Lakera Mosscap — large but not labeled as injection

- Official dataset card: `https://huggingface.co/datasets/Lakera/mosscap_prompt_injection`
- Reported size: 278,945 user-submitted prompts, with train/validation/test splits.
- The publisher states every received prompt is included, whether or not it is truly an
  injection, and that many entries are not injections.
- Intended role: **not usable as a binary labeled corpus as-published**. The fields include
  prompts and model answers, but no publisher-provided injection label.
- Status: `not_admitted_unlabeled_for_target_task`.
- Do not infer labels from model answers or present new annotations as publisher ground
  truth.

### 6. deepset prompt-injections — small set with license metadata conflict

- Official dataset card: `https://huggingface.co/datasets/deepset/prompt-injections`
- Reported size: 546 train and 116 test examples.
- The card's visible license field says Apache-2.0, while embedded dataset metadata says
  CC-BY-4.0.
- Intended role: candidate for task-specific audit only after the publisher clarifies
  terms and exact revision/data files are pinned.
- Status: `blocked_license_metadata_conflict`.
- Even if resolved, assess its label semantics and duplicates before training; 662 rows
  alone do not establish representative coverage.

### 4. SafetyBench — multilingual safety evaluation

- Official repository: `https://github.com/thu-coai/SafetyBench`
- Reported size: 11,435 multiple-choice questions across 7 safety categories, in Chinese
  and English.
- Intended role: **safety evaluation**, not direct prompt-injection training.
- Status: `secondary_evaluation`.
- Reason: its task format is broader safety evaluation and does not map cleanly to the
  AICAS direct prompt-injection classifier.

## Priority order

1. **Direct prompt-injection training/evaluation gap**
   - Investigate open, clearly licensed datasets whose labels explicitly distinguish
     prompt injection from benign/hard-negative text. Do not use unadjudicated Mosscap
     prompts as labels or admit deepset until its license metadata is resolved.
2. **Independent direct prompt-injection test set**
   - Prefer a source not used for model fitting.
   - PINT is a candidate, but keep it evaluation-only unless rights and benchmark policy
     justify another use.
3. **Indirect/agentic injection evaluation**
   - Add InjecAgent and/or BIPIA after source and license audit.
4. **Multilingual security**
   - Identify a source with explicit labels and balanced language coverage.
5. **DefAn reference-grounded subset**
   - Audit and quantify which local records have legitimate reference/evidence fields
     before any supervised expansion.

## Dataset size policy

AICAS will not set a target row count first and then search for data to fill it.

For each task, the target size will be derived from:

- number of classes and class balance,
- diversity of attack families,
- language coverage,
- source diversity,
- duplicate/near-duplicate rate,
- desired confidence interval width,
- independent test-set size,
- and whether the task is training or evaluation.

A larger dataset with uncertain labels is not considered an improvement.

## Acquisition gate

No external dataset should be copied into AICAS until all of these are recorded:

- official source/repository,
- publisher/authors,
- paper/release,
- version/commit,
- license and permitted use,
- acquisition date,
- SHA-256,
- raw record count,
- schema,
- label definitions,
- provenance notes,
- duplication/leakage findings,
- train/evaluation eligibility,
- known limitations.

## Current recommendation

Do **not** add PINT, BIPIA, InjecAgent, SafetyBench, Mosscap, or deepset data to a training
pool yet. Mosscap has no publisher-provided injection labels; deepset has a card license
conflict; PINT is held-out and partly proprietary; BIPIA and InjecAgent are contextual
agent benchmarks with distinct semantics.

The next implementation step should be a **candidate-source verifier and acquisition manifest**
for the direct prompt-injection gap. Once a source passes the gate, it can be downloaded into
the immutable RAW layer and audited before processing.


## Acquisition decision — S-Labs Prompt Injection Detection Dataset

S-Labs is the first external source selected for local acquisition. Its upstream card
declares MIT licensing, 11,089 training rows, 2,101 validation rows, 2,101 test rows,
binary `text`/`label` schema, English language, and explicit injection categories/hard
negatives. The latest reviewed repository commit is `002a9dd`, marked verified.

AICAS status: **BLOCKED for training**. The supplied local train split contains one normalized text with contradictory labels (0 and 1); the pinned upstream bytes were verified identical on 2026-10-17 and contain the same conflict. Do not train on this source unless the contradiction is resolved by the publisher or authoritative source documentation and the full acquisition gate is rerun.

It is not yet part of the model training set. The acquisition script must first produce
`PASS_LOCAL_SOURCE_AUDIT`, followed by cross-source overlap checks against existing AICAS
JailbreakBench/HarmBench data. The upstream test split remains independent.
