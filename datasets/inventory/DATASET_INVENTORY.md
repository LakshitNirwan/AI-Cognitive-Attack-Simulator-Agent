\# AICAS Master Dataset Inventory



\## Project



\*\*Project:\*\* AI Cognitive Attack Simulator Agent (AICAS)



\*\*Purpose of this inventory:\*\*  

This document records the external datasets currently collected for AICAS, their provenance, local representation, structure, purpose, and known data-quality observations. Raw benchmark files are preserved separately and are not modified during inventory creation.



\---



\# 1. Dataset Overview



| Dataset | Local Records / Scenarios | Main Purpose in AICAS | Data Type |

|---|---:|---|---|

| JailbreakBench | 200 | Jailbreak and harmful-behavior attack scenarios | CSV |

| HarmBench | 400 benchmark behaviors | Harmful-behavior attack scenarios | CSV |

| IndiBias | 561 sampled records | Bias evaluation | CSV |

| DefAn | 70,793 rows currently collected | Hallucination / factuality evaluation | CSV |

| AgentDojo v1.2.2 | 35 injection scenarios | Agentic and indirect prompt-injection evaluation | JSON |



> \*\*Important:\*\* The record counts above refer to the files currently collected locally. They should not automatically be interpreted as the number of unique records in the original published datasets.



\---



\# 2. JailbreakBench



\## 2.1 Purpose



JailbreakBench provides data relevant to jailbreak and harmful-behavior evaluation.



For AICAS, it is used as a source of established attack/behavior scenarios that can serve as seed material for attack generation and evaluation.



\## 2.2 Local files



```text

datasets/jailbreak/raw/

├── benign-behaviors.csv

└── harmful-behaviors.csv

## Current readiness checkpoint

See [`datasets/audit/DATA_READINESS_REPORT.md`](../audit/DATA_READINESS_REPORT.md) for the current source-aware eligibility decisions, local artifact hashes, and unresolved gates. S-Labs remains blocked because the byte-verified pinned upstream training split contains a contradictory-label text; byte identity does not resolve label quality.
