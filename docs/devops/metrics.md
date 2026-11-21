# Pipeline Metrics

## Current service identity refresh — 2026-11-21

This read-only refresh records service identity and endpoint behavior, not a
performance sample. Production serves `811980c2cbf70d9957146bf329627f0826a018f1`
from Render deploy `dep-dc07rs67bikc73fjgjq0`. `/version`, `/health`, `/ready`
and `/model-info` returned HTTP 200; analysis is disabled
(`analysis_enabled=false`, `provider_mode=disabled`). GitHub `main` later
advanced through `06f89d7a0b5b9dec316dfa11f2846767a32086c5` to
`95975cd47dceeac74ea36054610956f0a1db1fa9`; this record does not verify a later
production deploy. Staging serves
`ba0b6c5475eb6a8f99c509c40384020d292e17e6` from deploy
`dep-dc0im3h7lnhs738pncng`; the same four GET endpoints returned 200 with
TF-IDF mode. Anonymous `/api/analyses` returned 401 with a Bearer challenge.
No inference, database write, or production smoke workflow run was made.
An earlier workstation smoke attempt timed out on staging `/health`. GET-only
smokes at 08:15 and about 08:35 UTC passed `/health`, `/ready`, and anonymous
history authentication (`401 Bearer`) using review-branch code. The later run
used the mainline-synchronized smoke helper. Neither run checked
`/version`, deployed PR identity, or authenticated CRUD, and it is not a
performance sample. Treat the deployment identity above as the 07:31 UTC
control-plane observation.

