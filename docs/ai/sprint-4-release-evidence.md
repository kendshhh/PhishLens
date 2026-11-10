# Sprint 4 AI provenance and verification

Audited source: `fa9a23fbb5d1d60c45d0fc06333c50415d04d57e` on November 10, 2026.
This is the source baseline for the checks below. Release candidate selection,
deployment verification, and model-quality approval are separate gates.

## Model and runtime

| Layer | Identity and behavior |
| --- | --- |
| Primary saved-analysis model | TF-IDF v12a, `word_plus_char_wb_C1p0`. SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. Browser and backend use the same exported linear classifier and decision contract. |
| Input and decision | Visible text only. The shared preprocessing masks email local parts, phone-like patterns and long numbers, collapses whitespace, and retains the first 2,000 and last 300 Unicode code points for long inputs. The server scores the saved body. Word and within-word character TF-IDF features produce a raw margin. The alert cutoff is zero, corresponding to a displayed score of about 88.71% under the frozen sigmoid. The score depends on the evaluation mixture. |
| Explanation and persistence | The backend validates evidence against the submitted text and writes server-owned prediction, risk and provenance. TF-IDF saves use `analysis_mode=real`, provider `tfidf`, and the model SHA. Word-feature quotes give partial attribution. Browser review uses KRR, LightGBM and the pinned local Llama judge. The backend records the judge as browser-reported. Missing judge assets or incompatible WebGPU can yield `Uncertain`. |
| Other modes | Gemini is an optional real adapter. Its saved-create SDK budget is 15 seconds with one attempt. Unsaved `/analyses` uses a separate 30-second SDK timeout. Mock is deterministic CI evidence. Pinned CPU DistilBERT is an optional unsaved development path, with historical smoke evidence. |

See [TF-IDF attribution](../../extension/ai/ATTRIBUTION.md) for the Kaggle
compilation’s declared CC BY-SA 4.0 license, the Nazario source’s declared CC BY
4.0 license, and the limits on underlying message rights. The archived report
provides the source mix and labeling rules. Keep raw examples and per-message
predictions in the authorized local workspace. For the optional browser judge,
use the [asset manifest](../../extension/ai/judge-assets.json) and its pinned
license file. See [the browser workflow](live-workflow.md) for package and
hardware requirements.

## Frozen evaluation and rerun evidence

The [v12a study](../../benchmark-records/tfidf_false_alarm_v12a/summary.md)
records a once-only fresh confirmation of the selected model on 1,200
source-labelled messages across 1,135 groups. The prepared cohort SHA-256 is
`005a67455b0f31f7f7e59be6b8949bcfd5dadb1a539ba1af8fae8eee5f9e27de`.
The [scoring lock](../../benchmark-records/tfidf_false_alarm_v12a/final_lock.json)
was checked against its archived run record.

| Scoped result | Reconciled value |
| --- | --- |
| Phishing | 190 detected, 10 missed out of 200. Recall 95.0%. |
| Benign | 1 false alert, 999 below threshold out of 1,000. False-positive rate 0.1%. |
| Precision | 190/191 (99.48%) at the study’s class mix. |
| Valid output | 1,200/1,200 for v12a. |

Selection and calibration used development, calibration and threshold roles
before final scoring. The audit rechecked six role hashes, all 60 pairwise
checks across row IDs, full-text hashes, prepared-input hashes and group IDs,
and recomputed confusion counts from the three archived prediction sets
(3,600 rows). This reproduces the recorded counts without new inference or
tuning. Fresh here means unused in this project’s development. The cohort
contains source-labelled historic messages, a single phishing collector and
source/class confounding. It excludes a separate spam class. One false alert
was a bank statement. Independent contemporary security notices, adversarial
or distribution-shift cases, short selections, Mac performance and human-rated
explanations remain open. Browser timing in the study covers prepared-text
scoring and observations. It does not measure hosted latency, installation or
the complete browser review. The combined judge workflow has its own
[functional evidence](live-workflow-verification.md).

Run from the repository root with Python 3.12:

```sh
python scripts/verify_tfidf_evaluation.py
python scripts/verify_tfidf_evaluation.py --prepared-dir benchmarks/tfidf_false_alarm_v12/data/prepared --predictions-dir benchmarks/tfidf_false_alarm_v12a/results/predictions
```

The first command checks the bundled model, decision contract and archived
metadata. The second requires the existing authorized local corpus and saved
predictions. Both print only aggregate evidence and hashes. Both passed. A
fresh scoring pass needs a separately approved protocol and case set. The
original lock preserves the once-only confirmation.

