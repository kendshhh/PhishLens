# English real-email benchmark: known checkpoint data excluded

**No model is fully qualified.** English ID results assess the original broad spam/fraud/phishing task. No admitted two-class OOD or validated adversarial/bank/OTP population is available. Missing evidence is not a pass.

The original gates, weights and 2% validation alert target remain unchanged. Historical experiments and submitted ratings are preserved. No synthetic messages, translations, AI binary labels, generated perturbations or AI human ratings were used.

The earlier v4 attempt was halted before test scoring after finding exact overlap with the downloaded classifier’s public fine-tuning emails. This separate attempt excludes complete groups touching any of the publisher’s 22,644 email records across its train, validation and test splits, using the original exact, 0.9 Jaccard and shared-passage rules. Shared URL/domain features and other undocumented training sources are not claimed disjoint. The 1,000-message calibration target, 2,000-message cutoff cohort and 1,000-message ID target remain intact. Source-only eligibility and class counts determined replacement IDs. Fixed prompt/runtime choices and unchanged training weights carry forward from documented development; calibration maps and alert cutoffs are fitted again. Retained real validation outputs have an explicit provenance record. No old test output is reused.

[Detailed definitions and interpretation limits](interpretation_guide.md) explain the labels, risk percentages, known-training-data exclusion, browser measurements and remaining human judgments.

## How and why

1. Verified raw publisher downloads and hashes, then parsed MIME as inert text. This preserves collected email evidence without executing message content.
2. Applied the shared HTML/whitespace/identifier cleaning and 2,000-head + 300-tail rule. All three models receive the same prepared text; cut counts are reported below.
3. Checked the complete source pool for exact, near and shared-passage overlap. Quarantined affected groups before sampling; retained the original 70/15/15 pool membership. This reduces reuse of messages and quoted/template material.
4. Used an offline statistical English filter before model inference. Uncertain/short inputs were quarantined; English eligibility is fallible metadata, not human verification or binary truth.
5. Separated development, calibration fitting, threshold selection and previously unscored ID groups. Only training rows fit TF-IDF/LR; neural weights remain as downloaded. Accuracy/risk evaluation uses JavaScript CPU for TF-IDF/LR, WASM for DistilBERT and WebGPU for the LLM. Other backend cells are timing probes, not additional full accuracy tests.
6. Compared identity and nondecreasing sigmoid calibration by grouped fivefold validation log loss. Fit the chosen map on calibration rows, then selected cutoffs on a different cohort with 1,000 legitimate messages. Invalid output remains safe at probability zero.
7. Tested two English prompts, fixed token caps and browser variants on development validation only. The selected prompt/configuration is frozen before new test scoring. Strict JSON, probability/label consistency and English-output checks do not rewrite model answers.
8. Score each admitted new test once. Chrome timing uses 10 discarded warmups, 100 real validation emails and three cold readiness trials; both neural backends and normal/4x CPU conditions retain their original limits.
9. Keep actual human explanation review separate from model metrics. Rank only full hard-gate survivors; missing adversarial evidence prevents a qualified winner.

## Cohorts

| Role | Legitimate | Source-positive | Cut |
|---|---:|---:|---:|
| train | 26150 | 22714 | 9666 |
| calibration | 500 | 500 | 84 |
| threshold | 1000 | 1000 | 176 |
| test_id | 500 | 500 | 106 |

## Results

| Model | ID source-positive recall [95% CI] | ID FPR [95% CI] | ID ECE | Valid outputs | Qualification |
|---|---:|---:|---:|---:|---|
| tfidf_lr | 98.20% [96.99, 99.21] | 1.00% [0.20, 1.99] | 0.0066 | 100.00% | not_qualified_missing_evidence |
| distilbert | 83.40% [79.96, 86.97] | 1.20% [0.40, 2.21] | 0.0235 | 100.00% | fail |
| llm | 0.00% [0.00, 0.00] | 0.00% [0.00, 0.00] | 0.2745 | 47.30% | fail |

Calibration is fitted on a separate validation role, never on these tests. Final study sample counts above are subsets of the original fixed 70/15/15 source pools; the final sampled roles are not themselves a new 70/15/15 repartition.

| Model | Raw ID ECE | Calibrated ID ECE | Frozen primary risk cutoff |
|---|---:|---:|---:|
| tfidf_lr | 0.049758 | 0.006619 | 0.619611 |
| distilbert | 0.044311 | 0.023470 | 0.943754 |
| llm | 0.490560 | 0.274517 | 0.483123 |

