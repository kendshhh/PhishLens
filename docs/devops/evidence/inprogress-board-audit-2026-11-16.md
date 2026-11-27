# In-progress board audit — 2026-11-16

## Scope and method

Read the GitHub Project **PhishLens — Sprint 3**, view **Sprint 3 — Backlog by person**, and the acceptance criteria for every item shown as **In Progress**. The alternate **Sprint 3 — S3 tasks** view has a `label:sprint-3 -label:carryover` filter and currently shows 14 matching items; because that filter excludes carryover work, it is not the full backlog view. The full backlog-by-person view has 14 In Progress items across four assignees; the five Kendra items visible in the supplied screenshot are only part of that list.

The signed-in board was rechecked while updating the existing audit PR #233. The same 14 target issues remain In Progress; no additional In Progress item appeared in the full view. The current board owner choices and evidence needed to resume each blocked acceptance are in [the owner decision packet](inprogress-owner-decisions-2026-11-16.md).

The initial PR #233 check on 2026-11-16 recorded it as open and draft. On audit head `9293b8b`, backend, extension, staging integration, CodeQL, dependency checks, migration preflight and workflow lint passed. `Secretary staging` returned `action_required` with “Draft: mark ready for review to request staging”; hosted staging and preflight were skipped. This is a historical draft observation. GitHub reported PR #233 open and ready for review (`draft: false`) in its 2026-11-18 status. Hosted staging remains unrequested: the exact protected target, database mapping and owner approval for a hosted write are still unavailable. No live staging acceptance is claimed.

The repository checks below ran from an isolated worktree at main `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c`. The pre-existing workspace's dirty files were left untouched. Live probes were GET-only. No hosted writes, provider calls, failure injection, database mutations, secret reads, or human sign-offs were performed or inferred.

## Full board snapshot

