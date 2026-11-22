# PhishLens release record — November 23, 2026

**Decision: NO-GO.** This is a read-only current-state update plus a local documentation change. It does not claim product acceptance or authorize deployment.

## Evidence boundaries

- Checked at 2026-11-22 21:50 UTC (November 23 in Asia/Manila).
- No production product data was read. The only service requests were staging and production health/version/model metadata; the production `/version` request timed out. No `/api/analyses` endpoint was called.
- No migrations, staging CRUD, account creation, settings changes, Git staging, commit, push, merge, tag, or deploy was performed.
- No environment secret values, Auth account identifiers, passwords, or tokens were revealed.

## Repository and workflow

| Item | Current evidence | Status |
|---|---|---|
| Remote `main` | `0338ad163a4892987a6a682aed29b95c22c322da` (PR #279). `git ls-remote` agrees. | Verified |
| Local checkout | `codex/ai-evaluation-spend-20261114` at `16f955321caf5dc368181be7ce5c00643750545d`, 13 commits behind `origin/main`. Thirty-three tracked files are modified; numerous untracked files and nested worktrees remain. Nothing is staged. | Verified; preserve local work |
| Main branch protection | The live branch-protection API now reports strict checks and eight required contexts: `Backend checks`, `Extension checks`, `Staging integration`, `CodeQL`, `Secretary staging`, `Deterministic AI Evaluation`, `Dependency security`, and `Workflow lint`. One approval and latest-push approval are required; stale reviews are dismissed; admin enforcement is enabled. | Verified; closes the earlier uncertainty about main’s required-check list |
| Releases and tags | `gh release list` and `git ls-remote --tags origin` returned no releases or remote tags. | Verified absent |
| [PR #281](https://github.com/kendshhh/PhishLens/pull/281) | Open at `889da1b541b871ce6c056f0c8f388813511b8146`, based on current `main`. Backend, extension, disposable staging integration, CodeQL, dependency security, deterministic AI evaluation, and workflow lint pass. `Hosted staging` is skipped; required `Secretary staging` fails because runtime changes need the `needs-hosted-staging` label. GitHub reports `CHANGES_REQUESTED` and merge state `BLOCKED`. | Not accepted; no staging run from this PR |
| [PR #267](https://github.com/kendshhh/PhishLens/pull/267) | Open at `6f26617186ea48a51ac692e7fe0bfe00f8cbf3e9`. Its [hosted acceptance run](https://github.com/kendshhh/PhishLens/actions/runs/45073205707) fails at sign-in; the output says the account email must be verified. CRUD, isolation, cleanup, and extension acceptance did not pass. | Fail |
| [PR #266](https://github.com/kendshhh/PhishLens/pull/266) | Open at `4e4481d6279a7404d35b21d4a32ef5d0c280311b`, based on current `main`. Its [hosted acceptance run](https://github.com/kendshhh/PhishLens/actions/runs/45040106942) remains failing; release gate evidence rejects sign-in, CRUD, extension UX, and related acceptance fields. | Fail |

The local checkout is older than current `main`; its uncommitted workflow changes are not effective in GitHub. PR #281 contains newer target-pinning work and must be reviewed against its requested changes before any staging run.

## Staging target and product path

The staging owner selected Neon project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`. The Render staging page currently shows `STAGING_NEON_BRANCH_ID=br-rough-sea-a1l6ehi1`; the service is Git-backed to `main`, service ID `srv-db92irlg1s2s739404i0`, and the dashboard showed live deploy `dep-dc1m2vl6e07s73do86cg` at `6f26617186ea48a51ac692e7fe0bfe00f8cbf3e9`.

Read-only public staging probes now report:

- `/version`: `environment=staging`, commit `6f26617186ea48a51ac692e7fe0bfe00f8cbf3e9`.
- `/health`: HTTP 200, `ok`.
- `/ready`: HTTP 200, database `connected`.
- `/model-info`: provider `tfidf`, model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`, `accepts_tfidf_reports=true`.

These checks establish service metadata only. They do not prove the database project/branch mapping, migration revision, Auth mapping, authenticated CRUD, or extension acceptance. Render masks the project ID, database URLs, migration URL, Auth URL, and database host in its UI; those values were not revealed. The current PR #281 source pins the owner-selected project, branch, expected database host, and Auth host in trusted configuration and validates Render’s runtime values against them, but that source is unmerged and has not passed hosted staging.

The most recent observed hosted Auth attempt used the staging Auth endpoint and failed because the synthetic account email was not verified. That attempt ran a single-account check; it is not evidence for two-user ownership isolation. No new staging write was performed for this update. Do not claim Auth acceptance until the owner verifies the isolated synthetic A/B accounts and an exact-candidate run passes create, list, read, update, delete, reload persistence, cross-account denial, failure handling, cleanup, and the authenticated extension flow.

## Model quality and release control

Wilber’s reproduced historical English evaluation reports 190/200 phishing detected, one false alert among 1,000 legitimate messages, and 1,200/1,200 valid outputs. This is an approved advisory result for its historical source-pair cohort. It does not establish contemporary-source or spam performance, nor model acceptance for the current release candidate. Staging currently advertises TF-IDF; its health result does not establish quality. A reviewed representative holdout, approved thresholds, independent labeling, and an exact-model evidence report remain required. Keep AI/release approval blocked until the model owner accepts those results.

The prior November 22 Render metadata reported production Auto-Deploy off; this setting was not freshly re-read here. Production `/version` timed out during this check, so current production SHA and health are not reverified in this record. The service is still reported as a native Python/Git-backed Render service; no backend image digest promotion, exact same artifact promotion, approved version tag, or release record is evidenced. No remote GitHub release or tag exists.

## Ordered closure plan

1. **Finish private staging identity verification.** The selected branch ID matches Render’s visible branch variable. A staging/database owner must privately confirm that runtime URL, migration URL, `STAGING_DATABASE_HOST`, project ID, branch ID, database name/roles, and `NEON_AUTH_BASE_URL` all resolve to the selected project/branch and the production target is distinct. Do not publish credentials or run another migration until that mapping is confirmed.
2. **Repair test-account readiness.** The synthetic Auth account used by the latest staging attempt needs verified email status. Confirm two distinct, verified, isolated A/B accounts and their protected secret mapping. Do not create, verify, or change accounts from this read-only update.
3. **Complete exact-candidate product acceptance.** Resolve PR #281’s requested review changes. Only after the owner authorizes a hosted write, request the required staging run for one current SHA. Require successful authenticated sign-in and complete CRUD/persistence/isolation/failure/cleanup checks plus the exact packaged extension-to-staging-backend journey. Preserve redacted, SHA-bound evidence.
4. **Close model quality.** Wilber/AI owner must complete the permissioned, independently reviewed holdout plan, publish the redacted aggregate report and digests, and approve the thresholds. The CI release gate must fail for missing, mismatched, or below-threshold evidence.
5. **Prove production release controls.** Production Auto-Deploy was previously reported off, but needs a current read. Configure and verify independent non-bypassable approval, same immutable backend artifact and extension package through staging and production, manifest/digests, exact-SHA post-deploy product smoke, changelog, and version tag. Current Render is not image-digest promotion.
6. **Complete operational recovery proof.** Separately rehearse compatible application rollback and isolated database restore; measure approved RTO/RPO; verify alert delivery, responder ownership, and current user-flow monitoring. Update the handover only from dated test evidence.

Until those gates pass on one candidate, issue #153 remains **NO-GO**. Health/readiness, a green disposable-database test, a historical advisory evaluation, or the staging branch ID alone cannot close the product or release criteria.
