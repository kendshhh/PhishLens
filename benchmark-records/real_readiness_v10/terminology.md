# Reading this retest

| Term | Meaning in this run |
|---|---|
| Recall | Detected publisher-phishing inputs divided by 249. A low value means many missed attacks under those labels. |
| False-positive rate (FPR) | Falsely alerted collector-attested controls divided by 41. It is not divided by all 290 messages. |
| Valid output | Output obeyed the frozen numeric/JSON/English rules. Valid does not mean correct. |
| Fail-open | Unusable output counted as safe and invalid. It remained in all applicable denominators. |
| Consistency | All five Llama outputs were valid and label-identical. Denominator: 30 preselected inputs. |
| 2% validation target | The cutoff was selected on earlier validation only. It does not promise 2% false alarms on other email populations. |
| Risk score | A probability mapping fitted to the old validation study. This shift test does not establish a reliable personal-inbox percentage. |
| Group-bootstrap interval | Resamples related-text groups to reflect dependence. It does not remove source bias or prove correctness of inherited labels. |
| Exact binomial interval | Additional diagnostic assuming independent examples. Repeated templates make that assumption optimistic here. |
| Previously inventoried | A source text was parsed/indexed before. That alone is not model fitting or scored-test reuse. Actual role overlaps were excluded before scoring. |
| Selected model | The project owner's implementation choice. |
| Qualified model | A system satisfying every required gate with supporting evidence. No system qualified in this run. |
| Observational latency | Browser inference time observed while scoring. It is not the complete warmed/throttled/cold matrix or installed-extension latency. |

These are source-pair results with 249 positives and 41 negatives. Precision and accuracy depend on that class mix and must not be advertised as population-wide inbox performance. The raw counts, labels, source provenance and uncertainty are necessary context for the percentages.
