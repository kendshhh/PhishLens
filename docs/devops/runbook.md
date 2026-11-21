# Deployment and Recovery Runbook

## Current recovery position — 2026-11-21

Release remains **NO-GO**. The current service identities and evidence limits
are maintained in the [release record](release-record-2026-11-21.md) and
[environment map](environment-map-2026-11-21.md). The recorded production
deployment is `dep-dc07rs67bikc73fjgjq0` on
`811980c2cbf70d9957146bf329627f0826a018f1`, with analysis disabled. The
recorded staging deployment is `dep-dc0im3h7lnhs738pncng` on
`ba0b6c5475eb6a8f99c509c40384020d292e17e6`; its anonymous saved-report
endpoint requires a Bearer session. Direct GET-only smokes from the review
branch passed at 08:15 and about 08:35 UTC for health, readiness and anonymous
`401 Bearer`; they do not verify deployed PR identity, authenticated CRUD, or
deployment state.

The review branch includes main's Bearer-aware history correction and adds
bounded smoke retries, failure summaries, local server-exit monitoring and log
retention. Hosted deployment requires
successful staging, hosted preflight and backend results at both job and deploy
step level. The synchronized candidate passed 321 local Node tests and the
GET-only smoke. PR #265 merged to main at `95975cd47dceeac74ea36054610956f0a1db1fa9`;
its CI [44889931821](https://github.com/kendshhh/PhishLens/actions/runs/44889931821)
and CodeQL [44889931096](https://github.com/kendshhh/PhishLens/actions/runs/44889931096)
passed. PR #268 head `2e26327254c71b6cb7d655181cffb21e8dd1ee9b` passed Backend,
Extension, Staging integration, migration preflight and hosted preflight in
[run 44891131201](https://github.com/kendshhh/PhishLens/actions/runs/44891131201);
workflow lint [44891131261](https://github.com/kendshhh/PhishLens/actions/runs/44891131261),
dependency security and Dependency graph review [44891131162](https://github.com/kendshhh/PhishLens/actions/runs/44891131162),
and deterministic evaluation [44891131190](https://github.com/kendshhh/PhishLens/actions/runs/44891131190)
passed. Hosted staging job 136807616481 ended with conclusion success, but its
final freshness guard marked the request superseded after the label was removed
at 09:54 UTC; deployment, smoke, CRUD and artifact steps were skipped. The job
summary classifies this as blocked, not hosted acceptance. Required `Secretary
staging` failed in [run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807).
No current PR CodeQL result appeared. The hosted CRUD runner remains unauthenticated,
required-check settings are not reverified, and the effective production deploy
trigger remains unresolved. The PR still targets the merged #265 branch and
should be retargeted to main before merge. Do not merge, promote, or claim release
readiness from these changes alone. Earlier PR #268 CI run
[44883590782](https://github.com/kendshhh/PhishLens/actions/runs/44883590782)
passed local staging integration and guard tests. On `2e26327`, Dependency
graph review passed after the graph was enabled; 15 existing Dependabot alerts
(12 high, 3 moderate) remain open. See [CI maintenance](ci-maintenance.md) and
the [dependency audit](dependency-audits.md).

At 11:08 UTC, PR #268 head `a151585ff92d55f21e0364e9838287a9cf04a68d` failed
`Extension checks` at the packaged Saved reports view keyboard-focus assertion
in `scripts/browser_acceptance.mjs:700` ([CI
44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076)).
Staging integration and hosted staging/preflight were skipped. Required
`Secretary staging` failed in [run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167)
because the request label and exact-head hosted verification were absent. This
supersedes the 10:14 check snapshot for current PR status; it does not establish
hosted acceptance. No Render deployment or authenticated CRUD occurred.

On the latest completed docs-only head `dffdc4c29338142f458350b51c8ce69e0f36e988`,
Backend, Extension and Staging integration passed in [CI 44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208).
Hosted preflight and Hosted staging were skipped. Required `Secretary staging`
failed in [run 44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)
because the request label and exact-head hosted verification were absent. The
docs-only sync after this snapshot needs fresh checks; no Render deployment or
authenticated CRUD is established.

The owner-approved recovery objectives are RTO no greater than 30 minutes and
RPO no greater than one hour. Neither has been measured. The November 20
isolated restore verified schema and aggregate integrity, not service recovery
time or recoverable-point age. Production-compatible app/config/schema rollback,
durable backup scheduling, and named primary/backup responders remain open.
See the [November 20 recovery drill](recovery-drill-2026-11-20.md).

## Historical recovery position — 2026-11-20

Render has deployed application SHA
`0c382dda175db3570e6bb7122841122254ba131d` as deploy
`dep-dc04rb0473hc738839ug`. The owner-approved `AI_ANALYSIS_ENABLED=false`
setting triggered follow-up deploy `dep-dc04t5dg1s2s73e5pc00`, which reached
Live at 13:44:56 UTC on the same SHA. Direct post-deploy endpoint GETs returned
HTTP 403 from this audit client; `/model-info` has not confirmed the effective
disabled state. The last successful production endpoint checks at 12:18 UTC
belonged to SHA
`16f955321caf5dc368181be7ce5c00643750545d`. Staging remains on
`d6612c258f289b3a45d8229e4a4803cac75a91ee`, with TF-IDF mode. The current
production known-good app/config/schema combination and rollback rehearsal are
not established; do not choose a rollback target from recency alone.

The later November 21 07:31 UTC Render refresh showed staging Live on deploy
`dep-dc0im3h7lnhs738pncng` / SHA
`ba0b6c5475eb6a8f99c509c40384020d292e17e6`, not the November 20 SHA listed
above. GET-only smokes later passed `/health`, `/ready` and anonymous history
authentication (`401 Bearer`); no authenticated history or CRUD was exercised.
PR #268's code/test source passed the recorded CI snapshot on docs-only PR
revision `631b0ef`; hosted deployment and preflight were skipped, and the
required `Secretary staging` context failed for missing hosted verification.
Keep deployment, health and authenticated acceptance as separate gates.

On November 20, a manual snapshot was restored into a new isolated Neon branch
without finalizing or changing production. Schema revision and aggregate
user/report counts matched the source; no orphaned report owners were found.
The provider reported the restored branch ready about one second after
creation. This small-data snapshot-to-ready sample is not a full-service RTO
measurement or proof of the approved RTO ≤30 minutes / RPO ≤1 hour targets.
See the [dated recovery drill](recovery-drill-2026-11-20.md).

Neon reports six-hour history retention. The manual snapshot and recovery
branch expire November 27, 2026. Automatic schedules require a paid plan, and
the current free plan rejected production branch protection because its
protected-branch limit is zero. The production branch remains unprotected and
there is no recurring snapshot schedule; no plan upgrade was made. The earlier
November 8 staging rollback rehearsal below does not prove current production
rollback.

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

### Alert delivery and incident evidence

No alert delivery path, backup recipient, or acknowledgement record was
verified on November 20. The thresholds below remain candidates until the
service owner approves them, configures a monitor and tests delivery. A failed
scheduled workflow is not evidence that an alert reached an on-call responder.

For the alert drill, preserve the signal and threshold, injected test event,
event/delivery/acknowledgement timestamps, recipient and channel, first
response, containment, recovery timestamp, post-recovery health and affected
journey checks, data-integrity check, measured recovery time, and follow-up
owner. Link the redacted record from the incident log. The production release
cannot claim tested alert response until this record exists.

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
2. Stop promotion. PR #256 deployed `AI_ANALYSIS_ENABLED` support; the owner
   set `AI_ANALYSIS_ENABLED=false` on Render and the matching-SHA configuration
   deploy is Live. Endpoint verification remains pending because this audit
   client received HTTP 403. Confirm the exact deployed SHA and that
   `/model-info` reports analysis disabled. If verification fails, keep the
   provider unconfigured and do not send inference traffic. When unset, the
   variable defaults to enabled, so preserve the explicit false setting until
   a shared budget and approved model are configured.
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

At the time of this November 20 note, the owner-approved RTO ≤30 minutes and
RPO ≤1 hour targets had not been measured. The current position above retains
that limit and records that these objectives remain unproven.

> The entries below are dated observations. The [current pipeline status](../../PIPELINE.md)
> supersedes older statements where service SHAs or release state differ.

## Historical October 21 playbook handoff

See [October 21 close-out](playbook-closeout-2026-10-21.md) for current evidence,
the corrected Week 2 instructions and remaining integration gates. Production
evidence run 39449283551 passed for main `149808e`; this is dated observer evidence,
not a claim that every later independent endpoint probe succeeded.

## Historical post-merge verification — October 29, 2026 00:31 UTC

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

At this October 2026 snapshot, source had migration `0001_initial_schema`. That
is historical context, not the current schema revision; staging's observed
revision is `0004_neon_auth_subject`. Before a future rollback, compare the
exact app/schema revisions and use the current approved recovery procedure.
Do not reuse the October 14 drill as proof of current production recovery.

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

## Historical service configuration snapshot — initial deployment

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

## Historical initial deployment procedure

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

## Current deployment procedure — fail closed

Release remains **NO-GO** until every current gate in the
[scorecard](release-readiness-scorecard-2026-11-21.md) passes for one exact
candidate and reviewers accept its linked evidence.

1. Review the current DevOps index, candidate record, and open blockers. Keep
   the original dirty checkout untouched; use a clean review branch.
2. Require the relevant CI checks and independent review. The hosted-staging
   job must run only when the local staging integration, current-head preflight
   and backend migration lineage all succeed. Skipped or failed dependencies
   cannot authorize a Render staging deploy.
3. Verify current PR head immediately before deployment, then verify the exact
   deployed `/version` SHA, migration, readiness, history/auth contract,
   authenticated CRUD/cleanup and package provenance. A local integration pass
   does not establish hosted service health.
4. Do not merge a candidate while hosted CRUD lacks a supported Auth session,
   or while required-check protection, deployment settings, secret scopes,
   service-to-Neon mapping or test cleanup are unresolved.
5. Render metadata was observed with auto-deploy off for production and staging,
   while a production deploy record reported `new_commit`. Reconcile that
   discrepancy in the control plane before relying on an automatic deploy.
   Do not manually deploy production from this runbook; use only the separately
   authorized release procedure after GO.
6. The production observer is manual and read-only. A disabled-provider
   observer pass establishes service state only, never inference, persistence
   or product acceptance. Do not make paid calls or saved-report writes in
   production.
7. Record the exact source/deploy/package identities, run URL, statuses,
   artifacts, recovery point and owner decisions. Keep unverified evidence open.

For database-dependent changes, verify `/ready` and exact `/version` on the
candidate. Readiness currently checks database connectivity, not full table or
record integrity. Confirm the private Render-to-Neon branch/database/role
mapping without displaying connection strings or secrets. The API base URL may
have no homepage and return 404.

## Deployment Failure

1. Open Render deployment logs.
2. Identify the first meaningful error.
3. Check dependency installation, Python version, start command
   and environment configuration.
4. Prepare a focused repair PR and repeat the normal review process.
5. Record the incident, impact, repair and recovery time.

Never paste secrets into issues or logs shared with teammates.

## Current rollback position and procedure

No current production app/config/schema combination is proven as a compatible
rollback target. Stop promotion, declare the incident, preserve deploy and
migration identities, and have the release lead and database owner select and
review an exact compatible target. Do not select a target by recency or use the
historical SHA records below as current approval.

For an authorized application rollback: identify the exact Render deploy and
matching non-secret configuration; check schema compatibility; use Render's
rollback/deploy controls only under the approved incident procedure; verify
deploy ID and `/version`; check `/health`, `/ready`, model/provider state and
the affected user flow; retain logs and timestamps. Database restore/cutover is
a separate decision and must use an isolated recovery branch first. Record
actual service RTO and achieved recovery point; do not infer them from provider
branch-ready timing.

### Historical rollback observations — October 2026

Rollback to 717334d was successful in 35.7 seconds. Restoration to 8a8634e
succeeded on retry after an initial health-check/port-detection timeout.
Full restoration duration remains unmeasured. This was a planned drill.

If replacement deployment times out, inspect that deployment's own logs.
General service logs can come from the still-running older instance. Preserve
the health check; do not change ports or suppress errors without evidence.

Rolling back application code does not automatically reverse
database migrations. Coordinate database recovery with Trixia.

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

## Evidence

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
