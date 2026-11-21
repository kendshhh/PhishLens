# DevOps evidence and release records

**Current as of November 21, 2026. Release decision: NO-GO.** This index names
the current evidence set and its limits. Historical records stay dated and
retain their original findings; successor links may be added, but do not treat old
service IDs, workflow settings or deployment observations as current.

The staging smoke and CI guard implementation is on review branch
`codex/devops-staging-closeout-20261121`. Latest observed `main` is
`95975cd47dceeac74ea36054610956f0a1db1fa9`, after PR #265 merged the shared
readiness baseline. Main includes the Bearer-aware history fix from `06f89d7`.
The review branch contains that code through merge commit
`14874d339bbb4042172df954f97596080aa303ee` and the PR #265 documentation baseline
at `ca29235`. Latest code/test commit is
`83a0df1af1d64048b3b5fa3158f6509e83d71555`; its local `npm test` passed 321
tests, and a GET-only live staging smoke passed at about 08:35 UTC. Those are
historical implementation evidence, not current-head checks.

At 10:14 UTC, PR #268 head
`2e26327254c71b6cb7d655181cffb21e8dd1ee9b` passed Backend, Extension, migration
preflight, Staging integration, hosted preflight, workflow lint, dependency
security, Dependency graph review and deterministic evaluation (CI
[44891131201](https://github.com/kendshhh/PhishLens/actions/runs/44891131201),
workflow lint [44891131261](https://github.com/kendshhh/PhishLens/actions/runs/44891131261),
dependency checks [44891131162](https://github.com/kendshhh/PhishLens/actions/runs/44891131162),
evaluation [44891131190](https://github.com/kendshhh/PhishLens/actions/runs/44891131190)).
The Hosted staging job wrapper concluded `success`, but its final freshness
guard superseded the run after the request label was removed; deployment,
smoke, CRUD and artifact steps were skipped, and the job summary calls the run
blocked. Required `Secretary staging` failed because the request label and
exact-head hosted verification were absent
([run 44892082807](https://github.com/kendshhh/PhishLens/actions/runs/44892082807)).
No current PR CodeQL result, Render deployment or authenticated CRUD evidence
exists. The merged `main` revision `95975cd` passed CI and CodeQL. PR #268 is
still based on the now-merged PR #265 branch and must be retargeted to `main`
before merge. Fifteen Dependabot alerts (12 high, 3 moderate) remain open. The
10:14 snapshot and earlier dated check history are detailed in the
[staging evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

At 11:08 UTC, documentation reconciliation was pushed as head
`a151585ff92d55f21e0364e9838287a9cf04a68d`. Backend, migration source
preflight, workflow lint, dependency security and graph review, deterministic
evaluation and the Secretary report passed. Packaged `Extension checks` failed
the keyboard-focus assertion in `scripts/browser_acceptance.mjs:700`; Staging
integration and hosted staging/preflight were skipped. The required
`Secretary staging` status failed because the request label and exact-head
hosted verification were absent. See the current [release record](release-record-2026-11-21.md)
and [staging evidence](evidence/2026-11-21-staging-neon-auth-smoke.md). The
10:14 snapshot is historical for the previous head.

The preceding completed workflow snapshot before this docs-only sync was head
`dffdc4c29338142f458350b51c8ce69e0f36e988` at 11:21 UTC: Backend, Extension,
migration preflight, Staging integration, workflow lint, dependency review and
security, deterministic evaluation, and the Secretary report passed. Hosted
preflight/deployment were skipped, and required `Secretary staging` failed
because the request label and exact-head hosted verification were absent
([run 44898698685](https://github.com/kendshhh/PhishLens/actions/runs/44898698685)).
The focus-order failure on the previous head did not recur; its cause is still
unresolved. The docs-only sync following this snapshot needs its own check run.

That sync was pushed as `f79098cc075784563d2022cbca87d7abe8f0a635` and its
checks completed at 11:31 UTC. Backend, Extension, migration preflight, Staging
integration, workflow lint, dependency checks, deterministic evaluation and
the Secretary report passed. Hosted staging/preflight were skipped; required
`Secretary staging` failed in [run 44899423134](https://github.com/kendshhh/PhishLens/actions/runs/44899423134)
because the request label and exact-head hosted verification were absent. The
following docs-only sync needs a new exact-head run.

## Current source of truth

- [Release record](release-record-2026-11-21.md): candidate identities,
  decision, exact blockers and next acceptance evidence.
- [Environment and secret map](environment-map-2026-11-21.md): service and
  database targets, non-secret settings, and unverified secret/mapping controls.
- [Readiness scorecard](release-readiness-scorecard-2026-11-21.md): seven
  release areas, evidence needed for a full pass, and scoring status.
- [Staging Neon Auth smoke evidence](evidence/2026-11-21-staging-neon-auth-smoke.md):
  supplied failure, current live observations, code/workflow mismatch and fix
  acceptance plan.
- [Reusable closeout prompt](devops-evidence-closeout-prompt-2026-11-21.md):
  an evidence-first instruction for resolving the remaining gaps safely.
- [CI maintenance and dependency-review setup](ci-maintenance.md) and
  [dependency audit record](dependency-audits.md): enablement state and
  unresolved Dependabot alerts.
- [Deployment and recovery runbook](runbook.md), [staging runbook](staging.md),
  [production smoke](production-deploy-smoke.md), [metrics](metrics.md), and
  [Secretary verification](secretary-verification.md): operating instructions
  and current limitations.
- [Pipeline overview](../../PIPELINE.md): concise current delivery state and
  preserved historical snapshots.

The November 20 isolated Neon recovery drill is on upstream `main` at commit
[`811980c`](https://github.com/kendshhh/PhishLens/blob/811980c2cbf70d9957146bf329627f0826a018f1/docs/devops/recovery-drill-2026-11-20.md).
It verified an isolated restore's schema and aggregate integrity. Its one-
second branch-ready time is not service RTO, RPO was not measured, and the
temporary snapshot/restore branch expire November 27.

## Evidence rules

1. Bind every acceptance result to the exact source SHA, deployed service,
   extension package hash, model/provider identity, Auth mode, database branch,
   test identity and timestamp needed to reproduce it.
2. Label each source as repository inspection, CI run, control-plane observation,
   live read-only probe, synthetic test, human acceptance, or owner decision.
   A planned action, local test, historical result or skipped job cannot stand
   in for another evidence type.
3. Keep secrets, connection strings, tokens, personal data and report contents
   out of docs and artifacts. Record only names, masked identities, scopes,
   hashes, counts, outcomes and owners.
4. Preserve evidence snapshots. Add a new dated record when current state
   changes; do not silently rewrite older observations.
5. Mark a criterion `Pass` only when all of its approved evidence requirements
   are satisfied for one candidate. Otherwise keep it `Open` and list the exact
   missing proof and accountable owner.
6. Do not report a percentage until the team/instructor approve weights and a
   scoring rule. Do not label an unapproved score as 100% or imply that a code
   change can manufacture external decisions, human test results, or live
   evidence.
7. Push, merge, deploy, change service/secret settings, write shared databases,
   or perform destructive recovery only with explicit authorization. This
   closeout is prepared on `codex/devops-staging-closeout-20261121`, based on
   `3c858f7` (descended from `811980c`). The branch includes the CI/smoke fix
   and reconciled records; it is not merged into `main`. The original dirty
   checkout is preserved.

## Before proposing merge or release

- Review the complete diff on `codex/devops-staging-closeout-20261121`, based
  on `3c858f7df51666e0545dea1a6dd5997574c16d43`. The original dirty checkout
  remains preserved; this closeout branch is not merged into `main`.
- Merge the smoke and fail-closed CI guard correction into the trusted workflow
  path only after review and required checks pass.
- Land the authenticated staging acceptance correction in the trusted workflow path;
  add a safe test identity/session and make the CRUD runner authenticate without
  weakening authorization. Prove the complete flow on an isolated staging
  target, including cleanup.
- Reconcile Render's auto-deploy setting and observed deployment trigger; verify
  the private Render-to-Neon branch and role mapping and GitHub environment
  protections without exposing secret values.
- Verify effective required checks on GitHub; establish an approved exact
  extension/backend/model/Auth candidate; pass installed-extension and
  authenticated persistence/isolation acceptance.
- Obtain approved model-quality evidence, compatible application rollback,
  measured recovery objectives, named responders, actual participant records,
  and owner/instructor sign-off.

Until the [scorecard](release-readiness-scorecard-2026-11-21.md) is fully
evidenced and the responsible reviewers accept one candidate, the release stays
**NO-GO**.
