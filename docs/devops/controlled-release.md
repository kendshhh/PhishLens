# Controlled PhishLens release path

Status snapshot at 2026-11-27 08:22 UTC: issue #153 remains **NO-GO**. Trusted
hosted Auth/CRUD and extension acceptance passed on prior PR #268 SHA
`554fd223ec98852acb12ebca01812530a84fde2d` in run
`45958860400`; redacted evidence is in
[the acceptance record](evidence/2026-11-27-staging-acceptance-554fd223.md).
It reported AI quality blocked and no backend image digest. Current integrated
PR #268 SHA `9039d1a490d283cc7bcca9243aa02b705036a7dd` passed trusted Neon
preflight, but its initial `Staging integration` run failed because
`test_hosted_staging_gate.py` referenced undefined `ROOT`; `Secretary staging`
failed as a result. The path correction is part of this PR update, and fresh
exact-head checks plus protected staging are still required. Current #281 is
`0c48cbf240b963a35b5e4669417e118d5ea6573b`, current #282 is
`3131dae6f09c30b267ca4aa7b864694a44fd744c`; both are integrated in order into
#268. No production release, version tag, or authorization exists. Render Auto
Deploy is off, but both services remain Git-backed and no tested image has been
promoted. Do not dispatch production promotion.

See the current [environment map](environment-map-2026-11-27.md),
[rubric crosswalk](devops-rubric-readiness-2026-11-27.md), and
[PR alignment record](pr-alignment-2026-11-27.md) for live identities, current
branch relationships, and remaining criteria.

## What the workflow does

`.github/workflows/release-promotion.yml` is manual-only and rejects any ref
other than the current `main` SHA. It finds the unique merged PR for that main
commit, verifies the PR head and merge commit have the same Git tree, then
requires the existing eight protected check names and expected GitHub App
identities to pass on the exact tested PR head. `Secretary staging` is read
from its commit-status API because it is not a check-run; an explicit Secretary
N/A is recorded as such, and the protected release-staging acceptance still
has to pass before production. The required context names remain pinned in
`scripts/release_readiness.py` and its tests. CI also builds the backend
Dockerfile without publishing it. The release workflow then builds one
linux/amd64 backend image and one Auth-enabled extension ZIP, records their
immutable digests, and carries those artifacts through the same workflow run.
The backend image is pushed to GHCR; the extension ZIP remains a workflow
artifact until a successful release publishes that exact ZIP.

The trusted `workflow_run` controller is active on the default branch. It
verifies the current PR head and required check results, then separates the
Render deployment from PR-head acceptance. The required `Secretary staging`
status is emitted only after successful exact-head authenticated acceptance;
a skipped or missing acceptance cannot be a success. Run #282 passed this
path on its recorded head. Each later PR head needs its own run and approval.

The release-promotion workflow separates authority across three protected
environments: `staging-neon-preflight` verifies isolated Neon metadata and
migrates only the attested schema-only branch; `release-staging` uses the
Render staging credential to deploy the image digest; and `staging` runs the
authenticated extension acceptance with synthetic accounts and the reviewed
AI report. All three require xxTrixia, prevent self-review, and permit only
`main`; production remains a separate protected environment with independent
review. The workflow verifies these settings before using each environment.
Render staging still has to be configured for the image-backed service, and
the pending/missing variables and secrets below must be provisioned before a
release dispatch can pass. See [staging procedure](staging.md) for the current
PR path and the separate release-quality gate.

Neon validation reads branch/endpoint metadata only and refuses an unexpected
project, branch, host, parent, production branch, or production-row attestation.
Migrations run only after that validation. Render staging receives the exact
image digest. Chromium installs the exact ZIP and performs real Neon Auth
sign-in plus persistent create/list/read/update/delete, reload persistence,
two-account isolation, ownership checks, cleanup, and extension
loading/success/auth/API/timeout checks. Production API and Auth origins are
monitored; any request to them blocks acceptance. Model approval is validated
against the frozen policy and exact provider/model identity; missing or weak
evidence fails the run.

