# Owner decision packet — Sprint 3 in-progress work

Prepared 2026-11-16 for the existing board audit PR #233. The current **Sprint 3 — Backlog by person** view was rechecked in the signed-in browser: it still has the same 14 target issues In Progress. The filtered **Sprint 3 — S3 tasks** view is not the complete carryover view. This packet proposes choices and records the exact evidence needed to resume; it does not authorize provider calls, staging writes, failure injection, or a status change.

## 1. AI evaluation decisions — #92 and #93

**Owners:** Wilberr (`EnviousCoal`) for #92; Kendra (`kendshhh`) for #93. The named AI-owner approval for #93 is still EnviousCoal; Trixia (`xxTrixia`) is the #92 reviewer.

- **#92 candidate:** the issue currently proposes TF-IDF v12a `word_plus_char_wb_C1p0`, model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`, raw-margin cutoff zero. Confirm this candidate for protocol work, or name the alternative model and exact revision. This is not a provider or release decision.
- **#92 data route:** (A) provide an approved, licensed source and its rights/provenance record; or (B) approve a clearly labeled synthetic holdout with an explicit nonrepresentative limitation. For either route, Wilberr/Trixia must supply score-blind adjudicated labels, labeling rules, class/family counts, duplicate and known-overlap report, frozen split/revision and lock hash, plus final criteria before any scoring. Do not use private inbox content or tune against holdout results.
- **#92 metrics proposal:** the issue describes 90% recall and at most 3% legitimate-only false positives for primary actual mail, with valid-result and minimum-coverage requirements; security-notice and spam rates are diagnostic. Confirm or replace these proposed criteria before the holdout is frozen. No result exists yet.
- **#93 gate:** EnviousCoal should approve the current pinned development baseline and zero-tolerance behavior for missing/failed/skipped required cases, or supply a replacement baseline and blocking threshold in a reviewed change. Keep held-out quality thresholds separate from development regression thresholds.

**Next step after decisions:** freeze the reviewed data/protocol artifacts, run the exact named candidate once, publish revision-linked class-wise metrics, failures, latency/limits, limitations and owner review. Until then #92 and #93 remain In Progress.

## 2. Provider smoke and failure drill — #94, #95, #96

**Owners:** Kendra for #94/#95; Trixia (`xxTrixia`) for #96. EnviousCoal is the named reviewer for these AI gates.

Choose one path:

1. **Defer live provider work.** Keep all runs deterministic/local and keep the live acceptance criteria open; or
2. **Authorize a bounded staging run.** Record the approved provider and exact model revision, exact staging service and deployed SHA, confirmed nonproduction Neon branch, fixed synthetic input, maximum request count (the #94 smoke permits at most one), maximum spend in USD, timeout, retry policy (zero automatic retries), quota stop rule, failure cases, rollback/stop owner, and approving owner. No value is assumed in this packet.

For #95/#96, the proposed failure matrix is unavailable configuration/provider, timeout, quota/rate limit, malformed or unsupported output, and database-save failure. Mark each scenario as deterministic simulation or approved live injection. Define what counts as detection/recovery before measuring it. Existing deterministic tests and staging rollback timing are not AI failure/recovery measurements.

**Next step after approval:** verify the exact target with a current `/version` check and redacted service-to-Neon branch evidence; run only the approved scope; publish request count, source/model/deployment identities, outcomes and measured timings without payloads or secrets. Stop if identity, quota, timeout or spend controls fail. Until the owner packet and exact target are recorded, #94/#95/#96 remain In Progress.

## 3. Environment and connected CRUD evidence — #37, #42, #44, #45, #7, #23, #87, #98

**Owners:** Kendra for #37; Trixia for #42; Leyan (`inaki3023`) for #44/#45/#7/#23/#87/#98. Reviewers are the ones named on the respective issues.

The last read-only probe recorded production on main `6544364` with its provider unavailable, and staging on open PR #156 SHA `a448fbb` in TF-IDF mode. Readiness alone does not identify the Neon branch. The required owner-supplied environment record is a redacted attestation of each Render service → Neon branch mapping and external API-key scope; include identifiers and scope names, never secret values. The environment owner must confirm staging is isolated and disposable writes are authorized before any synthetic record is created.

After that record and exact deployed candidate are verified, the frontend/API owners can run the scoped synthetic connected acceptance: create once → use returned ID → detail/history reread → edit and reread → delete and confirm absent → reopen/refresh. Record redacted HTTP statuses, source/client/backend/package SHA, browser/version, cleanup and failure-state results. Include #7/#23 changed-record and loading/empty/request-failure/malformed-response checks; #44/#45 real client/API and UI composition plus sprint-log handoff; #87/#98 saved-report behavior, no blind retries, and controlled error handling; #42 persistence and schema behavior. Do not use production or existing seeded/user records.

For #37, the package, manifest and local checks pass, but effective service/key scope and the existing history finding have not been resolved. The issue criterion about private emails in repository history cannot be certified under the recorded **no-rewrite** disposition. Kendra and reviewer inaki3023 must either provide a non-history-rewriting remediation that satisfies the criterion or record an explicit accepted exception/change to that criterion; do not rewrite refs or disclose the identities.

## 4. Actual process records — #41

**Owner:** Kendra; reviewer: inaki3023.

Supply the actual dates and records for two or three async standups (done/next/blocked), a written retrospective (went well/did not/one next change), and the whole-team 15-minute rehearsal (actual participants/attendance and each participant's own technical explanation). Also provide real slip reasons, owners and replans where applicable. If those activities have not happened, hold them with the actual team and write contemporaneous records; do not backdate or infer them from PRs/CI. The board/status/evidence audit is current, but cannot substitute for these events. #41 stays In Progress until the actual records and handoff are attached.

## Reply fields to unblock the next pass

Provide decisions or records in this shape; “defer” is a valid answer and leaves the relevant issue open:

- AI owner / decision for #92 and #93: candidate/revision; licensed or synthetic data route; approved final criteria; reviewed development baseline/threshold.
- Provider and staging owner / decision for #94–#96: provider/model revision; spend cap; request cap; timeout/retry/quota controls; failure matrix; exact staging service/SHA and Neon branch; approval for the bounded actions.
- Environment evidence for #37 and connected CRUD tasks: redacted Render-service-to-Neon-branch mapping, API-key scope names, staging isolation and synthetic-write authorization.
- Consultation records for #41: actual dated standups, retro, rehearsal attendance and delivered explanations, or confirmation that the events still need to be held.
- #37 history criterion: non-rewrite remediation or explicit owner-approved criterion exception consistent with the existing no-rewrite disposition.
