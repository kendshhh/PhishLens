# Release AI quality preregistration

Proposal for the release gate in #266 and the model acceptance in #147 and #153. The quality policy remains pending review. The release decision is NO-GO.

## Candidate

Propose the bundled CPU TF-IDF v12a provider (`AI_MODE=tfidf`), model `word_plus_char_wb_C1p0`. The following bytes were verified against the Git blobs at `f9061f4d81f0f9261e4bdf5273fe6506264b725e`.

| File | SHA-256 |
| --- | --- |
| `extension/ai/tfidf_v12a.json` | `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` |
| `extension/ai/contract.json` | `c1b0df6d0eb3aaf94794dc549fe1240cd77be9fdc7101db333d346c8bdba6947` |
| `backend/ai/tfidf_provider.py` | `6a7853ca0b88f31227c7f73abaf276ce00c0b245f387d3eed4a50a43bb0587bd` |
| `backend/ai/service.py` | `2c89c17f9bba5acc0143d14e42ba8d75a4c86aeacb8e4f2ff9c8b99348729368` |
| `scripts/evaluate_tfidf_cohort.py` | `2b64309ae5d06f63ebcba2b981f344550bf90140d5b71e42dcc0eedc46ab5cca` |
| `docs/devops/release-quality-policy.json` (pending snapshot) | `12a40c84868ca1cde0bc54380f21e10cc03d7d829360d92c5cdf16ca040e5c12` |

The frozen input is the visible plain-text selection. The backend accepts at most 30,000 UTF-16 units, masks email local parts, phone-like strings and numbers of six or more digits, collapses whitespace, and keeps the first 2,000 and last 300 Unicode code points when prepared input exceeds 2,300. Run that production preprocessing once. An alert is a raw margin at or above zero. The existing sigmoid maps the margin for display.

At freeze, record the final reviewed source SHA, code and artifact digests, runtime dependencies, and approved policy digest. Qualify the backend provider against that lock and match the eventual deployment to the provider and artifact. The historical source-pair sign-off retains its advisory English scope.

## Intake and blind review

Propose a recent, authentic English held-out cohort. The sources below are intake candidates only; none is admitted or cleared by this proposal. For every candidate, verify written permission for this evaluation, exact source revision, absolute delivery dates, original collection provenance, permitted reuse, scoreable text, and independent family counts before admission. Keep the names of the two custodians and their exports restricted in the private source register.

### Intake-candidate source-by-label matrix

| Intake candidate | Phishing | Legitimate | Spam | Security notices within legitimate | Intake status |
| --- | --- | --- | --- | --- | --- |
| Arizona / Cornell phishing candidates | Screen | — | — | — | Candidate only; exact datasets, revisions, rights, provenance, and counts pending |
| Bruce Guenter / cw-l spam candidates | — | — | Screen | — | Candidate only; exact datasets, revisions, rights, provenance, and counts pending |
| Arizona UAnnounce | — | Screen | — | Screen only if the original message is a genuine account-security notice | Candidate only; rights, revisions, delivery dates, provenance, and counts pending |
| Cornell Verified Communications | — | Screen | — | Screen only if the original message is a genuine account-security notice | Candidate only; rights, revisions, delivery dates, provenance, and counts pending |
| USNH verified legitimate mail | — | Screen | — | Screen if genuine account-security notices are present | Candidate only; rights, revisions, delivery dates, provenance, and counts pending |
| Custodian export A (identity restricted) | — | Screen | — | Eligible only if verified as a genuine notice | Written permission and all inventory fields pending |
| Custodian export B (identity restricted) | — | Screen | — | Eligible only if verified as a genuine notice | Written permission and all inventory fields pending |
| Nitrosend security index / screened gallery | — | Screen as a notice lead | — | Screen | Wilberr reports 55 real notices sent in 2025–2026; rights, original collection provenance, absolute dates, scoreable text, and unique families unverified |
| Sequenzy sign-in and account-change index | — | Screen as a notice lead | — | Screen | Candidate only; rights, original collection provenance, absolute dates, scoreable text, and unique families pending |

Collapse shared issuer templates, reminders, and duplicates across all sources before counting independent families. The account-security target is at least 50 independent families within the legitimate set; the reported Nitrosend count is an intake lead, not an admitted count.

### Proposed primary cohort minima

| Label | Minimum eligible primary families |
| --- | ---: |
| Phishing | 100 |
| Legitimate | 200 |
| Spam | 100 |
| Genuine account-security notices | 50, included within the 200 legitimate families |

