# Week 2 finish checklist

Week 2 is October 16–22, 2026, per the retained professor report. Work after October 22 is carryover.

## Latest carryover status — October 28, 2026 17:31 UTC

The dated sections below preserve earlier Week 2 snapshots. The current Kendra
Week 1–4 crosswalk is in [kendra-week1-4-closeout-2026-10-28.md](kendra-week1-4-closeout-2026-10-28.md).
The previous PR #86 code head passed Hosted staging and its exact merge SHA is
still Live with successful read-only health/readiness checks. Current snapshot
head `dcafd2f539a3dafdc6a3c50e62cc35ae71c24d86` passed all automated checks
except Hosted staging, pending at the protected environment; no current-head
deployment is claimed. Staging CRUD remains gated because the runtime role has
excess grants. Dependency Review now runs by default unless explicitly disabled
and passed on this head. Existing status remains At risk; production persistence,
Chrome, recovery/optimization, actual team events, and Week 4 dates/issue
assignments are still open.

## Verified October 21

- PR #55: open, head 040bfdb4db34a2b9d753158ab502a1f7b9909ce7. Backend, extension and isolated staging pass in run 39521541137. Hosted staging is pending with no executed steps; the API does not establish the reason.
- PR #57: draft, head f67a8a32fd4338c7b5bf891ab6e64a49970ba777. The same three automatic checks pass in run 39522153467; hosted staging is skipped.
- Re-ran package-verifier and metrics-reporting suites: 23 tests passed. Ruff passed for both scripts and their tests. No installed-browser acceptance is claimed.

## Before Consultation 2 on October 22

- [ ] Inspect #55 hosted staging in Actions for its actual pending reason. The configured human reviewer handles any environment approval; retain shared staging serialization.
- [ ] Verify exact deployed SHA, health, readiness and hosted client smoke after execution.
- [ ] Download the matching staging artifact and evidence. Do not substitute the older local production package. The production-only verifier does not verify staging packages.
- [ ] Test in installed Chrome and record tester, timestamp, browser/version, full source/deployed SHA, artifact/run link, actions, expected/actual results, screenshots and PASS/FAIL.
- [ ] Exercise synthetic history/details, selected-text analysis, accurate mock/provider labeling, loading, empty and error states. Native app control is disabled in this session; installed-extension verification requires someone with Chrome access.
- [ ] Obtain formal teammate review for the latest head. Environment approval and bot reports do not replace it.
- [ ] Environment owner verifies Neon branch/role identity, least privilege, secret scopes and saved branch-protection enforcement. Record sanitized outcomes without credential values.
- [ ] After approved merge, trace main CI to automatic deployment; verify live SHA, health/readiness and changed behavior; record actual timings.
- [ ] Use week2-professor-report-2026-10-21.md for the consultation script. Refresh evidence before presenting.
- [ ] Participants supply actual standups, retrospective and timed rehearsal. Record actual instructor feedback, decisions, owners and dates.

## Feature-dependent acceptance

Trixia supplies reviewed persistent CRUD/database tests; Leyan and Andrei supply client/UI integration. Kendra then registers actual CRUD test IDs and verifies synthetic create/list/detail/update/delete, refresh and redeployment persistence on a confirmed test target. These remain pending until demonstrated.

Keep metrics dates and sample sizes visible. Historical Week 1 replay is not fresh Week 2 evidence. Existing samples do not establish overall pipeline speedup.

## Reconciliation and Week 3 entry — October 25, 2026

This is a current snapshot of Kendra's DevOps work. Week 1/2 dates remain
historical team planning dates; a passing component or pipeline job does not
close a full delivery issue.

### Main protection and current pull request checks

- GitHub reports `main` at `96d118eb262693edea4a5540e7bde469529963ea` and
  protected. Its branch summary lists the required contexts `Backend checks`,
  `Extension checks`, `Hosted staging`, and `Staging integration`. The branch
  protection detail endpoint returned 403 to this integration, so current
  approval count, stale-approval, bypass and review-conversation settings were
  not independently verified.
