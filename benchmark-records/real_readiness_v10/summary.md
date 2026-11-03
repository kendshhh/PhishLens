# PhishLens real-email operational retest

**No tested system passed. There is no qualified winner.** This conclusion comes from actual new Chrome predictions, not a synthetic-only substitute or missing-data status alone.

| Frozen system | Collected phishing detected | Attested legitimate controls falsely alerted | Valid output | Result |
|---|---:|---:|---:|---|
| tfidf_lr | 221/249 (88.8%) | 38/41 (92.7%) | 100.0% | Fails |
| distilbert | 59/249 (23.7%) | 1/41 (2.4%) | 100.0% | Fails |
| llm | 0/249 (0.0%) | 0/41 (0.0%) | 46.6% | Fails |

The workload contains 249 unused body-unique English publisher-phishing messages from Nazario 2025 (223 groups) and 41 body-unique collector-attested received/redacted security controls (18 conservative text groups). All retained inputs passed the recorded role/checkpoint overlap check. The positive mailbox was previously inventoried; these inputs were not previously scored, not newly collected from another publisher. The legitimate origin/label is collector-attested, not independently authenticated. These facts limit generalization without invalidating the recorded observations. No synthetic attack fixture contributes to this table.

Models, calibration maps, prompts and cutoffs were reused unchanged from the previous validation-only 2% selection. No new test outcome was used to adjust them. All model inputs and outputs stayed local. The exact metrics, group-bootstrap 95% intervals, thresholds, paired tests, source hashes and per-backend execution evidence are saved alongside this report.

TF-IDF/LR retained higher collected-phishing recall than the other tested systems but produced 38 false alerts among 41 routine controls. The original training task inherited spam/fraud as well as phishing labels. Mathematical feature attribution in the new false positives frequently includes ordinary phrases such as “your account” and “the link.” A strong same-corpus historical result therefore did not establish reliable account-security screening. DistilBERT's low false-alarm rate is accompanied by many missed collected phishing messages. Llama's frozen calibration has zero slope, and invalid outputs remain safe under the required fail-open rule; its valid-output rate and consistency must accompany any apparently favorable FPR.

This retest is a source-pair study, not a representative inbox sample. Its precision and percentages must not be advertised as population-wide effectiveness, absence of bias or real-inbox risk probabilities. Substantial class/source differences and template dependence remain. Historical ID, constructed stress and browser-matrix numbers are preserved as separately labeled evidence. The new per-message browser times are observational and do not replace the full warmed/throttled/cold-start matrix or installed-extension testing. No Mac result or new human explanation rating was invented.

## What can be applied to the project

The frozen TF-IDF artifact and local scoring interface are reproducible implementation references. These measurements do **not** support enabling this version as a reliable automatic phishing verdict engine. A blanket passing claim or release-ready label would contradict the observed false alarms. Retain it as an internal baseline while a phishing-specific training task and independent hard-negative development population are built; new model development must use validation only and reserve an untouched final cohort. Do not convert these now-scored controls into a supposedly fresh confirmatory test after tuning.

The previous declaration choosing TF-IDF remains a project decision. This new release-readiness finding is a measured limitation of that artifact; no previous report, source label or gate was overwritten to manufacture a winner. Remaining real-world/adaptive-adversarial evidence and human explanation-quality review stay explicit. No further upload was needed to obtain this result.

Read the [visual report](visual_report.html), [error analysis](error_analysis.md), [terminology](terminology.md), [CSV results](Graph.csv), [model/label source definitions](model_and_label_sources.json), and [verification record](verification.json).
