# TF-IDF sprint verification and demo

November 13, 2026. Application source audited at `81fb4103bf859b96f950489e397eac7adb26ea2e`.
The model is TF-IDF v12a, `word_plus_char_wb_C1p0`, with SHA-256
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
The [AI contract](../ai.md) describes the input, alert policy, evidence and
saved provenance. The [artifact attribution](../../extension/ai/ATTRIBUTION.md)
records the source licenses and the limits on underlying message rights.

| Sprint | Issue | Evidence and open acceptance |
| --- | --- | --- |
| 1 | [#8](https://github.com/kendshhh/PhishLens/issues/8), [#21](https://github.com/kendshhh/PhishLens/issues/21) | Trixia reproduced all three TF-IDF smoke cases through the shared backend at `2bd72c6`. The October 18 DistilBERT run remains historical. Record the agreed change in scope on the original issues before counting TF-IDF against criteria that name DistilBERT. |
| 2 | [#48](https://github.com/kendshhh/PhishLens/issues/48) | Trixia confirmed the output, error and persistence contract at `2bd72c6`. [PR #121](https://github.com/kendshhh/PhishLens/pull/121) covers saved-provider mapping and persistence. [Issue #90](https://github.com/kendshhh/PhishLens/issues/90#issuecomment-6683245280) records the earlier protected TF-IDF create/read/list/delete run. Fresh staging evidence is needed on the revision selected for acceptance. |
| 2 | [#49](https://github.com/kendshhh/PhishLens/issues/49) | Model metadata, local smoke, runtime measurements and a leakage-controlled evaluation are available. The failure rehearsal below can be repeated without a database. Record instructor acceptance of the TF-IDF scope and the resulting evaluation decision. |
| 3 | [#92](https://github.com/kendshhh/PhishLens/issues/92) | The frozen source-pair evaluation and the current development results are reported below. Fresh separately labelled spam and modern phishing coverage still need review before making a broader quality claim. |
| 4 | [#132](https://github.com/kendshhh/PhishLens/issues/132), [#142](https://github.com/kendshhh/PhishLens/issues/142) | Model identity, input policy, attribution, data roles and coverage limits are documented. The release owner still needs to freeze the application candidate under [#153](https://github.com/kendshhh/PhishLens/issues/153). |
| 4 | [#137](https://github.com/kendshhh/PhishLens/issues/137) | Replayed all 1,200 archived TF-IDF decisions with the pinned backend scorer and reran development and failure checks. The replay checks reproducibility against the historical confirmation. |
| 4 | [#147](https://github.com/kendshhh/PhishLens/issues/147), [#152](https://github.com/kendshhh/PhishLens/issues/152) | A guarded saved-report check and a local demo sequence are ready. Candidate deployment evidence and the actual presentation and Q&A remain open. |

## Reproduce the evaluations

Use Python 3.12 with the backend requirements. Install `psutil` to include
peak process RSS and system RAM. Without it, those fields are null and the
benchmark still reports predictions and timing. Run from the repository root:

```sh
python scripts/ai_smoke.py --mode tfidf
python scripts/benchmark_ai.py --models tfidf --repeats 1
python scripts/verify_tfidf_evaluation.py
```

The three smoke cases returned the expected labels for `p01-credential`,
`l01-meeting` and `l12-document`. On Windows 11 with Python 3.12.10,
the 40-case development run completed with no inference errors. The first
shared-service call, including loading the model, took about 38 ms. Warm
p50/p95 were 0.38/0.52 ms and sampled process RSS peaked at 115.2 MiB.
These are local backend measurements. The browser timing in the original
study measures a different workflow.

| Evidence | Phishing | Legitimate | Spam |
| --- | --- | --- | --- |
| Historical frozen source pair | 190 alerts, 10 misses | 1 false alert, 999 below threshold | No separate spam cohort |
| Local `synthetic-v1` development rerun | 3 alerts, 13 misses | 1 false alert, 15 below threshold | 0 alerts, 8 below threshold |

The historical result gives 95.0% phishing recall, 99.48% alert precision
and 0.1% false positives on legitimate mail. The development run gives
18.75% phishing recall and 75% alert precision. The legitimate-only false
positive rate was 1/16 (6.25%). The spam phishing-alert rate was 0/8 (0%).
The combined non-phishing false positive rate was 1/24 (4.17%). TF-IDF emits
binary labels, so spam is reported as an input group. The development examples are CC0,
version `synthetic-v1`, SHA-256
`a755533aa841bc695574196b3147f2c3b408129872a62204c1f4c5f149ab226f`.
The missed phishing examples are evidence of limited transfer to this set.
Neither cohort estimates performance across current user inboxes. Trixia
independently reproduced the development counts and the archived hash/count
checks at `2bd72c6`. The archive check she ran performed zero classifier
inferences. The private 1,200-case replay and the Windows timing and memory
measurements are from the author's run.

For the [frozen study](../../benchmark-records/tfidf_false_alarm_v12a/summary.md),
the source pair contains 1,200 messages in 1,135 groups. Its prepared SHA-256 is
`005a67455b0f31f7f7e59be6b8949bcfd5dadb1a539ba1af8fae8eee5f9e27de`.
With the authorized local corpus and saved predictions, rerun the archive
check using `--prepared-dir` and `--predictions-dir` together. All six role
hashes, 60 overlap comparisons and 3,600 saved prediction rows across the
three study models reconciled. The existing [parity checker](../../scripts/check_tfidf_parity.py)
also replayed 52 development fixtures against archived margins and Python/Node
visible-text scoring. The largest margin difference was below `1e-12`.
These checks leave the original score lock and held-out predictions intact.

Add `--replay-tfidf` when running the archive verifier with both local
directories to reproduce the TF-IDF scores from the already prepared cohort.
The replay reproduced 1,200 of 1,200 alert decisions. The largest absolute
margin and sigmoid score differences were about `9.77e-15` and `1.11e-15`,
respectively. The script checks input and prediction hashes before inference
and emits aggregate values only. This is a read-only reproduction of an
existing result on the same data. Use a new frozen cohort for an independent
quality test.

The [proposed Sprint 3 cohort protocol](tfidf-sprint-3-evaluation-protocol.md)
defines source admission, labels, overlap checks, reporting and proposed
thresholds for Trixia's review before any new scoring.

## Candidate verification and recovery

The November 13 read-only probe found staging at `199fa5b8263d334a7d1f88f63eec2fb9f96ae971`,
reporting TF-IDF with the expected model hash. Production reported
`81fb4103bf859b96f950489e397eac7adb26ea2e` and returned
`provider_mode=unavailable` and `accepts_tfidf_reports=false` at
`/model-info`. That endpoint does not identify why TF-IDF saves are unavailable.
The release candidate and its saved-report provenance are still unverified.

Once the release owner identifies the reviewed candidate and confirms the
isolated staging database, run the artifact verifier from that checkout. Then
run the following from the verifier checkout with the approved staging target:

```powershell
node scripts/verify_saved_report.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha CONFIRMED_BACKEND_SHA --expected-model-sha a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c --allow-writes
```

The verifier checks the deployed app SHA, database readiness and advertised
model before saving. It uses one synthetic record and compares returned and
reread provenance, then verifies cleanup. Retain the JSON result with the
deployment link. Recheck the target version if shared staging changes.

If the approved target requires Neon report authentication, add
`--auth-token-file PRIVATE_LOCAL_FILE` to the same command. Keep the token
file outside the checkout and use a current access token for the authorized
synthetic account. Remove the local token file when finished. The verifier expects
anonymous report access to return 401 and uses the same token for create,
read and cleanup. Use the installed extension for OTP, token renewal and
two-account isolation checks.

The previous staging recovery target `0769de936c349f57bf32540d92adaab97f7c402a`
contains the same TF-IDF decision contract. The recorded staging rehearsal
restored `46a2b27c199c64a25261d3cbba7e52a3352e7a98`. Since current
`main` also includes the applied Neon Auth migration, compare the candidate's
schema expectations with the selected recovery target before choosing it.
See [the recovery evidence](https://github.com/kendshhh/PhishLens/issues/95)
and [runbook](../devops/runbook.md). The release owner must select and verify
a compatible recovery revision for the actual target.

## Demonstration

1. Show the candidate revision and model hash. Run the TF-IDF smoke and explain
   which text is scored, how the alert is set and how evidence is validated.
2. Show the authorized synthetic saved report's provider and model revision
   in its detail response. Use the guarded verifier output for the cleanup.
3. For a local failure rehearsal, start the app in `AI_MODE=tfidf` and use
   a fixed synthetic payload. Send it to `POST /analyses` and expect 200.
   Send the body to `POST /api/analyses` with a valid `Idempotency-Key` and
   64 zeroes in `X-PhishLens-Model`. Expect 503 and
   `analysis_unavailable` before storage. Repeat the unsaved request and
   expect 200. This sequence was verified in process against the FastAPI app.
4. Present both metric rows, including the 13 development misses. Explain
   that the model screens text and does not authenticate senders or classify
   spam. Browser `Uncertain` comes from the review layer. Record actual
   questions and answers after the presentation.

The local mismatch exercises the real TF-IDF request path. The protected
failure and recovery drill remains with [#95](https://github.com/kendshhh/PhishLens/issues/95).
