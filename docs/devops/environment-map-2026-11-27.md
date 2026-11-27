# PhishLens environment and artifact map — 2026-11-27 14:35 UTC

This record combines the 14:32–14:33 UTC public read-only service probes, the
14:35 UTC DORA/main snapshot, exact staging acceptance run 45999893591
(completed 12:40 UTC), and GitHub/Render control-plane metadata last read at
10:11–10:12 UTC. No secret values or production product data were read.

## Current source and deployment identities

| Layer | Staging | Production | Finding |
|---|---|---|---|
| Git source | Live SHA `131d282222361a6d29601f90a2930445ee4a61cf`; exact authenticated acceptance passed in [run 45999893591](https://github.com/kendshhh/PhishLens/actions/runs/45999893591). | Live SHA `811980c2cbf70d9957146bf329627f0826a018f1`; current GitHub `main` is `fd23b186ad85f9d33e7f80dec03f09d9b7005403`. | `main` and accepted candidate differ only in docs/schema-guide files; no application/migration source changed. Release provenance must still rebuild/bind the exact main SHA. |
| Render service | `phishlens-staging`, `srv-db92irlg1s2s739404i0`, `https://phishlens-staging.onrender.com`, Git-backed; Auto Deploy off in 10:11 metadata. | `phishlens-api`, `srv-db7eap25b2lc73fkelpg`, `https://phishlens-api-ocvt.onrender.com`, Git-backed; Auto Deploy off in 10:11 metadata. | At 14:33 both health and readiness returned 200; staging DB connected. Render reports its Production environment unprotected, so the GitHub production environment does not by itself prove Render-side protection. |
| Neon database | Project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, database `phishlens_dev`; schema-only branch. | Project `patient-bird-25428852`, branch `br-orange-sky-b3zzzyqc`; expected host `ep-dawn-band-b37l1bil.c-4.ap-southeast-1.aws.neon.tech`. | Protected staging run verified isolated staging project/branch, migration `0005_ai_request_quota`, and no production requests/writes. No production DB was queried. |
| Runtime roles/Auth | Staging Auth mode `neon-auth`; A/B sign-in succeeded; runtime and migration role identities were validated in the protected acceptance path. | Production Auth was not exercised. | Current production Auth mapping and least-privilege/access controls are not re-attested. |
| Extension artifact | ZIP SHA-256 `376b26a4de0307c00b331d2e66ea4caf363ab8347c8a037df83e1a8b22ffeb08`; exact candidate SHA `131d282`. | No approved production package/release artifact. | ZIP hash was independently verified after downloading the run artifact. The 14.8 MB ZIP was not committed; GitHub artifact retention is through 2026-12-04, so this is not durable release storage. |
| Model/provider | TF-IDF revision `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`; staging product run passed; AI quality blocked (`approval_not_provided`). | `/model-info` reports provider disabled and analysis disabled. | Wilbert's 190/200 historical English phishing result, 1/1,000 legitimate false alerts and 1,200 valid outputs supports advisory use on that historical cohort only; it does not approve current model quality. |

## Read-only live probes — 2026-11-27 14:32–14:33 UTC

| Service | `/health` | `/ready` | `/version` | `/model-info` |
|---|---|---|---|---|
| Production | 200, `ok` | 200, DB connected | `811980c2cbf70d9957146bf329627f0826a018f1` | 200, `provider_mode=disabled`, `analysis_enabled=false`, required provider unsupported |
| Staging | 200, `ok` | 200, DB connected | `131d282222361a6d29601f90a2930445ee4a61cf` | 200, TF-IDF revision `a2f13c…`; see acceptance report for complete digest |

Machine-readable responses are in
[`evidence/live-endpoint-probe-2026-11-27-1432z.json`](evidence/live-endpoint-probe-2026-11-27-1432z.json).
These were unauthenticated GETs to health/readiness/version/model-info only.
The exact staging Auth/CRUD journey is separately recorded in
[`evidence/2026-11-27-staging-acceptance-131d282.md`](evidence/2026-11-27-staging-acceptance-131d282.md).

## GitHub and Render control-plane state

The following reviewer, ruleset, service and secret-name inventory was read at
10:11–10:12 UTC; it was not re-read during the public endpoint probe. Secret
values were not read.

| Environment | Previously verified protection | Missing/unverified inputs from last name-only inventory |
|---|---|---|
| `staging-neon-preflight` | Reviewers `xxTrixia` and `kendshhh`; self-review off; main-only refs. | `STAGING_MIGRATION_DATABASE_URL` absent; verify it is a fresh least-privilege migration credential before use. |
| `release-staging` | Reviewers `xxTrixia` and `kendshhh`; self-review off; main-only refs. | `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION`, `STAGING_RELEASE_PROVIDER`, and `STAGING_RELEASE_MODEL_REVISION` absent. |
| `staging` | Reviewers `xxTrixia` and `kendshhh`; self-review off; main-only refs; synthetic acceptance credentials present by name. | `STAGING_AI_APPROVAL_JSON` absent because AI-owner approval has not been supplied. |
| `production` | GitHub environment reviewer `inaki3023`; self-review off. | Production release variables/credentials absent from inventories; a second independent reviewer and Render-side protection are not evidenced. |

At 10:11 UTC, classic branch protection and active ruleset `#27733591` agreed
on eight strict contexts: Backend checks, Extension checks, Staging integration,
CodeQL, Secretary staging, Deterministic AI Evaluation, Dependency security,
and Workflow lint. One approval including latest-push approval and stale-review
dismissal are enabled. A deliberate negative check-to-merge-blocking experiment
has not been recorded.

## Remaining closure items

1. Platform owner privately re-attests Render runtime, migration and Auth
   mappings against the approved staging Neon branch; create/provision a fresh
   migration-only credential through the protected environment.
2. Configure a supported image-backed Render path; retain one backend image
   digest and extension ZIP durably; bind exact source, schema, model, Auth,
   staging evidence and changelog in the release manifest.
3. Obtain Wilbert/AI-owner threshold approval plus a permitted representative
   holdout with independent labels, overlap review and exact model provenance.
4. Configure protected production deployment authority and require exact-SHA
   health, readiness, model/provider, and product acceptance after promotion.
5. Rehearse compatible app rollback and fresh isolated Neon restore; measure
   approved RTO/RPO and test alert delivery with named primary/backup responders.
6. Keep issue #153 **NO-GO** until the above evidence exists. Never infer
   production safety from a staging pass or health endpoint.