Require at least two independent sources for every label and at least 400 attempted primary results. Source-level allocations and actual admitted counts remain pending until permissions, independent labels, and overlap review are complete.

Freeze one primary message selection per independent family. Require at least 100 phishing, 200 legitimate, and 100 spam families, at least two independent sources for every label, and at least 50 genuine security-notice families among the legitimate cases. Primary screening uses self-contained selected text. Keep context-dependent and stress cases as separate diagnostics. Count at least 400 attempted primary results.

Have two authorized reviewers label the selected text independently and without access to model scores or each other's labels. Resolve disagreements with an authorized adjudicator and keep unresolved cases outside the admitted set. Check raw and prepared duplicates and campaign-family overlap within the cohort and against training, calibration, threshold selection, development fixtures, and consumed holdouts. Record the checking method, affected family counts, and known limits. Have the manifest, rights register, adjudication and overlap report reviewed before locking the cohort.

Follow the [existing cohort protocol](tfidf-sprint-3-evaluation-protocol.md) and its zero-inference preflight. Keep message text, recipient identifiers, source credentials, and individual reviewer packets in the authorized private data store.

### Reviewer assignments and pre-scoring approval

| Role | Reviewer |
| --- | --- |
| Blind label reviewer 1 | Trixia (`xxTrixia`) |
| Blind label reviewer 2 | Wilberr (`EnviousCoal`) |
| Source inventory and cohort lock approver | Trixia (`xxTrixia`) |
| Evaluation and AI decision owner | Wilberr (`EnviousCoal`) |

Trixia (`xxTrixia`) reviews source permissions and the frozen cohort before scoring, and approves the private source inventory and exact final cohort lock SHA-256. Trixia and Wilberr (`EnviousCoal`) label independently without access to model scores or each other's labels; record both names in the private review record. Scoring requires Trixia's source-inventory and lock approval, confirmed written permissions, resolved labels, cleared overlap review, and a lock that matches the reviewed candidate and policy.

### Current pre-scoring review record

- Private source inventory revision/digest: not supplied for Trixia's review.
- Trixia (`xxTrixia`) approval of the inventory: pending.
- Exact frozen cohort lock SHA-256: not supplied for Trixia's review.
- Trixia (`xxTrixia`) approval of the lock: pending.
- First scoring run: blocked.

The archived October 29 v12a advisory cohort is not the lock for this proposed cohort: its recorded scope used one phishing-collector family and excluded generic spam. Do not reuse that historical lock for this run.

Share the lock SHA-256 and the redacted aggregate report. Keep raw mail, private source permissions, and reviewer packets in the authorized data store. Include the approved policy and report SHA-256 values in the model decision. The release remains NO-GO until the exact pinned run passes and its evidence is accepted.

## Proposed release thresholds

**Proposed decision for owner review:** retain the existing inference cutoff (alert when the raw TF-IDF margin is at least 0) and retain the release targets of at least 90% phishing recall, at most 3% legitimate false-positive rate, and 100% valid primary results. Do not tune the cutoff on the frozen cohort. These are proposed policy thresholds, not an approved decision; Wilberr (`EnviousCoal`) must approve or revise them before scoring. Apply the targets to unrounded metrics on the frozen actual-mail primary set. At the intake minima, at least 90 of 100 phishing families must alert, no more than 6 of 200 legitimate families may alert (including the 50 security-notice families), and all 400 attempts must return valid results.

| Metric | Proposed threshold | Denominator |
| --- | ---: | --- |
| Phishing recall | ≥90% | All primary phishing families attempted |
| Legitimate false-positive rate | ≤3% | All primary legitimate families attempted |
| Valid result rate | 100% | All primary results attempted |

A missed or unusable phishing result earns no true positive. Every missing, invalid, timed-out or failed result prevents a pass. Report spam and security-notice false alerts, per-source counts, failures and uncertainty separately. Use the [offline runner](../../scripts/evaluate_tfidf_cohort.py) on the reviewed lock and publish the redacted report with counts, denominators, limitations and the candidate, approved policy and cohort hashes.

Record the owner decision against the final approved policy SHA-256 and the redacted report SHA-256 after independent review. Keep NO-GO if clearance is incomplete or any threshold fails. Preserve failed results, retune on development data, and freeze a fresh holdout for the next candidate. The model-quality decision covers the exact provider and model it tested.
