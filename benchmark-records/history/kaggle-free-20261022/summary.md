# PhishLens benchmark report

Generated (UTC): 2026-10-22T14:28:38.176676+00:00

**Decision: no model is approved as meeting the production false-positive requirement of 0.1%.**

The new evaluation is free and local. DistilBERT was tested using its saved checkpoint. Gemini 3.1 Flash-Lite and Gemini 3.8 Flash have historical synthetic evidence only; neither has a new Kaggle score here. The attempted hosted command was blocked before execution. No new paid API inference, account signup, subscription, OmniRoute setup, or provider upload occurred.

## Data quality and scope

The input ZIP contains 164,972 rows across seven CSV files. Cleaning retained 81,891 unique records from the six source corpora for the pooled benchmark. The separately cleaned combined file contains 82,075 records and is excluded from that pool.

| Dataset | Original rows | Cleaned rows | Removed |
|---|---:|---:|---:|
| CEAS_08.csv | 39,154 | 38,963 | 191 |
| Enron.csv | 29,767 | 29,423 | 344 |
| Ling.csv | 2,859 | 2,859 | 0 |
| Nazario.csv | 1,565 | 1,551 | 14 |
| Nigerian_Fraud.csv | 3,332 | 3,293 | 39 |
| SpamAssasin.csv | 5,809 | 5,802 | 7 |
| phishing_email.csv | 82,486 | 82,075 | 411 |

Cleaning normalizes UTF-8/NFC, line endings, surrounding whitespace and nonprinting ASCII controls. It retains punctuation, URLs, letter case, optional missing metadata, subject-only messages and long real emails. Exact normalized message duplicates are removed, with original source row IDs and retained-copy links in the audit. Mail-folder internal-data artifacts and empty model text are quarantined, with originals recoverable from the source ZIP or quarantine JSONL.

The combined file has the same total/class counts and recognizable source boundaries, but 340 labels differ at the same inferred row positions. Inspected examples show message reordering. These are positional mismatches, **not proof of 340 incorrect labels**. No one-to-one source mapping or relabeling was invented.

The source labels are binary. They mix unwanted advertising, fraud and phishing with legitimate email and cannot certify separate phishing/spam/legitimate ground truth. Gemini would map spam and phishing to source-positive for this protocol; historical synthetic binary metrics treat spam as non-phishing. The tasks differ, so their accuracy figures must not be ranked in one leaderboard.

Nazario and Nigerian_Fraud contain only label 1; their standalone false-positive rates cannot be measured. No Kaggle URL, dataset license or labeling protocol was supplied. Data cleaning does not establish that every original label is correct.

## Frozen experiment and statistics

The deterministic seed is 20261022. Canonical text and identical non-empty bodies are linked before assigning approximately 70%/15%/15% train/validation/test partitions. The cohort contains one record per detected duplicate group. Validation and test each contain 4,000 label-0 and 1,000 label-1 examples, selected deterministically from separate groups. This constructs a 20% positive prevalence; accuracy and precision do not estimate the production prevalence.

255 messages exceed the 30,000-character API limit. They remain in the cleaned files and are listed in ineligible_for_api.csv; no benchmark input is silently truncated. The tokenizer processes every accepted overflow window (512 tokens, stride 64), batches up to four windows and aggregates the maximum positive score.

The false-positive rate is FP/(TN+FP), distinct from 1-precision. Confidence limits are two-sided 95% exact Clopper-Pearson intervals. Zero false positives among 4,000 independent negatives has an upper bound of 0.092179%, below 0.1%. At least 3,688 zero-error independent negatives are required for this interval to fit below the target. Semantic near-duplicates, common campaigns and source correlation may remain; these bounds do not resolve label quality or training overlap.

The threshold is selected using validation data only, maximizing true-positive detections subject to the validation FPR upper bound <=0.001. The test set is evaluated once with that frozen choice. The default 0.5 threshold is retained as a separate view of the same checkpoint. A threshold that predicts no positives is explicitly unusable as a detector even if its false-positive count is zero.

## New DistilBERT results

Run: `20261022T135307259615Z_local`. Started: 2026-10-22T13:53:07.259615+00:00. Ended: 2026-10-22T14:24:55.071065+00:00.

| Policy | Threshold | TN | FP | FN | TP | FPR | FPR 95% upper bound | Recall | Source-label gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Production default | 0.5 | 3608 | 392 | 66 | 934 | 9.800000% | 10.763453% | 93.400000% | not_met_on_source_labels |
| Validation selected | 0.99991011619567871 | 3996 | 4 | 711 | 289 | 0.100000% | 0.255840% | 28.900000% | not_met_on_source_labels |

The validation-selected threshold detected 279 positives in the 1,000-positive validation cohort. This is an uncalibrated softmax decision threshold, not a calibrated probability. No model weights were retrained.

