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
   missing, stale, skipped or has the wrong identity.
5. DevOps evidence and records agree with current repository/workflow/Render/
   Neon evidence. Old dated observations remain historical; no result, owner
   approval, workflow pass, control-plane setting, metric, meeting or acceptance
   is fabricated or silently upgraded.
6. Every release gate is either fully passed with linked, identity-bound
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
- The workspace's `scripts/staging_smoke.mjs` accepts a valid anonymous Bearer
  challenge and retains seeded-history checks for `200`, but this change was
  not in the then-current `main`.
- The then-current `.github/workflows/ci.yml` checked out trusted default-branch
  code for the legacy smoke, then ran a separate exact-PR-head
  `scripts/verify_crud.mjs --allow-writes` path without an authenticated
  session. Verify current workflow code before acting.
- Production was observed with analysis disabled. A disabled observer result is
  not product/AI acceptance. Production smoke is manual and must not make paid
  calls or saved-report writes.
- Render metadata showed auto-deploy off even though a production deploy record
  showed `new_commit`; reconcile the settings and event source with the owner.
- The local branch was four commits behind `origin/main` and had user changes.
  Inspect the actual tree, do not reset, clean, stash, rebase, merge or push over
  that work.

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
