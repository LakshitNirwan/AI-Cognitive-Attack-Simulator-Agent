# AICAS External Dataset Acquisition Gate

## Selected candidate: S-Labs Prompt Injection Detection Dataset

Upstream:
`https://huggingface.co/datasets/S-Labs/prompt-injection-dataset`

Pinned upstream revision observed during AICAS review:
`002a9dd` (verified commit)

The upstream dataset currently declares:
- MIT license
- English
- text classification
- train: 11,089
- validation: 2,101
- test: 2,101
- labels: 0 = BENIGN, 1 = INJECTION
- hard negatives and multiple injection categories

AICAS does **not** copy this data into the repository ZIP. Run the acquisition
script to download the three immutable RAW files into `datasets/raw/external/slabs_prompt_injection/`.

The acquisition script:
1. downloads train/validation/test from the upstream repository;
2. records SHA-256 hashes;
3. validates the expected schema and labels;
4. checks empty text and duplicate rows;
5. checks exact text overlap across splits;
6. records counts and label distributions;
7. writes a provenance manifest.

Only after this audit passes should the source be admitted to the AICAS processed ML dataset.

Important: the upstream README describes the dataset as a binary prompt-injection detector
dataset and says the validation/test sets are manually curated. It also states English-only
coverage and that emerging attacks may be missing. These limitations remain part of AICAS provenance.