The model-quality policy in `docs/devops/release-quality-policy.json` has
provisional floor values, but its approval state is deliberately `pending`.
Those values are not represented as AI-owner-approved thresholds. An AI/model
owner must review and approve the policy in a reviewed change, record the reviewer,
timestamp, and GitHub review record, then supply a report bound to the resulting
policy digest. The report must include a representative held-out cohort, blind
label review, clear overlap review, immutable model identity, and measured metrics.
Until then model quality is BLOCKED, even if the product acceptance and live
inference request pass.

Production promotion is a separate opt-in input. After approval it rechecks
that the release SHA is still current `main` and that the version tag is still
unused. It waits on the protected
`production` environment, verifies that the environment approval is independent
of the source author, revalidates the machine-readable manifest, and checks the
public provider identity before deploying. Render must be configured as an
image-backed service; the workflow deploys the same backend digest tested in
staging. It then checks the production deploy identity, `/version`, `/health`,
`/ready`, and `/model-info`. It does not perform production CRUD or read
production product rows. The accepted product journey is the staging journey
bound to the same extension ZIP and backend image digest. A production
authenticated journey remains unverified until an approved isolated production
test database/account exists; the current no-production-data constraint forbids
using live product records to satisfy that check.

Only after all gates pass does the workflow publish the matching version tag,
GitHub release, changelog notes, ZIP, provenance, and release manifest. It does
not close issue #153. Release ownership must update the issue only after the
published evidence supports GO.

## External setup required

These service settings are not changed by this pull request. A read-only Render
check on 2026-11-27 found production service
`srv-db7eap25b2lc73fkelpg` Git-backed to `main` with
`autoDeploy=no` / `autoDeployTrigger=off`; its live deploy is still SHA
`811980c2cbf70d9957146bf329627f0826a018f1`. Staging service
`srv-db92irlg1s2s739404i0` is also Git-backed with auto-deploy off. Trusted
staging run `45958860400` deployed and accepted prior PR #268 SHA `554fd223`
on the isolated staging target; this does not establish the current integrated
head and produced no backend image digest. The production auto-deploy stop is
verified, but it is an interim control, not proof of
digest-based promotion. The release preflight refuses Git-backed targets, so
promotion remains blocked until both services are configured for the
image-backed path. GitHub settings were rechecked and the required
non-secret staging variables were aligned on 2026-11-27 without printing
values. `staging-neon-preflight` has the selected Neon target identities,
database/role names, and metadata key, but no migration URL secret.
`release-staging` has its Render key and an explicit `pending` mapping
attestation; provider and model revision variables are empty. `staging` has the
two Auth test accounts and its acceptance flag/origin, but no AI approval
report. The GitHub `production` environment has no variables/secrets; the
production Render key, service ID, release enable flag, and production
configuration attestation are not provisioned. The current Render services are
still Git-backed, so no image promotion or production release is possible. Do
not treat a queued or historical run as current acceptance. Render values
remain private. Render must be changed by an administrator, without deploying:

1. Keep production Git auto-deploy off. Convert staging and production to
   prebuilt-image services configured for `ghcr.io/kendshhh/phishlens-api` and
   configure Render to pull the private GHCR package. Set service environments
   and secrets to the correct branch-specific values without copying production
   product data into staging. Changing an existing Render service's backing
   source triggers a deployment; schedule and approve that transition or
   provision an image-backed replacement service. Do not switch the live
   production service during this PR.
2. Configure the image service's migration procedure and runtime database role.
   Staging migration credentials must be separate from the app role. The
   production schema migration must follow the team's reviewed expand/contract
   procedure; this workflow never reads or copies production product rows.
3. Use only the approved Neon project `ancient-brook-17208049` and independent
   root branch `br-rough-sea-a1l6ehi1` for staging. Earlier read-only catalog
   inspection reported no public application tables or Alembic revision there;
   recheck that state, verify the `phishlens_dev` and `neondb` databases/roles,
   and apply migrations and least-privilege grants only after confirming the
   Render mapping. Do not use the older `hidden-shadow` target, a production
   project branch, or a restored production snapshot.
