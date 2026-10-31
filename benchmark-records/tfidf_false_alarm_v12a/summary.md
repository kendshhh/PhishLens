# TF-IDF false-alarm reduction: fresh confirmation

Completed 29 October 2026, Asia/Manila. **Use v12a as the candidate for an advisory integration pilot. It passed all eight measured scoped checks. Original full qualification remains incomplete.** The candidate was chosen on development data before opening the fresh cohort. This study does not re-rank neural models tested on other data.

| System | Caught / 200 | False alerts / 1,000 | Recall | FPR | ECE |
|---|---:|---:|---:|---:|---:|
| Original TF-IDF | 190 | 11 | 95.00% | 1.10% | 0.0136 |
| Recalibrated original | 189 | 11 | 94.50% | 1.10% | 0.0138 |
| TF-IDF v12a | 190 | 1 | 95.00% | 0.10% | 0.0054 |

The change produced **10 fewer false alerts on the same 1,000 ham inputs, with the same 190/200 phishing detections**. Seven original misses were recovered and seven different phishing messages were newly missed. Paired overall accuracy differences were not established after Holm correction (original vs v12a p=0.1299). Treat the overall comparison as a statistical tie under the original rule; this is not proof of equivalence. The pre-test selection favored fewer development security-control alerts.

## Why these steps were used

1. **Audit actual historical exposure before training.** Preserve old predictions and reports; distinguish fresh-to-this-project data from newly collected email. Admit source-labelled ham and publisher-labelled phishing only. Synthetic emails and broad spam/fraud positives are excluded from the primary test. This avoids counting known examples as new evidence or treating all spam as phishing.
2. **Group duplicates and shared passages before allocation.** Exact hashes, family matches and shared 30-word passages join related messages across full and truncated views. Three mixed-label families (3,648 rows) were quarantined. The first allocation failed leakage checks; the corrected global grouping and prospective quarantine passed before any model predictions. Automated checks reduce detected overlap, not all conceivable semantic leakage.
3. **Separate model fitting, probability calibration, threshold choice and final scoring.** Train/development: 27,391 rows (25,311 ham, 2,080 phishing), 16,891 groups. Calibration: 600 (500/100), 549 groups. Threshold validation: 1,100 (1,000/100), 1,042 groups. Fresh confirmation: 1,200 (1,000/200), 1,135 groups. Another 364 unused records remain reserved. These are the approved fresh-role allocations, not a new claim that the original 70/15/15 split was used.
4. **Compare six fixed training configurations.** Word unigrams/bigrams alone or plus within-word character 3–5-grams; LR C=0.5, 1 or 2. Vocabulary is fitted only within training folds. Each feature block uses sublinear TF and L2 normalization; source/family weights preserve each label's original total mass. Five outer grouped folds use separate inner cutoff groups. Thirty nested fits and six full-development exports were made. Source balancing reduces domination by prolific sources but cannot remove source/class confounding.
5. **Keep the failed search visible.** All six original v12 configurations failed development eligibility under its permissive cutoff policy. The best general FPR was 4.322%; the best exposed-control result was 26/41 false alerts, from a different configuration. No fresh test was opened. A cached raw-margin-zero diagnostic motivated a separately approved v12a protocol. It reused the six weights, changed no numeric gate, and performed zero additional classifier fits.
6. **Choose a conservative operating policy before final testing.** Set the cutoff to max(0, lowest validation cutoff with FPR ≤2%). The 2% target remains an upper bound, not an instruction to force false alarms. C=1 word+character was selected because its development replay caught 1,890/2,080 phishing with 0/41 exposed-control alerts; C=2 caught more but falsely alerted 6/41. These reused development controls are not independent modern controls. The chosen system then caught 92/100 phishing with 0/1,000 false alerts on threshold validation.
7. **Calibrate the displayed score separately.** A nondecreasing sigmoid was selected using grouped out-of-fold log loss on the 600 calibration messages, then fitted there only. For v12a: sigmoid(1.6158795082744162 × raw_margin + 2.0617153419475205). Alert at raw margin ≥0; its corresponding displayed threshold is 88.71%, not 50%. Do not change it to 50% during integration. This mapping reflects the research mixture, not a guaranteed personal-inbox phishing probability.
8. **Verify the actual Chrome implementation, then freeze and score once.** Python/Chrome parity covered 52 development/validation inputs for each of three systems. Final model, code, configs, data and timing evidence were hashed before 3,600 fresh browser predictions. Every system saw each of the same 1,200 inputs once. No thresholds, labels or inputs changed after results. The static integration package matched all 52 candidate fixture decisions and quote spans with no external requests.

