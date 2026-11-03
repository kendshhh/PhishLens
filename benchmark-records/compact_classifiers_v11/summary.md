# PhishLens compact classifier benchmark

Completed comparison of three pinned quantized models. **The highest operational balanced-accuracy point estimate is dima DistilBERT. No model is certified as a fully qualified original-benchmark winner.** The original independent OOD/adversarial requirements remain unassessed. A point-estimate leader is distinct from a statistically demonstrated winner and a release-qualified system.

| Model | Broad ID recall / FPR | Operational phishing detected | Controls falsely alerted | Operational balanced accuracy |
|---|---:|---:|---:|---:|
| BERT-small | 79.0% / 2.0% | 85/249 (34.1%) | 5/41 (12.2%) | 61.0% |
| MobileBERT | 0.0% / 0.0% | 0/249 (0.0%) | 0/41 (0.0%) | 50.0% |
| dima DistilBERT | 79.0% / 1.0% | 60/249 (24.1%) | 0/41 (0.0%) | 62.0% |


BERT-small on **WASM** is the strongest engineering baseline for the next development iteration: its measured workflow p95 is 97.05 ms at 1x and 377.28 ms at 4x CPU throttle, its worst recorded WASM cold readiness is 2,977.60 ms, and its required browser assets total 57.23 MB. It is the only candidate meeting all measured WASM speed/cold/size/validity limits in both throttle conditions. The cold result is close to the 3-second limit and is not a guarantee on another machine. Its 4x WebGPU cell fails, so it does not pass the entire original matrix.

**That is not a release recommendation.** BERT-small detected only 85/249 operational publisher-positive messages and falsely alerted 5/41 controls; broad ID recall was 79%. These are measured recall failures, beyond the original missing independent OOD/adversarial requirements. No model is a fully qualified winner, and the existing owner-selected TF-IDF application has not been replaced.

The original MobileBERT zero-alert result is partly a calibration-pipeline precision defect, not evidence that its weights detect no phishing. The old 1e-6 clipping flattened high validation scores. A separate, validation-only precision correction and raw-ranking alert cutoff recover 106/249 operational detections with 4/41 false alerts; ID recall is 65.4%. This diagnostic reuses saved raw outputs; it is not a fresh confirmatory test and does not overwrite the frozen experiment. See the precision follow-up report for the corrected risk mapping and counts.

After that correction, MobileBERT has the highest operational balanced-accuracy point estimate (66.41%), versus dima 62.05% and BERT-small 60.97%. MobileBERT versus BERT-small is not statistically established on the operational set after Holm correction (McNemar p=0.06415), which does not prove equivalence. BERT-small and dima are inconclusive on broad ID (p=0.68486); the frozen speed/simplicity tie preference favors BERT-small there. MobileBERT's ID outcome is significantly weaker than BERT-small's, and its 4x WASM and WebGPU paths exceed the latency limits. These are different tradeoffs, not a universal accuracy winner or an original weighted ranking.

Dima has the fewest observed operational control false alerts (0/41), accompanied by only 60/249 detections and a slower browser path. Zero errors on 41 controls does not establish a zero population false-positive rate. It cannot be selected as a reliable phishing screen on that favorable FPR alone.

The workflow advantages that were demonstrated are local browser inference, zero generated tokens, valid numeric outputs, shared text coverage and complete English software evidence/advice. The outstanding problem is detection quality under source/task shift. Increasing generation length or changing a prompt cannot fix these non-generative classifiers; a revised learned artifact would require development/validation and separately reported evaluation.


## What was measured

All three use the same prepared text and body-unique operational inputs. There are 1,000 calibration inputs, 2,000 separate cutoff-validation inputs (1,000 legitimate), 1,003 broad ID inputs (503 legitimate, 500 source-positive), and 290 operational inputs (249 publisher-phishing and 41 collector-attested controls). The ID overshoot preserves complete text groups. No model fine-tuning or synthetic primary data was used. Every model generated zero output tokens. The classification/threshold/risk/evidence-advice path executes locally in Chrome; external browser requests are blocked and checked.

