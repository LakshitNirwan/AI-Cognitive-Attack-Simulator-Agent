# AICAS Dataset Source Verification

This file records the external source identities checked during the initial AICAS dataset audit.

| Dataset | Source | Verification |
|---|---|---|
| JailbreakBench | https://github.com/JailbreakBench/jailbreakbench | Official JailbreakBench repository; describes JBB-Behaviors and its 200 benign/misuse behaviors |
| HarmBench | https://github.com/centerforaisafety/HarmBench | Official Center for AI Safety HarmBench repository |
| IndiBias | https://github.com/sahoonihar/IndiBias | Author-maintained public repository; cross-checked against NAACL 2024 paper |
| DefAn | https://github.com/ashikiut/DefAn | Author repository; links to the paper and public Hugging Face repository |
| AgentDojo | https://github.com/ethz-spylab/agentdojo | Official ETH Zurich/SPY Lab repository; local metadata identifies v1.2.2 |

## Important licensing note

Repository-level licenses do not automatically establish that every embedded dataset artifact has identical redistribution terms. AICAS therefore records license status separately and will not assume redistribution rights where they have not been explicitly verified.

## Versioning note

For future expansion, source URLs alone are insufficient. AICAS should record an immutable release/tag/commit or dataset version plus raw SHA-256 whenever possible.
