# Controlled PhishLens release path

Status refreshed 2026-11-27 14:35 UTC. Issue #153 remains **NO-GO**.

The latest trusted staging acceptance is PR #306 source/backend SHA
`131d282222361a6d29601f90a2930445ee4a61cf`, run
[45999893591](https://github.com/kendshhh/PhishLens/actions/runs/45999893591).
It passed exact-candidate inspection, isolated Neon validation, deployment,
authenticated extension CRUD acceptance, and the required Secretary status.
The installed extension ZIP SHA-256 is
`376b26a4de0307c00b331d2e66ea4caf363ab8347c8a037df83e1a8b22ffeb08`.
The run verified sign-in, persistent CRUD, reload, isolation, ownership,
cleanup, and loading/success/auth/API/timeout UX, with zero production
requests or writes. The current staging `/version` at 14:33 UTC still reports
that accepted SHA. Full evidence is in
[the exact-head record](evidence/2026-11-27-staging-acceptance-131d282.md).

Current `main` is `fd23b186ad85f9d33e7f80dec03f09d9b7005403` (PR #307). A full
Git-tree comparison confirms no application or migration files changed since
the accepted candidate; only `docs/devops/local-backend-verification-2026-11-27.md`
and `docs/schema.md` changed. This supports the product-path result for the
same application/extension code, but the accepted ZIP still embeds PR SHA
`131d282`; a release build must bind fresh exact-main provenance.

Read-only endpoint probes at 14:32–14:33 UTC found production `/health` and
`/ready` HTTP 200 with database connected, `/version` SHA
`811980c2cbf70d9957146bf329627f0826a018f1`, and `/model-info` reporting
`provider_mode=disabled`, `analysis_enabled=false`. Staging returned HTTP 200
for those routes and reported TF-IDF revision
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. The
staging acceptance explicitly records model quality blocked as
`approval_not_provided`; production inference remains disabled. These service
checks did not access production product data.

At 10:11–10:12 UTC, Render metadata still showed both services Git-backed with
Auto Deploy off; the Render Production environment was unprotected. The
repository release workflow has an image-backed digest promotion design, but
no backend image digest or same-digest promotion exists yet. Production
variables/credentials and staging release/migration inputs were missing from
the last secret-name inventory. No production tag/release/changelog,
production exact-SHA product smoke, current-compatible rollback rehearsal,
fresh isolated restore/RTO/RPO, or tested alert delivery is evidenced. Do not
dispatch production promotion or close issue #153.

The current reproducible 28-day DORA report was collected at 14:35 UTC against
main `fd23b18`. It reports a 3.66-minute merge-to-live proxy median (`60/146`
matched), 63 successful deployment records (2.25/day), and 67-second main-CI
median (`n=121`, 119 pass/2 fail). Change failure, failed-deployment recovery,
and rework remain unknown. The measured PR #119 Backend-job improvement is
small-sample (`n=2` each) and not an end-to-end trend. See the
[report](dora-report-2026-11-27.md) and [rubric crosswalk](devops-rubric-readiness-2026-11-27.md).
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
verifies the PR head and required checks, then separates Render deployment from
PR-head acceptance. The required `Secretary staging` status is emitted only
after successful exact-head authenticated acceptance; a skipped or missing
applicable acceptance cannot be a success. The latest completed hosted run,
[45999893591](https://github.com/kendshhh/PhishLens/actions/runs/45999893591),
passed on exact candidate SHA `131d282222361a6d29601f90a2930445ee4a61cf` and
emitted the required status only after product acceptance passed. Its detailed
proof is in [the #306 acceptance record](evidence/2026-11-27-staging-acceptance-131d282.md).
Later current-main differences are documentation-only; the PR candidate's
package digest still embeds its original SHA, so a release must build and
accept a manifest for the exact release SHA.
The release-promotion workflow separates authority across three protected
environments: `staging-neon-preflight` verifies isolated Neon metadata and
migrates only the attested schema-only branch; `release-staging` uses the
Render staging credential to deploy the image digest; and `staging` runs the
authenticated extension acceptance with synthetic accounts and the reviewed
AI report. The three staging environments list `xxTrixia` and `kendshhh`, now
prevent self-review, and permit only `main`; production remains a separate
protected environment with independent review. The workflow verifies these
settings before using each environment. Render staging still has to be
configured for the image-backed service, and the missing variables and secrets
below must be provisioned before a release dispatch can pass. See
[staging procedure](staging.md) for the current
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

These Render services remain Git-backed; control-plane metadata was refreshed
at 10:11 UTC. The production service is
`srv-db7eap25b2lc73fkelpg` Git-backed to `main` with
`autoDeploy=no` / `autoDeployTrigger=off`; its live deploy is still SHA
`811980c2cbf70d9957146bf329627f0826a018f1`. Staging service
`srv-db92irlg1s2s739404i0` is also Git-backed with auto-deploy off. The latest
deployment inventory still reports production SHA `811980c`; no current live
HTTP acceptance was performed. Render marks the Production environment
unprotected and network-wide (`0.0.0.0/0`, network isolation off). GitHub's
separate `production` environment requires `inaki3023` and prevents self-review,
but its environment and repository inventories contain no production release
variables or secrets. The Render production auto-deploy stop is an interim
control, not proof of digest-based promotion. The release preflight refuses
Git-backed targets, so promotion remains blocked until both services are
configured for the image-backed path.

GitHub environment and repository inventories were rechecked at 10:12 UTC; only
names/presence were read. `staging-neon-preflight` has `NEON_API_KEY` and the
selected target identity variables, but `STAGING_MIGRATION_DATABASE_URL` is
absent at both repository and environment scope. `release-staging` has
`RENDER_STAGING_API_KEY`, but its mapping attestation, provider identity, and
model revision variables are absent. `staging` has synthetic A/B accounts and
its acceptance flag/origin, but no `STAGING_AI_APPROVAL_JSON`. Production lacks
`RENDER_PRODUCTION_API_KEY`, `RENDER_PRODUCTION_SERVICE_ID`,
`RELEASE_PROMOTION_ENABLED`, and `PRODUCTION_RELEASE_CONFIG_ATTESTATION`.
Therefore the release workflow cannot currently pass its external preflight.
Do not treat a queued or historical run as current acceptance. Render values
remain private. The remaining service setup must be performed by an
administrator without deploying:

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
 3. Use only the approved Neon project `ancient-brook-17208049` and branch
    `br-rough-sea-a1l6ehi1` for staging. Trusted acceptance run `45966647832`
    verified candidate migration revision `0005_ai_request_quota` on that
    isolated branch and completed staging CRUD. It did not prove the current
    Render runtime settings still map to that branch. Privately re-attest the
    service-to-Neon host, project, branch, databases, roles, and Auth endpoint
    before another deployment. Do not use `hidden-shadow`, a production branch,
    or a restored production snapshot.
 4. GitHub's production/staging Auth URL and database variables are present.
   The staging extension-origin variable is tied to the pinned package identity.
   Neon Auth must still be verified to trust that same extension ID. Configure
   Render staging runtime and migration URLs, database host, branch ID, database
    name, and separate roles to target only the approved branch.
    `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION` is absent from the current
    repository/environment variable inventories, not pending. Create it only
    after a masked Render-to-Neon identity comparison, then run the exact
    candidate through protected staging. Staging startup checks the configured
    mapping before migrating or seeding.
5. On 2026-11-27, `staging-neon-preflight`, `staging`, and `release-staging`
   were verified with `xxTrixia` and `kendshhh` listed as reviewers, self-review
   prevented, and `main`-only deployment refs. The GitHub environment API did not
   expose the administrator-bypass setting, so its state is unverified.
   `production` lists `inaki3023`, prevents self-review, and restricts deploy
   refs; the API also does not expose its administrator-bypass state. The
   workflow rechecks the settings it can observe. A production reviewer must
   differ from the source author.
6. Configure the exact variables and secrets below. Never put credential values
   in the repository, workflow logs, screenshots, or evidence JSON.
7. Review and approve a held-out model evaluation report meeting its stated
   thresholds. Current production reports `AI_ANALYSIS_ENABLED=false`; do not
   turn it on until the provider identity, evaluation approval, and bounded
   spend controls are established.

### Configuration scopes used by the release workflow

GitHub environment and repository inventories were checked at 10:12 UTC; only
names and presence were inspected, never secret values. The public build Auth
URL/database variable names exist at repository scope. `RENDER_STAGING_SERVICE_ID`
is present at repository scope.

- `staging-neon-preflight` contains `NEON_API_KEY` and the configured staging
  and production identity variable names. `STAGING_MIGRATION_DATABASE_URL` is
  absent from both repository and environment secret inventories. A fresh
  least-privilege migration credential must be provisioned in this environment
  after its mapping is privately attested; never reuse a credential pasted into
  chat or a runtime role credential.
- `release-staging` contains `RENDER_STAGING_API_KEY`. Its
  `STAGING_RENDER_DATABASE_CONFIG_ATTESTATION`, `STAGING_RELEASE_PROVIDER`, and
  `STAGING_RELEASE_MODEL_REVISION` variables are absent from repository and
  environment inventories. The mapping attestation must be created only after a
  masked Render-to-Neon host/project/branch/database/role comparison. Provider
  and immutable model identity must come from the reviewed AI decision.
- `staging` contains the acceptance flag, trusted extension origin, and
  synthetic A/B account credentials. `STAGING_AI_APPROVAL_JSON` is absent. This
  environment does not contain the Render deploy key or Neon API key.
- `production` has no environment secrets or variables. Repository and
  environment inventories lack `RENDER_PRODUCTION_API_KEY`,
  `RENDER_PRODUCTION_SERVICE_ID`, `RELEASE_PROMOTION_ENABLED`, and
  `PRODUCTION_RELEASE_CONFIG_ATTESTATION`. Do not provision these until the
  image-backed path, production mapping, and independent reviewer are ready.

Self-review is prevented in `staging`, `release-staging`, and
`staging-neon-preflight`; their reviewer lists and `main`-only ref policies were
preserved. Production requires `inaki3023` and prevents self-review. The GitHub
environment API does not expose the environment reviewer-rule administrator
bypass flag, so this report does not claim it is off. The Render service's own
Production environment is separately marked unprotected. These missing
credentials/attestations and the Git-backed Render services make the release
workflow fail closed. Do not move credentials between scopes by copying values.

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

The latest protected staging report is for PR #306 exact head `131d282`, not
PR #268. Its source/backend SHA and package digest are recorded in
[`the #306 acceptance evidence`](evidence/2026-11-27-staging-acceptance-131d282.md).
It proves Auth/CRUD and extension UX for that candidate, but reports model
quality `approval_not_provided` and no backend image digest. The release remains
NO-GO until AI-owner approval exists, Render supports same-digest promotion,
production post-deploy checks pass, and rollback, restore, and alert evidence
are recorded.