4. GitHub's production/staging Auth URL and database variables are configured.
   The staging extension-origin variable is tied to the pinned package identity.
   Neon Auth must still be verified to trust that same extension ID. Configure
   Render staging runtime and migration URLs, database host, branch ID, database
   name, and separate roles to target only the approved branch. The GitHub
   variable `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is currently `pending`;
   keep it pending until the masked Render identity values are verified in an
   audited check. Only then may an administrator change it to `current`. Confirm
   the mapping with a successful exact-candidate staging run before relying on
   it. Staging startup checks the configured mapping before migrating or seeding.
5. On 2026-11-27, `staging-neon-preflight`, `staging`, and `release-staging`
   were verified with xxTrixia as independent reviewer, self-review disabled,
   administrator bypass disabled, and `main`-only deployment refs. `production`
   has independent approval, self-review disabled, administrator bypass
   disabled, and protected-branch-only deployment. The workflow rechecks these
   settings. At least one production reviewer must differ from the source author.
6. Configure the exact variables and secrets below. Never put credential values
   in the repository, workflow logs, screenshots, or evidence JSON.
7. Review and approve a held-out model evaluation report meeting its stated
   thresholds. Current production reports `AI_ANALYSIS_ENABLED=false`; do not
   turn it on until the provider identity, evaluation approval, and bounded
   spend controls are established.

### Configuration scopes used by the release workflow

Public build configuration is stored as repository variables and is available
to the artifact-building job:

- `PHISHLENS_PRODUCTION_AUTH_URL`
- `PHISHLENS_PRODUCTION_AUTH_DATABASE`
- `PHISHLENS_STAGING_AUTH_URL`
- `PHISHLENS_STAGING_AUTH_DATABASE`

`staging-neon-preflight` is the only release job scope that receives Neon
metadata and migration authority. It needs `STAGING_NEON_PROJECT_ID`,
`STAGING_NEON_BRANCH_ID`, `STAGING_NEON_EXPECTED_HOST`,
`STAGING_NEON_SCHEMA_ONLY_ATTESTATION=true`,
`STAGING_NEON_PRODUCTION_ROWS_PRESENT=false`,
`PRODUCTION_NEON_PROJECT_ID`, `PRODUCTION_NEON_BRANCH_ID`, and
`PRODUCTION_NEON_EXPECTED_HOST`. It also needs `STAGING_NEON_DATABASE_NAME`,
`STAGING_NEON_MIGRATION_ROLE`, and no/empty `STAGING_NEON_PARENT_ID`. Current
live scope inspection found the staging and production project/branch IDs,
staging and production expected hosts, schema-only and no-production-row
attestations, database name, and migration role. Its configured secret is
`NEON_API_KEY`; `STAGING_MIGRATION_DATABASE_URL` is still missing and must be
provisioned as a new least-privilege migration credential. Do not reuse any
credential pasted into chat or a runtime app credential.

`release-staging` is the only release job scope that receives
`RENDER_STAGING_API_KEY`; the repository-level `RENDER_STAGING_SERVICE_ID` is
available. `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is explicitly `pending`
until an administrator privately verifies Render's runtime and
migration host, database, branch, and app/migration role separation. Only then
change it to `current`. Add `STAGING_RELEASE_PROVIDER` and
`STAGING_RELEASE_MODEL_REVISION` only after the AI owner approves the exact
provider/model report; the revision must be immutable. These release variables
are currently absent. Never put Neon credentials or synthetic account
passwords in this environment.

