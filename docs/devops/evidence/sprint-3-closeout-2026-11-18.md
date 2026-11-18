# Sprint 3 closeout evidence — November 18, 2026

Prepared as EnviousCoal from main
`41951749768f1e5d718b19c087e41c2ec6418923` in an isolated worktree, with the
deterministic regression guard added in this change. The existing working copy
was left untouched. The signed-in browser confirmed EnviousCoal and the
[Sprint 3 backlog](https://github.com/users/kendshhh/projects/5): the same 14
issues remain In Progress. No issue or project item was marked Done from these
local results. [Single consolidated owner handoff: #243](https://github.com/kendshhh/PhishLens/issues/243).

## Environment and observed results

Windows 11, build 26300; Python 3.12.10; FastAPI 0.162.0; Pydantic 2.14.1;
Psycopg 3.3.9; SQLAlchemy 2.1.8; Alembic 1.20.1; pytest 9.2.0;
PostgreSQL 17.12; Node 24.13.0. Dependencies came from the checked-in development
locks. Browser checks used Microsoft Edge 157.0.4341.60 with a disposable profile.

| Check | Expected | Observed and boundary |
| --- | --- | --- |
| Selected AI contracts and guard tests | Every required test passes | 113 passed, 36 subtests passed; zero skipped required tests. Includes 11 HTTP-substitute controller tests. |
| Development benchmark plus new baseline guard | 40 cases; exact case/model hashes; zero errors and external provider calls | Passed. Development recall remains 3/16 phishing, with 1/16 legitimate false alerts; this is not a quality acceptance. |
| Backend and Python script suite on fresh local PostgreSQL | All ordinary/database cases pass with fixture cleanup | 588 passed, 2 skipped, 157 subtests passed. The two separate opt-in entry points (Auth cleanup SQL and seed integrity) then passed in their own run against the local seeded database. All 590 distinct tests ran across the two database setups. Two Alembic configuration deprecation warnings occurred. |
| Migration upgrade, repeated | Head `0004_neon_auth_subject`; second upgrade makes no change | Both heads matched; second upgrade proposed/executed no revision. |
| Seeder, repeated in a separate local `phishlens_dev` | One unlinked demo user and one analysis, subject `Synthetic account notice` | Passed twice. Counts, ownership and full-row fingerprint were identical. The test database had zero users/analyses after fixture cleanup; separate cleanup/seed checks preserved the one-user/one-analysis seed database. The local PostgreSQL server was stopped. |
| Extension tests | No failures or skips | 300 passed, zero failed/skipped. |
| Extension lint, manifest and package | Valid assets/package | Passed. No installed staging/Auth acceptance is inferred. |
| Existing packaged-browser suite | 18 browser scenarios | All 18 passed using a loopback synthetic server and test-only session. Covers CRUD/reopen, keyboard/focus, retained input and error states; substitutes do not establish hosted behavior. |
| Frozen historical evaluation replay | Exact model/cohort, six roles and saved predictions reconcile | All six data roles and 3,600 archived prediction rows reconciled. All 1,200 TF-IDF decisions reproduced; maximum raw-margin delta `9.769962616701378e-15`. Counts: 190 TP, 10 FN, 1 FP, 999 TN. This replays an already-consumed holdout. |
| Corrected #92 preflight | Exact existing lock; zero candidate inferences | Reproduced lock `7a5d7280efca7849a8e9b34f498b4e073d7ce5773f6c613ea0d15487286a9b51` in the historical Python 3.12.10/Pydantic 2.13.4 runtime. The newer Pydantic 2.14.1 produced a different environment pin and was rejected for this replay. First scoring still awaits Trixia's corrected-lock approval. |

The historical diagnostic lock records Pydantic 2.13.4 even though its source
requirements pin is 2.14.1. Reproducing the lock required installing its recorded
version in a separate environment. This is a disclosed historical diagnostic
environment, not a claim of current-release dependency acceptance. The reviewed
lock and bundle were not modified. No contemporary candidate was scored.

The first local PostgreSQL harness attempt started the disposable server but
timed out collecting its startup output. It reached no migration or test phase.
That server was stopped, output handling was corrected, and a fresh cluster
completed the run above. No hosted app/database was used in either attempt.

## Reproduction

The selected contract paths and exact JUnit identities are in
`scripts/ai-regression-baseline.json`. The workflow records their commands and
retains its JUnit and development benchmark artifacts. Additional commands used:

```text
uv pip sync --python .review-env/Scripts/python.exe backend/requirements-dev.txt
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini upgrade head
python -m pytest backend/tests scripts/tests -q -p no:cacheprovider --junitxml=<local-report>
python scripts/seed_demo.py
python scripts/seed_demo.py
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run lint
python scripts/validate_extension.py
python scripts/package_extension.py
node scripts/browser_acceptance.mjs
python scripts/verify_tfidf_evaluation.py --prepared-dir <private-frozen-roles> --predictions-dir <private-archived-predictions> --replay-tfidf
python -m ruff check scripts/verify_ai_regression.py scripts/tests/test_ai_regression_gate.py scripts/ai_evaluation_summary.py
git diff --check
```

Database tests used a new SCRAM-authenticated, loopback-only PostgreSQL cluster
and `RUN_DATABASE_TESTS=1`, `AI_MODE=mock`, `REPORT_AUTH_MODE=demo`.
The seeded database was separate from `phishlens_s2_t1_test`. Connection values,
raw mail and per-message historical predictions are intentionally absent.

## Reconciled acceptance and next actions

| Cards | Evidence resolved tonight | Remaining acceptance |
| --- | --- | --- |
| #92 | Existing source-pair approval confirmed; historical replay passed; exact corrected preflight lock reproduced | Trixia's approval of the corrected lock and first synthetic diagnostic run; contemporary actual-mail rights/coverage and explanation review remain open. The small synthetic cohort cannot satisfy the actual-mail minima. |
| #93 | Existing AI-owner approval located; explicit test/case/model baseline and fail-closed artifact guard implemented and tested | Review/merge this guard with #220's required-status fix; verify applicable and unrelated-change outcomes before Done. |
| #94 | Guarded controller now supports one revision-bound TF-IDF request with the pinned model, zero external-provider cost, no retries and no saved-report write. Eleven substitute tests cover both TF-IDF guards and retained Gemini cost controls. | Review/merge the controller; confirm the existing target/preflight/idle-window conditions and record a specifically approved exact-target smoke. No workflow was enabled or dispatched and no paid call was authorized or made here. |
| #95, #96 | Exact #107 rereview approved; local persistence and controlled failures passed; migration/seeder evidence added | Protected-staging failure/recovery evidence and operator stop/recovery verification remain open under the existing authorization limits. Do not convert local timing to hosted recovery/RTO. |
| #37 | Current package/manifest/local verification refreshed | Effective production/staging database and key scope attestations; preserve the history/no-rewrite exception as an unresolved acceptance item. |
| #42 | Local PostgreSQL CRUD/atomicity/rollback tests now run instead of being skipped | One authorized selected-deployment full CRUD/PATCH/reread run, identities, cleanup and delivery evidence. |
| #44, #45, #7, #23, #87, #98 | Current client and 18 packaged-browser scenarios pass locally | One matching authorized backend/Auth/package/browser journey, changed-record/restoration as applicable, controlled failures, cleanup and required owner review. Reuse one bounded run; map each criterion separately. |
| #41 | Actual current source/checks/slips and one consolidated handoff are recorded | Actual standups/retrospective and consultation/attendance/explanations from participants; no historical event was invented. |

The November 16 #233 audit's claim that the #92/#93 AI approvals were absent is
superseded by the actual [#92 owner decision](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6891137984)
and [#93 owner sign-off](https://github.com/kendshhh/PhishLens/issues/93#issuecomment-6891138424).
PR #233 is currently ready for review, not draft. Its recorded historical draft
observations retain their dates. It still needs those corrections before approval.

The newer [#235 rollout record](https://github.com/kendshhh/PhishLens/pull/235)
reports rotated-credential/connectivity work and a later staging revision; it
narrows the older environment blocker. That report still leaves candidate
deployment/Auth configuration, exact runtime pairing and hosted acceptance on
hold. Its broader results belong to earlier source `7444d1469de062f1b7c16b8ad53e1dae35f819cd`,
not automatically to current candidate `af2895e93ce931699386adf823f6768cd5f23913`.

New [PR #244](https://github.com/kendshhh/PhishLens/pull/244) proposes a separate
web frontend while retaining the extension. Its own record leaves sign-in and
saved reports disabled and hosted CORS/Auth setup pending. Its local web results
do not satisfy the existing connected Chrome/API cards or establish a deployed
web acceptance. No frontend target or acceptance scope was changed in this
closeout.

## Slip, ownership and next-sprint risk

The shared-environment acceptance slipped because the effective target/Auth and
package pairing, an idle window and operator-confirmed prerequisites have not all
been recorded for the current candidate. Kendra owns the Render/Neon attestation
and operations; Leyan/Andrei own the connected package/browser record; Trixia owns
backend acceptance and independent cohort review; EnviousCoal owns the evaluation
and regression policy. #243 requests one consolidated response instead of separate
repeated review requests.

The next-sprint risk is treating a local/older green run as current deployment
acceptance. Mitigate it with a single exact-source acceptance record, explicit
expected/actual results, cleanup, and a per-card mapping before changing status.
Sprint 3 remains incomplete until its open acceptance gates have evidence. No
staging/production HTTP request, provider spend, deployment, Auth/account change,
hosted write or invented participant sign-off was performed in this closeout.
