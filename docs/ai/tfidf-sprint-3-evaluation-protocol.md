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
files and the runner in the manifest. Preserve the existing development
suite and the historical 1,200-message holdout as separate evidence.

## Report and review

Report attempted, alerted, below-threshold and failed counts by input class,
source and scenario. Report phishing recall and alert precision, the
legitimate-only false-positive rate, the spam phishing-alert rate and the
combined non-phishing rate with explicit denominators. Include 95% Wilson
intervals using one observation per family. TF-IDF has two output labels, so spam detection
accuracy is undefined. Count failed phishing calls as missed detection
opportunities and list errors, timeouts and unattempted cases separately.
A failed negative call does not count as a correct below-threshold result.

Record commands, hashes, hardware, cold first-call time, warm p50/p95
and sampled process RSS when available. Report scoring runtime separately
from browser, hosted and saved-report acceptance.

Proposed screening criteria for this cohort are **at least 70% modern
phishing recall**, **at most 3% legitimate-only false positives**, **at
most 15% false positives in the legitimate security-notice subset**, **at
most 15% phishing alerts on spam**, and **100% valid results**. These are
proposed point-estimate thresholds. Report interval bounds and small strata
alongside each result. A missing planned group leaves that criterion
unassessed. The recall and legitimate-mail limits draw from the
[original study gates](../../benchmark-records/tfidf_false_alarm_v12a/summary.md).
The security-notice and spam limits are proposed for the new groups.
The reviewer should confirm or revise these limits before the freeze.
Use any misses to plan work on development data. A model or threshold
change requires a different untouched cohort for confirmation.
