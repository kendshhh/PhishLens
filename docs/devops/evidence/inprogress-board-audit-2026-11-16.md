# In-progress board audit — 2026-11-16

## Scope and method

Read the GitHub Project **PhishLens — Sprint 3**, view **Sprint 3 — Backlog by person**, and the acceptance criteria for every item shown as **In Progress**. The alternate **Sprint 3 — S3 tasks** view currently has a `label:sprint-3 -label:carryover` filter with zero matching items. The full backlog-by-person view has 14 In Progress items across four assignees; the five Kendra items visible in the supplied screenshot are only part of that list.

The repository checks below ran from an isolated worktree at main `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c`. The pre-existing workspace's dirty files were left untouched. Live probes were GET-only. No hosted writes, provider calls, failure injection, database mutations, secret reads, or human sign-offs were performed or inferred.

## Full board snapshot

| Issue | Owner | Board item | Current completion boundary |
| --- | --- | --- | --- |
| [#92](https://github.com/kendshhh/PhishLens/issues/92) | EnviousCoal | Run leakage-controlled held-out AI evaluation | No approved data provenance/license, frozen held-out cohort, or model/revision decision is recorded. No holdout was accessed or evaluated. |
| [#44](https://github.com/kendshhh/PhishLens/issues/44) | inaki3023 | Build the injectable CRUD API client | Local client tests pass. Real connected verification and the remaining board/sprint-log handoff are open; PR #183 records partial staging evidence, including a detail 404. |
| [#45](https://github.com/kendshhh/PhishLens/issues/45) | inaki3023 | Deliver replayable HTTP CRUD acceptance and real client integration | Local substitute tests pass. Current deployed HTTP results and the owner/UI composition acceptance are incomplete. |
| [#7](https://github.com/kendshhh/PhishLens/issues/7) | inaki3023 | Connect extension history to the database-backed API | The safe changed-record display, remaining browser states, and current frontend sign-off are still open. |
| [#23](https://github.com/kendshhh/PhishLens/issues/23) | inaki3023 | Verify deployed history flow from extension to PostgreSQL | Changed-record, complete browser-state, and backend/frontend review evidence remain open. |
| [#87](https://github.com/kendshhh/PhishLens/issues/87) | inaki3023 | Connect saved report creation to detail and history refresh | Local client behavior is covered. Exact-revision connected backend/database/UI behavior and delivery evidence remain open. |
| [#98](https://github.com/kendshhh/PhishLens/issues/98) | inaki3023 | Verify saved-report client flow with local and live checks | Protected staging replay, safe cleanup, live failure paths, and redacted exact-revision evidence remain open. |
| [#93](https://github.com/kendshhh/PhishLens/issues/93) | kendshhh | Gate AI behavior changes with deterministic evaluation | The active deterministic gate and tests are present. The AI owner's approval of the blocking baseline/threshold is missing; no threshold was invented. |
| [#94](https://github.com/kendshhh/PhishLens/issues/94) | kendshhh | Add guarded real-evaluation and provider-smoke gates | The guarded workflow is separate from ordinary CI. Provider/model approval, an owner-reviewed aggregate quota/cost limit, and a real-provider report are missing; no paid request was made. |
| [#37](https://github.com/kendshhh/PhishLens/issues/37) | kendshhh | Verify isolated environments and extension delivery package | Current package identity and bounded package scan pass. Effective Render key scope and service-to-Neon database mapping are not exposed by the available connector. Existing repository history retains personal-provider email identities under the previously recorded no-rewrite disposition. |
| [#41](https://github.com/kendshhh/PhishLens/issues/41) | kendshhh | Prepare Consultation 2 evidence, sprint logs, and requirements audit | This audit refreshes the board snapshot. Actual standups, retrospective, full-team rehearsal, attendance, and each person's delivered explanation are not recorded and cannot be reconstructed from PRs or CI. |
| [#95](https://github.com/kendshhh/PhishLens/issues/95) | kendshhh | Run controlled AI failure drill and record recovery | Deterministic failure tests and platform rollback evidence exist. No owner-approved AI failure matrix/provider configuration or AI failure/recovery measurements are available; staging currently reports TF-IDF. |
| [#42](https://github.com/kendshhh/PhishLens/issues/42) | xxTrixia | Implement persistent CRUD endpoints and compatible schema | Local CRUD/API tests pass. Connected staging persistence is not verified because the Render-to-Neon branch mapping is unknown. |
| [#96](https://github.com/kendshhh/PhishLens/issues/96) | xxTrixia | Bound provider inference and verify controlled failures | Focused backend failure/API tests pass; the approved staging run and exact revision/reviewer evidence remain open. |

All 14 remain **In Progress**. No item was changed to Done because each issue has an outstanding acceptance boundary above.

## Verification performed

- `npm test`: 298 passed, 0 failed, 0 skipped.
- `npm run lint`: passed.
- `npm run validate`: passed (manifest and required assets).
- Focused backend CRUD/AI-failure/readiness/version suite: 122 passed, 35 skipped. All skips were PostgreSQL integration cases; no test database was configured.
- Focused evaluation/staging/package guard suite: 70 passed.
- Production extension package built and verified with the project's Python 3.12 environment against source `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c`: 48 files verified. The sidecar is unsigned; this is integrity/source-consistency evidence, not installed-Chrome acceptance.
- Bounded package scan: 0 recognized credential-pattern matches, 0 recognized model-weight files, and 2 email-like matches in `vendor/neon/THIRD_PARTY_NOTICES.txt` (public third-party license attribution). The scan is pattern-based, not a guarantee against every secret format.

The default `npm run package` invocation resolved system Python 3.10.11 and failed at Python 3.11-only `hashlib.file_digest`; rerunning `scripts/package_extension.py` and the verifier with the repository's Python 3.12 environment passed. CI pins Python 3.12.

## Current read-only deployment identity

| Service | `/version` | `/health` | `/ready` | `/model-info` |
| --- | --- | --- | --- | --- |
| Production | `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c` (`production`) | 200 | 200, database connected | 200, provider unavailable |
| Staging | `a448fbba4acad48ac9026658c42a879cd3d2fa4a` (`staging`) | 200 | 200, database connected | 200, TF-IDF |

Render service metadata lists both `phishlens-api` and `phishlens-staging` as configured from branch `main`. The live staging SHA is the open PR #156 head, not current main. Neon lists `production` as the primary/default branch and `pr-58-staging` as a separate branch. Readiness confirms connectivity only; it does not identify the branch or database behind `DATABASE_URL`. The Render connector does not expose a service-variable inventory, so this audit cannot verify effective URL mapping or external Render API-key scopes. No write was attempted.

## Remaining owner-sourced inputs

- AI evaluation owner: approve evaluation data provenance/rights, the held-out split, model revision, and any deterministic blocking threshold before evaluating or enforcing it.
- AI/staging owners: approve a bounded provider/failure matrix and quota/cost limits before live provider smoke or AI failure injection.
- Environment owner: verify production/staging database branch mapping and external API-key scope using an approved read-only method; do not infer either from readiness.
- Frontend/API owners: complete the matching installed-browser and deployed CRUD/history acceptance, then record current-head review and cleanup evidence.
- Consultation participants: supply actual event records (standups, retro, rehearsal/attendance, delivered explanations). Do not fabricate historical participation.
