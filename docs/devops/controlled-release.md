# Controlled PhishLens release path

Status as of 2026-11-25: the controlled-release workflow exists on `main`; its
latest hardening and evidence updates are on a review branch. There is no
accepted current-candidate product run, no version tag, and no release
authorization. Keep issue #153 at NO-GO. Do not dispatch production promotion
until the external setup below is complete.

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

The review branch replaces the PR-triggered `Hosted staging` job with a trusted
`workflow_run` controller. The controller is defined on the default branch,
verifies the current PR head and required check results, and separates the
Render deployment job from PR-source acceptance. The authenticated browser
runner uses default-branch test code and dependencies; it only loads the ZIP
built from the exact PR head. The status mirror does not write runtime results,
leaving the trusted controller as the sole `Secretary staging` writer for
runtime changes. The PR CI workflow no longer maps deployment credentials or
staging-account passwords. The stable required
`Secretary staging` status remains pending for runtime changes until the
trusted controller reports successful exact-head acceptance; a missing or
skipped acceptance job cannot be reported as success.

The live `staging` environment now permits `main` only, so the old PR-ref job
cannot request its secrets. This intentionally pauses the old PR-triggered
staging path during migration. The controller is not active until the review
branch is merged, and `release-staging` has no Render key or migration/AI
secrets. Its approved-target mapping variables are present, but the mapping
attestation remains pending. No current PR has authenticated acceptance from the new
controller. Rejected or previously queued runs are not evidence for a newer
head. See [staging procedure](staging.md) for current prerequisites and the
separate release-quality gate.

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
check on 2026-11-25 found production service
`srv-db7eap25b2lc73fkelpg` Git-backed to `main` with
`autoDeploy=no` / `autoDeployTrigger=off`; staging service
`srv-db92irlg1s2s739404i0` is also Git-backed with auto-deploy off. The
production auto-deploy stop is verified, but it is an interim control, not
proof of digest-based promotion. The release preflight refuses Git-backed
targets, so promotion remains blocked until both services are configured for
the image-backed path. GitHub staging variables were rechecked without printing
values and now match the selected isolated Neon project `ancient-brook-17208049`,
root branch `br-rough-sea-a1l6ehi1`, database name/role, staging Auth endpoint,
extension origin, and production-separation checks. The main-only
`release-staging` environment has the required non-secret target variables;
its secrets are not provisioned. `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION`
is `pending`, because the masked Render runtime/migration URLs have not been
verified. No current deployment has verified the mapping. The previous Neon
catalog read found no public app tables or Alembic history in this target;
recheck before migrating. Do not treat any queued or historical run as current
acceptance. Render values remain private. Render must be changed by an
administrator, without deploying:

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
4. The GitHub staging variables now use the approved Auth URL/database and
   trusted extension origin. Add the same extension ID as a trusted Neon Auth
   origin in Neon. Configure Render
   staging runtime and migration URLs, database host, branch ID, database name,
    and separate roles to target only the approved branch. The GitHub variable
    `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is currently `pending`; keep it
    pending until the masked Render identity values are verified in an audited
    check. Only then may an administrator change it to `current`. Confirm the
    mapping with a successful exact-candidate staging run before relying on it.
    Staging startup checks the configured mapping before migrating or seeding.
5. `staging` and `release-staging` are configured with xxTrixia as independent
   reviewer, self-review disabled, and `main`-only deployment refs. `production`
   also has independent approval and prevents self-review. Verify these live
   policies again after workflow migration; at least one production reviewer
   must differ from the source author.
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
  `PRODUCTION_NEON_PROJECT_ID`, and `PRODUCTION_NEON_BRANCH_ID`; the staging and
  production project IDs must differ.
- `STAGING_NEON_PARENT_ID` unset/empty and
  `STAGING_NEON_SCHEMA_ONLY_ATTESTATION=true`
- `STAGING_NEON_EXPECTED_HOST`, `PRODUCTION_NEON_EXPECTED_HOST`,
  `STAGING_NEON_DATABASE_NAME`, and `STAGING_NEON_MIGRATION_ROLE`
- `STAGING_NEON_PRODUCTION_ROWS_PRESENT=false`
- `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION=pending` until an administrator
  privately verifies Render's staging runtime and migration URL host, database,
  branch mapping, and app/migration role separation. Set it to `current` only
  after that check.
- `STAGING_AUTH_TRUSTED_CHROME_ORIGIN=chrome-extension://<release-extension-id>`
- `RENDER_STAGING_SERVICE_ID`
- `PHISHLENS_STAGING_AUTH_URL` and `PHISHLENS_STAGING_AUTH_DATABASE`

For the PR-required `staging` environment, duplicate the isolated project,
branch, endpoint, production-identity, and Auth mapping variables above and
configure `STAGING_BASE_URL`, `SECRETARY_STAGING_DB_HOST`,
`SECRETARY_PRODUCTION_DB_HOST`, `STAGING_ACCEPTANCE_ENABLED=true`, and
`RENDER_STAGING_SERVICE_ID`. Its protected secrets are `RENDER_STAGING_API_KEY`,
`NEON_API_KEY`, and the two dedicated synthetic Auth account email/password
pairs. The Render staging service must set `NEON_AUTH_BASE_URL` to exactly the
same isolated Auth URL as `PHISHLENS_STAGING_AUTH_URL`; the hosted deploy
preflight checks this mapping. The hosted PR workflow does not receive
`STAGING_AI_APPROVAL_JSON`.

In `production`:

- `RENDER_PRODUCTION_SERVICE_ID`
- `RELEASE_PROMOTION_ENABLED=true`
- `PRODUCTION_RELEASE_CONFIG_ATTESTATION=current`, set only after an
  administrator has privately verified production Auth, database mapping,
  environment mode, provider identity, and runtime roles.

GitHub-protected environment secrets:

- `release-staging`: `RENDER_STAGING_API_KEY`, `NEON_API_KEY`,
  `STAGING_MIGRATION_DATABASE_URL`, `STAGING_AI_APPROVAL_JSON`,
  `STAGING_AUTH_USER_A_EMAIL`, `STAGING_AUTH_USER_A_PASSWORD`,
  `STAGING_AUTH_USER_B_EMAIL`, `STAGING_AUTH_USER_B_PASSWORD`.
- `production`: `RENDER_PRODUCTION_API_KEY`.

The existing staging environment credentials are scoped only to `staging`;
GitHub does not expose their values for copying. Provision separate credentials
in `release-staging` after confirming the mapping. That protected environment
now has the approved non-secret target variables, but no secrets, so its
workflow still fails closed before migration or deployment until the required
credentials are provisioned.

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
Until the protected staging flow passes live Auth and persistent CRUD, criterion
pp. 3/49 remains blocked. That product pass alone does not approve model quality
or authorize a release. The release remains NO-GO until the AI owner approves the
quality policy/report, the protected release workflow accepts it, and Render is
image-backed for digest promotion.
