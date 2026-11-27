# DevOps closeout snapshot — 2026-11-25

This is a historical evidence snapshot, not a release approval. It is
superseded by the [November 27 rubric closeout](devops-finalization-2026-11-27.md)
and [current pipeline snapshot](../../PIPELINE.md). Product release remains
**NO-GO** until the model-quality and immutable-artifact gates pass.

## Verified controls and current evidence

| Area | Current result | Evidence and remaining boundary |
|---|---|---|
| DORA 4+1 and CI timing | Report published; incomplete metric coverage is explicit | [Current DORA report](dora-report-2026-11-25.md) and its redacted [source snapshot](evidence/dora-source-2026-11-25.json). The window is 28 days; change fail rate, recovery, deployment rework, and a current comparable optimization result remain unmeasured. |
| Main merge gate | Aligned and strict | Classic protection and active ruleset #27733591 both require the same eight stable contexts: Backend checks, Extension checks, Staging integration, CodeQL, Secretary staging, Deterministic AI Evaluation, Dependency security, and Workflow lint. Up-to-date branches, one approval, stale-review dismissal, and latest-push approval are enabled. |
| Staging approval and credential boundary | Independent, main-only | `staging` and `release-staging` require xxTrixia and prevent self-review. `staging` now permits only `main`; PR refs were removed so PR-authored workflow changes cannot request its secrets. The old Render key remains in `staging` but is inaccessible from PR refs. `release-staging` has no Render key yet. |
| Production approval | Independent, no admin bypass | Production keeps `inaki3023` as reviewer, prevents self-review and administrator bypass, and limits deployments to protected branches. No production deployment or data access was performed. |
| Staging target | GitHub mappings aligned; Render mapping is not verified | GitHub non-secret variables now identify project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, expected host, `phishlens_dev`, `neondb_owner`, the new Auth URL/database, trusted extension origin, production separation, and no production rows. Acceptance is enabled only behind exact-target and Render checks. `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is now `pending` in `staging` and `release-staging` because masked Render runtime/migration values are not verified. `release-staging` has target variables but no secrets. Render staging was last observed on SHA `30743b077169357455620b55233f75806ea636aa`; recheck the empty Neon schema before migrations. |
| Authenticated product acceptance | **Not passed on the current candidate** | No accepted exact-head Auth/CRUD run exists. The review branch replaces the PR-triggered staging job with a default-branch `workflow_run` controller, but it is not active until merged. The old staging environment now rejects PR refs; no current candidate was deployed or written to staging during this update. |
| Model quality | Still blocked | Wilber’s reported 190/200 phishing detections, 1/1,000 legitimate false alerts, and 1,200 valid outputs support advisory use only on the historical English cohort. Draft PR #269’s approved policy and reviewed representative holdout report are not yet accepted for the release candidate. |
| Immutable promotion | Workflow present; execution/configuration incomplete | `release-promotion.yml` builds an image and extension once, validates digests, gates staging and production, and writes a manifest only after checks. `release-staging` has target variables but no Render key or migration/AI/account secrets. Render staging and production remain Git-backed Python services, so the same immutable artifact has not been promoted. |
| Current deployment identity | Main and production differ | Main is `46f0298d8e3299afa74e02882081be56c1de4933` (PR #295); CI run [45581846349](https://github.com/kendshhh/PhishLens/actions/runs/45581846349) passed. Render production remains on `811980c2cbf70d9957146bf329627f0826a018f1`; Render auto-deploy is off. No production release tag or candidate release was created. |
| Recovery and alerting | Still incomplete | No current-production rollback rehearsal, verified alert delivery/response, or measured recovery objectives are evidenced. Historical staging drills and the Nov 20 isolated database restore are not current-production recovery proof. |

## Remaining items before claiming completion

1. Merge the trusted workflow change only after its current-SHA CI and workflow-lint checks pass and an independent reviewer approves it. The old pull-request staging route is intentionally blocked by the main-only environment policy.
2. Before staging deploy/migrations, privately confirm Render's runtime and migration URLs, database, branch, Auth endpoint, and least-privilege roles against the selected Neon target. The GitHub mapping-attestation variable is now deliberately `pending`; set it to `current` only after Render values are privately verified. Recheck that the isolated database schema is initialized and safe; then require exact-head preflight and authenticated acceptance.
3. Have the AI owner approve the policy and submit the independently reviewed, permissioned holdout report bound to the exact release model. Keep release blocked until the agreed thresholds pass.
4. After the Render mapping and schema are verified, provision a newly issued staging Render key, Neon migration key/URL, approved AI evidence, and synthetic account credentials in protected `release-staging`. Its non-secret target variables are present now; no secrets are. Provision `RENDER_PRODUCTION_API_KEY` only after an image-backed production service is ready. Verify secret presence without printing values. Reconcile production Render to an image-backed service before promotion and keep its auto-deploy off.
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