| Issue | Owner | Board item | Current completion boundary |
| --- | --- | --- | --- |
| [#92](https://github.com/kendshhh/PhishLens/issues/92) | EnviousCoal | Run leakage-controlled held-out AI evaluation | The Nov 15 owner sign-off accepts TF-IDF v12a for advisory screening on the frozen English source-pair, with at least 90% phishing recall, at most 3% legitimate-only false positives, and 100% valid output. This scoped approval does not establish broader contemporary-source performance. Rights-cleared contemporary data and its frozen protocol remain open. One offline diagnostic on the corrected synthetic bundle completed on Nov 18 under the recorded owner-authorized exception: it detected 1/12 primary synthetic phishing cases and returned 45/45 valid outputs. Independent final-lock review and contemporary-mail qualification remain open. |
| [#44](https://github.com/kendshhh/PhishLens/issues/44) | inaki3023 | Build the injectable CRUD API client | Local client tests pass. Real connected verification and the remaining board/sprint-log handoff are open; PR #183 records partial staging evidence, including a detail 404. |
| [#45](https://github.com/kendshhh/PhishLens/issues/45) | inaki3023 | Deliver replayable HTTP CRUD acceptance and real client integration | Local substitute tests pass. Current deployed HTTP results and the owner/UI composition acceptance are incomplete. |
| [#7](https://github.com/kendshhh/PhishLens/issues/7) | inaki3023 | Connect extension history to the database-backed API | The safe changed-record display, remaining browser states, and current frontend sign-off are still open. |
| [#23](https://github.com/kendshhh/PhishLens/issues/23) | inaki3023 | Verify deployed history flow from extension to PostgreSQL | Changed-record, complete browser-state, and backend/frontend review evidence remain open. |
| [#87](https://github.com/kendshhh/PhishLens/issues/87) | inaki3023 | Connect saved report creation to detail and history refresh | Local client behavior is covered. Exact-revision connected backend/database/UI behavior and delivery evidence remain open. |
| [#98](https://github.com/kendshhh/PhishLens/issues/98) | inaki3023 | Verify saved-report client flow with local and live checks | Protected staging replay, safe cleanup, live failure paths, and redacted exact-revision evidence remain open. |
| [#93](https://github.com/kendshhh/PhishLens/issues/93) | kendshhh | Gate AI behavior changes with deterministic evaluation | The Nov 15 AI-owner sign-off approves zero missing, failed or skipped required cases and valid, correctly identified results for all 40 development cases, with no paid/external inference or model downloads. The Nov 18 update approves the 113-test inventory and pins the case/model identities; both applicable and not-applicable status paths were observed. Required review, merge and main-branch delivery remain open. |
| [#94](https://github.com/kendshhh/PhishLens/issues/94) | kendshhh | Add guarded real-evaluation and provider-smoke gates | The guarded workflow is separate from ordinary CI. Provider/model approval, an owner-reviewed aggregate quota/cost limit, and a real-provider report are missing; no paid request was made. |
| [#37](https://github.com/kendshhh/PhishLens/issues/37) | kendshhh | Verify isolated environments and extension delivery package | Current package identity and bounded package scan pass. Effective Render key scope and service-to-Neon database mapping are not exposed by the available connector. Existing repository history retains personal-provider email identities under the previously recorded no-rewrite disposition. |
| [#41](https://github.com/kendshhh/PhishLens/issues/41) | kendshhh | Prepare Consultation 2 evidence, sprint logs, and requirements audit | This audit refreshes the board snapshot. Actual standups, retrospective, full-team rehearsal, attendance, and each person's delivered explanation are not recorded and cannot be reconstructed from PRs or CI. |
| [#95](https://github.com/kendshhh/PhishLens/issues/95) | kendshhh | Run controlled AI failure drill and record recovery | Deterministic failure tests and platform rollback evidence exist. No owner-approved AI failure matrix/provider configuration or AI failure/recovery measurements are available; staging currently reports TF-IDF. |
| [#42](https://github.com/kendshhh/PhishLens/issues/42) | xxTrixia | Implement persistent CRUD endpoints and compatible schema | Local CRUD/API tests pass. Connected staging persistence is not verified because the Render-to-Neon branch mapping is unknown. |
| [#96](https://github.com/kendshhh/PhishLens/issues/96) | xxTrixia | Bound provider inference and verify controlled failures | Focused backend failure/API tests pass; the approved staging run and exact revision/reviewer evidence remain open. |

All 14 remain **In Progress**. No item was changed to Done because each issue has an outstanding acceptance boundary above.

## AI-owner decision reconciliation — refreshed 2026-11-20

- **#92:** The Nov 15 sign-off records the model identity, frozen English source-pair result and scoped thresholds; it is not a blanket approval of contemporary-mail performance. The corrected synthetic manifest and lock are available. The earlier Nov 18 preflight reproduced the lock and replayed saved predictions with zero candidate inferences. Later that day, one offline diagnostic completed under the recorded owner-authorized exception to the pending independent final-lock review ([exception](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6983613256), [result](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6983792340)): it detected 1/12 primary synthetic phishing cases (11 missed), with 0/12 legitimate and 0/12 spam alerts, and returned 45/45 valid outputs. This is a synthetic diagnostic, not an actual-mail result or quality acceptance. The single authorized run is complete; no rerun or tuning is claimed. Independent final-lock review, rights-cleared contemporary data with a frozen protocol, and explanation review remain open.
- **#93:** The Nov 15 owner decision is recorded, not missing. The Nov 18 owner update approves the 113 required tests and the 40-case/model pins; it reports the applicable and explicit N/A status paths on PRs [#245](https://github.com/kendshhh/PhishLens/pull/245) and [#246](https://github.com/kendshhh/PhishLens/pull/246). The implementation still needs required review, merge and delivery on `main`; development fixtures have no numeric model-quality threshold.
- **PR #233 status:** The Nov 16 draft observation above is historical. GitHub reported the PR open and ready for review on Nov 18. Hosted staging and preflight were not requested or run, so there is no live staging acceptance claim.

## Verification performed

- `npm test`: 298 passed, 0 failed, 0 skipped.
- `npm run lint`: passed.
- `npm run validate`: passed (manifest and required assets).
- Focused backend CRUD/AI-failure/readiness/version suite: 122 passed, 35 skipped. All skips were PostgreSQL integration cases; no test database was configured.
- Focused evaluation/staging/package guard suite: 70 passed.
- Production extension package built and verified with the project's Python 3.12 environment against source `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c`: 48 files verified. The sidecar is unsigned; this is integrity/source-consistency evidence, not installed-Chrome acceptance.
- Bounded package scan: 0 recognized credential-pattern matches, 0 recognized model-weight files, and 2 email-like matches in `vendor/neon/THIRD_PARTY_NOTICES.txt` (public third-party license attribution). The scan is pattern-based, not a guarantee against every secret format.

The default `npm run package` invocation resolved system Python 3.10.11 and failed at Python 3.11-only `hashlib.file_digest`; rerunning `scripts/package_extension.py` and the verifier with the repository's Python 3.12 environment passed. CI pins Python 3.12.

## Read-only deployment evidence — refreshed 2026-11-16

The earlier successful GET-only responses recorded in this audit are historical observations. Fresh GET-only /version retries to production and staging around 03:11 UTC each timed out after 8 seconds, so neither service returned a runtime identity during the latest check.

At 03:14:58 UTC, Render's deployment API still listed the latest phishlens-staging deployment as live at the [PR #156 revision](https://github.com/kendshhh/PhishLens/pull/156), SHA a448fbba4acad48ac9026658c42a879cd3d2fa4a (deploy dep-dbt6d9m7bikc73d6a7r0; last updated 03:11:31 UTC). This is control-plane evidence, not a successful current /version response.

The staging target is now corroborated at the source/configuration level: Render service metadata names python scripts/start_staging.py as the startup command; the exact deployed [PR #156 staging guard](https://github.com/kendshhh/PhishLens/blob/a448fbba4acad48ac9026658c42a879cd3d2fa4a/scripts/start_staging.py) pins the allowed endpoint to Neon endpoint ep-soft-fog-b3orfa8a; Neon maps that endpoint to branch pr-58-staging. The script checks the runtime and migration URLs against the expected database and roles. This identifies the intended isolated target for that exact revision, but the timed-out runtime check means the effective live connection was not re-proven in this pass. No database values or secret values were read.

Production's Render service runs Uvicorn directly and has no equivalent source-level branch pin. Its Neon branch mapping remains unverified. The Render connector does not expose service-variable inventory or effective external API-key scopes, so those remain unverified for both services. No write was attempted.
## Remaining owner-sourced inputs

- #92 evaluation owner/reviewer: complete independent review of the final synthetic lock and explanation grounding; provide rights-cleared contemporary data, score-blind labels, independent-family and overlap evidence, a frozen protocol, and a revision-linked report for prospective actual-mail qualification. The one authorized synthetic diagnostic run is complete; do not rerun or tune against that consumed bundle.
- #93: the owner policy is recorded. Complete required review, merge and main-branch delivery of the approved deterministic inventory and its exact applicable/not-applicable check paths.
- AI/staging owners: approve a bounded provider/failure matrix and quota/cost limits before live provider smoke or AI failure injection.
- Environment owner: verify production/staging database branch mapping and external API-key scope using an approved read-only method; do not infer either from readiness.
- Frontend/API owners: complete the matching installed-browser and deployed CRUD/history acceptance, then record current-head review and cleanup evidence.
- Consultation participants: supply actual event records (standups, retro, rehearsal/attendance, delivered explanations). Do not fabricate historical participation.