`staging` is the acceptance scope. Its `STAGING_ACCEPTANCE_ENABLED=true` and
`STAGING_AUTH_TRUSTED_CHROME_ORIGIN` variables are configured, with the origin
derived from the pinned extension identity. Its isolated Auth URL/database
variables and protected secrets `STAGING_AUTH_USER_A_EMAIL`,
`STAGING_AUTH_USER_A_PASSWORD`,
`STAGING_AUTH_USER_B_EMAIL`, and `STAGING_AUTH_USER_B_PASSWORD` are present.
`STAGING_AI_APPROVAL_JSON` is missing; add it only after the AI owner's policy
and held-out report have been reviewed. The acceptance job receives no Neon
API key, migration URL, or Render deploy key; it gets verified Neon identities
and the migration revision only as outputs from the completed preflight job.

The redundant `RENDER_STAGING_API_KEY` copy has been removed from `staging`
after checking all repository workflows. The key remains in `release-staging`,
where both trusted Render deployment workflows consume it; the authenticated
acceptance environment receives no Render deploy credential. This narrows the
credential scope without changing the key or triggering a deployment.

In `production`:

- `RENDER_PRODUCTION_SERVICE_ID`
- `RELEASE_PROMOTION_ENABLED=true`
- `PRODUCTION_RELEASE_CONFIG_ATTESTATION=current`, set only after an
  administrator has privately verified production Auth, database mapping,
  environment mode, provider identity, and runtime roles.

GitHub-protected environment secrets:

- `staging-neon-preflight`: `NEON_API_KEY`,
  `STAGING_MIGRATION_DATABASE_URL` (missing; provision only after confirming
  the approved database target and migration role).
- `release-staging`: `RENDER_STAGING_API_KEY` (present).
- `staging`: synthetic Auth account email/password pairs (present) and
  `STAGING_AI_APPROVAL_JSON` (missing; requires the AI-owner-approved report).
- `production`: `RENDER_PRODUCTION_API_KEY` (missing as of 2026-11-27).

The `production` GitHub environment currently has no variables or secrets;
repository variables also lack `RENDER_PRODUCTION_SERVICE_ID`,
`RELEASE_PROMOTION_ENABLED`, and `PRODUCTION_RELEASE_CONFIG_ATTESTATION`.
Provision these only after the production image-backed path and its independent
approval are ready; do not enable promotion to the current Git-backed service.

The release workflow remains fail-closed while any listed configuration or
approval evidence is missing. Do not move credentials between scopes by
copying secret values; provision distinct scoped credentials where required.

The Render API key should be scoped to the designated PhishLens services. The
Neon API key is used by the staging job for branch metadata only. Do not grant
this workflow the production database URL or a production data credential.

## Runtime failure switch

The backend's `AI_ANALYSIS_ENABLED=false` setting is the inference kill switch.
It causes `/model-info` to report `disabled` and stops analysis routes before
provider lookup. Backend CI exercises that fail-closed behavior. Keep the switch
off while model/provider approval is absent. A production promotion fails before
deployment if the current public model identity is disabled/unavailable or does
not match the approved provider/model revision. During an incident, stop
promotion and have the release responder set the Render switch off using the
approved dashboard procedure; this PR does not change production settings.

The promotion switch is the conjunction of `promote_production=true`, the
protected `production` environment approval, exact-SHA checks, verified staging
acceptance, and the current production configuration attestation. A failed gate
prevents version tag and release publication.

## Release evidence and limits

The manifest schema is `docs/devops/release-manifest.schema.json`; the runtime
validator is `scripts/release_readiness.py`. Staging evidence records SHA-256
digests and branch/service identities, not passwords, bearer tokens, email
addresses, or report bodies. The staged report records only account subject
hashes and synthetic row IDs are not emitted.

No accepted staging evidence or production promotion has been generated by PR
#281's new release-promotion workflow. Separate trusted hosted runs passed live
Auth, persistent CRUD, isolation, and extension UX for the exact PR #268 and #282
heads; those reports explicitly block AI quality, have no backend image digest,
and do not represent a merged production candidate. CI tests validate the new
gate logic and unpublished backend image build, not promotion or production
acceptance. The release remains NO-GO until the AI owner approves the
quality policy/report, PR #281's protected release workflow passes for the
current exact candidate, Render supports image-digest promotion, and production
post-deploy verification passes.
