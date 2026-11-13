# Sprint 3 TF-IDF held-out evaluation proposal

This protocol covers [#92](https://github.com/kendshhh/PhishLens/issues/92).
Wilberr owns the evaluation and Trixia reviews it. Approve the sources,
case inventory and thresholds before the first model run. The question is
how the existing TF-IDF v12a alert behaves on new visible-text examples
of current phishing, legitimate mail and non-phishing spam.

## Sources and labels

- Target at least 100 independent phishing families, 200 legitimate
  families and 100 spam families. Aim for at least 50 legitimate security
  notices within the legitimate group and 50 short selections of up to 200
  characters within each input class. For actual mail, propose cases dated
  January 2024 or later. Include more than one source or author per class
  and report class counts by source and collection period.
- Cover credential and MFA theft, invoice or payment redirection, delivery
  impersonation and text that directs the reader to a QR code. Include
  legitimate sign-in, OTP, password-reset and billing notices alongside
  routine mail. Separate unsolicited bulk promotions from consented
  newsletters, and retain short and long selections. Record when a label
  depends on context outside the selected text. [FTC phishing guidance](https://consumer.ftc.gov/articles/how-recognize-avoid-phishing-scams)
- Admit only public sources with documented permission for the evaluation
  or original examples with recorded contributor permission. The source
  manifest records publisher or author, publication or creation date,
  source revision, license or permission, collection method and allowed
  redistribution. Keep restricted examples local. If contemporary source
  rights cannot be established, propose an original synthetic challenge
  with inert domains and fictional identities. Report it separately from
  actual mail and identify the source gap.
- Label **phishing** when documented provenance or the synthetic scenario
  establishes a deceptive attempt to obtain credentials, money or access.
  Label **legitimate** for authentic or intentionally benign messages,
  including opt-in bulk mail. Label **spam** for unsolicited bulk mail
  without evidence of phishing. Phishing takes precedence over bulk delivery.
  Wilberr and Trixia label or adjudicate without seeing scores. Record
  disagreements and quarantine unresolved cases before the freeze.

### Selections that require outside context

Assign the message label using documented provenance or the synthetic scenario.
Independently, the two reviewers mark the selected text as `self_contained`
or `external_required` before scoring. A selection needs external context
when its meaning depends on a sender/domain, URL destination, attachment,
conversation history, or omitted text. Record a reason code in the manifest
and the supporting evidence in the private label review. Cases whose message
label cannot be resolved stay out of the scored manifest. For a known message
label and a context-dependent selection, send only the selected text to the
classifier and report the result under the context challenge. This measures
whether the selection triggers the alert when the true label depends on
information outside the model input.

Choose at most one primary and one context representative per family.
Keep remaining variants in the stress split. A family stays within a single
source kind and label. Report each split for actual mail and synthetic examples
separately. Context and stress results stay outside the primary screening
decision.

## Freeze and leakage checks

Record case ID, label, source revision, template family, selected body and
scenario tags in a private manifest. Check the raw and model-prepared text
hashes against each other, known training, calibration and threshold roles,
development fixtures including `synthetic-v1`, and the historical holdout.
Flag a shared normalized 30-word span or word-trigram Jaccard similarity
of at least 0.8 for manual template review. Review short selections
alongside their full texts and treat near-duplicates as one family.
Remove families that overlap earlier data before scoring.
Use one prespecified example per family for the main metrics. Keep variants
together and report stress variants separately. Record admitted and excluded
counts, the overlap rules and any data the team could not check.

Before scoring, pin the sorted manifest SHA-256, split IDs, source commit,
environment, scorer and decision contract. Use the bundled
`word_plus_char_wb_C1p0` artifact, SHA-256
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
Score the selected body once through the shared backend service in
`AI_MODE=tfidf`. Use its production masking and whitespace normalization
and first-2,000/last-300-code-point truncation. The phishing cutoff is raw
margin `>= 0` with the frozen sigmoid for display. Pin those implementation
files and the runner in the lock. Preserve the existing development
suite and the historical 1,200-message holdout as separate evidence.

## Runner and review bundle

Use Python 3.12 with `backend/requirements.txt` installed. Optional `psutil`
adds sampled process RSS. From the exact reviewed checkout, prepare a private
bundle directory with these files:

| File | Required contents |
| --- | --- |
| `manifest.jsonl` | UTF-8 JSON Lines sorted by unique `id`. Each row contains `id`, `source`, `family`, `label`, `split` (`primary`, `context`, `stress`), `scenario` (use `security_notice` for that subset), `context`, `body`, and `context_reason` for `external_required`. IDs and reason codes use lowercase letters, digits, underscores, dots or hyphens and begin with a letter or digit. |
| `sources.json` | JSON array. Each source contains `id`, `kind` (`actual_mail` or `synthetic`), `attribution`, `revision`, `date_range`, `permission`, `collection`, `redistribution`, and `evaluation_allowed`. Set the last field to true only after rights verification. Include the license or permission reference, source diversity and collection dates in the review. |
| `label-review.json` | Object with `manifest_sha256`, `reviewers` (two distinct names), `score_blind`, and `unresolved_admitted`. Include label/context rules, disposition of disagreements and excluded counts in the private review record. |
| `overlap.json` | Object with `manifest_sha256`, `reviewer`, `method`, `unresolved_admitted`, and `roles`. Include `within_cohort`, `synthetic-v1`, `training`, `calibration`, `threshold`, and `historical_holdout` in `roles`. Each value has `status` (`checked` or `limited`) and a `reference` to the report or reason for the limitation. Document exact and near-duplicate checks, comparison revisions, flagged and excluded family counts, and manual resolutions. |

Run the read-only preflight and capture its output as UTF-8. In PowerShell:

```powershell
$lockJson = python scripts/evaluate_tfidf_cohort.py preflight --bundle $CohortBundle
if ($LASTEXITCODE -ne 0) { throw "Cohort preflight failed" }
$lockJson | Set-Content -LiteralPath $CohortLock -Encoding utf8NoBOM
Get-FileHash -LiteralPath $CohortLock -Algorithm SHA256
```

The preflight performs zero classifier inferences. It validates the manifest,
checks exact raw/prepared duplicates and overlap with `synthetic-v1`, and
pins the review files, family counts, model contract, Python/Pydantic versions
and implementation hashes. The private overlap report supplies the near-duplicate
review and checks against earlier data. Submit the source-rights inventory,
label adjudication and context decisions, family counts, overlap report, lock
SHA-256, and final criteria to Trixia before the freeze. If contemporary source
rights or label evidence are missing, record the gap before proposing any
separate synthetic-only exercise.

After Trixia approves the frozen bundle and separately approves the first
scoring run, use the SHA-256 she reviewed and a fresh private output path:

```powershell
python scripts/evaluate_tfidf_cohort.py score --bundle $CohortBundle --lock $CohortLock --expected-lock-sha $ApprovedLockSha --output $PrivateReport
```

The scorer checks the lock against the current bundle, checkout, and runtime
before reserving the output path with a sibling `.running` directory and
publishing an `incomplete` JSON status record. The runner replaces the
status record atomically with the final report. An unexpected scoring error
records `execution_failed` without raw error text. A hard stop can leave
the reservation and the last published record. If the record is absent or
still says `incomplete`, no final results were published. Keep the evidence
for review before using a fresh path for a rerun.

The scorer runs the pinned TF-IDF adapter through
the backend `AIService` once per selected case. Keep the per-case report private.
Share aggregates, hashes, and sanitized limitations. Use a new approved lock
for any input, source, or scoring change. A failed or interrupted run stays
recorded and requires review before a rerun.

Exercise the procedure with separate repository fixtures using
`python -m unittest scripts.tests.test_evaluate_tfidf_cohort -v`.
The fixtures test the local runner and do not supply held-out evidence.

## Report and review

Report attempted, alerted, below-threshold and failed counts by input class,
source and scenario. Report phishing recall and alert precision for the
observed cohort class mix, the
legitimate-only false-positive rate, the spam phishing-alert rate and the
combined non-phishing rate with explicit denominators. Include 95% Wilson
intervals using one observation per family. Stress variants receive descriptive
counts and rates. TF-IDF has two output labels, so spam detection
accuracy is undefined. Count failed phishing calls as missed detection
opportunities and list errors, timeouts and unattempted cases separately.
A failed negative call does not count as a correct below-threshold result.

Record commands, hashes, hardware, cold first-call time, warm p50/p95
and sampled process RSS when available. Report scoring runtime separately
from browser, hosted and saved-report acceptance.

For primary actual mail, propose **at least 90% phishing recall**, **at most
3% legitimate-only false positives**, and **100% valid results**. The
[historical study](../../benchmark-records/tfidf_false_alarm_v12a/summary.md#metrics-and-gates)
used a 90% recall floor and a 3% source-pair false-positive ceiling. Applying
those values to this new cohort is a proposal. At those values, at most one in
ten phishing selections can be missed and at most three in a hundred
legitimate selections can trigger an alert. The earlier 70% proposal is withdrawn.

Report security notices and non-phishing spam as diagnostic strata. Their
false-alert rates reflect different costs: a security-notice alert can
interfere with a legitimate account action, while a spam phishing alert can
increase alert fatigue. The earlier 15% proposals are withdrawn because the
available evidence does not establish acceptable costs or a baseline for either
stratum. Use the counts and intervals to identify scenarios for follow-up.
Review a proposed numeric limit on fresh data before using one as a gate.

The primary decision stays unassessed if any primary family minimum, the
50-notice minimum, the two-source minimum per input class, or a required
overlap comparison is missing. Review the source inventory for genuine
diversity and assess the short-selection targets before approval.
The thresholds are point estimates and the intervals describe uncertainty.
Meeting them supports continued evaluation of the pinned configuration.
A miss calls for investigation on development data. These results provide
neither release nor instructor acceptance.
Use any misses to plan work on development data. A model or threshold
change requires a different untouched cohort for confirmation.