| Model | Measured failed gates | Unassessed gates |
|---|---|---|
| tfidf_lr | none observed | OOD false-positive rate; OOD recall; Adversarial false-positive rate |
| distilbert | ID recall: 83.40% (minimum 90.00%); Worst required p95 latency: 1682 ms (maximum 500 ms); Worst required cold readiness: 4450 ms (maximum 3000 ms) | OOD false-positive rate; OOD recall; Adversarial false-positive rate |
| llm | ID recall: 0.00% (minimum 90.00%); ID calibration error: 0.2745 (maximum 0.1000); Valid output rate: 47.30% (minimum 99.00%); Worst required p95 latency: 5969 ms (maximum 5000 ms); Worst required cold readiness: 17802 ms (maximum 15000 ms); Five-repeat consistency: 48.00% (minimum 95.00%) | OOD false-positive rate; OOD recall; Adversarial false-positive rate; Required download size |

## Actual Chrome model timing

Values below measure model inference/generation. Full extension postprocessing latency remains unmeasured. Cold is the maximum of three fresh-page trials; MB means decimal megabytes. Missing or failed backend cells do not pass.

| Case | Status | p50 ms | p95 ms | p99 ms | Cold ms | Static download MB | JS heap MB |
|---|---|---:|---:|---:|---:|---:|---:|
| distilbert_wasm_x1 | measured | 64.94 | 335.47 | 467.63 | 1040.38 | 95.86 | 11.21 |
| distilbert_wasm_x4 | measured | 210.44 | 1111.61 | 1366.39 | 3540.81 | 95.86 | 8.60 |
| distilbert_webgpu_x1 | measured | 156.14 | 581.72 | 652.25 | 1219.94 | 95.86 | 11.04 |
| distilbert_webgpu_x4 | measured | 406.09 | 1682.34 | 2182.27 | 4450.34 | 95.86 | 11.71 |
| llm_wasm_x1 | timeout_incomplete | — | — | — | — | — | — |
| llm_wasm_x4 | timeout_incomplete | — | — | — | — | — | — |
| llm_webgpu_x1 | measured | 1428.75 | 2568.04 | 2689.91 | 5258.64 | 1128.99 | 343.00 |
| llm_webgpu_x4 | measured | 3170.20 | 5968.81 | 6322.21 | 17802.00 | 1128.99 | 734.15 |
| tfidf_lr_javascript_cpu_x1 | measured | 0.04 | 0.24 | 0.39 | 265.54 | 1.34 | 4.89 |
| tfidf_lr_javascript_cpu_x4 | measured | 0.22 | 1.61 | 1.83 | 313.49 | 1.34 | 4.68 |

## Paired ID comparisons

Exact McNemar tests compare correctness on the same broad-label ID inputs, with Holm adjustment across three pairs. Campaign dependence may violate message-level independence. These comparisons do not override missing hard gates.

| Pair | First correct / second wrong | Second correct / first wrong | Adjusted p |
|---|---:|---:|---:|
| tfidf_lr vs distilbert | 80 | 5 | 1.81e-18 |
| tfidf_lr vs llm | 491 | 5 | 7.26e-138 |
| distilbert vs llm | 417 | 6 | 1.44e-114 |

The confidence intervals, raw-versus-calibrated ECE, curves, actual browser timings and sizes are in Graph.csv. Threshold-cohort metrics are descriptive validation results, not an independent test. No incomplete test population receives a partial score.

[Qualitative error observations](error_analysis/observations.md) document actual message reading by the AI engineering agent, separately from independent human explanation ratings. Original source truth labels remain unchanged.

## Definitions and limits

