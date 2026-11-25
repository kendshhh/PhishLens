# DevOps closeout snapshot — 2026-11-25

This is a current evidence snapshot, not a release approval. Product release
remains **NO-GO** until the model-quality and immutable-artifact gates pass.

## Verified controls and current evidence

| Area | Current result | Evidence and remaining boundary |
|---|---|---|
| DORA 4+1 and CI timing | Report published; incomplete metric coverage is explicit | [Current DORA report](dora-report-2026-11-25.md) and its redacted [source snapshot](evidence/dora-source-2026-11-25.json). The window is 28 days; change fail rate, recovery, deployment rework, and a current comparable optimization result remain unmeasured. |
| Main merge gate | Aligned and strict | Classic protection and active ruleset #27733591 both require the same eight stable contexts: Backend checks, Extension checks, Staging integration, CodeQL, Secretary staging, Deterministic AI Evaluation, Dependency security, and Workflow lint. Up-to-date branches, one approval, stale-review dismissal, and latest-push approval are enabled. |
| Staging approval | Independent review required | `staging` now requires xxTrixia and prevents self-review. Allowed refs are `main` and `refs/pull/*/merge`; stale `refs/pull/33/merge` was removed. `release-staging` now exists, requires xxTrixia, prevents self-review/admin bypass, and allows only `main`. |
| Production approval | Independent, no admin bypass | Production keeps `inaki3023` as reviewer, prevents self-review and administrator bypass, and limits deployments to protected branches. No production deployment or data access was performed. |
| Staging target | Isolated target variables now align; live mapping still needs deployed verification | GitHub environment variables were checked without printing values: project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, expected host, `phishlens_dev`, `neondb_owner`, both Auth URL/database settings, Auth origin presence, production separation, and `STAGING_NEON_PRODUCTION_ROWS_PRESENT=false` match the approved staging target. `STAGING_ACCEPTANCE_ENABLED=true` and `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION=current` are recorded. This is configuration evidence, not independent proof of Render runtime/migration URLs; no candidate deployment has verified them. Render staging was last observed on SHA `30743b077169357455620b55233f75806ea636aa` (`dep-dc3595m8bjmc73ekclig`). `release-staging` still has no variables or secrets. The prior Neon catalog read found no public app tables or Alembic history; recheck schema before migrations. |
| Authenticated product acceptance | **Not passed on the current candidate** | PR #291 head `28052e825f413d170b24fa78375065f3487c3321` run [45580145160](https://github.com/kendshhh/PhishLens/actions/runs/45580145160) passed Backend checks, Extension checks, Staging integration, and Hosted staging preflight. Its Hosted staging job is queued with no runner and no pending reviewer request. The shared staging queue is held by PR #268 run [45539051728](https://github.com/kendshhh/PhishLens/actions/runs/45539051728), awaiting `xxTrixia` approval for superseded head `7d32f3da98f5b0b02ae47f678aec9062dacc896d`; current PR #268 head run [45541536613](https://github.com/kendshhh/PhishLens/actions/runs/45541536613) is ahead of #291. Kendra approved the test window and asked xxTrixia to reject the stale run and review only the current head. No deployment, authenticated CRUD, or isolation result has occurred. The trusted `pull_request_target` controller on main excludes stacked-base PRs; this branch removes that filter, effective only after merge. |
| Model quality | Still blocked | Wilber’s reported 190/200 phishing detections, 1/1,000 legitimate false alerts, and 1,200 valid outputs support advisory use only on the historical English cohort. Draft PR #269’s approved policy and reviewed representative holdout report are not yet accepted for the release candidate. |
| Immutable promotion | Workflow present; execution/configuration incomplete | `release-promotion.yml` builds an image and extension once, validates digests, gates staging and production, and writes a manifest only after checks. Render credentials use separate `RENDER_STAGING_API_KEY` and `RENDER_PRODUCTION_API_KEY` names. `release-staging` is protected but currently has no variables or secrets. Production Render is still a native Python service rather than an image-backed service. The same artifact has not been promoted. |
| Current deployment identity | Main and production differ | Main is `46f0298d8e3299afa74e02882081be56c1de4933` (PR #295); CI run [45581846349](https://github.com/kendshhh/PhishLens/actions/runs/45581846349) passed. Render production remains on `811980c2cbf70d9957146bf329627f0826a018f1`; Render auto-deploy is off. No production release tag or candidate release was created. |
| Recovery and alerting | Still incomplete | No current-production rollback rehearsal, verified alert delivery/response, or measured recovery objectives are evidenced. Historical staging drills and the Nov 20 isolated database restore are not current-production recovery proof. |

## Remaining items before claiming completion

1. Clear the shared staging queue safely. Run [45539051728](https://github.com/kendshhh/PhishLens/actions/runs/45539051728) is waiting on `xxTrixia` for superseded SHA `7d32f3d`; do not deploy that SHA. The current PR #268 run [45541536613](https://github.com/kendshhh/PhishLens/actions/runs/45541536613) is ahead of PR #291. Kendra authorized the test window; the independent GitHub reviewer gate still applies. The trusted-preflight branch-filter fix is in this review branch and only takes effect after merge. Do not accept a skipped preflight.
2. Before staging deploy/migrations, privately confirm Render's runtime and migration URLs, database, branch, Auth endpoint, and least-privilege roles against the selected Neon target. The GitHub mapping-attestation variable now says `current`, but the underlying Render values were not exposed or independently validated in this check. Recheck that the isolated database schema is initialized and safe; then require exact-head preflight and authenticated acceptance.
3. Have the AI owner approve the policy and submit the independently reviewed, permissioned holdout report bound to the exact release model. Keep release blocked until the agreed thresholds pass.
4. After Render mapping and schema are verified, provision non-secret variables and secrets in protected `release-staging`: `NEON_API_KEY`, `STAGING_MIGRATION_DATABASE_URL`, `RENDER_STAGING_API_KEY`, `STAGING_AI_APPROVAL_JSON`, and the two synthetic account email/password pairs. Provision `RENDER_PRODUCTION_API_KEY` only after the image-backed production service is ready. Verify secret presence without printing values. Reconcile production Render to an image-backed service before promotion and keep its auto-deploy off.
5. Record production change-failure incidents against release SHAs; classify planned versus rework deployments; capture detection-to-verified-recovery timestamps. Until then, keep the corresponding DORA values not measured.
6. Rehearse application rollback and isolated data restore, measure approved RTO/RPO, and verify alert delivery and named responders.
7. Run a like-for-like end-to-end optimization experiment with the same event, required checks, runner, and queue treatment. Report either result without claiming the historical cache trials as a gain.

## Reproduce the DORA snapshot

From the repository root, with GitHub CLI and the authenticated Render CLI
available, collect and render a 28-day snapshot:

```powershell
./scripts/collect_dora_evidence.ps1 -OutputPath docs/devops/evidence/dora-source-2026-11-25.json
python -m scripts.report_dora_metrics docs/devops/evidence/dora-source-2026-11-25.json docs/devops/dora-report-2026-11-25.md
```

The collector combines paginated GitHub metadata, the latest Render deploy
inventory, and the retained Render inventory through Nov 14. It stores no
secret values or product content. Refresh the retained deployment inventory
before later windows outgrow the Render CLI’s recent-deploy listing.