The original shared cleaning and first 2,000/last 300 Unicode characters remain. Character-cut counts are development: 2/16; calibration: 122/1000; threshold: 258/2000; test_id: 161/1003; operational: 34/290. The separate truncation audit links original full-source records because the earlier operational copy did not retain its truncation flag. All encoders use nonoverlapping 510-content-token windows plus two special tokens, then the maximum phishing score. This preserves the entire common text rather than silently dropping its tail. Probabilities and cutoffs are fitted from actual Chrome WASM q8 validation outputs, not Python speed or substitute outputs. The 2% validation FPR target stays fixed; each model receives its own cutoff. Identity versus nondecreasing sigmoid calibration is selected by fivefold grouped validation log loss.

## Why the data handling was used

The declared BERT-small corpus and the complete corpus linked in the recovered dima training notebook provide 38,930 nonempty known-source records, 20,071 distinct prepared inputs. Prospective whole-group exclusions remove exact, >=0.9 word-set Jaccard or identical 30-word passage matches. Shared passages are grouped before new stratified group 70/15/15 allocation. The unused 70% partition is not fitted; the validation partition supplies disjoint calibration/cutoff roles. Final selected roles have zero detected known-corpus or cross-role matches. Full MobileBERT training provenance and unknown pretraining remain unresolved. Dima's full corpus link is stronger than its short card, but exact publisher split membership and weight lineage are not independently reconstructed.

Broad source-positive ID labels include spam and fraud. Operational positives retain Nazario's hand-classified phishing labels, including its admitted possible errors. The controls retain the collector's received/redacted legitimate attestation; sender authentication is not independently proven. Operational inputs were already tested by earlier models and influenced candidate development, so this is a shared diagnostic comparison, not a newly untouched final test. The class/source pairing, 41 controls and repeated text families limit real-inbox conclusions. Do not advertise these research probabilities as population inbox risk or the study as bias-free.

## Browser behavior

| Model | Backend / CPU throttle | Workflow p50 / p95 / p99 (ms) | Cold max (ms) | Required assets (MB) | Status |
|---|---|---:|---:|---:|---|
| BERT-small | wasm / 1x | 17.60 / 97.05 / 151.89 | 1017.50 | 57.23 | complete |
| BERT-small | wasm / 4x | 72.20 / 377.28 / 517.82 | 2977.60 | 57.23 | complete |
| BERT-small | webgpu / 1x | 90.61 / 249.11 / 317.33 | 1272.51 | 57.23 | complete |
| BERT-small | webgpu / 4x | 175.78 / 591.17 / 769.32 | 3746.29 | 57.23 | complete |
| MobileBERT | wasm / 1x | 47.46 / 209.78 / 263.82 | 1353.70 | 54.82 | complete |
| MobileBERT | wasm / 4x | 196.61 / 820.31 / 1083.04 | 6379.97 | 54.82 | complete |
| MobileBERT | webgpu / 1x | 1030.80 / 2378.13 / 2579.33 | 3263.18 | 54.82 | complete |
| MobileBERT | webgpu / 4x | 1681.43 / 3966.03 / 4443.59 | 10449.12 | 54.82 | complete |
| dima DistilBERT | wasm / 1x | 63.09 / 362.38 / 547.94 | 972.50 | 94.39 | complete |
| dima DistilBERT | wasm / 4x | 229.50 / 1355.10 / 1808.33 | 3417.98 | 94.39 | complete |
| dima DistilBERT | webgpu / 1x | 154.59 / 558.91 / 782.58 | 1381.91 | 94.39 | complete |
| dima DistilBERT | webgpu / 4x | 365.69 / 1494.69 / 2249.66 | 4180.59 | 94.39 | complete |


Each completed cell has 10 discarded warmups and 100 timed validation emails using performance.now, plus three fresh-context cold trials. Cold readiness includes a first usable classification and explanation. Required assets include the actual graph, tokenizer and loaded browser libraries; source F32 graphs downloaded only for development checks are excluded from q8 deployment size. JS heap is recorded separately and does not measure all GPU/native allocations. Throttling applies to CPU, not GPU hardware. These are local harness measurements, not installed-extension or Mac measurements. Cold timings use loopback-hosted local assets and OS disk cache; they are not internet installation times.

