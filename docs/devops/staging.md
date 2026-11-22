# PhishLens staging acceptance

**Current state (2026-11-22):** PR #266 contains the candidate authenticated
acceptance path and pins the protected staging mapping. No current live Auth/CRUD
evidence is accepted. Its last hosted preflight failed closed because the checked-in
Neon project/branch and Auth mapping did not match the protected variables; this
reconciliation updates those pins. The current candidate still requires a fresh
exact-head run. Historical staging records do not establish acceptance for it.

## PR-required Hosted staging

The stable `Hosted staging` job runs for a same-repository, non-draft runtime PR
with the `needs-hosted-staging` label and `SECRETARY_PREVIEW_ENABLED=true`. It
retains the existing check name. Its eligibility and prerequisite logic is
fail-closed: if backend checks, isolated integration, or exact-head preflight
fails, the job fails rather than being treated as a successful skipped job.

Before any deployment or product-data write, the job:

- confirms the PR is still open at the queued exact head and still labeled;
- requires staging and production Neon project IDs to differ;
- verifies the configured staging branch is a root branch, differs from the
  production branch, has the expected endpoint, and has a protected schema-only
  attestation;
- requires the staging Render runtime mapping to match that endpoint and
  requires enabled Neon Auth;
- refuses a changed or superseded PR head immediately before deployment.

Do not enable this run against `pr-58-staging` (`br-delicate-paper-b381z98i`),
any production-derived branch, or the restored production snapshot. A root branch
in the production project is not sufficient isolation: keep staging in its
separate Neon project and verify the protected branch, Auth target, runtime
mapping, and attestations against `.github/secretary.json` before deployment.

After preflight, CI packages the extension from the exact PR merge candidate,
checks its archive digest and Auth/API origins, deploys that exact candidate to
the allowlisted Render staging service, and installs the package in Chromium.
Two dedicated synthetic users exercise sign-in, saved-report create/list/read/
update/delete, persistence after reload, user isolation, ownership checks,
cleanup, anonymous-history rejection, and loading/success/auth/API/timeout UI
states. The test blocks production API/Auth and unexpected external requests.
Persistent acceptance uses the live staging API and Neon Auth; mock results do
not satisfy it. The workflow captures sanitized evidence bound to the extension
ZIP, backend SHA, project/branch, and service identity.

The model gate is reported separately. Product CRUD evidence may identify
`model_quality=blocked`, but that cannot authorize release. Release staging and
production promotion require an approved representative held-out evaluation,
an AI/model-owner-approved numeric policy, immutable model/provider identity,
and the exact accepted model in staging. The checked-in policy remains pending
approval. A missing, disabled, unavailable, mocked, or unapproved model leaves
the release NO-GO.

## Secretary staging status

`Secretary staging` remains the stable required context. The new trusted
`workflow_run` bridge checks out default-branch code only and mirrors success for
a runtime PR only after the same latest CI run has passed Backend checks,
Extension checks, Staging integration, and Hosted staging. It does not deploy or
receive Render/Neon credentials. Missing, skipped, failed, stale, or pending
Hosted staging produces a non-green status. Documentation-only changes can be
marked not applicable only after ordinary CI succeeds.

GitHub executes `workflow_run` definitions from the default branch. Until a
reviewed bridge is on `main`, the branch cannot activate this new status logic.
Do not manually write a green status to bypass that boundary. Hosted staging
remains a direct required check and no live acceptance is claimed by this PR.

## Release promotion and production

`.github/workflows/release-promotion.yml` is manual-only. It builds one backend
image and one extension ZIP, records their immutable digests, tests those same
artifacts in a protected staging environment, and requires a distinct protected
production approval before promotion. It verifies the production SHA, provider,
health, readiness, exact image digest, manifest, version tag, and changelog
before publishing. Production is never deployed by PR acceptance.

Render production `srv-db7eap25b2lc73fkelpg` is Git-backed with auto-deploy off;
staging `srv-db92irlg1s2s739404i0` is also Git-backed. That read-only metadata
was checked on 2026-11-21. The release workflow refuses Git-backed targets, so
no digest promotion is possible yet. Changing Render's backing source triggers
a deploy; an administrator must schedule and approve a safe transition or
provision an image-backed replacement. No production setting was changed and no
production deployment was triggered by this work.

## Required external setup

Complete through protected GitHub/Render/Neon settings, not committed secrets:

1. Keep the configured Neon project separate from production; verify its root
   branch, schema-only initialization, current migrations, Neon Auth, and absence
   of production rows against current protected attestations.
2. Privately verify the Render staging service's runtime and migration URLs,
   database, branch, Auth mode, and separate least-privilege roles. Record the
   project IDs, branch IDs, endpoint hosts, and attestations in protected GitHub
   variables. Use a separate owner credential for migrations and an app role for
   runtime.
3. Create two empty synthetic Auth accounts and trust the extension ID as the
   Chrome origin. Configure protected `staging` reviewers and prevent self-review.
4. Set `SECRETARY_PREVIEW_ENABLED=true` only once all isolation and mapping
   checks are current. Keep production database URLs and credentials out of the
   staging environment.
5. Configure `release-staging` and `production` protected environments. The
   production approval must be independent of the source author.
6. Have the AI/model owner approve the quality-policy thresholds and a reviewed
   held-out report. Do not invent the approval or turn on production analysis to
   make the check green.
7. Schedule the Render Git-to-image source transition or a replacement service;
   switching the existing source can deploy, so it requires an approved
   maintenance/release window.

See [controlled release](controlled-release.md) for exact variables, gates, and
manifest contents. Never store secret values in source or evidence artifacts.

## Local and CI verification

Offline checks validate the workflow decision and evidence parsers; they do not
prove hosted Auth, persistent CRUD, provider quality, or production promotion.
Use the latest exact-head Actions run and its sanitized artifact for hosted
evidence. A previous PR's artifact or a different backend SHA cannot satisfy the
current candidate.

The older point-in-time records in this directory document their own historical
SHA and environment. They must not be described as acceptance for current main,
PR #266, or a later release unless the exact identity matches and the run is
repeated.