## Metrics and gates

Candidate group-bootstrap 95% intervals (2,000 whole-group replicates, seed42):

| Metric | Point and 95% interval |
|---|---|
| Recall | 95.00% (91.63%–97.93%) |
| FPR | 0.10% (0.00%–0.30%) |
| Precision | 99.48% (98.39%–100.00%) |
| F1 | 97.19% (95.26%–98.73%) |
| MCC | 0.9668 (0.9447–0.9849) |
| ROC-AUC | 0.99850 (0.99612–0.99985) |
| PR-AUC (average precision) | 0.99502 (0.98848–0.99926) |
| ECE | 0.00542 (0.00401–0.01147) |

ROC/PR use raw decision margins; ECE uses the validation-fitted probability mapping; confusion matrices use the frozen cutoff. Group-bootstrap intervals are conditional on this fixed model and these source families; they do not include retraining uncertainty or unseen-source shift. Degenerate empirical validity CI [1,1] does not guarantee perfect future outputs.

| Measured check | Frozen limit | Candidate result | Status |
|---|---:|---:|---|
| Fresh source-pair recall | ≥90% | 95% | Pass |
| Fresh source-pair FPR | ≤3% | 0.1% | Pass |
| ECE | ≤0.10 | 0.00542 | Pass |
| Valid output | 100% | 1,200/1,200 | Pass observed |
| Model p95, worst measured cell | ≤100 ms | 4.663 ms | Pass |
| Complete workflow p95, worst measured cell | ≤100 ms | 6.673 ms | Pass |
| Cold readiness, max of measured trials | ≤1,000 ms | 374.425 ms | Pass |
| Required benchmark client assets | ≤5,000,000 bytes | 2,579,649 bytes | Pass |

These eight checks include a separate full-workflow speed check in addition to model inference. They do not turn the source-pair cohort into original independent OOD/adversarial evidence. Every reference also passed these scoped checks. The original robustness-weighted score, weight sensitivity and full-gate winner cannot be computed honestly without the missing roles.

## Actual browser performance

Windows 11 Home Single Language 10.0.26300, Intel Core i5-14450HX (10 cores/16 logical), Python3.12.10, Chrome156.0.8078.73. Inference is JavaScript CPU, not the installed GPU. No Mac numbers, WASM or WebGPU numbers were substituted.

| Candidate backend | Condition | p50 workflow | p95 | p99 | Cold max |
|---|---|---:|---:|---:|---:|
| Web Worker | 1× | 0.480 ms | 1.169 ms | 1.552 ms | 129.960 ms |
| Web Worker | 4× | 0.630 ms | 1.586 ms | 1.834 ms | 256.910 ms |
| Direct main-thread stress reference | 1× | 0.433 ms | 1.356 ms | 1.552 ms | 154.305 ms |
| Direct main-thread stress reference | 4× | 2.502 ms | 6.673 ms | 9.914 ms | 374.425 ms |

Each of 12 cells (three systems × two backend placements × normal/4×) discarded 10 warmups, timed 100 validation inputs with performance.now(), and ran three fresh-context cold trials: 1,200 timed observations, 120 discarded warmups, 36 cold trials. These are repeated timings, not 1,200 additional independent accuracy tests. “Full workflow” here is the measured prepared-text classifier, observations, attributions, quote checks and worker round trip where used. It excludes extension capture/DOM rendering, dataset MIME parsing and the public input-normalization adapter. CDP page throttling may not throttle dedicated-worker computation, so direct main-thread runs provide an explicitly throttled kernel stress reference. This does not emulate an entire slower computer. Cold readiness uses local assets with possibly warm OS/file caches, not Internet installation time. The original reference's normal main-thread cold max was 889 ms; it is retained.

