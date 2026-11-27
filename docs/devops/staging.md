# Staging and candidate acceptance

**Status as of November 27, 2026 08:22 UTC:** authenticated staging acceptance
passed on prior PR #268 SHA `554fd223ec98852acb12ebca01812530a84fde2d` in
[trusted run 45958860400](https://github.com/kendshhh/PhishLens/actions/runs/45958860400).
It verified Auth sign-in, persistent saved-report CRUD, reload persistence,
ownership, two-account isolation, cleanup, and the exact extension UX. Its
redacted evidence is in
[the 554fd223 record](evidence/2026-11-27-staging-acceptance-554fd223.md).

PR #268 now includes the latest #281 and #282 heads at integrated SHA
`9039d1a490d283cc7bcca9243aa02b705036a7dd`. That SHA's initial Staging
integration and `Secretary staging` checks failed because
`test_hosted_staging_gate.py` referenced an undefined `ROOT`; no hosted
acceptance ran for it. A correction is included in this PR update, but the
resulting exact head still needs fresh CI, protected Neon preflight, reviewer
approval, and hosted authenticated acceptance. The historical pass does not
transfer to that new head. Release remains **NO-GO** because AI-quality approval
and production promotion/recovery gates remain open.

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

The live `staging` and `release-staging` environments permit deployments from
`main` only and do not allow administrator bypass. Both have required reviewers
`xxTrixia` and `kendshhh`; self-review prevention is enabled, so the deployment
author cannot approve their own run. The `staging` environment retains its
non-production Auth test credentials, while `release-staging` contains the
`RENDER_STAGING_API_KEY` secret name. Secret values were not read. Presence is
not proof the key works; only a successful protected deploy can establish that.
Do not copy a masked value through chat or logs.

These controls preserve the required context name `Secretary staging`; they do
not add or rename required checks. The latest GitHub ruleset read shows active
strict ruleset #27733591 requires the eight CI/staging contexts. Ruleset
#26782191 requires one review and approval of the latest push. Classic branch
protection was not independently verified. `PIPELINE.md` and live settings
should be refreshed whenever these controls change.

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

## Preconditions still required for the integrated candidate

1. Use the approved isolated Neon target project
   `ancient-brook-17208049`, root branch `br-rough-sea-a1l6ehi1`, with no
   `ancient-brook-17208049`, root branch `br-rough-sea-a1l6ehi1`; prior trusted
   run 45958860400 confirmed this schema-only branch and reported no production
   rows for its exact candidate. Reconfirm on the new head.
2. Privately align Render runtime and migration database URLs, database name,
   branch, app/owner roles, and Neon Auth URL with the selected target. Keep
   credentials out of logs and reports. The deploy preflight must verify the
   mapping before Render is changed.
3. Confirm migrations and grants remain safe and compatible with the
   integrated backend. The accepted prior candidate reported migration
   revision `0005_ai_request_quota`; verify the exact new head before acceptance.
4. Current protected workflow configuration must require independent
   xxTrixia approval and `main`-only deployment refs. Confirm that this is
   still true for the new run; never approve a stale SHA.
5. Keep secret values private. The prior successful run proves its test
   accounts authenticated against the selected staging Auth path, but does not
   validate production credentials or imply model-quality approval.
6. Run the trusted workflow for the current PR head. A prior head, a queued
   stale deployment, or a previous run's artifact is not evidence for the
   current candidate.

The prior staging run did perform a staging deployment, migrations/validation,
and synthetic-account CRUD; it reported zero pending cleanup and zero
production requests or writes. No production data access or production deploy
is claimed. A fresh exact-head run is required for the integrated candidate.
