# Staging and candidate acceptance

**Status as of November 25, 2026:** authenticated staging acceptance has not
passed for a current release candidate. The release remains **NO-GO**. The
trusted-controller changes described below are in the DevOps review branch and
do not become the default-branch workflow until merged.

## Credential boundary

The pull-request CI workflow must run only build, test, lint, and security
checks. It must not request the `staging` or `release-staging` environment and
must not reference Render, Neon, or staging-account credentials. The protected
staging controller runs from the default branch after CI completes. It resolves
the source PR and exact head SHA from GitHub, requires the `needs-hosted-staging`
label, and waits for every predeployment check in `.github/secretary.json` to
pass on that SHA.

The controller uses separate jobs and environments:

- `staging-neon-preflight` verifies the isolated Neon project and branch and
  emits only verified, non-secret identities.
- `release-staging` runs trusted default-branch deployment code with the
  Render credential. It checks the live PR head immediately before requesting
  a deploy. It never checks out or executes PR-authored files.
- `staging` performs acceptance for the deployed candidate. It checks out
  default-branch verification code and the exact PR source separately. The
  candidate source is used only for migration-graph inspection and building
  the extension ZIP; the browser acceptance script and its npm dependencies
  come from the default branch. It gets only the synthetic Auth test-account
  credentials; the Render and Neon deployment credentials are not mapped to
  this job.
- The final `Secretary staging` status becomes green only when inspection,
  protected deployment, and authenticated product acceptance all pass. Any
  failed, skipped, stale, or missing stage produces failure for a runtime PR.
  The workflow-run mirror publishes non-runtime N/A and pre-staging failures;
  it publishes nothing for an eligible runtime PR, so it cannot overwrite the
  trusted controller's final result.

The live `staging` environment now permits deployments from `main` only. This
prevents a PR-authored workflow from requesting its environment secrets. The
existing `RENDER_STAGING_API_KEY` secret is still stored in that environment,
but PR refs are denied by the environment policy. The trusted workflow instead
expects a separately provisioned `RENDER_STAGING_API_KEY` in the main-only
`release-staging` environment. Its non-secret variables now identify the
approved isolated Neon/Auth target, but it has no secrets, so deployment still
fails closed until a new Render key and required Neon migration credentials are
provisioned there. Do not copy a masked value through chat or logs.

These changes preserve the required context name `Secretary staging`; they do
not add or rename required checks. The main branch still must use the same
eight-context strict contract in classic protection and ruleset #27733591.
`PIPELINE.md` and the live settings should be rechecked after the controller is
merged.

## Exact-candidate acceptance

The protected staging run is for a same-repository, non-draft runtime PR with
the opt-in label. Before deployment it requires the current CI run, exact source
SHA, current open PR state, correct base branch, approved staging target, and
the configured security, AI-regression, workflow, integration, backend, and
extension checks. It refuses forks and stale PR heads.

After the exact candidate is live, the acceptance job verifies `/version`,
`/health`, `/ready`, the anonymous Auth challenge, Auth bridge assets, and the
extension identity. It builds the extension ZIP from the exact PR head and
tests sign-in and persistent saved-report create/list/read/update/delete,
reload persistence, cross-user isolation, ownership, cleanup, and visible
loading/success/auth/API/timeout states. It uses synthetic staging accounts and
records redacted evidence with source, backend, package, Neon branch, and
migration identities. No production rows are used. Mock responses and
health-only checks cannot satisfy acceptance.

This product-acceptance gate is separate from AI model-quality approval. The
reported historical English evaluation (190/200 phishing detections, one false
alert in 1,000 legitimate messages, and 1,200 valid outputs) supports advisory
use on that historical cohort only. It is not a current-source holdout or proof
for the release model. Until the AI owner approves a representative, reviewed
holdout and numeric thresholds and the exact model/provider passes them, the
release remains **NO-GO**.

## Artifact promotion boundary

The existing `release-promotion.yml` builds an immutable backend image and
extension ZIP once, and binds them to a release manifest. However, Render's
current production and staging services are Git-backed Python services. No
current evidence shows a backend image digest deployed to staging and promoted
unchanged to production. The release workflow rejects these Git-backed targets.
The same-artifact criterion remains blocked until an administrator provisions
or safely transitions to supported image-backed services, configures the
protected environments, and verifies digest identity in both environments.
Do not switch production during PR review.

## Preconditions still required for a hosted run

1. Confirm the selected isolated Neon target remains project
   `ancient-brook-17208049`, root branch `br-rough-sea-a1l6ehi1`, with no
   production-derived data. The environment attestation is not proof of the
   Render runtime or migration connection strings.
2. Privately align Render runtime and migration database URLs, database name,
   branch, app/owner roles, and Neon Auth URL with the selected target. Keep
   credentials out of logs and reports. The deploy preflight must verify the
   mapping before Render is changed.
3. Confirm migrations and grants are safe and compatible with the current
   backend. The selected database previously had no application tables or
   Alembic history; migration setup is a staging-only operation.
4. Provision a newly issued Render staging key and the remaining protected
   migration/AI/account secrets in `release-staging`. Keep the environment
   restricted to `main` and require independent review with self-review disabled.
5. The GitHub `staging` and `release-staging` variables now point at the
   approved Neon Auth endpoint, database, extension origin, and project/branch.
   `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is `pending` until the masked
   Render runtime and migration settings are privately verified. Confirm the
   two synthetic accounts belong to the approved Auth project, not the older
   `hidden-shadow` project.
6. Run the trusted workflow for the current PR head. A prior head, a queued
   stale deployment, or a previous run's artifact is not evidence for the
   current candidate.

No staging deployment, migration, account write, production data access, or
production deployment is claimed by this document. Offline tests verify the
controller logic; only a successful exact-head hosted run can establish the
live product path.