- Label 0 preserves publisher/curator legitimate or ham truth. It does not certify the identity of a sender or bank.
- Label 1 in the Kaggle-based ID experiment preserves the original positive class, which includes ordinary spam and fraud. It is not uniformly human-verified credential phishing. Do not present ID recall as strict phishing recall.
- Nazario 2024/2025 are hand-classified real-inbox candidate phishing messages. The same collector/source family is represented in historical Kaggle material. New mailbox messages and text exclusions do not establish collector/campaign independence. Single-inbox selection and possible publisher annotation errors remain.
- TREC_06 label-0 rows remain provisional because original record-level ham linkage and original reuse terms could not be fully verified. Malformed rows are excluded without label rescue; spam rows are not treated as phishing.
- A mixed-script token or HTML-only body is objective structural evidence, not proof of deliberate adversarial intent. Genuine legitimate urgent-bank/OTP controls and human technique validation remain missing.
- Neural pretraining/fine-tuning contamination cannot be fully ruled out. Exact/near/passage grouping cannot prove campaign independence. Statistical English detection can accept mixed-language fragments.
- Shared redaction masks email localparts, phone numbers and long numbers; it is not complete anonymization of names or URL query values. Raw/private audit files are not publication-ready.
- Recalibration changes score interpretation, not the information available to a model. Balanced research cohorts do not establish real-inbox probabilities. The 2% validation target is not a guarantee of test FPR.
- Browser latency measures model inference and generation. Server-side JSON/English validation, probability mapping, verdict selection and append-only audit storage are outside that timer. Browser probability-map parity is checked separately; complete extension verdict/risk/reason latency remains unmeasured.
- Actual output reading found stray non-Latin fragments in some automatically accepted LLM reasons. Statistical language eligibility does not guarantee English-only or grounded semantic output. The post-test character diagnostics do not rewrite reasons, change validity labels or provide human ratings.
- Browser results apply to the recorded hardware, software, power state and backend. CPU emulation does not throttle the GPU and may affect WASM workers differently. Fresh-page cold trials retain OS/driver caches.
- Group-bootstrap intervals describe resampling of the observed groups. Intervals can collapse at zero or one; they do not prove zero future error or perfect reliability.
- Human ratings from earlier prompts or Spanish messages do not transfer. No automatic system can supply the independent human judgments required here.

## Status

| Component | Status |
|---|---|
| English preparation, source hashes, role/passage leakage checks | Built and checked |
| New train-only baseline | Built |
| Validation calibration/thresholds | 3/3 complete |
| Fresh ID scored populations | 3/3 complete |
| Chrome matrix | 10/10 cells recorded; incomplete cells do not pass |
| Human review | pending; 30 selected |
| Independent English two-class OOD | Unadmitted; source truth/terms checks incomplete |
| Validated adversarial and real bank/OTP controls | Unassessed; required evidence unavailable |
| Original full-gate ranking and sensitivity | No qualified survivors; no winner |

Sources: [Nazario README](https://monkey.org/~jose/phishing/README.txt), [curated TREC release](https://zenodo.org/records/8339691), [NIST TREC source index](https://trec.nist.gov/data/spam.html). Supplied Kaggle Phish No More: Al-Subaiey et al. (2024). Full per-row corpus provenance and hashes are in the data manifest.


## Collected English phishing recall challenge

A separate 100-message recall challenge uses the original publisher-hand-classified Nazario 2025 mailbox, restricted to English-eligible messages with a claimed 2025 Date header. It passed source, checkpoint-email and passage-group exclusion before any new test inference. The original shared cleaning/truncation and frozen validation thresholds apply. No message, binary truth label, translation, typo or negative control was generated.

| Model | Recall on publisher-phishing [95% CI] | Valid outputs |
|---|---:|---:|
| tfidf_lr | 92.00% [85.57, 97.00] | 100.00% |
| distilbert | 17.00% [9.37, 25.01] | 100.00% |
| llm | 0.00% [0.00, 0.00] | 45.00% |

This positive-only sample cannot estimate a false-positive rate, population precision, ROC/PR-AUC, balanced accuracy or population calibration. It supplies separate recall evidence and does not satisfy the complete OOD or adversarial gates. Header dates are not authenticated receipt dates. The Nazario source family is already represented in historical Kaggle material, so new messages and text exclusion do not establish an independent collector or all-new campaigns. Its single-inbox selection, class definition and source mixture differ from the broad legacy ID task. No full OOD drop or weighted robustness score is substituted.


## Actual explanation review

Actual human reviews: **0/30**. The fixed borderline sample contains 12 automatically accepted explanations and 18 missing-output cases. No human score has been supplied for this run.

[Open the review form](human_review/review_form.html), read the [instructions](human_review/instructions.md), and download english_ratings_completed.csv after rating. Missing outputs receive a review decision rather than an invented numerical quality score. Earlier ratings do not transfer. The machine-readable [review status](human_review/status.json) distinguishes availability from human quality.