- Main CI run
  [40206846109](https://github.com/kendshhh/PhishLens/actions/runs/40206846109)
  passed Backend checks, Extension checks and Staging integration; Hosted
  staging was skipped on the main push path.
- [PR #55](https://github.com/kendshhh/PhishLens/pull/55), head
  `751b299e7fb22cf1985a41a5f4c6834ef23aa189`, run
  [40207010284](https://github.com/kendshhh/PhishLens/actions/runs/40207010284):
  Backend checks, Extension checks and Staging integration passed. Hosted
  staging is pending and has no executed steps.
- [PR #56](https://github.com/kendshhh/PhishLens/pull/56), head
  `d067ebed17967eec7bc97b8ec27e23e9c731aaa4`, run
  [40206872831](https://github.com/kendshhh/PhishLens/actions/runs/40206872831),
  and [PR #57](https://github.com/kendshhh/PhishLens/pull/57), head
  `0a3eeb75c7e7d142d02b14ce97ddf96be7d94e4c`, run
  [40206897540](https://github.com/kendshhh/PhishLens/actions/runs/40206897540),
  have the same three automatic checks passing and Hosted staging pending with
  no executed steps. The pending reason is not established by these job records.
- All three PRs remain open. No merge, deployment, hosted database write,
  teammate approval or instructor acceptance is inferred.

### Week 1 closeout

W1-D1 and W1-D2 remain verified from the merged setup/CI work. W1-D3 remains
open: historical source-to-CI/deploy and health/readiness evidence plus the
runbook are recorded, but a fresh live-SHA check for current main, a comparable
pipeline improvement/recovery measurement, and actual consultation or
retrospective evidence are not established.

Read-only production probe at approximately 2026-10-25 15:42 UTC returned
`/health` 200 (`status: ok`), `/ready` 200 (`status: ready`, database connected),
and `/version` 200 with commit
`149808e3f76d9182688b5438153f57bd3cc03774`. At that time, GitHub `main` was
`96d118eb262693edea4a5540e7bde469529963ea`, committed about 18 minutes earlier.
The `/version` endpoint was queried again at 15:43:57 UTC and still returned the
same older commit. The service was healthy but did not report the current main
SHA. The reason for the lag is unverified; recheck the Render deployment and
live SHA before marking current automatic delivery verified. These probes made
no writes or deployment changes.

### Week 2 DevOps closeout

- **Planning and carryover (#36):** scope, owner/reviewer mapping, evidence
  targets and implemented-versus-proposed interfaces are recorded in
  `docs/sprint-2.md` and
  [`sprint-2-work-2026-10-20.md`](sprint-2-work-2026-10-20.md). Unconfirmed
  API/client/AI choices remain explicitly pending; no teammate agreement is
  inferred.
- **PostgreSQL CI (#38):** PR #52 is merged and its evidence guard covers the
  existing required PostgreSQL history/relationship checks. Real persistent
  CRUD test IDs are not yet registered; keep #38 open until reviewed backend
  CRUD tests and current-head CI evidence exist.
- **Environment/package (#37):** PR #55's current CI passes package identity
  and exact-source migration-history checks. Its hosted staging job has not
  started. Private database-branch identity, least-privilege roles, scoped
  secrets, and a complete current credential/configuration audit remain open.
- **Delivery (#39):** historical main-to-production identity evidence remains
  useful and the current main check run is green. The public production
  `/version` currently reports `149808e3f76d9182688b5438153f57bd3cc03774`, while
  main is `96d118eb262693edea4a5540e7bde469529963ea`; health/readiness are 200,
  but the live source trace is not current. Reconcile the deployment and recheck
  the exact SHA. Current exact staging acceptance and persistent CRUD through a
  confirmed synthetic target also remain open.
- **Metrics/recovery (#40):** retained samples show staging install averages of
  9 seconds before and 7 seconds cached (n=2 each), while whole staging jobs
  average 40.5 versus 44 seconds. This does not establish an end-to-end gain.
  One 184.294784-second merge-to-live sample exists; comprehensive counts,
  recovery duration and a new safe recovery drill remain unknown.
- **Consultation (#41):** PR #56 carries the preparation pack. Actual standups,
  retrospective, whole-team rehearsal, integrated CRUD demonstration and
  instructor feedback must be supplied by participants; none are inferred.

### Week 3 entry — Friday October 23

The entry audit is recorded against the October 25 GitHub snapshot. DevOps
carryover remains #36–#41; PR #52 is merged partial support, while PRs #55–#57
are open. Missing gates above stay open. The Week 3 owner map in `docs/sprint-2.md`
routes backend contract/storage and PostgreSQL tests to Trixia, HTTP/client
integration to Leyan, report UI/browser acceptance to Andrei, and model
revision/label/preprocessing/evaluation inputs to Wilberr. Kendra's next
DevOps boundary is pinned, reproducible runtime plus deterministic mocked CI,
without model downloads or claiming real-provider acceptance. No dedicated
Week 3 issue set is present; use the labeled carryover IDs. W3-D2 is dated
Monday October 26 and had not started in this October 25 snapshot.

## Week 2 DevOps closeout refresh — October 26, 2026

This refresh uses the current GitHub snapshot and read-only production probes.
Week 2's planned dates remain October 16–22. The items below are the evidence
and carryover status after that window; they do not imply team or instructor
acceptance. This is a local documentation update; the CI links below describe
the named remote heads and do not include these uncommitted document edits.

### Current source and delivery trace

- GitHub `main` is `96d118eb262693edea4a5540e7bde469529963ea`, committed
  October 25 at 15:25:13 UTC. Main CI
  [40206846109](https://github.com/kendshhh/PhishLens/actions/runs/40206846109)
  passed Backend checks, Extension checks and Staging integration; Hosted
  staging was skipped on the main-push path.
- Read-only production GETs at approximately October 26 01:12 UTC returned
  `/version` HTTP 200 with commit
  `149808e3f76d9182688b5438153f57bd3cc03774` and environment `production`.
  `/health` and `/ready` each timed out after 20 seconds. No service-level
  status was obtained for those two requests, and the cause is unknown. The
  live SHA therefore does not match current `main`; no write or deployment was
  performed. See the [runbook](runbook.md).
- The required checks and protected-main summary were last reported in the
  October 25 snapshot above. The repository protection detail request returned
  403, so approval-count, stale-review and bypass settings remain unverified.

### Current Week 2 PR evidence

| PR | Current head | Automatic checks | Remaining gate |
|---|---|---|---|
| [#55](https://github.com/kendshhh/PhishLens/pull/55) package/delivery, `751b299e7fb22cf1985a41a5f4c6834ef23aa189` | [Run 40207010284](https://github.com/kendshhh/PhishLens/actions/runs/40207010284): Backend, Extension and Staging integration passed | Hosted staging is pending with no steps; PR remains open. The earlier package-source finding was implemented in `34599e7` and its change request was dismissed on October 25; no current approval is recorded. |
| [#56](https://github.com/kendshhh/PhishLens/pull/56) consultation docs, `d067ebed17967eec7bc97b8ec27e23e9c731aaa4` | [Run 40206872831](https://github.com/kendshhh/PhishLens/actions/runs/40206872831): Backend, Extension and Staging integration passed | Hosted staging is pending with no steps; PR remains open. A teammate approval is recorded on October 25, but current-head applicability was not exposed by the review data. |
| [#57](https://github.com/kendshhh/PhishLens/pull/57) metrics reporter, `0a3eeb75c7e7d142d02b14ce97ddf96be7d94e4c` | [Run 40206897540](https://github.com/kendshhh/PhishLens/actions/runs/40206897540): Backend, Extension and Staging integration passed | Hosted staging is pending with no steps; PR remains open. A reviewer approval is recorded, while backend-owner migration review and hosted staging remain separate gates. |

The Actions job records did not establish why Hosted staging is pending. The
three runs above are not hosted acceptance. Related backend CRUD PR #58 and UI
PR #59 remain open; their automatic checks pass, while Hosted staging is
pending. PR #63, which adds superseded-deployment handling, also remains open;
its hosted-staging preflight passed but its Hosted staging job is pending.

### DevOps issue closeout

| Issue | Verified in this snapshot | Still open |
|---|---|---|
| [#36](https://github.com/kendshhh/PhishLens/issues/36) planning/contract | Sprint ownership, scope, interface audit and carryover are documented. | Shared API/client/AI decisions and owner acknowledgements; issue remains open. |
| [#37](https://github.com/kendshhh/PhishLens/issues/37) environment/package | Package identity and contents are checked in PR #55 CI. | Hosted staging, Chrome installation, complete private database/role/secret-scope verification and formal current-head review. |
| [#38](https://github.com/kendshhh/PhishLens/issues/38) PostgreSQL CI | The merged #52 evidence guard and current main PostgreSQL checks pass. | Backend CRUD PR #58 is not merged, so its real CRUD test IDs are not registered; branch-protection detail also remains unverified. |
| [#39](https://github.com/kendshhh/PhishLens/issues/39) automatic delivery | Main CI passes and a production version endpoint responds. | Production SHA is behind main; health/readiness timed out; full persistent CRUD and changed-behavior delivery are not verified. |
| [#40](https://github.com/kendshhh/PhishLens/issues/40) metrics/recovery | Offline reporting is exercised in PR #57; historical install and deployment observations remain documented. | No comparable end-to-end pipeline gain is established; full deployment counts and recovery duration are unknown; no new recovery drill is claimed. |
| [#41](https://github.com/kendshhh/PhishLens/issues/41) consultation | The preparation pack is available in PR #56. | Actual standups, retrospective, whole-team rehearsal and instructor feedback were not supplied; no consultation acceptance is inferred. |

Week 2 DevOps implementation and evidence preparation are recorded. The six
issues remain open for their listed integration and acceptance criteria. Carry
the open gates into Week 3; do not close an issue based on component CI alone.

## Post-week-2 carryover update — October 28, 2026

PR [#68](https://github.com/kendshhh/PhishLens/pull/68) addresses the preview
flag normalization and its hosted-staging safety follow-up. Its conflict with
current `main` was resolved by merging `2ce4051` into the PR branch; the pushed
head is `d15a5b109a6170599a943213f22219ee1069f100`. GitHub currently reports the
PR open and mergeable.

- Local `python -m unittest discover -s scripts/tests -v`: 104 tests passed.
- Ruff passed for the touched Python tests and migration verifier.
- On the pushed head, Backend checks, Extension checks, Staging integration,
  Workflow lint, Dependency review, and CodeQL passed.
- Hosted staging is still waiting. The check diagnostics did not expose its
  reason, so hosted deployment or browser acceptance is not claimed.
- The latest formal review is still `CHANGES_REQUESTED`; updated review remains
  pending. No review or merge is inferred from the automated checks.

This is post-week-2 carryover evidence. It does not close issues #36–#41 or
replace the outstanding private-environment, installed-Chrome, persistent CRUD,
production-delivery, team-process, and instructor-acceptance evidence listed
above.
