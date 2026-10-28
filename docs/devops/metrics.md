# Pipeline Metrics

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

## Current staging observation — October 28, 2026

At 15:43 UTC, the staging service's latest Live deployment was
[`dep-dbh14vbl550s738ddfc0`](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dbh14vbl550s738ddfc0)
at SHA `57da457be77fcf7a132e3a5e2f0d704c676040d6`. Read-only `/version`,
`/health`, and `/ready` probes all returned HTTP 200; the version identified
`staging`, and readiness reported a connected database. Compared with current
main `6414914dfa8eb8322839597c4cd6912145a442a0`, this SHA is divergent (13 ahead,
one behind; merge base `79aef1a`), not the current main or PR #86 head. This is
endpoint health evidence for that staging SHA only. The prior guarded CRUD result
was on the now-deactivated `e3c6e37` SHA; no CRUD write was made against `57da457`.
The exact Neon host mapping and app-role grants remain unverified.

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