Test latency measures AIService.analyze_email once per email on this machine, after validation warmed the model; it excludes HTTP routing/serialization, database writes and browser/network time. Mean: 191.485657 ms; median: 85.276900 ms; p95: 629.523165 ms; p99: 1372.937396 ms; minimum: 6.967200 ms; maximum: 3767.124500 ms. Percentiles use NumPy linear interpolation across 5,000 different inputs, not repeated trials on one email.

Loading the saved checkpoint/tokenizer took 0.362159 seconds, excluding imports and snapshot copying. This is not an OS-cold startup measurement. Peak isolated-process RSS: 853.312500 MiB, including data, Python and model. CPU threads: 4. Hardware/OS/package versions are in run.json. This does not establish cloud-host latency, concurrency capacity or extension timeout compatibility.

Model: `dima806/phishing-email-detection`; revision: `310a5602280486e01dd60e37230980cfcc327b41`. Saved weights SHA-256: `45bb5e5608370c51e63ef9120627515093b1ef4d7cd6693e54301a894a2d910c`. The worker loaded the saved copy, not an unfrozen model alias. The snapshot includes weights, configuration, vocabulary and model card. Runtime-source hashes are preserved; metrics are recomputed independently from persisted prediction logs.

## Historical comparisons

Original evidence from October 22 is copied intact under historical/. Report timestamps and missing original call/start/end timestamps are explicitly distinguished. Retried cases remain diagnostic follow-ups; they do not replace failed primary attempts.

| Model | Valid / attempted | Binary accuracy (all requested) | Three-class accuracy | False-positive rate as originally reported | Median valid latency |
|---|---:|---:|---:|---:|---:|
| local | 40/40 | 60.000000% | 60.000000% | 50.000000% | 0.016443 s |
| gemini-3.1-flash-lite | 37/40 | 92.500000% | 90.000000% | 0.000000% | 4.246637 s |
| gemini-3.8-flash | 2/20 | unavailable | unavailable | unavailable | 23.109028 s |

The prior Flash-Lite recommendation is supported only by that synthetic development suite: 37 valid responses from 40 attempts and zero false phishing accusations. This is too small to verify a 0.1% false-positive rate. Gemini 3.8 stopped at daily quota after 20 attempts and is not a completed accuracy comparison. Old latency statistics exclude failed requests unless the column explicitly states otherwise. Historical token usage, billing and resolved hosted versions were not recorded, so those fields remain unavailable.

## Engineering decision

DistilBERT provides a no-API-cost baseline and a recoverable local checkpoint. Its binary label mapping, false-positive behavior and validation/test results must be considered together. No new comparison establishes Gemini as a Kaggle winner. Retain the existing application configuration pending a representative, independently labeled three-class evaluation and a verified billing-disabled hosted comparison. Do not treat a model as accepted solely because it is fast, has high softmax scores or avoids flags by missing all threats.

The local AI branch is feat/ai-engine at 00d0bf60deb4f90544435e2af24563b3a5b376fe. The remote main commit was independently checked and is 149808e3f76d9182688b5438153f57bd3cc03774. Its configuration still defaults to mock, while the local AI branch defaults to Gemini Flash-Lite. Main also contains newer initialization locking, bounded rule evidence, a deployment /version endpoint and Week 2 CRUD client work. The benchmark uses local branch AIService code; it does not establish deployed behavior. TEAM_HANDOFF.md records the backend/full-stack implications.

## Files and reproduction

- Graph.csv: one row per model/run/policy with task, provenance, exact counts, timestamps, metrics, units and status. Filter by task and suite before comparing.
- false_positives.csv: source-label false positives with record IDs, scores, thresholds and measured latency; join with data/benchmark.csv for review.
- per_source_metrics.csv: test confusion counts and intervals by corpus. Missing negative support produces unavailable FPR, never a fabricated zero.
- historical_runs.jsonl and runs/: append-only execution metadata and raw local predictions. Historical imports remain separately identified.
- data/data_manifest.json and audit/: checksums, cleaning decisions, row accounting, exclusions and quarantined originals.
- scripts/: reproducible cleaning, benchmark and report scripts. Run each benchmark in a fresh process. Never overwrite a run directory.

From the project Python 3.12 environment, with its already installed optional CPU requirements and scipy available:

Use a new experiment folder for preparation. Existing saved run evidence must remain frozen:

```powershell
python scripts/clean_datasets.py archive.zip data
python scripts/benchmark_requested.py --root . --project D:\Phishlens\PhishLens --prepare
python scripts/benchmark_requested.py --root . --project D:\Phishlens\PhishLens --model local
```

The saved runs record exact installed versions. The source cleaner uses only Python standard libraries. The model runner uses the project environment; isolated statistics dependencies used during this run are recorded separately. No credential values are included. Leave hosted flags unset for the free-only workflow.

Method references: [Clopper-Pearson intervals via SciPy beta distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html), [scikit-learn guidance on preventing data leakage](https://scikit-learn.org/stable/common_pitfalls.html).
