# Secretary verification and rollout log

## Hosted-controller status snapshot — 2026-11-21 13:45 UTC

At 13:45 UTC, PR #268 head `9036132d8ff70cbf9ceae97175a7f59ba0b1e61d`
targeted `main` at `31e86c78523cbdcfb6da83f99d331c86409bf0fa`; PR #265 had
merged. Backend, Extension, Staging integration, migration preflight, workflow
lint, dependency, evaluation, CodeQL and the Secretary report passed on this
head. Hosted preflight passed; Hosted staging is waiting at the protected
`staging` environment and has not started. The previous head failed on a stale
endpoint pin; this head updates the pin and fixtures. The hosted `Secretary
staging` assessment remains pending successful exact-head hosted verification.
Collaborator re-review remains pending. The dated PR checks below are historical
snapshots.

The latest observed staging route is the legacy hosted-staging workflow in
`origin/main`'s `.github/workflows/ci.yml`: it deploys via the trusted default
branch controller, runs `scripts/staging_smoke.mjs`, then invokes the exact-PR
head `scripts/verify_crud.mjs --allow-writes`. Main commit
`06f89d7a0b5b9dec316dfa11f2846767a32086c5` added a Bearer-aware helper so a
valid anonymous `401 Bearer` response passes the smoke's auth-boundary check.
The supplied earlier smoke log omitted the HTTP status/body, so it does not
prove that this was its response. Review branch merge commit `14874d339bbb4042172df954f97596080aa303ee` adds
bounded transient-only retries, endpoint/status/error summaries, local
server-exit monitoring and log retention, plus fail-closed hosted deployment
conditions. Code/test commit `83a0df1af1d64048b3b5fa3158f6509e83d71555` passed
321 Node tests and a fresh GET-only staging smoke passed at about 08:35 UTC.
PR #265 has merged to main at `95975cd`; CI and CodeQL passed for that main
revision. Earlier verified PR head `631b0ef21849e8abe877bb16b4676047f2aca86a`; CI
[44888140094](https://github.com/kendshhh/PhishLens/actions/runs/44888140094),
workflow lint [44888140104](https://github.com/kendshhh/PhishLens/actions/runs/44888140104),
dependency security [44888140135](https://github.com/kendshhh/PhishLens/actions/runs/44888140135),
and deterministic evaluation [44888140114](https://github.com/kendshhh/PhishLens/actions/runs/44888140114)
passed.
Hosted staging and preflight were skipped. The PR's `Secretary staging`
context is **failed** with the message that `needs-hosted-staging` and exact-head
hosted verification are required ([check run
44888369939](https://github.com/kendshhh/PhishLens/actions/runs/44888369939)).
The controller assessment passed but skipped its preview job; no Render deploy
or CRUD ran. The CRUD step has no authenticated session and remains a blocker.
These results apply to `631b0ef`; the PR #265 documentation reconciliation
requires fresh checks on the resulting PR head.
At 09:22 UTC the later remote PR head `7dbebfd060298a80e99a38a52663901e776935cb`
had Backend, Extension and migration source preflight passed; Staging
integration remained in progress. Workflow lint, dependency security and
deterministic evaluation passed. Dependency graph review failed because GitHub
reports the repository Dependency graph is disabled. CodeQL later failed its
three language jobs; annotations attribute the failure to Actions installation
API rate limits and report no CodeQL findings. By 09:31 UTC, Staging integration
had passed, while hosted staging and preflight remained skipped. Secretary report
[44889108682](https://github.com/kendshhh/PhishLens/actions/runs/44889108682)
said **WAITING FOR CHECKS** at 09:22. Hosted staging was not requested. The exact
timestamped result and scope are in the
[staging evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
At 10:14 UTC, PR #268 head `2e26327254c71b6cb7d655181cffb21e8dd1ee9b` passed
Backend, Extension, migration preflight, Staging integration, hosted preflight,
workflow lint, dependency security, Dependency graph review and deterministic
evaluation. Hosted staging job 136807616481 ended with conclusion success, but
its final freshness guard marked the request superseded after the label was
removed at 09:54 UTC; deployment, smoke, CRUD and artifact steps were skipped.
The job summary classifies it as blocked. Required `Secretary staging` failed
in [run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807).
No current PR CodeQL result appeared. Authenticated CRUD remains unverified.
PR #268 still targets the merged PR #265
branch; retarget it to main before merge. The exact run links and prior CodeQL
rate-limit failure are in the
[staging evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

At 11:08 UTC, PR #268 head was `a151585ff92d55f21e0364e9838287a9cf04a68d`.
The Secretary report workflow passed in [run 44897544530](https://github.com/kendshhh/PhishLens/actions/runs/44897544530),
but required `Secretary staging` failed in [run 44897660167](https://github.com/kendshhh/PhishLens/actions/runs/44897660167)
because the request label and exact-head hosted verification were absent.
`Extension checks` also failed; Staging integration and hosted staging were
skipped. No hosted deployment or authenticated CRUD was run. The 10:14
snapshot above applies to the previous head only.

On preceding docs-only follow-up head `dffdc4c29338142f458350b51c8ce69e0f36e988`,
Backend, Extension, migration preflight and Staging integration passed in [CI
44898467208](https://github.com/kendshhh/PhishLens/actions/runs/44898467208).
The Secretary report passed in [44898465856](https://github.com/kendshhh/PhishLens/actions/runs/44898465856),
but required `Secretary staging` failed because the hosted request label and
exact-head verification were absent ([run
44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)).
Hosted preflight/deployment were skipped; this is not staging acceptance.

The latest completed head `f79098cc075784563d2022cbca87d7abe8f0a635` passed
Backend, Extension, migration preflight and Staging integration in [CI
44899191736](https://github.com/kendshhh/PhishLens/actions/runs/44899191736).
The Secretary report passed in [44899190365](https://github.com/kendshhh/PhishLens/actions/runs/44899190365),
but required `Secretary staging` failed because the request label and exact-head
hosted verification were absent ([run
44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134)).
Hosted staging preflight/deployment were skipped; this is not hosted acceptance.

The last recorded Secretary preview
variables, from November 20, were `SECRETARY_PREVIEW_ENABLED=false` and
`SECRETARY_REPLACES_LEGACY_STAGING=false`; live values were not re-read in this
audit. No current Secretary exact-head authenticated CRUD acceptance is
verified. The legacy workflow result and the Secretary preview must not be
reported as interchangeable evidence.

## Previously recorded local checks (not rerun in this audit)

Final offline suite: **36 tests passed**, comprising 31 secretary tests and
five existing deployment-guard tests. Backend suite: **70 passed, 2 skipped**;
the skips require isolated PostgreSQL. An initial sandbox run had a Windows
temporary-directory permission error; the complete rerun outside that sandbox
passed. Extension suite: **18 passed**. Configured extension lint and Ruff on
secretary/backend changed code passed. No provider credentials or live AI calls
were used by these tests.

`python -m scripts.secretary.demo` creates the example report and actual demo ZIP.
The ZIP is made from local source with a staging banner and zero SHA; it has not
been deployed and must not be presented as acceptance evidence. Final check counts
may grow as regression coverage is added; use the PR's latest run for acceptance.

| Required scenario | Evidence actually exercised | Live acceptance still needed |
|---|---|---|
| Passing PR | Pure policy says ready for human review, never approval | Bot comment and full CI on installed workflow |
| Failed check | Failure/cancelled/skipped/timeout produce changes recommended | Intentional synthetic CI failure/repaired rerun |
| Pending or missing | Explicit waiting | Running UI transitions and missing-required-check case |
| Draft | Blocked; preview not approved | Open draft then mark ready |
| New commit | Old preview rejected; stale report not posted | Push correction and inspect replaced report/build SHA |
| CI rerun | Latest attempt is selected | Rerun on GitHub and inspect current evidence |
| Duplicate events | No new comment/AI call for same fingerprint | Event delivery on installed bot |
| Agent/provider failure | Provider failure gives unavailable; report API boundary has failure fallback | Revoke test key/access safely; verify ordinary CI remains usable |
| Invalid AI JSON | Invalid objects/types/oversized summary rejected | Optional provider integration, if enabled |
| Oversized/binary diff | Coverage gap and blocked recommendation | Real large test PR without private data |
| Fork PR | Explicit action required, no preview authorization | Fork CI permission behavior and trusted-branch handoff |
| Preview failure | Failed preview blocks recommendation; controller fails check | Controlled invalid staging start on disposable data |
| Shared staging conflict | Newer SHA invalidates report and old staging check only after Render reports it live; a failed deploy leaves prior evidence valid | Two PRs queue; confirm serialized runs, then verify a failed deploy preserves the previous check |
| Production failure | Deduplicated failed-deploy metric; incident boundary implemented | Controlled drill approved by human; do not break production casually |
| Database isolation | Wrong production host/service rejected | Private Neon host/role and Render env inspection |
| Extension package | Real local assets have SHA/banner/staging-only permission and valid ZIP | Install freshly generated CI artifact in Chrome |

An offline state-machine test is not a real deployment. There are no fabricated
screenshots, automatic approvals, or production rollback claims in this log.

## Current required-status bridge — 2026-11-21

The Secretary preview workflow is now a trusted status mirror. It does not
deploy staging. The `Secretary staging` commit status is successful for an
application/runtime PR only when the same latest CI run for the current PR head
has passed Backend checks, Extension checks, Staging integration, and the
protected authenticated `Hosted staging` job. A skipped, missing, stale, failed,
or incomplete Hosted staging job produces a non-green Secretary status. A
documentation-only PR may receive a not-applicable status only after ordinary
required CI succeeds. The controller checks out the default branch and has no
Render, Neon, or deployment credentials.

This PR cannot execute its new workflow-run controller before that controller
is on the default branch. The currently installed controller is still the old
implementation until an authorized merge; no required status is manually
written or treated as passed to bypass that bootstrap boundary. A passing
`Hosted staging` run remains the direct authenticated product evidence.

## Remaining live setup and acceptance — owner records links

- [ ] Review source and trust boundaries with a teammate.
- [ ] Create/verify protected `staging`, `release-staging`, and `production-observer` environments.
- [ ] Configure a new independent schema-only Neon staging root, Neon Auth, least-privilege roles, and empty synthetic accounts. Existing `pr-58-staging` is not accepted for this run.
- [ ] Privately verify the Render staging service maps to that branch and production remains disconnected from candidate staging credentials.
- [ ] An authorized reviewer approves the protected staging job for the exact current candidate.
- [ ] Confirm the candidate ZIP/backend identities and run the authenticated extension CRUD/UX acceptance.
- [ ] Verify `Secretary staging` mirrors success only when the current `Hosted staging` job succeeds; missing/skipped/failing Hosted staging stays non-green.
- [ ] Confirm one current exact-head status and artifact after a rerun; stale runs do not overwrite the latest status.
- [ ] Install the exact fresh artifact in Chrome and record any manual checks separately from automated evidence.
- [ ] Verify main auto-deploy and the exact merged SHA in Render.
- [ ] After Render shows that SHA live, manually run **Production evidence** from
  GitHub Actions on `main`; retain the artifact and confirm `/version`, `/health`
  and `/ready` match the live deployment.
- [ ] Download metrics before artifact expiry, record the reporting period and sources.
- [ ] Perform an authorized rollback drill later, checking database compatibility first.

The production observer is deliberately `workflow_dispatch`-only. A `workflow_run`
trigger would create a separate GitHub check on the same main commit while the
observer waits for Render to deploy it. The Secretary status mirror listens only
to completed PR CI runs and does not observe or gate production deployments.

## Consultation demonstration (about 3 minutes of DevOps segment)

1. **Before the meeting:** wake the free staging and production services; open the
   PR, Actions, staging `/docs` and `/version`, Chrome test profile, metrics and
   [pipeline guide](../../PIPELINE.md). Use synthetic data only. Preserve a known
   passing artifact and run link in case cold starts take longer than the segment.
2. **Teammate PR:** Andrei opens a small UI PR linked to an issue with acceptance
   criteria. Show CI waiting/running and the bot's waiting report. Narrate that
   lint/tests are ordinary tools, not AI opinions.
3. **Preview:** after CI and deployment trust approval, show Secretary preview,
   deployed SHA, green smoke, artifact and report. Explain shared staging and why
   the SHA must match. Do not call the API `/docs` page a browser-extension preview.
4. **Manual test:** Kendra loads the artifact and tests the changed behavior in
   Chrome; compare a separately labeled production build with the same data and
   viewport. Add the manual test record. It is separate from formal approval.
5. **Correction:** demonstrate a synthetic failure in a disposable PR, a teammate
   correction, new head SHA, fresh checks and updated report. The old evidence
   must not count. Show the offline adverse-scenario tests if live timing is tight,
   and clearly identify them as offline rather than pretending a live event ran.
6. **Human review:** a teammate reviews; when Kendra is the author, someone else
   approves. An authorized human merges after required checks. The bot cannot merge.
7. **Production:** main CI passes, existing Render automation deploys, observer
   verifies exact SHA/health/readiness and uploads metrics. If it fails, show the
   incident draft and discuss recovery; human controls rollback.
8. **Explain a decision:** one shared service keeps costs/operations small, but
   only one PR can occupy it; serialization and invalidation protect evidence.
   Explain one real unresolved risk rather than claiming everything is finished.

## Metrics definitions and retention

The observer samples CI workflows created during the preceding 28 days, paginated
up to 1,000 runs; hitting the cap fails collection visibly. It counts each workflow
ID once using its latest attempt, so success is a **latest-outcome rate**, not a
measure of every rerun failure. Cancelled, pending and other conclusions are
separate. Success rate = successes / (successes + failures) × 100; failures include
failed/timed-out/action-required outcomes. Retain attempted-run data separately if
you need flakiness or first-attempt rate.

PR and main durations are separate: latest attempt's last completed job time
minus workflow creation time, including queue time. Reruns therefore include the
wait until rerun; do not compare them to older job-only averages without noting
the method. Missing timestamps mean no duration sample. This is CI workflow
duration, **not full PR-to-preview lead time**.

Render observations cover at most the latest 100 production deployments and are
filtered to the period. Deployment IDs deduplicate records. Current live and
failed states are reported separately; Render's later `deactivated` records are
not assumed to prove historical success. The live count is a bounded lower bound,
not a complete lifetime deployment count. Merge-to-Render-live uses matching
merge SHA and finishedAt, with a separate application verifiedAt. If a matching
merge timestamp is absent, lead time is not available. Recovery time remains
not available until actual failure/restoration timestamps are supplied.

Download `Veriqo-Production-Evidence/metrics.json` and add its sources to the
existing [metrics log](metrics.md) each consultation. Do not average averages
without sample counts. The observer uploads artifacts and never pushes metrics
commits. Compare like-for-like runs before adding a claimed improvement to
[optimizations.md](optimizations.md).

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.

### PR #268 exact-head snapshot — 2026-11-21 12:02 UTC

Retargeted PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security and graph review, deterministic evaluation, DevOps Secretary report, and all three CodeQL analyses. [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617) completed at 12:02 UTC. Hosted staging preflight and Hosted staging were skipped. The required `Secretary staging` status failed because the `needs-hosted-staging` label and exact-head hosted verification were absent ([assessment 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269)); no Render deployment or authenticated hosted CRUD occurred. GitHub reports the PR open and mergeable on `main`; the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. The release remains **NO-GO**, and 41/100 is a descriptive evidence-progress score only. This documentation-only evidence update requires fresh exact-head CI before merge. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

### PR #268 main-sync snapshot — 2026-11-21 12:14 UTC

PR #268 now includes current `main` through `31e86c7` in merge head `aee49fe5a11da37ed441464c80ad9a09e0b9dda8`. Exact-head CI run [44902645800](https://github.com/kendshhh/PhishLens/actions/runs/44902645800) passed Backend, Extension, Staging integration and migration preflight. Workflow lint [44902645811](https://github.com/kendshhh/PhishLens/actions/runs/44902645811), dependency security/graph [44902645851](https://github.com/kendshhh/PhishLens/actions/runs/44902645851), deterministic evaluation [44902645832](https://github.com/kendshhh/PhishLens/actions/runs/44902645832), and CodeQL [44902643383](https://github.com/kendshhh/PhishLens/actions/runs/44902643383) passed. The exact-head DevOps Secretary report was cancelled during the branch sync ([44902644757](https://github.com/kendshhh/PhishLens/actions/runs/44902644757)); the Secretary preview assessment reports required `Secretary staging` failure because the `needs-hosted-staging` label and exact-head hosted verification are absent ([44902874550](https://github.com/kendshhh/PhishLens/actions/runs/44902874550)). Hosted preflight/deployment were skipped; no Render deploy or authenticated CRUD occurred. GitHub shows PR #268 open, mergeable on `main`, with review decision `CHANGES_REQUESTED`. Release remains **NO-GO**; 41/100 is descriptive evidence progress, not completion. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
