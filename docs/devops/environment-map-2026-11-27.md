# PhishLens environment and artifact map — 2026-11-27 08:22 UTC

This is a read-only configuration snapshot captured at the stated time. Secret values and product data were
not read or copied. GitHub variable comparisons report match/no-match only.
Render service configuration is limited to control-plane metadata; the dashboard
does not expose runtime variable values through this check.

## Candidate mapping

| Layer | Staging target | Production target | Evidence and state |
|---|---|---|---|
| Git source | PR #268 integrated head `9039d1a490d283cc7bcca9243aa02b705036a7dd`; current #281 `0c48cbf240b963a35b5e4669417e118d5ea6573b`; current #282 `3131dae6f09c30b267ca4aa7b864694a44fd744c` | `main` at `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | #268 contains current #281 then current #282. Its first exact-head CI failed in a test import; fresh checks are required after the correction. See [PR alignment](pr-alignment-2026-11-27.md). |
| Render service | `phishlens-staging`, `srv-db92irlg1s2s739404i0`, `https://phishlens-staging.onrender.com`; Git-backed Python, Auto Deploy off | `phishlens-api`, `srv-db7eap25b2lc73fkelpg`, `https://phishlens-api-ocvt.onrender.com`; Git-backed Python, Auto Deploy off | Trusted run `45958860400` deployed and accepted old PR #268 SHA `554fd223` on staging. That run has no backend image digest and is not the integrated head. Production metadata remains on `811980c` (2026-11-22); no image digest is deployed. |
| Neon project/branch | Project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, expected host `ep-winter-wind-a1y2r1db.ap-southeast-1.aws.neon.tech`, application database `phishlens_dev` | Project `patient-bird-25428852`, branch `br-orange-sky-b3zzzyqc`, expected host `ep-dawn-band-b37l1bil.c-4.ap-southeast-1.aws.neon.tech` | Non-secret GitHub environment variables match these identities. The isolated staging branch was independently checked by trusted staging runs; PR #268/#282 report branch `br-rough-sea-a1l6ehi1`. No production database was queried. |
| Database roles/schema | Runtime role `phishlens_staging_app`; migration role `neondb_owner`; schema-only root; prior accepted migration revision `0005_ai_request_quota` | Production identities are separate | Run `45958860400` verified the isolated staging target and completed Auth/CRUD on old SHA `554fd223`; integrated SHA `9039d1a` passed Neon preflight `45963430015` but never reached product acceptance because CI failed. `STAGING_MIGRATION_DATABASE_URL` is absent from `staging-neon-preflight`; do not reuse any credential pasted into chat. |
| Neon Auth | `https://ep-winter-wind-a1y2r1db.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth`; database `neondb`; staging API origin `https://phishlens-staging.onrender.com` | Separate production Auth and database values are configured at repository scope; they were not printed | The staging Auth URL/database variables match the approved staging endpoint; Auth sign-in passed on earlier exact-head candidates, not the current #268/#282 heads. This does not authorize production Auth acceptance. |
| Extension | Auth-enabled package built per candidate; Chrome extension ID `ceneonaedddlkdocdapimkfggbjcchlb`; trusted origin `chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb` | Production default points to the production API/Auth | Accepted old #268 ZIP SHA-256: `7d7082e1e1bc5f3c0fd0c89d8e1d85bb4ec0b3180cd19602cd87d322b955dccd`, bound to source/backend SHA `554fd223`. It does not identify the integrated candidate. |
| AI model/provider | Staging analysis/evaluation is still gated by release approval | Production `/model-info` returned 200 with `provider_mode=disabled`, `analysis_enabled=false`, and `accepts_tfidf_reports=false` | AI owner policy/representative holdout approval is absent. Do not reuse Wilbert’s historical English advisory result as current release approval. |

## GitHub controls and credential scopes

| Environment | Required reviewer / ref control | Current credential or configuration state |
|---|---|---|
| `staging-neon-preflight` | `xxTrixia`; self-review disabled; admin bypass disabled; only `main` | `NEON_API_KEY` is present; schema-only attestation is `true`; production-row attestation is `false`; migration URL secret is missing. |
| `release-staging` | `xxTrixia`; self-review disabled; admin bypass disabled; only `main` | `RENDER_STAGING_API_KEY` is present; `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is `pending`; provider and model revision variables are empty; do not dispatch promotion until the mapping is privately verified and model evidence is approved. |
| `staging` | `xxTrixia`; self-review disabled; admin bypass disabled; only `main` | Acceptance enabled and trusted extension origin match. Synthetic A/B account credentials are present. The Render deploy key has been removed from this environment. `STAGING_AI_APPROVAL_JSON` is absent. |
| `production` | `inaki3023`; self-review disabled; admin bypass disabled; protected branches only | The environment has no variables or secrets, and the repository has no `RENDER_PRODUCTION_API_KEY` or `RENDER_PRODUCTION_SERVICE_ID`. `RELEASE_PROMOTION_ENABLED` and `PRODUCTION_RELEASE_CONFIG_ATTESTATION` are not configured. Production promotion cannot pass. |

The classic `main` branch-protection endpoint and active ruleset `#27733591`
currently agree on eight strict required contexts: Backend checks, Extension
checks, Staging integration, CodeQL, Secretary staging, Deterministic AI
Evaluation, Dependency security, and Workflow lint. Main requires a pull request,
one approval including latest-push approval, stale-review dismissal, and no admin
bypass. A deliberately failing required check has not been demonstrated as a
merge-blocking experiment.

## Fresh public-service observations

At 2026-11-27 07:14 UTC, Render metadata showed the deploy identities above and
Auto Deploy off for both services. Around 07:16 UTC, production `/model-info`
returned HTTP 200 with analysis disabled. Read-only `/health`, `/ready`, and
`/version` requests timed out after 15 seconds from this client. No product data,
inference, or authenticated production request was made.

The GitHub `production` environment is protected; Render separately reports its
Production service environment as unprotected. The public API allowlist is
`0.0.0.0/0` and Render network isolation is off, consistent with a client-facing
API endpoint. This is not evidence that GitHub deployment credentials were
exposed. No production service setting was changed.

## Remaining mapping gates

1. A service owner must privately attest that Render staging's runtime, migration,
   and Auth settings use this approved Neon target and correct least-privilege
   roles. The release-specific attestation remains `pending` even though earlier
   exact-head staging acceptance passed.
2. Provision a fresh migration-only database URL in `staging-neon-preflight`;
   never reuse a credential from chat or copy the runtime role.
3. Have the AI owner approve the policy and representative holdout, then record
   the exact immutable provider/model identity and protected report.
4. Configure the Render services for the approved immutable image flow only
   through a reviewed service-owner change. Keep production untouched until the
   exact image, staging acceptance, post-deploy checks, and independent approval
   are all ready.
5. Provision production promotion variables/credentials only after the service
   mapping and image-backed release path exist. Keep issue #153 NO-GO in the
   meantime.

See [the 2026-11-27 rubric crosswalk](devops-rubric-readiness-2026-11-27.md),
[controlled release record](controlled-release.md), and
[current DORA report](dora-report-2026-11-27.md) and
[PR alignment record](pr-alignment-2026-11-27.md).
