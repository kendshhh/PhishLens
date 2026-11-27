# Release AI quality preregistration

The AI owner approved the evaluation build and thresholds for the release gate in #266. The release decision remains **NO-GO** while the representative cohort is prepared and reviewed.

## Approved evaluation build

Use the bundled offline CPU TF-IDF provider (`AI_MODE=tfidf`) with model `word_plus_char_wb_context_v1` at commit `b6c2f11344fe02cbece4e65906ae71a622e18687`. Build PR #294 is based on #266 at `18fa7c8efbdb6edb8c6c0bafabb30d061861a920`. [Exact build commit](https://github.com/kendshhh/PhishLens/commit/b6c2f11344fe02cbece4e65906ae71a622e18687). [Build PR #294](https://github.com/kendshhh/PhishLens/pull/294). [AI owner build approval](https://github.com/kendshhh/PhishLens/pull/269#issuecomment-7152721051).

The digests below cover the tracked blobs named by the pinned runner.

| File | SHA-256 |
| --- | --- |
| `scripts/evaluate_tfidf_cohort.py` | `4edf21881ddf8b9912292c248babff085b4d6e31d9f048625eba276009f094ee` |
| `backend/ai/service.py` | `2c89c17f9bba5acc0143d14e42ba8d75a4c86aeacb8e4f2ff9c8b99348729368` |
| `backend/ai/schemas.py` | `2a426d9aa830e7b45ab4a1907df6d48f85d26dbe0611682c0619a45e3c3a7df2` |
| `backend/ai/tfidf_provider.py` | `b89d81cbe011366fb9a887d002fbfcfa92060998f3199fea35a98f3b76feaeca` |
| `backend/ai/context_policy.py` | `2c22c6cbd87febfd738f7311df2237f6e6688ba6e6a333d704feab262e3fb2ce` |
| `docs/devops/release-quality-policy.json` | `82ff53bc97b427d431702dab423108a73688c772b6ba77e17ab8cff03052901d` |
| `backend/ai/evaluation_cases.py` | `adfde7a99f47b391413be11b9011b4c7ce188c31ee63c339fdb4c13cb03d8765` |
| `backend/requirements.txt` | `24ffb11378cfbaa051cd9ce21e9951ca0cfcd41d2d5e6437ac7bf5ae37ee35d0` |
| `extension/ai/contract.json` | `8bbb605a2c66b5e8a72ab5d06f47e2b8ad14e31295192596a3d03ded42acddb9` |
| `extension/ai/tfidf_v12a.json` | `adace5ad3cfb281a15b7bc85774ef158126800dc3f78c942f46547dfde33dc27` |
| `extension/ai/local-analyzer.mjs` | `ef554bc95340965ff5959b7d2715cdaf282d75e7b25eeef06af876a1914edae6` |
| `extension/ai/core.mjs` | `73d5b810f0c371cd9ebffaeb879d5e800615c0f5e81cbfd0c8c6cb7f786ce182` |
| `extension/ai/context-policy.mjs` | `f4ba637358a5efccc784ab25f81c147c324ddc3edac7366090d3886082ffa726` |

The frozen input is the visible plain-text selection. The backend accepts at most 30,000 UTF-16 units, masks email local parts, phone-like strings and numbers of six or more digits, collapses whitespace, and keeps the first 2,000 and last 300 Unicode code points when prepared input exceeds 2,300. Run that production preprocessing once. An alert is a raw margin at or above zero. The existing sigmoid maps the margin for display.

At freeze, record the exact source commit, code and artifact digests, runtime dependencies, and approved policy digest. Run preflight from the pinned checkout and match the deployed provider and artifact to the reviewed lock. The historical source-pair sign-off retains its advisory English scope.

### Local build verification

The exact backend and packaged extension agreed on all 207 diagnostic decisions. The representative release cohort remains unscored.

| Diagnostic cohort | Phishing alerted | Legitimate falsely alerted | Valid results |
| --- | ---: | ---: | ---: |
| Controlled regression | 8/8 | 0/12 | 26/26 |
| Archived English source-pair reserve | 60/64 | 0/117 | 181/181 |

The extension ZIP SHA-256 is `0a127b6d28c2ae05ff027262ad1d355bfdb33a0d0c3613e305ab2a5a83db13d1`. The redacted local verification report SHA-256 is `628b4da87575cd0392e12c68b00692c771599fb949d4ca595a53c4cdd634214f`. [Deterministic AI evaluation on the exact commit](https://github.com/kendshhh/PhishLens/actions/runs/45545588713).

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

- Trixia completed initial candidate intake review. Approval of the final source inventory is pending.
- Score-blind review was requested through the restricted channel. Independent labels, any adjudication, and overlap clearance are pending.
- Exact frozen cohort lock SHA-256 and Trixia's approval are pending.
- The first official scoring run remains on hold.

The archived October 29 v12a advisory cohort is not the lock for this proposed cohort: its recorded scope used one phishing-collector family and excluded generic spam. Do not reuse that historical lock for this run.

Share the lock SHA-256 and the redacted aggregate report. Keep raw mail, private source permissions, and reviewer packets in the authorized data store. Include the approved policy and report SHA-256 values in the model decision. The release remains NO-GO until the exact pinned run passes and its evidence is accepted.

## Approved release thresholds

Wilberr (`EnviousCoal`) approved the raw margin alert cutoff of at least 0 and the release policy with SHA-256 `82ff53bc97b427d431702dab423108a73688c772b6ba77e17ab8cff03052901d`. Keep the cutoff fixed. Apply the targets to unrounded metrics on the frozen actual-mail primary set. At the intake minima, at least 90 of 100 phishing families must alert, at most 6 of 200 legitimate families may alert, and all 400 attempts must return valid results. [AI owner threshold approval](https://github.com/kendshhh/PhishLens/pull/269#issuecomment-7152323482). [Pinned policy](https://github.com/kendshhh/PhishLens/blob/b6c2f11344fe02cbece4e65906ae71a622e18687/docs/devops/release-quality-policy.json).

| Metric | Approved threshold | Denominator |
| --- | ---: | --- |
| Phishing recall | ≥90% | All primary phishing families attempted |
| Legitimate false-positive rate | ≤3% | All primary legitimate families attempted |
| Valid result rate | 100% | All primary results attempted |

A missed or unusable phishing result earns no true positive. Every missing, invalid, timed-out or failed result prevents a pass. Report spam and security-notice false alerts, per-source counts, failures and uncertainty separately. Use the [offline runner](https://github.com/kendshhh/PhishLens/blob/b6c2f11344fe02cbece4e65906ae71a622e18687/scripts/evaluate_tfidf_cohort.py) on the reviewed lock and publish the redacted report with counts, denominators, limitations and the candidate, approved policy and cohort hashes.

Record the final owner decision against the final approved policy SHA-256 and the redacted report SHA-256 after independent review. Keep NO-GO if clearance is incomplete or any threshold fails. Preserve failed results, retune on development data, and freeze a fresh holdout for the next candidate. The model-quality decision covers the exact provider and model it tested.
