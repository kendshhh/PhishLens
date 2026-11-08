# Live DevOps execution audit — November 8, 2026

This records the latest evidence gathered for release-readiness issues
[#133](https://github.com/kendshhh/PhishLens/issues/133),
[#143](https://github.com/kendshhh/PhishLens/issues/143),
[#153](https://github.com/kendshhh/PhishLens/issues/153), and
[#148](https://github.com/kendshhh/PhishLens/issues/148). It is a point-in-time
execution record, not a release approval. Secret values and application data
were not read or changed.

## Current result

**Release readiness is below 90%; no final release candidate is established.**
The repository has substantial DevOps groundwork, but release acceptance still
depends on current staging and production SHA/health evidence, browser acceptance,
a measured compatible rollback, owner-approved AI evaluation limits, and real
team acceptance records. Those are explicit release gates, not documentation
polish.

The four GitHub issue bodies currently contain 27 explicit acceptance checkboxes;
all 27 are still unchecked. This is the issue tracker’s completion marking, not
a claim that no implementation exists: older evidence and the current findings
are recorded separately, while unproven acceptance stays open.

## Completed or reconfirmed in this pass

- GitHub `main` is protected at `10df92eb7d78229c8e4f93b10fc718f7752827f4`.
  Its required checks are `Backend checks`, `Extension checks`, `Hosted
  staging`, and `Staging integration`.
- GitHub's release list is empty. No release or final tag is claimed.
- PR #154 is merged. The current main commit is the source of truth; the local
  checkout is on `codex/devops-backlog-2026-10-28` at `a4ac24db` and contains
  many pre-existing modified and untracked files. It was left intact and is not
  used as release evidence.
- Following the owner's confirmation, GitHub now reports this repository as
  **private**. GitHub warned that Advanced Security will be disabled, custom
  Dependabot alert rules will be disabled unless Advanced Security is enabled,
  and existing forks will remain public but detach from this repository.
- PR #156 is still open at `1853ec90e432510e9709376c1586707d51f240e9`. Its
  latest `Backend checks`, `Extension checks`, `Hosted staging`, and
  `Staging integration` checks passed. That does not make it the accepted
  release candidate: it remains unmerged, and the corresponding live app
  version/readiness probes now time out.
- At the start of this pass, GitHub's `staging` environment had no required
  reviewer or self-review restriction, contradicting the November 7 closeout
  record. Following the owner's explicit confirmation, the gate is now saved
  and the UI shows the success message: required reviewer `inaki3023`,
  self-review prevented, administrator bypass off, wait timer off. Allowed
  deployment refs remain unchanged (`main`, `refs/pull/*/merge`,
  `refs/pull/33/merge`). Eligible GitHub Actions deployments to this environment
  now wait for the required reviewer.
- The `production-observer` environment has administrator bypass enabled. This
  was observed but not changed.

## Infrastructure and live-service gaps

- Direct `/version`, `/health`, and `/ready` checks timed out after 18 seconds
  on both services at about 00:28 UTC. A later `/version` retry with a 75-second
  timeout also timed out on both services. Render returned no request-log rows
  for these paths during 00:10–00:28 or 00:28–00:40 UTC. The results leave
  application-level health/readiness and database connectivity **unverified**;
  they do not by themselves establish that either service is down.
- Render service metadata reports the staging deployment `dep-dbnr0bs9v7es73dh7uig`
  as live at commit `1853ec90e432510e9709376c1586707d51f240e9`, from open PR #156.
  Its build and deploy succeeded at 23:12–23:13 UTC on November 7. Staging
  auto-deploy is off and no health-check path is configured. The production
  deployment `dep-dbndo768bjmc73a4vk1g` is reported live at
  `0fcc747725512df13ba8ae0900b6080591425928` from November 7 08:08 UTC; this
  trails protected GitHub `main` at `10df92eb7d78229c8e4f93b10fc718f7752827f4`.
  Production auto-deploy is enabled after checks pass, with `/health` configured.
  Both services are on Render's free plan. No deployment was triggered in this
  pass. Render's deploy metadata establishes the deployed commit, but the app's
  own version and readiness endpoints remain unverified.
- Render application logs show staging started successfully and returned
  `/ready` 200 at 23:13 UTC on November 7; its process then finished at 23:28
  UTC after inactivity. The last production process-finished log was at 20:36
  UTC; no later app logs appeared during the retry window. The free services
  appear to have scaled down, but the long retry did not produce a new request
  log or startup record, so scale-to-zero alone is not a confirmed explanation.
  Render's [public status page](https://status.render.com/) reported Singapore
  and Free Tier web services operational during this check.
- Render's deploy records provide build/deploy timing evidence: the latest
  staging build took about 30 seconds and deploy about 82 seconds; the latest
  production build took about 31 seconds and deploy about 84 seconds. These are
  observed deploys, not a rollback rehearsal.
- GitHub's latest `Check production SHA and health` run on main
  [failed at 23:48 UTC on November 7](https://github.com/kendshhh/PhishLens/actions/runs/42426724475).
  Its job reported production unavailable and could not read `/version`,
  `/health`, or `/ready` as JSON. This independently corroborates the current
  endpoint failures; it is not one of the four branch-protection required
  contexts listed above.
- Neon reports project `patient-bird-25428852` on the `free_v3` plan. An attempt
  to protect the production branch was rejected with HTTP 422 because the plan
  has no remaining protected-branch allowance. No branch setting changed, and
  no plan upgrade was made. Production and shared staging currently report
  unprotected. Hard cost/quota guardrails were not verified by the usage
  counters returned for this project.
- Current GitHub main protection is established, but this does not replace the
  exact-SHA staging/live checks or the rollback exercise required by #143.

## Remaining acceptance work

- **#133:** reconcile the GitHub staging gate with the prior recorded choice;
  complete environment/secret-scope and repository history/privacy checks;
  document and verify enforceable cost/usage limits. Main protection is now
  evidenced above. Neon production-branch protection is plan-blocked unless an
  owner chooses a different branch-protection/plan strategy.
- **#143:** PR #156's required checks pass and Render reports successful builds
  and deploys, but that PR is still open and not an accepted release candidate;
  its running app is not responding to version/health probes. Production is
  behind current `main`. Verify the exact app-reported SHA/health on both
  environments and record a measured rollback to a compatible version.
- **#153:** complete product/browser acceptance, bounded AI evidence and
  provenance, recovery evidence, docs, verified deployment, metrics with sample
  limits, and actual team records before release approval.
- **#148:** close out only after #153's candidate and team acceptance are
  supported by real records. Do not infer meetings, reviews, or decisions from
  commits or CI.
- Issues #94 and #95 still require owner-approved provider quota/cost controls
  and a protected-staging AI failure/recovery drill. No live provider call was
  made.
- Installed-browser save/history/edit/delete and reload persistence remain
  unverified. No browser acceptance result is claimed.

## Actions performed

- Read GitHub branch protection, release, and environment settings; read Neon
  project/branch/usage metadata; checked the two service `/version` endpoints.
- Restored the GitHub staging approval gate after the owner's confirmation and
  verified the saved reviewer/self-review/admin-bypass settings in the UI.
- Changed GitHub repository visibility from public to private after the
  owner's confirmation and verified the private setting in GitHub UI and
  repository metadata. GitHub displayed the side effects recorded above.
- Read Render service/deployment/event/metrics metadata and checked
  `/version`, `/health`, and `/ready` for both services. The checks timed out;
  no deploy or service setting changed.
- Tried the Neon production-branch protection update; Neon rejected it before
  mutation because of the plan limit.
- Added this evidence record. No application files, deployment, tag, release,
  database rows, grants, secret values, or team records were changed.
- Posted evidence-based status updates to GitHub issues #133, #143, #153, and
  #148: [#133](https://github.com/kendshhh/PhishLens/issues/133#issuecomment-6714926697),
  [#143](https://github.com/kendshhh/PhishLens/issues/143#issuecomment-6714926888),
  [#153](https://github.com/kendshhh/PhishLens/issues/153#issuecomment-6714927102),
  [#148](https://github.com/kendshhh/PhishLens/issues/148#issuecomment-6714927283).
  All four remain open because their acceptance criteria are not yet met.
- No tests were run in this audit pass.

