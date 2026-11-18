# TF-IDF v12a synthetic diagnostic — November 18, 2026

**The single run finished, but the primary synthetic phishing result is poor:
1/12 detected and 11/12 missed. This is not a model-quality acceptance.**
All 45 cases returned valid outputs with no inference error, timeout or
unattempted case. Contemporary actual-mail screening remains **unassessed**.

The earlier 1,200-message source-pair result (190 TP, 10 FN, 1 FP, 999 TN)
retains its historical scope. It must not be pooled with this challenge or used
as evidence that these different selections were detected successfully.

## Freeze, rights and review

- Candidate: 45 original fictional English selections, 42 families, one original
  synthetic source. The primary split has 12 independent families per label;
  six legitimate examples are security notices. Six context-dependent selections
  and three same-family stress variants have separate splits. No private inbox
  content was used. Attribution, creation method and evaluation permission are
  recorded in the original bundle's source inventory.
- Manifest: `dd9e312065eee718d1b5c6fac19b3582cd30079fdd60c98f610d3055407f366e`.
  Lock: `7a5d7280efca7849a8e9b34f498b4e073d7ce5773f6c613ea0d15487286a9b51`.
  [Exact bundle and overlap files](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6891932603).
- The renewed exact/30-word-span/trigram-Jaccard overlap audit raised zero flags
  against this cohort, 40 development cases and 30,291 archived rows across
  development/training, calibration, threshold and historical holdout roles.
  This cannot exclude semantic resemblance or overlap with unavailable texts.
- Trixia reviewed the initial labels/context/families score-blind and requested
  the `s07` bulk-delivery clarification. Its fictional scenario was corrected;
  message text, label and family stayed unchanged. Her final corrected-lock and
  first-run approval remained pending. The user had authorized EnviousCoal to
  approve the freeze and score locally. That [owner-authorized protocol
  exception](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6983613256)
  was recorded **before** the single scoring run. No final approval is attributed
  to Trixia.

The original author knew the earlier model/development findings. This is a small,
deliberately varied diagnostic challenge, not a random or representative sample
of current mail. Label/context decisions and the cutoff were frozen before scores
were viewed; no case was removed or relabeled after the results.

## Exact execution

Source: `8322fb802f59dd1db0b00563211e188b1cf858d4`. TF-IDF model
`word_plus_char_wb_C1p0`, SHA-256
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`, raw-margin
alert cutoff `>= 0`. The shared backend `AIService` and pinned preprocessing
were used. No model, threshold or preprocessing change followed this run.

Windows 11 build 26300, Python 3.12.10, Pydantic 2.13.4, x64/16 logical CPUs.
Pydantic matches the actual reviewed lock; the historical requirements file pins
2.14.1. This environment exception is disclosed and is not current-release
dependency acceptance. The exact lock bytes were reproduced before scoring.

```text
python scripts/evaluate_tfidf_cohort.py score --bundle <frozen-bundle> --lock <preflight-v2.lock.json> --expected-lock-sha 7a5d7280efca7849a8e9b34f498b4e073d7ce5773f6c613ea0d15487286a9b51 --output <fresh-private-output>
```

Only this one scoring invocation was made. The original per-case report is
retained locally, SHA-256
`42bbc9acbae2acdfc1beea4441072a3bd99ace171058a77203b34839cb1123b5`.
[Aggregate JSON](tfidf-synthetic-diagnostic-2026-11-18.json) contains the confusion
counts, denominators, intervals, identities and timing. Recalculating aggregates
from the retained report requires no inference. Future scoring of these cases
is a replay of consumed data, not an untouched confirmation.

## Results by split

| Split | Phishing alerts / phishing cases | Legitimate false alerts | Non-phishing spam alerts | Valid outputs |
| --- | --- | --- | --- | --- |
| Primary | 1/12 (8.33%) | 0/12 | 0/12 | 36/36 |
| Context-dependent | 0/2 | 0/2 | 0/2 | 6/6 |
| Stress variants | 0/1 | 0/1 | 0/1 | 3/3 |

Primary phishing recall's 95% Wilson interval is **1.49–35.39%**. Primary
legitimate FPR is 0/12, with interval approximately **0–24.25%**; zero observed
false alerts does not establish a population FPR below 3%. All six primary
legitimate security notices were below threshold, with interval approximately
0–39.03%. Alert precision at this synthetic class mix is 1/1, interval
20.65–100%; one alert supplies little precision evidence. TF-IDF is binary:
spam's phishing-alert rate is diagnostic, not three-class spam accuracy.
Context and stress cases are not pooled with primary metrics; stress variants
are correlated and receive descriptive rates only.

First measured inference: **22.42 ms**. Warm p50: **0.258 ms**; p95: **0.401 ms**.
These exclude process/dependency startup and preflight and are not hosted
cold-start or end-to-end timings. Process RSS was not measured. No provider call,
database request/write, staging request or deployment occurred.

## Error analysis and decision

Only primary case `p03` (payment redirection) alerted. Below-threshold misses
were `p01/p06/p09/p12` (credential theft), `p02/p11` (MFA theft), `p04` (delivery
impersonation), `p05` (QR lure), `p07` (another payment-redirection family), `p08`
(account access) and `p10` (wallet-secret theft). The cases' fictional provenance
establishes the labels; the model sees selected text only. Both context-dependent
phishing selections also stayed below threshold.

This is evidence of a detection gap on these selections. It does not establish
the cause or a population accuracy estimate. Valid schema/output delivery does
not establish correct classification or human-rated explanation quality. The
actual-mail decision remains unassessed: there is no admitted contemporary
actual-mail cohort meeting the protocol's family, source and notice minima.

**Decision:** do not claim the current model is accepted for broad contemporary
phishing screening or that Sprint 3's AI quality gate is complete. Preserve the
historical result with its original scope and keep #92 In Progress for the
remaining coverage/quality decision. No production configuration was changed.

Next, use development data and these now-consumed diagnostic errors to investigate
credential/MFA/QR/wallet and short-selection coverage. Evaluate an improved
configuration on development data, then freeze a different untouched confirmation
cohort with documented rights/labels/overlap and prospective criteria before
scoring it. Keep the approved actual-mail goals (90% recall, at most 3% legitimate
FPR, 100% valid output) separate from this small synthetic diagnostic. Do not lower
the cutoff or rewrite these labels to turn this report into a pass.