Source-to-F32 export tests passed and browser/Python token IDs matched on all 16 development emails. F32 Chrome outputs matched source model probabilities within 1e-4. The initial native-q8/browser-q8 equality check failed and is preserved: quantized runtime probabilities are not lossless equivalents, with the largest source/browser development drift in MobileBERT. This was diagnosed before validation, and the actual WASM q8 systems were calibrated and tested as such. No original hard gate was relaxed. Small development label agreement does not prove equivalence on future emails or another backend.

### BERT-small

At validation-selected cutoff `0.9553655426487072`, the operational set has TP=85, FN=164, FP=5, TN=36. MCC is 0.17; ECE is 0.384097; valid outputs are 100.0%. The worst completed-cell workflow p95 is 591.17 ms. Calibration: `{'kind': 'monotonic_sigmoid', 'slope': 0.68374078249441, 'intercept': 0.17978538948636463, 'epsilon': 1e-06}`.

### MobileBERT

At validation-selected cutoff `0.9409204693914101`, the operational set has TP=0, FN=249, FP=0, TN=41. MCC is n.a.; ECE is 0.151543; valid outputs are 100.0%. The worst completed-cell workflow p95 is 3966.03 ms. Calibration: `{'kind': 'monotonic_sigmoid', 'slope': 0.35855809688520035, 'intercept': -2.1856887083153618, 'epsilon': 1e-06}`.

### dima DistilBERT

At validation-selected cutoff `0.9387895182874094`, the operational set has TP=60, FN=189, FP=0, TN=41. MCC is 0.21; ECE is 0.100388; valid outputs are 100.0%. The worst completed-cell workflow p95 is 1494.69 ms. Calibration: `{'kind': 'monotonic_sigmoid', 'slope': 0.5040993268670699, 'intercept': -1.47123905216487, 'epsilon': 1e-06}`.



## Relation to the chosen TF-IDF baseline

On these identical 290 inputs, the earlier frozen TF-IDF/LR system detected 221/249 phishing and falsely alerted 38/41 controls. That historical evidence is retained, without rescoring it. New models use newly audited validation cohorts and their own cutoffs, so differences are system comparisons, not proof that architecture alone caused a change. The owner's documented TF-IDF choice and application code have not been silently changed or deployed.

## Qualification and applicability

The original common limits remain ID recall >=90%, ID FPR <=3%, OOD FPR <=15%, adversarial FPR <=15%, OOD recall >=70%, ECE <=0.10, plus encoder p95 <=500 ms, cold <=3 seconds, required assets <=100 MB and valid outputs 100%. Operational rate comparisons are reported as diagnostics; they are not renamed independent OOD/adversarial gates. Missing evidence is not passed. No original survivor-only weighted ranking or sensitivity winner is manufactured when full requirements are unavailable. Exact paired McNemar results with Holm correction and group-bootstrap 95% intervals are in metrics.json. McNemar assumes independent paired items, which repeated templates weaken; interpret it together with grouped intervals and per-class errors.

For this workflow, a classifier can provide a verdict and calibrated research score in one forward pass per window. The separate English software evidence/advice layer supplies exact excerpts, why the observed request matters, and complete suggested actions. Its validity checks cover sentence completeness and exact evidence offsets, not human-rated helpfulness or hidden model reasoning. Human explanation-quality review and actual highlighted-selection integration remain unassessed. Valid score output is not proof of a correct verdict. Error samples and observed setbacks are retained.

## Status

| Item | Status |
|---|---|
| Three pinned q8 artifacts and source/export checks | Built and measured |
| Known-source and common-role audit | Passed within documented scope |
| Validation-only calibration and 2% thresholds | Measured and frozen |
| Broad ID and shared operational comparison | Measured once per candidate |
| Chrome backend/throttle/cold matrix | Completed cells and failed/unsupported cells recorded |
| Zero generated tokens; local English evidence/advice path | Implemented and software-checked |
| Independent untouched release test and original adversarial/OOD completion | Unassessed |
| Human explanation quality, installed-extension and Mac evaluation | Unassessed |

Reproducibility: config.yaml, protocol.md, source revision/hash records, data manifest, export checks, calibration files, immutable scoring lock, raw private predictions, browser cell records, run_record.json and verification.json. Graph.csv is the sole chart-data table; PNG/SVG figures are generated with Matplotlib. Raw emails remain private and Git-ignored.
