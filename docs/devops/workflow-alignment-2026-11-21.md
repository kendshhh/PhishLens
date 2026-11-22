# Workflow alignment addendum — 2026-11-21

> **Superseded status note — November 22, 2026:** The implementation details
> below describe the earlier local Auth-in-CI proposal, not the safe current
> working-tree design. The PR-triggered `Hosted staging` job was removed from
> the local CI workflow because it ran PR-selected `verify_crud.mjs` while
> protected Auth credentials and the Render deploy key were available. The
> trusted `workflow_run` controller remains the only local staging deploy path;
> it does not yet perform authenticated CRUD. Remote `main` is still at
> `561c19da40165d7994d86232af63059a288b4ac2` and retains the legacy deploy job,
> so none of these local corrections is active in GitHub until reviewed and
> merged. Do not use the older implementation steps below as current run
> instructions.

This addendum records the workflow work prepared in the local workspace after
the release evidence snapshot. It does not change the release decision or
claim that hosted staging, Auth, or browser acceptance passed.

## Workspace identity and sync state

- Working branch: `codex/ai-evaluation-spend-20261114`.
- Working HEAD: `16f955321caf5dc368181be7ce5c00643750545d`.
- Fetched `origin/main` at `125a200b88f2e8e476fcf28f6f83113fc71cebb2` during
  this task. HEAD is zero commits ahead and nine behind `origin/main`, and is
  its ancestor. Git's separate `ahead 104` status is against the branch's
  `origin/codex/ai-evaluation-spend-20261114` upstream, not `main`. The
  fetch updated remote-tracking metadata only; no working branch update,
  merge, or rebase was performed.
- The working tree already contained numerous user edits and untracked files.
  It also contains a separate nested checkout at
  `.github/secretary-auth-preflight`, branch
  `codex/pr266-root-acceptance-fix`, commit
  `bc4ea04b344b3c78b93e82b6e589157dfa5f429c`.
  No existing changes were discarded, staged, committed, pushed, or merged.
  Reconcile those changes with the newer main files before asking GitHub to run
  the protected staging workflow.

## Workspace implementation

- `.github/workflows/ci.yml` now requires `STAGING_AUTH_USER_A_EMAIL`,
  `STAGING_AUTH_USER_A_PASSWORD`, `STAGING_AUTH_USER_B_EMAIL`, and
  `STAGING_AUTH_USER_B_PASSWORD` as protected staging-environment secrets. It
  rejects identical account emails and requires the existing
  `PHISHLENS_STAGING_AUTH_DATABASE` environment variable to match the database
  path in `STAGING_NEON_AUTH_URL` before deployment.
- `scripts/staging_auth.mjs` signs in through Neon Auth for accounts A and B.
  `scripts/verify_crud.mjs` creates a report as A, checks persistence through a
  fresh API client, and checks that B cannot list, read, update, or delete A's
  report. A's created report is still cleaned up by the existing `finally`
  path. The workflow finalizer requires persistence, isolation, consistent
  provider provenance, and cleanup before producing its acceptance artifact.
- `actions/dependency-review-action`, `astral-sh/setup-uv`, and uv are pinned
  to v5.0.1, v10.4.0, and 0.13.9. The setup action requires a known uv checksum.
  The Node.js 24, Python 3.12, checkout, setup-node, setup-python, and
  upload-artifact pins remain at the already-current versions recorded in
  [CI maintenance](ci-maintenance.md).
- The extension CI job now labels its package and isolated-Chromium evidence
  with the exact PR merge candidate SHA, requires both browser evidence outputs,
  and fails if the browser artifact is absent. Hosted evidence records the PR
  head and deployed merge SHA separately. The duplicate
  `.github/scripts/staging_auth.mjs` helper now re-exports the canonical
  root runner instead of maintaining a hard-coded single-account Auth contract.

These are local source changes. No GitHub settings/secrets, Auth user
accounts, Render environment values, or connection targets were changed.
Read-only GitHub, Neon project/Auth, and Render service metadata were inspected.

## Local verification

- `node --test extension/tests/staging-auth.test.mjs`: passed, 3 tests after
  aligning the environment variable name.
- `node --check scripts/staging_auth.mjs`: passed.
- `node --check scripts/verify_crud.mjs`: passed.
- `git -c core.whitespace=cr-at-eol diff --check` on the edited workflow,
  runner, test, and DevOps docs: passed.
- This workspace audit made no hosted Auth/CRUD request and wrote no staging
  record. A separate reported hosted attempt failed at sign-in before CRUD.

## Current configuration and conversation findings

- The protected GitHub `staging` environment currently names project
  `hidden-shadow-38533062`, branch `br-broad-feather-b3261w7l`
  (`staging-root`), and Auth database `phishlens_dev`. Its existing variable
  names are `STAGING_NEON_AUTH_URL` and
  `PHISHLENS_STAGING_AUTH_DATABASE`; the workflow now reads both exact names.
- The protected environment has the newer A/B test-account secrets and still
  contains the legacy single-account `STAGING_AUTH_TEST_EMAIL` and
  `STAGING_AUTH_TEST_PASSWORD`. The A/B contract is used by this workflow.
  Remove the legacy secrets only after an owner confirms no active workflow or
  rollback path still consumes them.
