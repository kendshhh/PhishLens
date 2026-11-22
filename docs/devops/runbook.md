# Deployment and Recovery Runbook

## Current recovery position — 2026-11-21

Render reports production deploy `dep-dc07rs67bikc73fjgjq0` live on
`811980c2cbf70d9957146bf329627f0826a018f1`. Read-only health, readiness,
version and model probes pass; production analysis is intentionally disabled.
Staging reports deploy `dep-dc0im3h7lnhs738pncng` live on
`ba0b6c5475eb6a8f99c509c40384020d292e17e6`, with TF-IDF enabled and anonymous
saved-report history protected by Bearer authentication. Neither deploy gives
us an accepted current-production rollback target. Do not choose a rollback
target from recency alone.

The [November 20 Neon recovery drill](https://github.com/kendshhh/PhishLens/blob/811980c2cbf70d9957146bf329627f0826a018f1/docs/devops/recovery-drill-2026-11-20.md)
restored a snapshot to an isolated branch and checked schema/aggregate
integrity. Its one-second provider branch-ready observation is not service RTO,
and RPO was not measured. The snapshot and restored branch expire November 27.
Neon history retention is six hours; scheduled snapshots are not configured,
and the free plan rejected branch protection. The current production
service-to-branch/role mapping, compatible application rollback, measured
RTO/RPO and named backup recovery responders remain open. Never restore over
production during a rehearsal.

### Operational ownership and escalation

The last named CI/deploy/runbook owner in repository evidence is Kendra
(`kendshhh`); reconfirm this assignment before launch. The AI/model decision
owner recorded in the November 14 handover is Wilberr (`EnviousCoal`). A
production backup responder, database restore operator, and incident contact
channel are **not named in current handover evidence**. Assign them before GO.
The release lead records the incident and stops promotion; the database owner
approves isolated restore/cutover; the AI owner approves model, evaluation and
provider decisions. If the primary cannot respond, escalate using the
pre-agreed backup/contact path; that path remains to be recorded.

### Proposed rollback triggers

These are starting recommendations, not configured alert thresholds. Agree
them with the service owner and test alert delivery before relying on them.

- **Immediate containment:** wrong deployed SHA, wrong provider/model identity,
  authentication or cross-user data isolation defect, critical extension action
  broken, or confirmed privacy/security incident.
- **Persistent service regression:** `/ready` fails on two consecutive probes
  60 seconds apart, or two independent exact-release synthetic acceptance
  checks fail one minute apart.
- **Sustained degradation:** 5xx rate exceeds 5% for five minutes where request
  volume is sufficient, or p95 user-flow latency exceeds twice the agreed
  baseline for ten minutes.
- **Single transient:** one timeout or failed probe causes a retry and close
  observation. It does not by itself trigger automatic rollback.

### Application rollback sequence

1. Kendra, as the last documented release operator, or the assigned backup
   responder declares the incident. Record time, deploy ID, commit SHA,
   observed failure and affected user flow. The backup responder must be named
   in the handover before launch.
2. Stop promotion. Disable the preconfigured AI/release feature flag if that
   flag has been verified for the current app. The current flag name and
   production effect are **not verified**; do not guess an environment key.
3. In Render, select the last explicitly verified compatible deployment, then
   use **Rollback to this deploy** (or **Manual Deploy > Deploy a specific
   commit** when that is the documented recovery path). Confirm the target
   commit and its expected schema/config compatibility before starting. If no
   compatible known-good SHA is recorded, keep the affected feature disabled
   and escalate rather than deploying an assumed predecessor.
4. Restore the target's matching non-secret configuration and feature-flag
   state from the controlled environment record. Never copy secret values into
   an issue, log, artifact or repository.
5. Confirm the deployment ID and `/version` SHA. Check `/health`, `/ready` and
   `/model-info`, then run exact-SHA smoke and the relevant synthetic extension
   journey. Verify authentication, saved-report behavior, ownership/isolation
   and cleanup in the approved test environment. Watch the agreed error and
   latency signals for at least 15 minutes.
6. Keep the feature disabled and escalate if any identity, readiness, model or
   critical user-flow check fails. Do not automatically roll forward or back
   again on a single transient.
7. Record the result and incident follow-up before resuming normal promotion.

### Database and data recovery — separate from application rollback

1. Stop writers for an affected data path and preserve the current app/schema
   identities. Do not run a reverse migration or reset the shared production
   branch during a rehearsal.
2. For an irreversible or destructive change, restore the selected point into
   an isolated Neon recovery branch using the provider's supported recovery
   method. Confirm the source point is within retention and record its ID/time.
3. Validate migration state, schema constraints, representative record counts,
   ownership/isolation and application compatibility against the recovery
   candidate. Record the data-loss window relative to the incident.
4. Cut over only through the approved recovery procedure after the database
   owner and release lead review the evidence. Recheck `/ready`, exact `/version`,
   affected behavior and data integrity after cutover.
5. Record recovery duration and data point achieved. Application rollback does
   not restore deleted or corrupted database state.

RTO and RPO targets are **not currently approved or measured**. Provisional
discussion targets are RTO ≤30 minutes and RPO ≤1 hour; confirm Neon capability
and owner tolerance before adopting them. Rehearse application rollback and
isolated data restore separately, recording start/end times, release/data
identities, steps, outcome, data-loss implication and follow-up actions.

> The entries below are dated observations. The [current pipeline status](../../PIPELINE.md)
> supersedes older statements where service SHAs or release state differ.

## October 21 playbook handoff

See [October 21 close-out](playbook-closeout-2026-10-21.md) for current evidence,
the corrected Week 2 instructions and remaining integration gates. Production
evidence run 39449283551 passed for main `149808e`; this is dated observer evidence,
not a claim that every later independent endpoint probe succeeded.

## Current post-merge verification — October 29, 2026 00:31 UTC

PR #86 merged as `1344fcb061272bac93ced5911f1ab8fbb3b6785d`; production deploy
`dep-dbh8v6ivcj2c73fql7c0` is Live on that commit. Read-only `/version`,
`/health`, and `/ready` requests returned HTTP 200, with the expected production
identity and connected database. Staging deploy `dep-dbh8s8942hec73bo7bt0` is
Live on candidate `fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2`; the same read-only
checks returned HTTP 200 and connected readiness.

The guarded synthetic CRUD verifier passed against that exact staging SHA after
the protected staging gate and the Neon `phishlens_staging_app` least-privilege
check passed. It cleaned up its synthetic record. Production remains read-only;
production persistence, installed-Chrome behavior, a comparable pipeline gain,
and complete recovery duration remain unverified.

## Recorded production and prior staging verification — October 28, 2026 17:07 UTC

Production service `phishlens-api` is configured on `main` with Render auto-deploy
trigger `checksPass`. At 2026-10-28 15:39 UTC, main was
`6414914dfa8eb8322839597c4cd6912145a442a0`. Main CI run
[40715810349](https://github.com/kendshhh/PhishLens/actions/runs/40715810349)
passed Backend and Extension; Workflow lint
[40715810515](https://github.com/kendshhh/PhishLens/actions/runs/40715810515)
passed. Render deployment
[`dep-dbh18p6i0phs73d1mtag`](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dbh18p6i0phs73d1mtag)
is Live on that exact SHA. `/version`, `/health`, and `/ready` returned HTTP 200;
version reported production and the matching SHA, and readiness reported the
database connected. See [metrics.md](metrics.md) for the 73.525-second deployment
duration; merge-to-live time for this SHA is not measured.

Staging service `phishlens-staging` is configured on `main` with auto-deploy off.
PR #86 Hosted staging passed and deployment
[`dep-dbh2cjnf3r2c73emoprg`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh2cjnf3r2c73emoprg)
is Live on exact merge SHA `d46cc09ecf7258a6bd10475f00cc8da035ef5e9a`.
Read-only `/version`, `/health`, and `/ready` GETs at 17:07 UTC returned HTTP
200; version matched the candidate and readiness reported the database connected.
The mapped Neon target is `pr-58-staging/phishlens_dev`. A read-only grant check
at 17:05 UTC still found public-schema `CREATE` and `INSERT`, `UPDATE`, and
`DELETE` on the migration and application tables for the runtime role. No grant
change or database write was made. The environment owner must remove the excess
privileges and repeat the read-only check before synthetic CRUD is run. The
historical guarded CRUD evidence on deactivated SHA `e3c6e37` does not verify this
candidate.

## Historical PR #86 staging gate — October 28, 2026 17:31 UTC

At this snapshot, current PR head `dcafd2f539a3dafdc6a3c50e62cc35ae71c24d86`
passed all automated checks except Hosted staging, pending at the protected
`staging` environment; connected diagnostics returned no steps or reason. The
Live staging candidate described above belongs to the previous PR code head and
does not establish this head's deployment or acceptance. The runtime role still
has excess grants, so staging CRUD remains blocked until the environment owner
cleans them up and a read-only recheck passes.

Production CRUD persistence across refresh/redeploy and installed-Chrome behavior
remain unverified. Production probes establish live version, process health, and
database readiness only. See [Kendra's Week 1–4 closeout](kendra-week1-4-closeout-2026-10-28.md)
for her per-week status and remaining owner-dependent acceptance.

For each deployment, retain main SHA, successful main CI, reviewer approval,
Render deploy ID/trigger/live timestamp, and the live `/version`/health/readiness
observations. Archive package `evidence.json` alongside the ZIP before expiry;
compare its source/tested SHA and ZIP hash before installing. Packaging does not
establish browser execution or database isolation.

Before a rollback, record both app revisions and their expected schema
revisions. The latest read-only staging migration head is
`0004_neon_auth_subject`; production's live migration head was not independently
queried in this audit, so do not assume it matches. Compare migration trees and
coordinate with the database owner before any schema-changing rollback. The
November 20 isolated restore drill checked schema/aggregate integrity but did
not measure end-to-end recovery. For any authorized recovery, record incident
start, action start, live result, independently restored
`/version`/health/readiness time, recoverable point, and actual affected behavior.

The [Secretary pilot operator guide](secretary.md) adds exact-SHA preview and
production observation. Its observer produces `metrics.json` and, on failure, an
incident draft under the Actions artifact `Veriqo-Production-Evidence`. Inspect
the exact failed deployment in Render before deciding recovery. The pilot never
deploys production, changes secrets, applies production migrations, or executes
rollback. The existing human recovery procedure below remains authoritative.

## Historical initial scaffold status

The FastAPI backend scaffold is publicly deployed on Render.

- Public /health endpoint verified.
- Auto-Deploy configured as After CI Checks Pass.
- Automatic deployment verified after PR #12 merged.
- Historical automatic-deployment baseline: 8a8634e. Later deployments are
  recorded in metrics.md; confirm the current Live SHA in Render for each release.
- Public /ready independently returned HTTP 200 and database connected.

Database connectivity is verified; schema-backed frontend and AI integration
remain pending. Rollback and restoration were exercised, including one failed
restoration attempt. See incidents.md for the evidence and limitations.

## Historical service configuration snapshot

The values below describe an earlier deployment setup. Current Render metadata
and its unresolved trigger discrepancy are recorded at the top of this runbook;
verify the Dashboard before relying on these settings.

- Repository: kendshhh/PhishLens
- Branch: main
- Runtime: Python 3
- Python version: 3.12.10
- Instance plan: Free
- Root directory: repository root; leave the field blank
- Health check path: /health
- Auto-deploy: After CI Checks Pass

Build command:

    python -m pip install -r backend/requirements.txt

Start command:

    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

## Historical initial deployment checklist

1. Confirm the backend PR is reviewed and merged.
2. Confirm CI passes on the merged main commit.
3. Verify the Render settings above.
4. Create the service and inspect deployment logs.
5. Confirm Auto-Deploy is set to After CI Checks Pass.
6. Open the service's public URL followed by /health.
7. Expect HTTP 200 and:
   {"status":"ok","service":"phishlens-api"}
8. Record the deployed commit, URL, deployment result and timings.

The health endpoint verifies the API process only.
It does not verify database access, AI inference or extension integration.

## Subsequent Deployments — current safe sequence

The release is currently **NO-GO**. The authenticated hosted staging gate and
effective GitHub required-check contract are not verified. Render metadata says
production auto-deploy is off while the latest production deployment record says
`new_commit`. Do not merge or deploy a release on the assumption that the
historical auto-deploy setting below is active.

1. Select and review one exact source/package/backend/model/Auth candidate.
2. Complete current [pre-merge staging](staging.md), including authenticated
   CRUD, persistence, isolation and cleanup. A green anonymous preflight alone
   is insufficient.
3. Verify effective GitHub required checks and independent review on that exact
   PR. Do not count skipped or stale jobs.
4. After an authorized merge, read the actual Render service setting and deploy
   history. Verify whether a deployment occurred; do not start a manual deploy
   unless its owner has approved that operation.
5. Confirm `/version` matches the exact intended SHA and environment. Check
   `/health`, `/ready`, and `/model-info`. Current production is intentionally
   disabled for analysis; its observer result is not AI/product acceptance.
6. If approved, run the manual **Production evidence** observer after the exact
   SHA is live. It is evidence collection, not a deployment gate or deploy
   action. Retain its redacted artifact.
7. Verify only authorized, relevant behavior. Use synthetic staging data for
   writes; production probes remain read-only unless separately approved.
8. Record SHA, deploy ID, event, run link, outcomes, limitations and timings.

For database-dependent changes, `/ready` returning HTTP 200 with
`{"status":"ready","database":"connected"}` proves connectivity only. It
does not identify branch, role, tables or record state. Privately verify the
Render-to-Neon target before any write. The base URL `/` may correctly return
404.

## Deployment Failure

1. Open Render deployment logs.
2. Identify the first meaningful error.
3. Check dependency installation, Python version, start command
   and environment configuration.
4. Prepare a focused repair PR and repeat the normal review process.
5. Record the incident, impact, repair and recovery time.

Never paste secrets into issues or logs shared with teammates.

## Rollback Plan

The current production known-good app/config/schema combination is **not
identified**. No production rollback target is approved. The November 20 Neon
drill restored to an isolated branch but did not measure end-to-end service RTO
or RPO. Keep analysis disabled and stop promotion if an identity or feature
failure occurs; do not select a target based on recency.

For an approved incident or drill:

1. Record incident/deploy IDs, source SHA, schema revision, settings scope,
   observed failure and start time. Stop further promotion.
2. Have the release and service owners identify an exact known-good deployment
   and verify schema/config compatibility. If no compatible target is known,
   contain the affected feature and escalate; do not guess.
3. Use the owner-approved Render rollback/deploy procedure. Re-read the auto-
   deploy setting afterward; do not change it back to a prior value unless the
   service owner explicitly approves that configuration.
4. Verify deployment ID and `/version`, then `/health`, `/ready`, and
   `/model-info`. Run only the authorized exact-SHA observer and relevant
   synthetic acceptance. Keep production data read-only.
5. If data recovery is required, stop writers and restore into an isolated
   Neon branch first. Never overwrite or finalize production for a rehearsal.
6. Record end-to-end time, recoverable point/data-loss window, cleanup,
   monitoring, and actual affected behavior. Do not report provider branch
   provisioning time as service RTO.

### Historical early rollback observation

Rollback to `717334d` was recorded as successful in 35.7 seconds. Restoration
to `8a8634e` succeeded on retry after a health-check/port-detection timeout;
full restoration duration was not measured. This early planned drill is not a
current-production-compatible rollback result.

If a replacement deployment times out, inspect that deployment's own logs;
general service logs may come from the still-running older instance. Rolling
back application code does not reverse database migrations; coordinate any
data recovery separately with the database owner.

Local migration compatibility and PostgreSQL dump/restore evidence is recorded in
[`migration-compatibility-recovery-2026-11-15.md`](../migration-compatibility-recovery-2026-11-15.md).
It covers disposable PostgreSQL only; it does not establish hosted backup or recovery.

## Candidate-compatible staging rollback — 2026-11-08

This bounded rehearsal covered application rollback and restore on Render staging only. It used no production writes and no live-provider request.

**Preconditions and target**

- Service: `phishlens-staging` (`srv-db92irlg1s2s739404i0`), auto-deploy off.
- Starting candidate app SHA: `46a2b27c199c64a25261d3cbba7e52a3352e7a98`, deploy `dep-dbntn4k9v7es73do87a0`.
- Prior successful target SHA: `0769de936c349f57bf32540d92adaab97f7c402a`, deploy `dep-dbnt775g1s2s73dkbrtg`. Render showed no configuration changes since the target deploy.
- No migration files differ between the two app SHAs; migration preflight reported `0003_saved_analysis_idempotency`.

**Procedure and observed results**

1. In Render, select the prior successful staging deploy and choose **Rollback to this deploy**.
2. Wait for its deployment to reach Live. Rollback deploy `dep-dbnvt2ajnfac73dhlda0` completed in 40.352 seconds on app SHA `0769de9`.
3. Check `/version`, `/health`, `/ready`, and `/model-info`; each returned HTTP 200. Readiness reported the database connected; model mode was TF-IDF.
4. Restore the original exact SHA using **Manual Deploy > Deploy a specific commit**, selecting `46a2b27c199c64a25261d3cbba7e52a3352e7a98`.
5. Restore deploy `dep-dbnvukk9v7es73dtsmrg` reached Live in 86.593 seconds. Repeat all four GET checks; each returned HTTP 200, `/version` matched the original SHA, readiness reported the database connected, and the TF-IDF model hash matched `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
6. Confirm auto-deploy remains off. Render reports `autoDeploy=no`.

**Stop and limits**

If the expected SHA or health/readiness response does not return after a transition, stop the drill, do not promote or deploy to production, inspect that deployment's own logs, and restore the last verified staging SHA through **Manual Deploy > Deploy a specific commit**. Confirm version, health, readiness, model identity and auto-deploy setting before ending the rehearsal.

This rehearsal proves the staging app rollback/restore path for this candidate only. It does not simulate provider timeout, quota or malformed output; it does not measure AI failure detection/recovery and does not establish production recovery. Owner: Kendra (`kendshhh`). Reviewer: `EnviousCoal`; review remains pending. Track remaining AI drill work in #95 and candidate review in #143.

## Historical deployment evidence — initial service

- Public URL: https://phishlens-api-ocvt.onrender.com
- Health endpoint: https://phishlens-api-ocvt.onrender.com/health
- First deployment: commit 717334d; duration 50.3 seconds.
- Verified automatic deployment: PR #12, commit 8a8634e.
- Automatic deployment duration: 44.9 seconds.
- Post-deployment health response:
  {"status":"ok","service":"phishlens-api"}
- Rollback verification: successful operation; see incidents.md.
- Database readiness: public /ready returned HTTP 200 and database connected.

Deployment duration is not the full merge-to-live lead time.