The candidate's largest measured main-thread JS heap was 11,858,220 bytes. Worker-page heap excludes the worker. Whole-user-agent memory calls timed out after 2 seconds, so total worker/JS memory is unavailable. AC power was observed after timing; power was not recorded per cell. File download size is recorded as bytes, not a measured network download duration.

## Insights and implementation

The local interface returns a verdict, model score and threshold, exact-quote observations, a reason explaining the concern, a practical next step, and partial word-feature contributions. Character features also affect the decision; the displayed three word features are not a complete explanation and are not proof of deception. English software explanations are deterministic; original quoted text preserves its language. Every returned quote is checked verbatim against the prepared analysis text. Offsets use UTF-16 positions in that text; extension DOM mapping still needs integration testing. Text-only scanning cannot verify sender identity, unseen links or attachments.

The package is an isolated static pilot with the exact selected weights. It does not switch the current backend or browser extension, deploy a public URL, save scans or change a database. Empty/invalid input or a failed worker displays “Unable to assess”, never a confident safe result. In metric accounting, unusable classifier output is fail-open and reduces valid-output rate; none occurred in this fresh run. No LLM tokens or cloud inference were used. The fallback does not constitute a passing human-rated explanation evaluation.

## Limits and remaining work

- Ham labels come from legacy Enron, SpamAssassin, Ling and CEAS sources. All phishing positives belong to the Nazario collector family, including the Kaggle mirror. This is collection/source confounding, not a representative sample of current user inboxes.
- “Fresh” means unused in this project's fitting/development/scoring; it does not mean newly collected. Training includes 2025 messages while final phishing includes 2020–2024, so this is not forward-time validation. There are no final 2025 samples.
- A statistical English filter admitted a CSS-heavy German example. It was kept. A publisher-positive licensing thread has unresolved intent ambiguity. Source labels were not silently replaced by AI judgements. See error_analysis.md.
- The remaining v12a false positive is a bank statement. Fresh authenticated security/OTP controls and independently validated natural-adversarial/OOD performance remain unassessed; 0/41 reused development controls is not a release guarantee.
- Calibration and precision depend on the research mixture (200 phishing/1,000 ham). A user's prevalence may differ. Highlight-only or very short-text behavior has not received a separate held-out evaluation.
- Thirty explanation cards await real human ratings. No human quality pass, Mac test, installed-extension end-to-end pass or public production readiness is claimed.

| Work item | Status |
|---|---|
| Data admission, leakage checks, six trained configs | Built and checked |
| Separate approved conservative policy and calibration | Built; original failed search preserved |
| Once-only fresh confirmation, CIs, paired test | Complete |
| Actual Chrome timing and kernel/package parity | Complete on this Windows machine |
| Graph.csv, charts, terminology, run record | Built |
| Complete software insights and failure path | Built; human quality unassessed |
| Static integration handoff | Built and checked; application provider unchanged |
| Independent OOD/adversarial and fresh authenticated bank/OTP evidence | Unassessed |
| Mac, installed-extension capture, public deployment | Unassessed |

## Evidence and sources

Graph.csv (5,393 rows × 17 columns) contains fresh metrics/CIs, ROC/PR points, actual latency samples, and separately labelled development/history phases. All six chart pairs are rendered from that CSV. No unsupported OOD-drop chart is invented. Full exact seeds, hashes, model IDs, library/Chrome versions, hardware and limitations are in run_record.json and final_lock.json. No raw email bodies are bundled for public redistribution.

- [Kaggle collected-source compilation](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset), DOI10.34740/kaggle/ds/5074342; [Al-Subaiey et al., 2024](https://arxiv.org/abs/2405.11619).
- [Nazario corpus provenance and licensing](https://monkey.org/~jose/phishing/README.txt): collected inbox messages, publisher labels may contain errors.
- [SpamAssassin corpus notes](https://spamassassin.apache.org/old/publiccorpus/readme.html): historic mail and source rights require careful handling.
- [scikit-learn feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html), [calibration](https://scikit-learn.org/stable/modules/calibration.html), and [decision thresholds](https://scikit-learn.org/stable/modules/classification_threshold.html) support the separation of representation, probability fitting and operating policy.
- [NIST spam data notice](https://trec.nist.gov/data/spam.html): TREC06/07 mirror candidates were excluded; they were not quietly substituted for admitted data.