- The local startup allowlist still targets project `patient-bird-25428852`,
  branch `br-delicate-paper-b381z98i` (`pr-58-staging`). Render's actual app
  and migration connection targets and roles have not been exposed by the
  read-only service tool. This source/config discrepancy is a release blocker;
  do not retarget the startup allowlist or deploy until an authorized owner
  privately confirms the Render host-to-branch and role mapping.
- Neon Auth inspection found the selected GitHub target currently permits
  localhost and does not require email verification. Align its Auth security
  policy with staging requirements before testing verified synthetic accounts.
- A separate nested candidate checkout contains full authenticated extension
  browser acceptance, but its workflow maps the Auth URL from
  `PHISHLENS_STAGING_AUTH_URL`; the protected environment currently uses
  `STAGING_NEON_AUTH_URL`. That candidate is not the active parent workflow.
  Reconcile this name, its branch/database IDs, and the live target before
  selecting it as the single acceptance workflow. The root workflow's isolated
  Chromium check alone does not prove the authenticated staging UI journey.
- The GitHub environment lists EnviousCoal and kendshhh as required reviewers,
  but prevent-self-review was off. Its branch allowlist included `main`,
  `refs/pull/*/merge`, and a redundant specific `refs/pull/33/merge` entry.
  Have the environment owner enable self-review prevention and remove the
  stale duplicate rule after verifying the intended policy.
- The latest reported hosted product-acceptance attempt failed sign-in; the
  report CRUD, persistence, isolation, cleanup, and packaged-extension UX
  checks therefore failed downstream. It is evidence of a failing candidate,
  not a pass. The next run must use a new reviewed candidate and record its
  run URL and exact SHAs.
- PR `#275` at `e2c2922` was reported mergeable into `main` at
  `125a200`. Simulated landing of PRs `#266` (`824cb60`) and
  `#251` (`5beb5d6`) produced conflicts in the CI workflow, staging
  controller, and hosted-identity/superseded-run tests. Reconcile those on a
  disposable integration branch in the agreed landing order; preserve the
  live PR-head validation guard.

## Required next steps

- [ ] Reconcile the dirty local checkout with current `origin/main` in a
  separate integration worktree. This checkout is nine commits behind and
  already contains user changes; do not merge over them as one bulk operation.
  First agree on the PR `#275` → `#266` → `#251` landing order, resolve
  shared-file conflicts, and retain exact PR-head validation.
- [ ] Choose and integrate one staging acceptance controller. Preserve the
  exact merge-candidate package/browser provenance, the authenticated A/B CRUD
  checks, and the full authenticated extension UX flow. Align Auth URL and
  database variable names across GitHub settings, CI, scripts, package
  validation, tests, and docs before enabling the gate.
- [ ] Have the authorized staging owner privately verify that Render's
  application URL and migration URL resolve to the approved isolated Neon
  project/branch/database and expected least-privilege/owner roles. Until that
  proof exists, keep the startup guard fail-closed and make no hosted writes.
- [ ] Resolve the GitHub target versus startup allowlist mismatch in reviewed
  source and environment changes. Confirm the staging Auth endpoint and
  `PHISHLENS_STAGING_AUTH_DATABASE` describe the same approved target, then
  disable localhost sign-in and require email verification (or document an
  owner-approved exception). Keep two distinct, registered, verified synthetic
  users in the protected A/B secrets; do not expose credentials or tokens.
- [ ] Correct protected-environment governance: prevent self-review, confirm
  the required reviewer and branch rules, and remove the stale PR #33 rule if
  the owner confirms it is redundant. Verify the required checks apply to the
  intended PR head and that a skipped step or absent artifact fails closed.
- [ ] On one exact candidate, run migration preflight first; then check
  anonymous Bearer rejection, A/B sign-in, create/list/read/update/delete,
  fresh-client persistence, cross-user list/read/update/delete denial, failure
  handling, cleanup, and post-run health/version/model/Auth identity.
- [ ] Package the extension from that same candidate, record its checksum,
  install that package in Chrome, and pass loading, success, sign-in failure,
  API error, timeout, and reload UX checks. Record PR head SHA, merge/deployed
  SHA, migration revision, masked target/role, model/provider identity, run
  URL, and artifact provenance together. Require independent reviewer approval
  for that same candidate.
- [ ] Close AI release gates: Wilberr approves thresholds and representative
  holdout evidence; Trixia approves the source inventory and frozen cohort lock
  SHA before scoring; name two score-blind label reviewers; secure permission
  for both independent sources; collect at least 100 phishing, 200 legitimate,
  and 100 spam families, including 50 genuine security notices in the
  legitimate set, plus an intake buffer for overlap/exclusions. Confirm the
  proposed thresholds (at least 90% phishing recall, at most 3% legitimate
  false positives, and 100% valid outputs), run one pinned evaluation, and
  review redacted aggregate results. Keep raw mail private.
- [ ] Agree team/instructor scope and acceptance criteria; rehearse application
  rollback and isolated Neon recovery; measure service RTO and recoverable
  point age/RPO; name primary and backup responders. The scorecard remains
  **0 of 7 complete**, so release remains **NO-GO**.
