# Controlled PhishLens release path

Status as of 2026-11-21: implementation is on a review branch. There is no
current live acceptance evidence for this workflow, no version tag, and no
release authorization. Keep issue #153 at NO-GO. The release path must not be
dispatched as a production promotion until the external setup below is complete.

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

The protected `release-staging` environment is required before the workflow
will access staging credentials. It checks Neon branch metadata and requires a
separate administrator attestation that the branch was created schema-only;
it refuses a branch with a parent, the production branch ID, a production host,
or a production database name. Migrations run only after these checks. Render
staging receives the exact image digest. Chromium then installs the exact ZIP
and performs real Neon Auth sign-in plus persistent create/list/read/update/
delete, reload persistence, two-account isolation, ownership checks, cleanup,
and extension loading/success/auth/API/timeout states. The test account data is
synthetic. Production API and Auth origins are monitored and any request to
them blocks acceptance. The approved model/provider and held-out evaluation are
also required; an unavailable or disabled provider blocks the run.

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

These settings are intentionally not changed by this pull request. A fresh
read-only Render check on 2026-11-21 found production service
`srv-db7eap25b2lc73fkelpg` still Git-backed to `main` with
`autoDeploy=yes` / `autoDeployTrigger=checksPass`; staging service
`srv-db92irlg1s2s739404i0` is also Git-backed, with auto-deploy off. This PR
does not stop the existing production auto-deploy. An administrator must turn
production auto-deploy off in Render before any further main push can be
considered release-controlled. The new release preflight refuses Git-backed
targets, so it cannot promote until both services are converted to the
image-backed path. Render must first be changed by an administrator, without
deploying:

1. Turn production Git auto-deploy off. Convert staging and production to
   prebuilt-image services configured for `ghcr.io/kendshhh/phishlens-api` and
   configure Render to pull the private GHCR package. Set service environments
   and secrets to the correct branch-specific values without copying production
   product data into staging.
2. Configure the image service's migration procedure and runtime database role.
   Staging migration credentials must be separate from the app role. The
   production schema migration must follow the team's reviewed expand/contract
   procedure; this workflow never reads or copies production product rows.
3. Create a fresh, independent Neon root branch with **schema only**, enable
   Neon Auth there, apply current migrations, and create two dedicated empty
   staging users. The current `pr-58-staging` branch derives from a data-bearing
   branch and is not acceptable for this release runner.
4. Add the staging extension ID as a trusted Neon Auth origin and verify that
   Render staging's runtime and migration roles target only the new branch.
5. Configure the protected GitHub environments `release-staging` and
   `production` with required reviewers. Production must prevent self-review;
   at least one production reviewer must be different from the source author.
6. Configure the exact variables and secrets below. Never put credential values
   in the repository, workflow logs, screenshots, or evidence JSON.
7. Review and approve a held-out model evaluation report meeting its stated
   thresholds. Current production reports `AI_ANALYSIS_ENABLED=false`; do not
   turn it on until the provider identity, evaluation approval, and bounded
   spend controls are established.

### Repository variables used by the workflow

Public build configuration:

- `PHISHLENS_PRODUCTION_AUTH_URL`
- `PHISHLENS_PRODUCTION_AUTH_DATABASE`
- `PHISHLENS_STAGING_AUTH_URL`
- `PHISHLENS_STAGING_AUTH_DATABASE`

In `release-staging`:

- `STAGING_ACCEPTANCE_ENABLED=true`
- `STAGING_NEON_PROJECT_ID`, `STAGING_NEON_BRANCH_ID`, and
  `PRODUCTION_NEON_BRANCH_ID`
- `STAGING_NEON_PARENT_ID` unset/empty and
  `STAGING_NEON_SCHEMA_ONLY_ATTESTATION=true`
- `STAGING_NEON_EXPECTED_HOST`, `PRODUCTION_NEON_EXPECTED_HOST`,
  `STAGING_NEON_DATABASE_NAME`, and `STAGING_NEON_MIGRATION_ROLE`
- `STAGING_NEON_PRODUCTION_ROWS_PRESENT=false`
- `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION=current`, set only after checking
  Render's staging runtime and migration URL host, database, branch mapping, and
  app/migration role separation privately.
- `STAGING_AUTH_TRUSTED_CHROME_ORIGIN=chrome-extension://<release-extension-id>`
- `RENDER_STAGING_SERVICE_ID`
- `PHISHLENS_STAGING_AUTH_URL` and `PHISHLENS_STAGING_AUTH_DATABASE`

In `production`:

- `RENDER_PRODUCTION_SERVICE_ID`
- `RELEASE_PROMOTION_ENABLED=true`
- `PRODUCTION_RELEASE_CONFIG_ATTESTATION=current`, set only after an
  administrator has privately verified production Auth, database mapping,
  environment mode, provider identity, and runtime roles.

GitHub-protected environment secrets:

- `release-staging`: `RENDER_API_KEY`, `NEON_API_KEY`,
  `STAGING_MIGRATION_DATABASE_URL`, `STAGING_AI_APPROVAL_JSON`,
  `STAGING_AUTH_USER_A_EMAIL`, `STAGING_AUTH_USER_A_PASSWORD`,
  `STAGING_AUTH_USER_B_EMAIL`, `STAGING_AUTH_USER_B_PASSWORD`.
- `production`: `RENDER_API_KEY`.

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

No accepted staging evidence or production promotion has been generated in this
pull request. CI tests validate gate logic, archive identity and an unpublished
backend image build only. They are not a substitute for a live staging run.
Until the protected environment is configured and the workflow passes with live
Auth, persistent CRUD, and approved model evidence, both requested criteria
remain BLOCKED/NO-GO.
