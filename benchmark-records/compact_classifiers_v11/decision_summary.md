# Model choice from the three-candidate comparison

**Recommended next development baseline: BERT-small, using WASM. Release-qualified winner: none.** This is an engineering preference among tested candidates, not an original weighted-scorecard winner or proof that the current checkpoint is suitable for release.

| Model | ID recall | ID FPR | Operational detections | Control false alerts | Operational balanced accuracy |
|---|---:|---:|---:|---:|---:|
| BERT-small | 79.0% | 2.0% | 85/249 (34.1%) | 5/41 (12.2%) | 61.0% |
| MobileBERT | 65.4% | 1.6% | 106/249 (42.6%) | 4/41 (9.8%) | 66.4% |
| dima DistilBERT | 79.0% | 1.0% | 60/249 (24.1%) | 0/41 (0.0%) | 62.0% |


These are the separately labeled precision-corrected diagnostic results. The original frozen MobileBERT pipeline produced no alerts because calibration clipping merged distinct high scores. The correction was fitted only on the existing calibration role; the raw-ranking alert cutoff still uses the separate 1,000-legitimate validation cohort at 2% FPR. All three models receive the same correction method. Cached raw test outputs were reanalysed; no classifier inference was repeated and no original result or gate was overwritten. This is not a newly untouched confirmatory test. JavaScript/Python arithmetic replay verified all 12,879 cached calibration, cutoff and test scores, with identical raw-threshold decisions.

BERT-small on **WASM** is the strongest engineering baseline for the next development iteration: its measured workflow p95 is 97.05 ms at 1x and 377.28 ms at 4x CPU throttle, its worst recorded WASM cold readiness is 2,977.60 ms, and its required browser assets total 57.23 MB. It is the only candidate meeting all measured WASM speed/cold/size/validity limits in both throttle conditions. The cold result is close to the 3-second limit and is not a guarantee on another machine. Its 4x WebGPU cell fails, so it does not pass the entire original matrix.

**That is not a release recommendation.** BERT-small detected only 85/249 operational publisher-positive messages and falsely alerted 5/41 controls; broad ID recall was 79%. These are measured recall failures, beyond the original missing independent OOD/adversarial requirements. No model is a fully qualified winner, and the existing owner-selected TF-IDF application has not been replaced.

The original MobileBERT zero-alert result is partly a calibration-pipeline precision defect, not evidence that its weights detect no phishing. The old 1e-6 clipping flattened high validation scores. A separate, validation-only precision correction and raw-ranking alert cutoff recover 106/249 operational detections with 4/41 false alerts; ID recall is 65.4%. This diagnostic reuses saved raw outputs; it is not a fresh confirmatory test and does not overwrite the frozen experiment. See the precision follow-up report for the corrected risk mapping and counts.

After that correction, MobileBERT has the highest operational balanced-accuracy point estimate (66.41%), versus dima 62.05% and BERT-small 60.97%. MobileBERT versus BERT-small is not statistically established on the operational set after Holm correction (McNemar p=0.06415), which does not prove equivalence. BERT-small and dima are inconclusive on broad ID (p=0.68486); the frozen speed/simplicity tie preference favors BERT-small there. MobileBERT's ID outcome is significantly weaker than BERT-small's, and its 4x WASM and WebGPU paths exceed the latency limits. These are different tradeoffs, not a universal accuracy winner or an original weighted ranking.

Dima has the fewest observed operational control false alerts (0/41), accompanied by only 60/249 detections and a slower browser path. Zero errors on 41 controls does not establish a zero population false-positive rate. It cannot be selected as a reliable phishing screen on that favorable FPR alone.

The workflow advantages that were demonstrated are local browser inference, zero generated tokens, valid numeric outputs, shared text coverage and complete English software evidence/advice. The outstanding problem is detection quality under source/task shift. Increasing generation length or changing a prompt cannot fix these non-generative classifiers; a revised learned artifact would require development/validation and separately reported evaluation.


All three have valid numeric outputs and zero generated tokens. Model weights are 28.99 MB (BERT-small), 26.58 MB (MobileBERT), and 66.19 MB (dima). Full required browser assets are larger because they include the loaded runtime and tokenizer. The speed matrix measures the original frozen workflow; the precision correction is separately verified postprocessing and was not given a new full Chrome latency run. Model weights, text windows and inference are unchanged. Never present these timings as separately measured corrected end-to-end response times.

There were 9,000 validation predictions and 3,879 final test predictions (1,003 ID plus 290 operational inputs per model). Twelve Chrome cells each timed 100 emails after 10 discarded warmups, with three cold trials. Five software tests passed. The assistant inspected 59 distinct error cases, including 25 false negatives per model and all available false positives up to 25. This is not independent human review. Source labels and origin caveats remain in the full report; examples that may be ambiguous were not removed to improve results.

The original cross-backend runtime gates fail for all candidates when every required cell is considered. BERT-small's two WASM cells alone fit their measured budgets; its 4x WebGPU cell fails. All three fail the required ID recall and the operational recall comparison, and no original independent two-class OOD/adversarial qualification is completed. No survivor-weighted ranking or sensitivity winner exists. The 2% target and original numeric limits remain fixed.

Implementation takeaway: compact local classification with a separate complete English evidence/advice layer is workable in this browser. These downloaded learned artifacts need further model development before their verdicts can support the promised security performance. Changing to another public checkpoint or declaring a pass does not repair these measured misses. The owner's TF-IDF choice and application runtime remain unchanged.

Source IDs and full versions are in config.yaml and run_record.json. BERT-small's declared corpus and dima's notebook-linked corpus were conservatively excluded by the recorded audit. MobileBERT training provenance remains incomplete. Results apply to this data and Windows laptop; no Mac, installed-extension, independently human-rated explanation or bias-free certification is claimed.
