# PhishLens environment and artifact map — 2026-11-27 08:45 UTC

This is a read-only configuration snapshot captured at the stated time. Secret values and product data were
not read or copied. GitHub variable comparisons report match/no-match only.
Render service configuration is limited to control-plane metadata; the dashboard
does not expose runtime variable values through this check.

## Candidate mapping

| Layer | Staging target | Production target | Evidence and state |
|---|---|---|---|
| Git source | PR #268 exact-head candidate `d77491d8fd91252190755714df8e5fa475e9c13b`; current #281 `0c48cbf240b963a35b5e4669417e118d5ea6573b`; current #282 `3131dae6f09c30b267ca4aa7b864694a44fd744c` | `main` at `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` | Exact-head CI and protected authenticated staging acceptance passed for #268 `d77491d` in run `45966647832`; the pass is for this PR SHA only. See [PR alignment](pr-alignment-2026-11-27.md) and [acceptance evidence](evidence/2026-11-27-staging-acceptance-d77491d.md). |
| Render service | `phishlens-staging`, `srv-db92irlg1s2s739404i0`, `https://phishlens-staging.onrender.com`; Git-backed Python, Auto Deploy off | `phishlens-api`, `srv-db7eap25b2lc73fkelpg`, `https://phishlens-api-ocvt.onrender.com`; Git-backed Python, Auto Deploy off | Trusted run `45966647832` deployed exact #268 SHA `d77491d` to staging; health, readiness, `/version`, Auth bridge, and accepted CRUD journey passed. `backend_image_digest` is null: this is a Git-backed deployment, not immutable image promotion. Production metadata snapshot remains on `811980c` (2026-11-22); the controller did not query production. |
| Neon project/branch | Project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, expected host `ep-winter-wind-a1y2r1db.ap-southeast-1.aws.neon.tech`, application database `phishlens_dev` | Project `patient-bird-25428852`, branch `br-orange-sky-b3zzzyqc`, expected host `ep-dawn-band-b37l1bil.c-4.ap-southeast-1.aws.neon.tech` | Non-secret GitHub environment variables match these identities. The isolated staging branch was independently checked by trusted staging runs; PR #268/#282 report branch `br-rough-sea-a1l6ehi1`. No production database was queried. |
| Database roles/schema | Runtime role `phishlens_staging_app`; migration role `neondb_owner`; schema-only root; candidate migration revision `0005_ai_request_quota` | Production identities are separate | Trusted Neon preflight and the accepted staging run verified the candidate target and migration revision without querying production rows. GitHub migration URL credentials remain incomplete for the separate image-promotion workflow; that missing release credential does not negate the successful Render staging acceptance. Never reuse a credential pasted into chat. |
| Neon Auth | Staging endpoint on the approved Neon project; database `neondb`; API origin `https://phishlens-staging.onrender.com` | Separate production Auth and database values are configured at repository scope; they were not printed | Exact-head staging run verified the live Auth bridge and successful A/B sign-in. This does not authorize production Auth acceptance or reveal hosted values. |
| Extension | Auth-enabled package built per candidate; Chrome extension ID `ceneonaedddlkdocdapimkfggbjcchlb`; trusted origin `chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb` | Production default points to the production API/Auth | Accepted #268 ZIP SHA-256 `495d9bb7d3a222b103a30de819f6a0e7c8d4c9844e9120c24b9d6f4a4b47bdb7`, bound to source/backend SHA `d77491d`. Run `45966647832` installed this exact package during staging acceptance. |
| AI model/provider | Staging candidate reported TF-IDF model revision `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`; model-quality gate remains blocked | Last production `/model-info` snapshot reported analysis disabled | AI owner policy/representative holdout approval is absent; run `45966647832` records `approval_not_provided`. Do not reuse Wilbert’s historical English advisory result as current release approval. |

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