CI evidence is not a performance metric. PR #265 merged to main at
`95975cd47dceeac74ea36054610956f0a1db1fa9`; its CI and CodeQL passed in runs
44889931821 and 44889931096. On PR #268 head
`2e26327254c71b6cb7d655181cffb21e8dd1ee9b` at 10:14 UTC, Backend, Extension,
migration source preflight, Staging integration, hosted preflight, workflow
lint, dependency security, Dependency graph review and deterministic evaluation
passed. Hosted staging job 136807616481 ended with conclusion success, but its
final freshness guard blocked deployment, smoke, CRUD and artifact steps after
the request label was removed at 09:54 UTC. The job summary says blocked, not
hosted acceptance. The separate required `Secretary staging` status failed in
[run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807).
No current PR CodeQL check appeared;
the prior `7dbebfd` CodeQL run failed because Actions hit installation API rate
limits. Dependency graph review passes after
graph enablement, while 15 existing Dependabot alerts (12 high, 3 moderate)
remain open. The latest checks are [CI 44891131201](https://github.com/kendshhh/PhishLens/actions/runs/44891131201),
[workflow lint 44891131261](https://github.com/kendshhh/PhishLens/actions/runs/44891131261),
[dependency checks 44891131162](https://github.com/kendshhh/PhishLens/actions/runs/44891131162),
and [evaluation 44891131190](https://github.com/kendshhh/PhishLens/actions/runs/44891131190).
See the [release record](release-record-2026-11-21.md) and [staging evidence](evidence/2026-11-21-staging-neon-auth-smoke.md).
Do not include these workflow outcomes in CI duration or deployment
performance samples below.

On the 11:08 UTC PR #268 head `a151585ff92d55f21e0364e9838287a9cf04a68d`,
Backend and migration preflight passed, while packaged `Extension checks`
failed the Saved reports view keyboard-focus assertion in
`scripts/browser_acceptance.mjs:700` ([CI
44897548076](https://github.com/kendshhh/PhishLens/actions/runs/44897548076)).
Workflow lint [44897548088](https://github.com/kendshhh/PhishLens/actions/runs/44897548088),
dependency security/graph [44897548010](https://github.com/kendshhh/PhishLens/actions/runs/44897548010),
deterministic evaluation [44897548070](https://github.com/kendshhh/PhishLens/actions/runs/44897548070),
and the Secretary report [44897544530](https://github.com/kendshhh/PhishLens/actions/runs/44897544530)
passed. Staging integration and hosted checks were skipped, and required
`Secretary staging` failed in [44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167).
No current PR CodeQL, Render deployment or authenticated CRUD evidence exists.
These workflow outcomes are not performance samples.

The 11:21 completed PR-head workflow snapshot was docs-only SHA `dffdc4c`
([CI 44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208)): Backend, Extension, migration preflight and Staging integration passed. Hosted staging/preflight were skipped; required `Secretary staging` failed in [44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685) because the hosted request label and exact-head verification were absent. The docs-only sync after that snapshot needs separate checks. No Render deploy or authenticated CRUD occurred; this status sample is not a performance measurement.

The following completed docs-only head, `f79098cc075784563d2022cbca87d7abe8f0a635`,
also passed Backend, Extension, migration preflight and Staging integration in
[CI 44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736).
Workflow lint [44899191771](https://github.com/kendshhh/PhishLens/actions/runs/44899191771),
dependency security/graph [44899191710](https://github.com/kendshhh/PhishLens/actions/runs/44899191710),
deterministic evaluation [44899191787](https://github.com/kendshhh/PhishLens/actions/runs/44899191787),
and the Secretary report [44899190365](https://github.com/kendshhh/PhishLens/actions/runs/44899190365)
passed. Hosted staging/preflight were skipped; required `Secretary staging`
failed in [44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134).
No current PR CodeQL, Render deployment or authenticated CRUD evidence exists.
This is a check snapshot, not a performance sample; the next docs-only sync
needs its own checks.

Render metadata reports auto-deploy disabled for both services. Production's
latest deployment record nevertheless has trigger `new_commit`; this discrepancy
is unresolved. See the [current environment map](environment-map-2026-11-21.md)
and [release record](release-record-2026-11-21.md). The November 20
delivery sample below remains the latest performance measurement; its service
identity is historical.

## Latest measured delivery sample — 2026-11-20 17:05 UTC

The four latest successful `CI` push runs available at the 17:05 UTC cutoff
covered successive `main` commits through
`811980c2cbf70d9957146bf329627f0826a018f1`. Workflow wall time from run start
to completion had median **1.30 minutes**, nearest-rank p90 **1.90 minutes**,
and range **1.10–1.90 minutes** (`n=4`). The latest [CI run
44779598624](https://github.com/kendshhh/PhishLens/actions/runs/44779598624)
passed Backend and Extension checks. Associated [AI evaluation
44779598647](https://github.com/kendshhh/PhishLens/actions/runs/44779598647),
[workflow lint 44779598943](https://github.com/kendshhh/PhishLens/actions/runs/44779598943),
[dependency security 44779598600](https://github.com/kendshhh/PhishLens/actions/runs/44779598600)
and [CodeQL 44779598763](https://github.com/kendshhh/PhishLens/actions/runs/44779598763)
also passed on that SHA. The scheduled [Production drift run
44812619162](https://github.com/kendshhh/PhishLens/actions/runs/44812619162)
passed source-SHA, health and readiness checks.

This is a historical performance sample, not the current main check result.
Main later advanced to `06f89d7a0b5b9dec316dfa11f2846767a32086c5`, then to
`95975cd47dceeac74ea36054610956f0a1db1fa9`. The CI failure at packaged-extension
Chromium browser acceptance on `06f89d7` in
[44885148600](https://github.com/kendshhh/PhishLens/actions/runs/44885148600)
is historical; the merged `95975cd` snapshot passed its complete CI and CodeQL
checks. The `06f89d7` Backend passed.
Workflow lint [44885148613](https://github.com/kendshhh/PhishLens/actions/runs/44885148613)
and dependency security [44885148629](https://github.com/kendshhh/PhishLens/actions/runs/44885148629)
passed. Those current statuses are not included in the timing sample above.

Render's 20 most recent production deploy records through November 20 17:05 UTC
showed one live deploy, 19 deactivated deploys and no failed statuses. Deployment
duration median was **74.1525 seconds**, nearest-rank p90 **93.142 seconds**,
and range **60.299–408.027 seconds** (`n=20`). At the November 21 07:31 UTC
service refresh, production remained Live on `811980c`; staging was Live on
`ba0b6c5`. Their deployment identities do not establish an accepted package or
staging promotion.

The timing sample is descriptive, not a before/after experiment. It excludes
queue time before workflow start, PR protected-environment waits, merge-to-live,
user-flow latency, inference cost and recovery. No speed improvement is
established. Do not present these workflow or deploy durations as extension
journey performance. No production inference or product data reads were part of
this metric refresh.

## Previous measured delivery sample — 2026-11-20 13:45 UTC

The latest four completed `CI` push runs to `main`, through PR #256, all
succeeded. Their workflow wall-time median was **66 seconds**, p90 **82
seconds**, and range **64–82 seconds**, measured from `startedAt` to
`updatedAt` (n=4). The latest run is
[44745905952](https://github.com/kendshhh/PhishLens/actions/runs/44745905952)
on main SHA `0c382dda175db3570e6bb7122841122254ba131d`; its backend and extension
jobs passed. Associated [workflow lint](https://github.com/kendshhh/PhishLens/actions/runs/44745905840),
[dependency security](https://github.com/kendshhh/PhishLens/actions/runs/44745905799),
[deterministic AI evaluation](https://github.com/kendshhh/PhishLens/actions/runs/44745905844)
and [CodeQL](https://github.com/kendshhh/PhishLens/actions/runs/44745905883)
also succeeded. Staging integration and hosted staging were skipped.

Render now has 23 completed deploy records in the November 15–20 window: one
`live`, 22 `deactivated`, and no failed statuses. Their duration median was
**74.379 seconds**, p90 **93.142 seconds**, and range **60.299–408.027 seconds**;
the first deploy started at 08:21:34 UTC on November 15 and the latest finished
at 13:44:56 UTC on November 20. The two newest deploys for `0c382dd` took
**97.316 seconds** (`dep-dc04rb0473hc738839ug`) and **66.954 seconds**
(`dep-dc04t5dg1s2s73e5pc00`, the environment update that set
`AI_ANALYSIS_ENABLED=false`). The latest deploy is Live on the same SHA as
main. Direct post-deploy endpoint GETs from this audit client returned HTTP
403, so health/readiness and the effective disabled model state were not
verified by this refresh.

Sources: [GitHub main workflow runs](https://api.github.com/repos/kendshhh/PhishLens/actions/runs?branch=main&per_page=100)
and the [Render production deploy inventory](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys).
This small latest-sample refresh is not a comparable optimization experiment.
It excludes PR pipeline time, queueing before workflow start, merge-to-live,
user-flow latency, cost and recovery. It cannot establish improvement against
the October 17–November 14 baseline below. The optimization criterion remains
**not met** until a like-for-like before/after experiment measures the same
workflow and check set over a sufficiently broad sample. No production
inference was sent. Do not present health/readiness timing as extension journey
latency or report AI cost without a verified inference path.

## 28-day delivery snapshot — 2026-11-14 03:12 UTC

Reporting window: **2026-10-17 00:00 UTC through 2026-11-14 03:12 UTC**.
Sources are the GitHub Actions `CI` workflow API, the GitHub merged-PR API, and
the Render production service deploy inventory. Run-level records are in
[ci-runs-2026-11-14.csv](evidence/ci-runs-2026-11-14.csv) and
[production-deploys-2026-11-14.csv](evidence/production-deploys-2026-11-14.csv).

| Metric | Current measurement | Sample and calculation |
|---|---|---|
| PR pipeline wall time | Mean **175.87 min**; median **4.58 min**; p90 **205.08 min** | 682 completed PR workflow attempts across 110 head branches; elapsed from `run_started_at` to `updated_at`. Attempts include synchronize events and reruns; this is not 682 distinct PRs. |
| PR pipeline success | **82.14%** when cancelled runs are excluded; **75.51%** including cancellations | 515 success, 112 failure, 55 cancelled; 515/(515+112), and 515/682 respectively. |
| Main pipeline wall time | Mean **1.39 min**; median **1.18 min**; p90 **1.92 min** | 86 completed main-push runs, all successful; same start-to-completion calculation. |
| Main pipeline success | **100%** | 86 success, 0 failed, 0 cancelled completed main-push runs. |
| Production deploys | **69 deploy records**; 1 currently `live`, 68 `deactivated` after later deploys; 0 failed statuses | Render inventory for this window; deploy duration n=69, mean **89.06 s**, median **74.23 s**, p90 **87.92 s**. |
| Merge-to-live | Mean **4.40 min**; median **3.42 min**; p90 **5.47 min** | 64 distinct merged PR SHAs matched to a Render deployment finish time. Of 95 merged PR SHAs, 31 had no matching deploy record; 5 deploy records had no unique merged-PR match. |
| Failed production deploys | **0 observed** | 69 deploy records in this window; this is not a lifetime count. |
| Time to recover | **Unknown** | No failed production deploy was observed, so recovery-time sample **n=0**; do not report zero minutes. |
| Change made and measured effect | **No speed improvement established** | At this November 14 snapshot, local work added deterministic AI evaluation, spend controls, security gates, and deployment-smoke coverage. The 40-case TF-IDF development evaluation found 18.75% phishing recall; the model threshold was not approved. That work was not yet merged/deployed at the snapshot and had no comparable after-pipeline sample. |

The PR pipeline mean is dominated by environment wait, not runner execution. The
longest sampled run was 111.4 hours: its Backend, Extension, and Staging
integration jobs finished in about a minute each, but `Hosted staging` began
more than four days later. Example: [run 39454875889](https://github.com/kendshhh/PhishLens/actions/runs/39454875889)
finished its ordinary jobs on October 20 and started the protected hosted job
on October 25. This is operational delay that needs a queue/approval policy
review; it is not a reason to omit the protected check.

The snapshot is descriptive, not a before/after experiment. The existing cached
uv backend comparison remains **n=2 baseline and n=2 candidate** and measures
the Backend job only. Its candidate median was 50.92 s versus 61.52 s, but that
small job-level sample does not establish a reliable end-to-end improvement.
PR and main workflows also have different check sets and are not an equivalent
optimization pair. No timing win is claimed.

## Historical observations

## Current main deployment observation — October 28, 2026

At 2026-10-28 15:39 UTC, main was `6414914dfa8eb8322839597c4cd6912145a442a0`.
[Main CI run 40715810349](https://github.com/kendshhh/PhishLens/actions/runs/40715810349)
passed Backend and Extension; [Workflow lint run 40715810515](https://github.com/kendshhh/PhishLens/actions/runs/40715810515)
passed. Render production deployment
[`dep-dbh18p6i0phs73d1mtag`](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dbh18p6i0phs73d1mtag)
was Live on that exact SHA. `/version`, `/health`, and `/ready` all returned
HTTP 200; `/version` identified production and the same SHA, and `/ready`
reported `database: connected`.

Render reported a 73.525-second deployment duration from `startedAt` to
`finishedAt`. This is one deployment observation, not merge-to-live lead time.
The earlier 150.607-second merge-to-live observation refers to `e4ea032` and
must not be attributed to this deployment. Production CRUD persistence after
refresh/redeploy, user-facing latency, a controlled recovery duration, and a
comparable optimization gain remain unmeasured. No production write was made.

## Read-only production endpoint timing — October 28, 2026 15:50 UTC

Five sequential GET requests per route were timed from this Windows PowerShell
client with `Invoke-WebRequest`; no saved-analysis route or production data was
read. All 10 requests returned HTTP 200.

| Route | Samples (ms, request order) | n | Min | Median | Max |
|---|---|---:|---:|---:|---:|
| `/health` | 835.5, 183.2, 414.3, 179.2, 227.7 | 5 | 179.2 | 227.7 | 835.5 |
| `/ready` | 868.6, 99.3, 185.4, 496.9, 243.7 | 5 | 99.3 | 243.7 | 868.6 |

These are client round-trip times, including local network/TLS/Render routing and
any runner or service startup variance; they are not server processing times.
The sample is small and ranged widely, so it is a smoke baseline only. It does not
measure extension/API user-flow latency, throughput, or load behavior. Do not
compare it with CI job/deploy durations or claim a performance improvement.

## Previous staging deployment observation — October 28, 2026 17:07 UTC

PR #86 head `aa91511c7eb0c43b8d52eb3adc26ac607a537293` passed Hosted staging.
Render deployment
[`dep-dbh2cjnf3r2c73emoprg`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh2cjnf3r2c73emoprg)
is Live on exact merge SHA `d46cc09ecf7258a6bd10475f00cc8da035ef5e9a`.
Read-only `/version`, `/health`, and `/ready` requests at 17:07 UTC returned
HTTP 200; version identified the exact merge SHA and `staging`, and readiness
reported a connected database. The target maps to Neon `pr-58-staging` /
`phishlens_dev`.

A 17:05 UTC read-only grant check still found `CREATE` on the public schema and
`INSERT`, `UPDATE`, and `DELETE` on `alembic_version`, `analyzed_emails`, and
`users` for `phishlens_staging_app`. No staging or production write was made.
The prior guarded CRUD result belongs to deactivated SHA `e3c6e37`; it does not
verify this candidate. The runbook requires environment-owner privilege cleanup
and a second read-only check before exact-SHA staging CRUD acceptance. Production
persistence after refresh/redeploy, installed-Chrome behavior, recovery
duration, and a comparable whole-pipeline gain remain unmeasured.

## Current post-merge staging acceptance — October 29, 2026 00:31 UTC

PR #86 merged at 00:11 UTC. Production is Live on merge commit
`1344fcb061272bac93ced5911f1ab8fbb3b6785d`; staging is Live on candidate SHA
`fc7db9bf5441af4cd68ec2efbcbc7ac8efdc20a2`. Read-only version, health, and
readiness checks returned HTTP 200 for both. The authorized exact-SHA staging
CRUD verifier passed and removed its synthetic record. No production write was
made. These are delivery/acceptance checks, not a new performance sample; the
cache comparison still shows no whole-pipeline improvement, and recovery
duration remains unknown.

## Historical PR #86 gate snapshot — October 28, 2026 17:31 UTC

At this snapshot, PR head `dcafd2f539a3dafdc6a3c50e62cc35ae71c24d86` passed all
automated checks except Hosted staging, pending at the protected `staging`
environment; diagnostics returned no steps or reason. The Live deployment above
belongs to the previous PR code head, so it is not current-head deployment
proof. The mapped staging role still has excess grants, and no staging or
production write was made.

## October 21 review (UTC observations October 20)

[Raw run/job timestamps and bounded sample](evidence/2026-10-21-ci-measurements.json).
At collection, 119 CI workflow IDs were returned: 85 success, 15 failure,
14 cancelled, three pending, one waiting and one in progress. This includes the
invalid CI-definition run named `.github/workflows/ci.yml` as a real failure.
Latest-outcome success rate excludes cancelled/pending/waiting/in-progress:
85 / (85 + 15) = 85.00%. Intentional failures remain in the failure count.

Five latest successful PR samples average 739.4 seconds including hosting/approval
queues; five latest successful main-push samples average 101.2 seconds. These are
different populations with changing coverage and cannot show an optimization gain.
Production observer 39449283551 succeeded for main 149808e and published artifact
12276999746. Deployment count, failed deploy count, merge-to-live and recovery
duration have not been freshly extracted; retain prior values as historical,
not zero. The comparative staging experiment is documented in optimizations.md.

The [Secretary observer](secretary-verification.md) implements a new 28-day,
latest-workflow-attempt calculation and produces downloadable evidence artifacts.
It does not overwrite this historical log or push metrics commits. Its durations
include workflow queue/rerun delay; the older job-only averages below use a
different method. Keep reporting periods/sample counts/sources with each entry.
The automation is now merged on main. See the October 19 Week 1 verification
record for observed runs; no optimization gain is inferred from implementation.

## Secretary read-only baseline — October 19, 2026

Source: [ten latest CI runs and job end timestamps](evidence/secretary-baseline-2026-10-19.json).
This bounded sample has 10 workflows, eight successes and two failures, with
zero cancellations or pending runs: latest-outcome success rate 80%. Eight PR
samples average 158.25 seconds (2.64 minutes); two main samples average 89.5
seconds (1.49 minutes). Durations run from workflow creation to the last job end.
These runs have different coverage/hosting behavior and are not a controlled
optimization comparison. Production count, merge-to-live, and recovery are not
available from this CI-only sample; see existing historical observations below.

Record actual measurements before each consultation.
Do not invent results or treat individual observations as averages.

## Sprint 1 Observations

| Observation | Result | Evidence |
|---|---|---|
| Main CI after PR #11 merged | Passed; displayed duration 18 seconds | Commit 717334d |
| Initial Render deployment | Successful; 50.3 seconds | Commit 717334d |
| Runbook PR backend-check job | Passed; 11 seconds | CI run linked below |
| Automatic deployment after PR #12 merged | Successful; 44.9 seconds | Commit 8a8634e; trigger Auto-Deploy |
| Public /health after automatic deployment | Expected JSON returned | Public endpoint linked below |

Job duration, workflow duration, and deployment duration are
different measurements. Do not combine them into one average.

## Required Sprint Metrics

| Metric | Result |
|---|---|
| Measurement period | Runs started October 14, 2026, 00:15:46-12:56:04 GMT+8; snapshot through readiness merge 2a70ad3 |
| PR pipeline runs sampled | 16 completed, single-job runs |
| Average PR pipeline duration | Backend job execution: 25.94 seconds (0.43 minutes); queue/orchestration overhead excluded |
| Main pipeline duration | Average backend job execution: 32.14 seconds (0.54 minutes), 7 runs |
| Pipeline success rate | 20/23 = 86.96%, including 2 intentional drill failures; PR 13/16 = 81.25%, main 7/7 = 100% |
| Successful production deployments | Multiple dashboard-evidenced automatic, initial and manual deployments; full deduplicated Render inventory pending, so no aggregate count claimed |
| Merge-to-live lead time | Not measured |
| Failed production deployments | 1 observed restoration timeout; full Render history not directly accessible |
| Recovery time | Rollback operation: 35.7 seconds; complete restoration/outage recovery time not measured |

These values describe the recorded baseline, not necessarily
the latest state of every run or deployment.

## Measurement Method

- Record the measurement period and sample count.
- Use complete GitHub Actions run timings for pipeline duration.
- Keep individual job timings separate from workflow timings.
- Calculate success rate as successful completed runs divided
  by all successful and failed completed runs in the period.
- Record cancelled and in-progress runs separately.
- Include intentional CI drill failures in the overall success
  rate and identify them explicitly.
- Measure merge-to-live lead time from merge to verified live service.
- Measure recovery time from service failure to restored service.
- Include links supporting each result.

Deployment duration alone is not merge-to-live lead time.

## CI Failure-and-Repair Evidence

- [Intentional failing run](https://github.com/kendshhh/PhishLens/actions/runs/38430884810)
- [Repaired passing run](https://github.com/kendshhh/PhishLens/actions/runs/38431990720)

Failure introduced: the test expected HTTP 201 while /health
returned HTTP 200.

Repair: restored the expected status to HTTP 200.

This was an intentional PR CI drill, not a failed production deployment.

## Deployment Evidence

- [Runbook PR CI run](https://github.com/kendshhh/PhishLens/actions/runs/38501111554)
- [Backend scaffold PR #11](https://github.com/kendshhh/PhishLens/pull/11)
- [Runbook PR #12](https://github.com/kendshhh/PhishLens/pull/12)
- [Public health endpoint](https://phishlens-api-ocvt.onrender.com/health)

Verified health response:

    {"status":"ok","service":"phishlens-api"}

Render observations:
- Initial deployment: commit 717334d; 50.3 seconds.
- Subsequent deployment: commit 8a8634e; 44.9 seconds.
- Subsequent trigger: Auto-Deploy.
- Auto-Deploy setting: After CI Checks Pass.

## Measured CI snapshot

[CI run evidence](ci-run-evidence.csv) records exact job start/end timestamps,
conclusions, commits, and source URLs from the public GitHub API.
There were 23 completed backend jobs: 20 success, 3 failure, no cancellations.
Two failures were deliberate drills and one was database-PR lint.
Excluding only the two deliberate drills gives 20/21 = 95.24%; this secondary
rate does not replace the inclusive 86.96% result.

Each run currently has one backend job. The calculated values measure execution
from job started_at to completed_at, not the entire workflow wall-clock duration.
Do not substitute the API updated_at timestamp for workflow completion time.
Coverage changed during this period, so these averages are not optimization evidence.

Additional dashboard observations:
- Manual deployment of 67538f8: 56.2 seconds.
- Automatic deployment of PR #13, a6336de: 48.9 seconds.
- Environment-save redeployment of 3ae80c2: 45.3 seconds, manual trigger.
- Another displayed Live deployment of 3ae80c2: 58.1 seconds; trigger not
  shown on that screenshot, so do not infer it from the duration alone.

Direct main CI sources:
- [PR #14 main run](https://github.com/kendshhh/PhishLens/actions/runs/38510446866)
- [PR #15 main run](https://github.com/kendshhh/PhishLens/actions/runs/38512502699)
- [Readiness main run](https://github.com/kendshhh/PhishLens/actions/runs/38513965042)

Direct Render deployment record links remain to be collected.

The health endpoint verifies the backend process only.
Database connectivity is established separately by the public /ready endpoint,
which was independently checked and returned HTTP 200 with
{"status":"ready","database":"connected"}. This does not prove the full
schema, correct environment selection, frontend integration, or AI behavior.

## Optimization Log

| Change | Before | After | Evidence |
|---|---|---|---|
| No measured optimization verified | Not measured | Not measured | Pending |

The two deployment durations are baseline observations.
Their difference alone does not prove an optimization.

## Remaining Measurements

- Extend the recorded snapshot as new runs finish.
- Capture whole-workflow duration separately from job execution time.
- Record merge-to-live lead time.
- Audit failed production deployments.
- Collect restoration duration and attach rollback deployment links.
- Measure future optimizations using comparable before-and-after runs.

## October 21 hosted verification follow-up

Read-only Render inspection now supplies a direct production deployment identity:
[dep-dbbois67bikc73b06fpg](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dbbois67bikc73b06fpg).
Main `149808e` deployed automatically (`new_commit`, service configured for
`checksPass`) and finished at 2026-10-20T15:33:17.294784Z. The merge commit timestamp
is 15:30:13Z: **184.294784 seconds** merge-to-live for this single observation.
Fresh browser response bodies matched version, health, readiness and synthetic
history. No new deployment or write was initiated. Full CRUD and recovery duration
remain unverified. [Sanitized source evidence](evidence/2026-10-21-hosted-verification.json).

## Week 1 verification follow-up - October 19, 2026

[Verified gate, frontend failure/repair, and timing evidence](week-1-verification-2026-10-19.md).
Main CI 39185832544: one successful sample at d6e5998; workflow creation to last
job completion was 98 seconds. Backend execution 49 seconds, extension 7 seconds,
staging integration 44 seconds. Hosted staging skipped on main by design.
This is one observation, not a comparable before/after optimization experiment.
Production evidence run 39185962984 succeeded; its downloaded report is retained
in [the source JSON](evidence/week1-production-2026-10-19.json).
Reporting period: September 21 through October 19, 2026, approximately 01:34 UTC.
66 workflows: 58 successful, 8 failed, zero cancelled/pending; latest-outcome
success rate 87.88%. PR durations: 47 samples, 103.49 seconds average; main:
18 samples, 51 seconds average. Coverage varies; no optimization gain is claimed.
The bounded deployment snapshot reports one currently live and one failed deploy;
these are not lifetime totals. One matched merge-to-Render-live sample is 172.56
seconds. Recovery time is unavailable. The observer verified production SHA
 d6e5998, health, and readiness at 01:35:35 UTC. Direct public read-only probes
subsequently returned 200 for version, health, readiness, and synthetic history.

## October 28 current delivery sample

PR #84 merged as `e4ea032615a6663d787a5b44714b5fc982fc6355` at
2026-10-28T05:14:47Z. Main CI
[40636853223](https://github.com/kendshhh/PhishLens/actions/runs/40636853223)
passed Backend checks and Extension checks. Render production deployment
[`dep-dbgoa7i9lscs738tse0g`](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dbgoa7i9lscs738tse0g)
was triggered by `new_commit` and went live at 05:17:17.607Z. Merge-to-live for
this single sample is **150.607 seconds**. Render deploy duration was 63.274
seconds. The production `/version`, `/health`, and `/ready` endpoints each returned
HTTP 200; the version matched the merged SHA and readiness reported a connected
database. This is one measured delivery sample, not an optimization comparison.

The staging service was live on exact SHA
`e3c6e37fd6661aeb582bd000507ef8cac677c23f`; its `/version` identified `staging`
and `/ready` returned HTTP 200. The guarded synthetic CRUD verifier passed against
that staging SHA and removed the record it created. Production writes were not
performed. Production record persistence across refresh/redeploy remains unknown.

For the October 28 no-cache extension baseline and completed one-cold/one-warm
npm-cache trial, see [optimizations.md](optimizations.md). No whole-job gain was
demonstrated; the cache and instrumentation were removed. Retain sample counts
and whole-job timings; do not infer improvement from the 1–2 second install step alone.

The npm-cache trial passed Extension checks on PR #86 runs
[40638816002](https://github.com/kendshhh/PhishLens/actions/runs/40638816002)
(cold miss, `npm ci` 1 second, whole job 11 seconds) and
[40639539541](https://github.com/kendshhh/PhishLens/actions/runs/40639539541)
(warm hit, `npm ci` 1 second, whole job 18 seconds). No end-to-end gain was
demonstrated; the cache and instrumentation were removed. This small sample does
not establish that the cache caused the longer warm job.

## November 4 draft backend-install comparison

The baseline was a docs-only PR run on the current main workflow, source head
`d3872972fb868eac137fc66e1c7d0f7792336564` based on main
`6b0e97f6c2b88a469614b0ce3aaf6773a501fd7a`. Backend job
[126285015665](https://github.com/kendshhh/PhishLens/actions/runs/41741824199/job/126285015665)
ran from `2026-11-03T23:47:07.093Z` to `23:48:05.853Z`: 58.76 seconds
(`n=1`). Its two pip install steps took 8.35 and 2.62 seconds.

Draft PR #119 replaces those installs with pinned uv. Two candidate samples:

| Candidate | Source | Backend job | Time (UTC) | Duration | Install notes |
|---|---|---|---|---:|---|
| 1 | `a9d13dec40cd9b7d1118365da4502db186c36a24` | [126290854493](https://github.com/kendshhh/PhishLens/actions/runs/41743549407/job/126290854493) | 00:00:49.702–00:01:42.139 | 52.44 s | setup-uv 1.00 s; uv install 0.78 s |
| 2 | `4e6c06dac623811c78cae7dd2683b791f868b59e` | [126292223108](https://github.com/kendshhh/PhishLens/actions/runs/41743953474/job/126292223108) | 00:03:57.536–00:05:01.964 | 64.43 s | setup-uv about 0.99 s; uv install about 0.90 s; no Actions cache hit |

Both candidate runs passed Backend checks, Extension checks and Staging
integration. Hosted staging was skipped because PR #119 is draft. No test
coverage was removed.

Candidate median is 58.44 seconds (`n=2`) versus the single baseline sample
of 58.76 seconds (`n=1`), a 0.33-second (0.55%) difference. This small,
uneven sample does not demonstrate a reliable end-to-end improvement; the
pinned uv candidate remains an unmerged experiment. Do not close #40 based on
these measurements. Production deploy totals and schema/model rollback
compatibility remain separate measurements or acceptance evidence.


## November 4 cache-matched backend install comparison

This comparison isolates Backend checks job execution. The two baseline samples
use the current-main pip-cache workflow; the two candidate samples use PR #119
head `33e942625f69bcc7bd2f4ed259817b59b17a81a9`, with the same pip cache and
cache dependency paths. All four runs report a restored/hit cache and passed
the Backend checks job. Candidate PR CI also passed Extension checks and
Staging integration; Hosted staging was skipped because PR #119 was draft.

| Sample | Source | Run/job | Backend job UTC | Whole job | Install step(s) |
|---|---|---|---|---:|---:|
| Baseline 1 | `d3872972fb868eac137fc66e1c7d0f7792336564` | [41741824199 / 126285015665](https://github.com/kendshhh/PhishLens/actions/runs/41741824199/job/126285015665) | 23:47:07.089–23:48:05.853 | 58.76 s | 8.35 s + 2.62 s |
| Baseline 2 (job rerun) | same source | [41741824199 / 126311833476](https://github.com/kendshhh/PhishLens/actions/runs/41741824199/job/126311833476) | 00:50:36.895–00:51:41.177 | 64.28 s | 7.22 s + 2.05 s |
| Candidate 1 | `33e942625f69bcc7bd2f4ed259817b59b17a81a9` | [41749865555 / 126312057648](https://github.com/kendshhh/PhishLens/actions/runs/41749865555/job/126312057648) | 00:51:10.725–00:52:10.318 | 59.59 s | 9.91 s |
| Candidate 2 (job rerun) | same source | [41749865555 / 126313726898](https://github.com/kendshhh/PhishLens/actions/runs/41749865555/job/126313726898) | 00:55:23.356–00:56:28.560 | 65.20 s | 9.92 s |

Baseline median is 61.52 seconds (`n=2`); candidate median is 62.40 seconds
(`n=2`), 0.88 seconds (1.42%) slower. The single pinned `--no-deps` install
step median is 9.92 seconds versus 10.12 seconds for both baseline install
steps together, a 0.20-second (2.0%) step-level difference. This small sample
does not demonstrate a whole-job improvement; job setup/database/test variance
is larger than the install-step difference. The candidate remains an
unmerged experiment and should not be described as a verified optimization.


## November 4 cached uv backend-job comparison

A second, cache-hit comparison used the pinned uv workflow from source
`4e6c06dac623811c78cae7dd2683b791f868b59e`. The test commands and Backend
checks stayed unchanged. Both baseline and candidate used restored dependency
caches; all measured Backend checks jobs passed. The candidate run also passed
Staging integration. Hosted staging was skipped while PR #119 was draft.

| Sample | Source/workflow | Run/job | Backend job UTC | Duration | Cache |
|---|---|---|---|---:|---|
| Baseline 1 | main pip workflow | [41741824199 / 126285015665](https://github.com/kendshhh/PhishLens/actions/runs/41741824199/job/126285015665) | 23:47:07.089–23:48:05.853 | 58.76 s | pip hit |
| Baseline 2 | same main pip workflow | [41741824199 / 126311833476](https://github.com/kendshhh/PhishLens/actions/runs/41741824199/job/126311833476) | 00:50:36.895–00:51:41.177 | 64.28 s | pip hit |
| Candidate 1 | pinned uv; source `4e6c06d` | [41743953474 / 126317649176](https://github.com/kendshhh/PhishLens/actions/runs/41743953474/job/126317649176) | 01:05:22.953–01:06:13.187 | 50.23 s | uv hit |
| Candidate 2 | same pinned uv workflow | [41743953474 / 126318609442](https://github.com/kendshhh/PhishLens/actions/runs/41743953474/job/126318609442) | 01:07:46.986–01:08:38.587 | 51.60 s | uv hit |

The baseline median is 61.52 seconds (`n=2`); the cached uv median is 50.92
seconds (`n=2`), 10.61 seconds (17.2%) lower. These are Backend job durations,
not complete PR workflow wall times. The small sample is an encouraging
measured candidate, not a guarantee for every run. Earlier uncached and mixed
uv trials remain separately reported above and are not included in this
cache-hit comparison.

The current PR branch now uses the same pinned uv setup and cache dependency
globs. Its new-head CI must pass before treating the updated PR head as verified.

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.

### PR #268 exact-head snapshot — 2026-11-21 12:02 UTC

Retargeted PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security and graph review, deterministic evaluation, DevOps Secretary report, and all three CodeQL analyses. [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617) completed at 12:02 UTC. Hosted staging preflight and Hosted staging were skipped. The required `Secretary staging` status failed because the `needs-hosted-staging` label and exact-head hosted verification were absent ([assessment 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269)); no Render deployment or authenticated hosted CRUD occurred. GitHub reports the PR open and mergeable on `main`; the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. The release remains **NO-GO**, and 41/100 is a descriptive evidence-progress score only. This documentation-only evidence update requires fresh exact-head CI before merge. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

### PR #268 main-sync snapshot — 2026-11-21 12:14 UTC

PR #268 now includes current `main` through `31e86c7` in merge head `aee49fe5a11da37ed441464c80ad9a09e0b9dda8`. Exact-head CI run [44902645800](https://github.com/kendshhh/PhishLens/actions/runs/44902645800) passed Backend, Extension, Staging integration and migration preflight. Workflow lint [44902645811](https://github.com/kendshhh/PhishLens/actions/runs/44902645811), dependency security/graph [44902645851](https://github.com/kendshhh/PhishLens/actions/runs/44902645851), deterministic evaluation [44902645832](https://github.com/kendshhh/PhishLens/actions/runs/44902645832), and CodeQL [44902643383](https://github.com/kendshhh/PhishLens/actions/runs/44902643383) passed. The exact-head DevOps Secretary report was cancelled during the branch sync ([44902644757](https://github.com/kendshhh/PhishLens/actions/runs/44902644757)); the Secretary preview assessment reports required `Secretary staging` failure because the `needs-hosted-staging` label and exact-head hosted verification are absent ([44902874550](https://github.com/kendshhh/PhishLens/actions/runs/44902874550)). Hosted preflight/deployment were skipped; no Render deploy or authenticated CRUD occurred. GitHub shows PR #268 open, mergeable on `main`, with review decision `CHANGES_REQUESTED`. Release remains **NO-GO**; 41/100 is descriptive evidence progress, not completion. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
