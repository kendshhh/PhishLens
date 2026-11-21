# Reusable prompt: PhishLens DevOps evidence closeout

Copy the prompt below when assigning an agent to finish the remaining staging,
release-readiness and documentation work.

---

You are the DevOps release engineer for the PhishLens repository. Close the
staging Neon Auth smoke failure and reconcile the DevOps evidence and Markdown
records before proposing a push or merge. Work in the existing repository and
preserve every pre-existing user modification, untracked artifact, historical
record and secret boundary.

## Desired outcome

Produce a reviewed, reproducible, exact-candidate staging path in which:

1. An anonymous request to protected saved-report history is treated correctly:
   `401` is accepted only with a valid `WWW-Authenticate: Bearer` challenge;
   a `200` legacy/demo mode continues to validate seeded history through the
   actual extension client.
2. Authenticated staging acceptance uses Neon Auth's supported sign-in/session
   flow and a dedicated synthetic test identity. The test authenticates every
   saved-report request and proves create/list/read/update/delete, reload
   persistence, ownership isolation, failure handling and cleanup.
3. No test bypasses Auth, weakens production/staging authorization, writes to
   production, leaks tokens or personal data, or reports an anonymous preflight
   as authenticated acceptance.
4. The hosted GitHub workflow runs the tested code from the correct trusted and
   exact-head revisions, verifies the requested/deployed SHA and migration,
   retains redacted artifacts, and fails closed when an expected check is
   missing, stale, skipped or has the wrong identity. Hosted deployment
   requires explicit success from local staging, hosted preflight and backend
   at both job and deployment-step level; no `always()` can bypass those gates.
5. Local staging startup is watched during health/readiness polling; an exited
   process fails promptly and its log is uploaded on failure. Smoke retries
   have a deliberate overall deadline and attempt cap. Permanent HTTP and
   data-contract errors are non-retryable. The final stage, endpoint, status and
   sanitized error appear in the job summary.
6. DevOps evidence and records agree with current repository/workflow/Render/
   Neon evidence. Old dated observations remain historical; no result, owner
   approval, workflow pass, control-plane setting, metric, meeting or acceptance
   is fabricated or silently upgraded.
7. Every release gate is either fully passed with linked, identity-bound
   evidence or remains explicitly open with a concrete next action and owner.
   Report `100%` only if every approved criterion passes under weights/scoring
   approved by the team/instructor. If weights are unapproved, report no
   percentage and explain the evidence gaps.

## Starting facts to re-verify

Treat these as audit leads, not as permanent truth. Recheck them read-only
before relying on them and add the actual observation date and source:

- User's supplied job log failed at `extension/js/api.js:111` with `Failed to
  load history`; it included staging URL and migration revision
  `0004_neon_auth_subject`, but no run ID or tested SHA.
- The Nov 21 staging observation was a live Render deployment with TF-IDF,
  healthy/readiness endpoints, migration head `0004_neon_auth_subject`, and
  anonymous `GET /api/analyses` returning `401 Bearer`.
- The supplied source commit `3c858f7df51666e0545dea1a6dd5997574c16d43`
  already adds detailed extension API errors and retries transient history
  failures. The review branch `codex/devops-staging-closeout-20261121` extends
  that base with a 120-second overall smoke deadline, a 30-attempt cap,
  transient-only retries, a strict anonymous `401 Bearer` check and endpoint/
  status/error summaries. Permanent HTTP statuses are classified before
  transient-looking response text, with focused Node regression coverage.
  Verify actual remote branch state before relying on these facts.
- The then-current `.github/workflows/ci.yml` checked out trusted default-branch
  code for the legacy smoke, then ran a separate exact-PR-head
  `scripts/verify_crud.mjs --allow-writes` path without an authenticated
  session. Verify current workflow code before acting.
- The linked hosted-staging condition used `always()` while also expressing
  success checks for staging, hosted preflight and backend. The review branch
  removes `always()`, retains all explicit result checks, and applies the same
  successes to the Render deployment step. Describe this as defense in depth;
  the linked snapshot already had explicit dependency-success predicates.
- Production was observed with analysis disabled. A disabled observer result is
  not product/AI acceptance. Production smoke is manual and must not make paid
  calls or saved-report writes.
- Render metadata showed auto-deploy off even though a production deploy record
  showed `new_commit`; reconcile the settings and event source with the owner.
- The original developer checkout contained pre-existing user changes and was
  preserved. The review work used an isolated worktree and synchronized latest
  main code through merge commit `14874d339bbb4042172df954f97596080aa303ee`.
  PR #265's docs at `ca29235` subsequently merged into main at `95975cd`. The
  review branch remains based on the merged #265 branch. Inspect the actual tree,
  do not reset, clean, stash, rebase, merge or push over
  unreviewed user work.

### Verified follow-up evidence — November 21, 2026

Recheck all live systems before reuse. At the `631b0ef` audit snapshot, PR #268
branch `codex/devops-staging-closeout-20261121` had code/test commit
`83a0df1af1d64048b3b5fa3158f6509e83d71555` and tested PR head
`631b0ef21849e8abe877bb16b4676047f2aca86a`:

- `npm test` passed 321 tests; the GET-only staging smoke passed health,
  readiness and the anonymous `401 Bearer` boundary. It did not perform writes,
  sign in, or verify authenticated history/CRUD.
- CI run [44888140094](https://github.com/kendshhh/PhishLens/actions/runs/44888140094)
  passed backend, extension, migration preflight and local staging integration.
  Workflow lint, dependency security and deterministic evaluation passed at
  44888140104, 44888140135 and 44888140114 respectively.
- Hosted staging and preflight were skipped. The required `Secretary staging`
  PR check is failed because `needs-hosted-staging` and exact-head hosted
  verification are absent ([check run
  44888369939](https://github.com/kendshhh/PhishLens/actions/runs/44888369939));
  its controller assessment passed but the preview job was skipped. No Render
  deployment or hosted CRUD/write occurred.
- At that snapshot, PR #268 remained open and marked `CHANGES_REQUESTED`. The
  review requested retry classification before transient-text matching and
  identified PR-description placeholders. The retry regression is present at
  code/test commit `83a0df1`; later branch-head checks and the documentation
  reconciliation are recorded in the staging evidence file. A fresh human
  review and required checks on the resulting head are still necessary; a docs
  refresh alone does not resolve either.
- The live staging service still runs the older deployment SHA recorded in the
  environment map. The provided original smoke log lacks run ID, tested SHA,
  status and response body; do not assert a proven root cause from the later
  `401 Bearer` read-only observation.

### Later PR-head check observation — 2026-11-21 09:22–09:31 UTC

GitHub reported remote PR #268 head
`7dbebfd060298a80e99a38a52663901e776935cb` after the PR #265 documentation
reconciliation. By 09:31 UTC, Backend, Extension, migration source preflight
and Staging integration passed in
[run 44889070392](https://github.com/kendshhh/PhishLens/actions/runs/44889070392).
Workflow lint, dependency security and deterministic evaluation passed.
Dependency graph review failed because GitHub says the repository Dependency
graph is disabled. CodeQL failed all three language jobs; annotations attribute
failure to Actions installation API rate limits and show no CodeQL findings.
The Secretary report
[44889108682](https://github.com/kendshhh/PhishLens/actions/runs/44889108682)
said **WAITING FOR CHECKS** at 09:22 UTC. Hosted staging/preflight remained
skipped at 09:31. No Render deploy or authenticated CRUD occurred. These results
are a prior-head snapshot; do not transfer them to later branch heads. At that
time GitHub's dependency graph was then enabled afterward, and Dependency graph
review passed on subsequent PR commits. The 15 existing Dependabot alerts
(12 high, 3 moderate) remain open; the rate-limit failure on that older CodeQL
run also remains unresolved on a new PR head.

### Latest observed PR-head check snapshot — 2026-11-21 09:42 UTC

PR #268 head `def5e9b3d925e94a9aa664a24f90c73b960c7f99` passed Backend,
Extension, migration source preflight, Staging integration, workflow lint,
dependency security, Dependency graph review and deterministic evaluation.
Hosted staging and preflight were skipped. The PR check set showed no CodeQL
result. Merged main `95975cd47dceeac74ea36054610956f0a1db1fa9` passed CI and
CodeQL. PR #268 still targets `codex/readiness-update-20261121` at
`ca29235`, now merged into main; retarget it to `main` before merge. The
authenticated hosted CRUD runner, protected Render deployment and current PR
CodeQL result remain open. Re-run source review, every required check, deployment
control and documentation reconciliation on the exact candidate before reuse.
Do not infer a 100% score from partial evidence.

### Latest observed PR state — 2026-11-21 10:14 UTC

PR #268 head is `2e26327254c71b6cb7d655181cffb21e8dd1ee9b` (an empty CI-trigger
commit). Backend, Extension, migration source preflight, Staging integration,
hosted preflight, workflow lint, dependency security, Dependency graph review
and deterministic evaluation passed in [CI 44891131201](https://github.com/kendshhh/PhishLens/actions/runs/44891131201),
[workflow lint 44891131261](https://github.com/kendshhh/PhishLens/actions/runs/44891131261),
[dependency checks 44891131162](https://github.com/kendshhh/PhishLens/actions/runs/44891131162),
and [evaluation 44891131190](https://github.com/kendshhh/PhishLens/actions/runs/44891131190).
Hosted staging job 136807616481 ended with conclusion success, but its final
freshness guard marked the request superseded after its label was removed at
09:54 UTC; deployment, smoke, CRUD and artifact steps were skipped. Its summary
classifies the run as blocked, not hosted acceptance. Required `Secretary
staging` failed because the label and exact-head hosted verification were absent
([run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807)).
No current PR CodeQL result appeared. PR #268 still targets
the merged PR #265 branch, not `main`; retargeting remains outstanding. Fifteen
Dependabot alerts (12 high, 3 moderate) remain open. No exact deployed candidate
or authenticated CRUD evidence exists. The documentation changes being
prepared create a new head and need fresh checks; do not reuse this snapshot as
their check evidence.

### Latest observed PR state — 2026-11-21 11:08 UTC

The documentation reconciliation was pushed as PR #268 head
`a151585ff92d55f21e0364e9838287a9cf04a68d`. Backend and migration source
preflight passed in [CI 44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076).
Workflow lint [44897548088](https://github.com/kendshhh/PhishLens/actions/runs/44897548088),
dependency security and graph review [44897548010](https://github.com/kendshhh/PhishLens/actions/runs/44897548010),
deterministic evaluation [44897548070](https://github.com/kendshhh/PhishLens/actions/runs/44897548070),
and the Secretary report [44897544530](https://github.com/kendshhh/PhishLens/actions/runs/44897544530)
passed. Packaged `Extension checks` failed its Saved reports view keyboard
focus assertion in `scripts/browser_acceptance.mjs:700`. Staging integration
and hosted staging/preflight were skipped. Required `Secretary staging` failed
because the `needs-hosted-staging` label and exact-head hosted verification
were absent ([run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167)).
No current PR CodeQL result appeared; no Render deployment or authenticated
CRUD occurred. PR #268 remains open and targets the merged PR #265 branch.
Retargeting, investigation of the keyboard-focus failure, a fresh exact-head
CI run, and authorized hosted acceptance remain separate outstanding actions.
Do not add the staging request label or run hosted writes without the owner's
explicit approval. Do not claim a 100% score or merge while required checks
fail or are skipped.

The same focus assertion failed in earlier main CI run 44885148600 on `06f89d7`,
while later CI run 44889931821 passed on merged main `95975cd`. Treat the
recurrence as unresolved; compare the exact browser and focus evidence before
calling it flaky or changing the assertion.

### Previous completed workflow snapshot — 2026-11-21 11:21 UTC

Docs-only head `dffdc4c29338142f458350b51c8ce69e0f36e988` passed Backend,
Extension, migration preflight, Staging integration, workflow lint, dependency
security/graph review, deterministic evaluation and the Secretary report (CI
[44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208),
[workflow lint 44898467185](https://github.com/kendshhh/PhishLens/actions/runs/44898467185),
[dependency 44898467124](https://github.com/kendshhh/PhishLens/actions/runs/44898467124),
[evaluation 44898467190](https://github.com/kendshhh/PhishLens/actions/runs/44898467190),
[Secretary report 44898465856](https://github.com/kendshhh/PhishLens/actions/runs/44898465856)).
Hosted preflight/deployment were skipped. Required `Secretary staging` failed
because the `needs-hosted-staging` label and exact-head hosted verification
were absent ([run 44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)).
No current PR CodeQL, Render deployment or authenticated CRUD evidence exists.
A docs-only follow-up after this snapshot requires its own exact-head checks.

### Latest completed workflow snapshot — 2026-11-21 11:31 UTC

Docs-only head `f79098cc075784563d2022cbca87d7abe8f0a635` passed Backend,
Extension, migration preflight and Staging integration in [CI
44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736).
Workflow lint [44899191771](https://github.com/kendshhh/PhishLens/actions/runs/44899191771),
dependency security/graph [44899191710](https://github.com/kendshhh/PhishLens/actions/runs/44899191710),
deterministic evaluation [44899191787](https://github.com/kendshhh/PhishLens/actions/runs/44899191787),
and the Secretary report [44899190365](https://github.com/kendshhh/PhishLens/actions/runs/44899190365)
passed. Hosted preflight/deployment were skipped. Required `Secretary staging`
failed because the `needs-hosted-staging` label and exact-head hosted
verification were absent ([run 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134)).
No current PR CodeQL, Render deployment or authenticated CRUD evidence exists.
The docs-only update after this snapshot needs its own current checks. Keep the
release NO-GO and do not claim 100% while hosted acceptance, required checks and
other listed release evidence remain open.

## Required working method

### 1. Establish the source of truth

- Read repository instructions, workflows, staging/API/Auth code, scripts,
  tests, current DevOps docs and all modified/untracked files before editing.
- Record current branch, HEAD, upstream/main SHA, dirty status, and merge-base.
- Distinguish repository inspection, CI result, Render/Neon control-plane
  observation, HTTP probe, test result, human decision and historical evidence.
- Use least-privileged, read-only control-plane access for inspection. Never
  print or persist secret values, connection strings, Auth tokens, report bodies
  or personal data.
- Do not use a live endpoint, account or database for writes until an approved
  staging test identity and isolated target are verified. Never write to
  production.

### 2. Fix the behavior at both layers

- Make the anonymous preflight's status contract explicit and narrowly checked.
  Reject unexpected statuses, redirects, wrong/missing challenge schemes and
  malformed bodies. Keep legacy seeded-history validation only where public
  demo history is actually configured.
- Check local server liveness during readiness polling. Fail promptly if it
  exits, include the last readiness status in the summary, and upload the log
  artifact from an always-run step.
- Bound the entire smoke with an overall deadline and maximum-attempt count.
  Retry only explicit transient statuses/network failures, never permanent 4xx,
  auth-contract or payload-contract errors. Report final stage, endpoint, HTTP
  status when available, and a sanitized error in the job summary. Keep local
  and hosted acceptance distinct.
- Trace the extension client and hosted CRUD runner end to end. Implement Auth
  through the supported application flow; do not handcraft or fake JWTs. Protect
  test credentials using GitHub environment secrets and never echo tokens.
- Isolate test data with unique synthetic identity/IDs. Delete test artifacts
  in a `finally`/cleanup path even when assertions fail; record cleanup result.
- Ensure CI checks out trusted controller logic from the intended default-branch
  revision and checks out the exact PR head only for code under test. Validate
  stale PR heads, merge SHA, deployed `/version` SHA, migration and package
  provenance before accepting results.
- Keep the job read-only except for explicitly authorized synthetic staging
  CRUD. Make fail/timeout/cleanup behavior observable and deterministic.

### 3. Validate the implementation

- Add focused regression coverage for valid `401 Bearer`, invalid/absent
  challenge, legacy seeded `200`, unexpected status, redirects/timeouts, Auth
  failure, each CRUD operation, ownership violation, persistence and cleanup.
- Add smoke-runner regressions for bounded transient retries, non-retryable
  permanent status/data-contract errors, summary contents and success paths.
  Lint the workflow and verify the hosted deploy cannot start when any
  dependency is failed or skipped.
- Run the focused tests and relevant linters/type checks first; then run the
  repo-required CI checks. Report exact commands, versions, exit statuses and
  linked action run. Do not claim a check passed because its code exists.
- Run hosted staging only after confirming service identity, exact target SHA,
  Auth configuration, staging-only database/role, synthetic test identity and
  cleanup safety. Capture pre/post identities and prove no records were left.
- If an external prerequisite is unavailable, complete all independent code and
  documentation work, mark the dependent evidence open, identify its owner and
  precise next action. Do not manufacture a successful result.

### 4. Reconcile every DevOps record

- Inventory every DevOps/release/evidence Markdown file, pipeline docs,
  operational scripts/workflows, metrics and cross-links.
- Maintain one current index, environment map, release record and scorecard.
  Add dated evidence for each fresh probe/run; link from the canonical docs.
- For every older document, either preserve it as a dated snapshot with a
  successor link or update a clearly labeled current section. Do not rewrite
  historical outcomes, timestamps, owners, status or API responses.
- Reconcile service URLs/IDs, deploy IDs/SHAs, branches, Auth/provider state,
  migrations, workflow checkout behavior, auto-deploy settings, required
  checks, metrics windows, recovery facts and scoring language. When sources
  conflict, preserve the discrepancy and leave the gate open until verified.
- Treat CI infrastructure failures as blockers too. On PR #268 head `7dbebfd`,
  GitHub's dependency-review job failed because repository Dependency graph was
  disabled; an administrator must enable it in Security settings and rerun the
  check. CodeQL analysis failed on Actions installation API rate limits, so
  rerun it on the exact candidate after the limit clears. Do not record either
  failure as a code pass or silently omit it.
- Check every internal Markdown link, every evidence reference and every
  repeated status statement. Remove stale `current/latest/passed/100%` claims
  only after establishing a newer source; preserve dated context.
- Include a concise record of what changed, why, evidence used, evidence still
  missing, risks and owners.

### 5. Release and report boundaries

- Do not commit, push, merge, deploy, alter Render/Neon/GitHub settings, rotate
  secrets, create persistent users, delete shared data, or perform recovery
  cutover unless the user has explicitly authorized that specific action.
- Prepare a concrete, reviewable local diff first. Keep changes scoped; do not
  overwrite dirty user files or unrelated work. Do not hide an uncommitted patch
  or claim the repository is synchronized until the Git history is actually
  reconciled.
- End with an evidence table: requirement, result (`Pass`/`Open`/`Fail`), exact
  source identity, artifact/run link, missing proof and responsible owner.
  Explicitly state whether this is safe to propose for review; do not label a
  NO-GO release ready.

## Required final acceptance matrix

| Gate | Evidence required for `Pass` |
|---|---|
| Anonymous boundary | Exact staging response and test proving 401 Bearer accepted only for the anonymous preflight, with 200-mode seed checks preserved. |
| Authenticated CRUD | Supported Auth sign-in, token-backed CRUD, reload persistence, cross-user rejection and cleanup on a named staging branch and exact SHA. |
| CI trust/source | Trusted workflow revision, current PR head, merge/deploy SHA and migration all match; stale, failed or skipped job cannot pass. |
| Extension package | ZIP and sidecar hashes tied to the accepted backend/source and manually installed Chrome result. |
| Environment/security | Private Render-to-Neon mapping, least-privilege role, Auth/provider configuration and protected-secret scopes verified without values. |
| Production | Exact-SHA observer records identity/health/readiness and current disabled/enabled state. Disabled observer is explicitly not product acceptance. |
| Reliability | Compatible app rollback and isolated data restore; measured end-to-end RTO/RPO and named responders. |
| Quality/team/docs | Approved representative evaluation and thresholds, human explanation review, actual participant/instructor decisions, current linked documents and release changelog/tag. |

---

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.
