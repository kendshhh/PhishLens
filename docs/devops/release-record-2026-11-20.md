# Release record — 2026-11-20

> Historical snapshot. Service identities and control-plane state were
> refreshed on November 21 in the
> [current release record](release-record-2026-11-21.md). Keep this dated
> evidence as history; do not use it as current deployment state.

## Decision

**NO-GO.** This record fixes the product scope and refreshes current main and
production identities observed on November 20. It is not approval to deploy or
a claim that application acceptance is complete.

## Release scope

The intended CSP221A product is the **PhishLens Chrome Manifest V3 extension,
backed by the PhishLens FastAPI service on Render and PostgreSQL/Auth on Neon**.
The `https://csp221a.vercel.app/` address is the CSP221A course guide, not the
PhishLens product release URL. Remove it from product-release links while
retaining it where the course guide itself is referenced.

This resolves the current local project documentation scope. The historical
web-app note in [issue #153](https://github.com/kendshhh/PhishLens/issues/153)
still needs an owner update so the project issue and this record agree.

## Observed candidate identities

| Component | Observed identity | Acceptance state |
|---|---|---|
| GitHub source | `main` at [`0c382dda175db3570e6bb7122841122254ba131d`](https://github.com/kendshhh/PhishLens/commit/0c382dda175db3570e6bb7122841122254ba131d), merged by PR #256 | Main CI, CodeQL, dependency, workflow-lint and deterministic AI-evaluation runs passed. No product release tag exists. |
| Production API | Render deploy [`dep-dc04t5dg1s2s73e5pc00`](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dc04t5dg1s2s73e5pc00), source SHA `0c382dda175db3570e6bb7122841122254ba131d`; Live since 13:44:56 UTC | The Render control plane confirms `AI_ANALYSIS_ENABLED=false` was set and the matching-SHA deploy completed. Post-deploy public GETs returned HTTP 403 from this audit client, so `/model-info` has not confirmed the effective disabled response. No live Auth/product acceptance is claimed. |
| Staging API | Source SHA `d6612c258f289b3a45d8229e4a4803cac75a91ee` | Health and DB readiness pass; TF-IDF mode; not the production SHA. |
| Extension package | `PhishLens-Extension` from [main CI run 44745905952](https://github.com/kendshhh/PhishLens/actions/runs/44745905952); version `0.1.0`; source/tested SHA `0c382dda175db3570e6bb7122841122254ba131d`; ZIP SHA-256 `6b17590cc7b10e9c643e7a885f3cd7cfe97c1aaf990f891f81e11e64a60b82c4`; GitHub artifact digest `sha256:432434aa43cb6f8164cd8f7375b0d4a3164eab116308c96a881eca55ddb9cbbe` | ZIP checksum matches CI evidence; source and tested SHAs match current main candidate. Synthetic packaged-browser checks passed. Artifact expires November 27, 2026; judge weights and full workflow assets are not included. No live Auth acceptance is inferred. |
| AI model | Staging reports TF-IDF model SHA `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`; PR #256 added `AI_ANALYSIS_ENABLED` | Broad model-quality acceptance still fails. Render production has `AI_ANALYSIS_ENABLED=false` and the configuration deploy is live, but this audit client could not verify the effective `/model-info` response. No provider key or budget was added. |
| Auth mode | Authenticated staging acceptance is still pending | **NOT VERIFIED**. |
| Neon target | Connected project exposes `production` and `pr-58-staging` branches | Exact Render-to-Neon mapping and runtime permissions require private owner verification. |

## Required release evidence

- [ ] Update issue #153 to remove or clearly close the historical web-app scope note.
- [x] Produce an installable extension package and record source/tested SHA plus ZIP SHA-256; see the artifact row above. Retain it beyond the seven-day CI artifact window only as part of an approved release.
- [ ] Complete the exact component contract: the production model is not approved; Auth mode, runtime database role and Render-to-Neon branch mapping remain unverified.
- [ ] Pass authenticated staging sign-in and saved-report create/list/read/update/delete, persistence, ownership/isolation, failure-state and cleanup checks on that same pair.
- [ ] Pass the approved AI quality evaluation on the intended, reviewed evaluation cohort; retain model/data provenance and results.
- [x] Verify the effective required GitHub checks and review settings: eight required contexts, strict mode, one approval, latest-push approval and admin enforcement. **Still open:** behavior and independent approval must be proven on a current runtime PR, including expected label/skip handling and a deliberately failing required check.
- [ ] Run exact-SHA deployment smoke and verify the disabled model state. The smoke workflow currently attempts synthetic inference when enabled; a local follow-up adds a read-only, zero-inference path when analysis is intentionally disabled. It is not in `main` yet, and the current audit client received HTTP 403 from production endpoints.
- [ ] Rehearse application rollback to a schema/config-compatible target in staging and record the exact identities, steps and result.
- [x] Restore a manual Neon snapshot into a separate, expiring branch and compare aggregate data/schema integrity; see [the dated recovery drill](recovery-drill-2026-11-20.md). **Still open:** production branch protection and scheduled snapshots are blocked by the free plan; full RTO/RPO remain unproven.
- [ ] Publish a versioned release and changelog only after all preceding evidence passes.

## Migration compatibility evidence

The [November 15 disposable-PostgreSQL report](../migration-compatibility-recovery-2026-11-15.md)
records repeatable upgrades through `0004_neon_auth_subject`, preservation of a
synthetic legacy row across `0003` to `0004`, and **11 passing saved-report CRUD
tests** from pre-Neon-Auth backend revision `270b7db` against schema `0004`.
This is useful local compatibility evidence for the covered migration and CRUD
paths. It does not establish compatibility of the current production
predecessor, hosted schema/configuration, application rollback, or Neon restore.
Keep the rollback and isolated hosted-restore acceptance items above open until
those exact-environment checks are completed and recorded.

The current release issue remains the source for team sign-off. Update this
record only with evidence tied to exact component identities; a planned action,
green unrelated check or skipped deployment job does not satisfy an item.