On the audited source, a Windows Python 3.12 virtual environment with
`AI_MODE=mock` and `RUN_DATABASE_TESTS=0` ran the following focused suite:

```sh
python -m pytest -q -p no:cacheprovider \
  backend/tests/test_ai_api.py backend/tests/test_ai_service.py \
  backend/tests/test_ai_providers.py backend/tests/test_provider_error_contract.py \
  backend/tests/test_tfidf_provider.py backend/tests/test_saved_create.py \
  backend/tests/test_saved_provider_pipeline.py backend/tests/test_analysis_deadlines.py \
  backend/tests/test_analysis_execution.py backend/tests/test_analysis_execution_process.py \
  backend/tests/test_analysis_worker.py backend/tests/test_analysis_database.py \
  backend/tests/test_analysis_persistence.py backend/tests/test_saved_create_postgres.py
```

**155 passed, 31 skipped.** The skipped cases require disposable PostgreSQL.
This suite includes real bundled TF-IDF scoring on software fixtures and
simulated provider and storage failures. The audit made no external inference
calls or hosted database writes. The proposed deterministic regression policy
still needs an AI-owner decision under [#93](https://github.com/kendshhh/PhishLens/issues/93).

## Earlier sprint carryover

| Sprint | Existing evidence | Remaining decision or evidence |
| --- | --- | --- |
| 1 | [PR #26](https://github.com/kendshhh/PhishLens/pull/26) merged the adapter and shared service work. The [October 18 handoff](../devops/ai-review-2026-10-18.md) records real-local DistilBERT smoke, timing and limitations. | [#8](https://github.com/kendshhh/PhishLens/issues/8) and [#21](https://github.com/kendshhh/PhishLens/issues/21) are open. Reconcile their remaining integration and reviewer checkboxes against the merged PR and the historical run. |
| 2 | [PR #99](https://github.com/kendshhh/PhishLens/pull/99) merged the current TF-IDF workflow. [PR #121](https://github.com/kendshhh/PhishLens/pull/121) added real-provider persistence coverage. [#90](https://github.com/kendshhh/PhishLens/issues/90) records an authorized staging TF-IDF lifecycle. | [#48](https://github.com/kendshhh/PhishLens/issues/48) and [#49](https://github.com/kendshhh/PhishLens/issues/49) still need an evidence crosswalk and scope sign-off. Keep DistilBERT’s historical suitability evidence separate from the TF-IDF release decision. |
| 3 | The archived v12a study supplies held-out evidence for the admitted source pair. [PR #104](https://github.com/kendshhh/PhishLens/pull/104) supplies deterministic gates and a guarded smoke path. [PR #107](https://github.com/kendshhh/PhishLens/pull/107) covers the model-hash mismatch and bounded Gemini behavior on its reviewed revision. | Review [#92](https://github.com/kendshhh/PhishLens/issues/92) against the scoped evaluation and its missing cohorts. Record the decision under [#93](https://github.com/kendshhh/PhishLens/issues/93). Coordinate protected smoke and supported failure/recovery evidence under [#94](https://github.com/kendshhh/PhishLens/issues/94), [#95](https://github.com/kendshhh/PhishLens/issues/95) and [#96](https://github.com/kendshhh/PhishLens/issues/96). |

## Release and demonstration gates

- [#132](https://github.com/kendshhh/PhishLens/issues/132),
  [#137](https://github.com/kendshhh/PhishLens/issues/137) and
  [#142](https://github.com/kendshhh/PhishLens/issues/142) can use this draft
  as their audit, reproduction and methodology record. Resolve the open scope
  and evaluation decisions before sign-off.
- For [#147](https://github.com/kendshhh/PhishLens/issues/147), repeat the
  artifact check from Kendra’s exact candidate checkout. Match its SHA to
  `/version`, the model hash to `/model-info`, and the model hash and provider
  to a synthetic saved report on the authorized target. Retain the compatible
  known-good app/model revision and record the recovery choice. A historical
  staging pass establishes the tested revision only.
- For [#152](https://github.com/kendshhh/PhishLens/issues/152), use the scoped
  confusion counts and a synthetic saved report alongside a labelled failure
  simulation. The [local 503 demo](../ai-failure-demo.md) shows missing Gemini
  configuration. Protected-staging failure and recovery timings require the
  approved drill. Coordinate package acceptance with the browser owner and
  keep [the release gate](https://github.com/kendshhh/PhishLens/issues/153)
  tied to the reviewed candidate.
