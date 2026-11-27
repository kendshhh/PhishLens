# DevOps evidence and release records

**Evidence snapshot: 2026-11-27 14:35 UTC. Release decision: NO-GO.** The
strongest current evidence is the exact-head protected staging acceptance for
PR #306, not a production release.

`main` is `fd23b186ad85f9d33e7f80dec03f09d9b7005403`. Protected staging run
[45999893591](https://github.com/kendshhh/PhishLens/actions/runs/45999893591)
passed exact candidate deployment, Neon isolation, Auth, saved-report CRUD,
persistence, isolation, ownership, cleanup, and extension UX on SHA
`131d282222361a6d29601f90a2930445ee4a61cf`. Staging remained on that SHA at
14:33 UTC. Current main differs from the accepted tree only in documentation
files; exact-main artifact provenance still needs a release build. See the
[acceptance evidence](evidence/2026-11-27-staging-acceptance-131d282.md).

Production at 14:32–14:33 UTC returned HTTP 200 for health/readiness with the
database connected. It runs `811980c2cbf70d9957146bf329627f0826a018f1` and
reports AI analysis disabled. Its service is still Git-backed; no backend image
digest, production acceptance, release tag, or changelog exists. AI quality is
blocked because reviewed representative holdout approval is missing.

The current [rubric crosswalk](devops-rubric-readiness-2026-11-27.md) records
no perfect score; the [DORA report](dora-report-2026-11-27.md) is reproducible
through 14:35 UTC and explicitly leaves change failure, failed-deployment
recovery, and rework unknown. See also the current
[environment map](environment-map-2026-11-27.md),
[controlled-release record](controlled-release.md),
[metrics](metrics.md), and [pipeline overview](../../PIPELINE.md).

The current open-PR alignment inventory was refreshed at 14:44 UTC against
main `fd23b18`; it records 16 open PRs, live target branch SHAs, authors, changed
files, stack relationships, duplicate updates, and migration-file results. See
the [report](pr-alignment-2026-11-27.md) and [JSON snapshot](evidence/open-pr-alignment-2026-11-27-1444z.json).

The November 20 isolated Neon recovery drill was recorded on upstream `main` at
commit [`811980c`](https://github.com/kendshhh/PhishLens/blob/811980c2cbf70d9957146bf329627f0826a018f1/docs/devops/recovery-drill-2026-11-20.md).
It verified an isolated restore's schema and aggregate integrity, but that
recovery point and drill branch were scheduled to expire November 27. Current
availability and measured RTO/RPO are not verified; repeat with a fresh point.

## Evidence rules

1. Bind acceptance to exact source SHA, backend/extension identities, model,
   Auth mode, database branch, workflow run, and timestamp.
2. Distinguish repository checks, control-plane observations, live GET probes,
   synthetic acceptance, human review, and owner approval.
3. Keep secrets, connection strings, tokens, personal data, and report contents
   out of evidence. Record only names, masked identities, hashes, counts, and
   outcomes.
4. Preserve dated snapshots; label old evidence instead of presenting it as
   current.
5. A staging PASS does not establish production release, AI quality, rollback,
   or recovery readiness.
6. Do not invent partial points: the rubric supplies criterion maxima and
   broad bands, not an allocation formula within the bands.
7. Do not merge/deploy production, publish a release, or alter shared data to
   make a score appear complete. Keep issue #153 **NO-GO** until current evidence
   supports GO.
## Historical PR snapshots

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

- [2026-11-27 DevOps rubric crosswalk](devops-rubric-readiness-2026-11-27.md):
  current evidence against all nine rows in the supplied 100-point rubric.
- [2026-11-27 environment map](environment-map-2026-11-27.md):
  Render, GitHub, Neon, Auth, and extension identities with current secret scopes.
- [2026-11-27 PR alignment record](pr-alignment-2026-11-27.md): current heads,
  migration status, pairwise merge-tree results, and integration order.
- [Current DORA 4+1 report](dora-report-2026-11-27.md) and
  [redacted input snapshot](evidence/dora-source-2026-11-27.json):
  reproducible window, denominators, and unmeasured reliability metrics.
- [Controlled release record](controlled-release.md): exact staging outcomes,
  promotion architecture, and current external blockers.
- [Release record](release-record-2026-11-21.md): candidate identities,
  historical decision and evidence; superseded by the current records above.
- [Environment and secret map](environment-map-2026-11-21.md): historical
  service/database targets and unverified controls; recheck before using.
- [Readiness scorecard](release-readiness-scorecard-2026-11-21.md): historical
  seven-area audit; use the 2026-11-27 rubric crosswalk above for current gaps.
- [Staging Neon Auth smoke evidence](evidence/2026-11-21-staging-neon-auth-smoke.md):
  historical failure and fix plan; later exact-head acceptance is recorded above.
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
temporary snapshot/restore branch were scheduled to expire November 27; current
availability was not verified here. Do not rely on them as the present recovery
point without checking Neon.

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
6. The supplied 100-point rubric provides criterion weights and qualitative
   bands. Its partial-credit method and the gaps between bands are unspecified;
   do not invent an aggregate point total. Use the current crosswalk to show
   evidence and gaps, and never label a blocked criterion Excellent or imply
   that code can manufacture owner approvals, human test results, or live
   evidence.
7. Push, merge, deploy, change service/secret settings, write shared databases,
   or perform destructive recovery only with explicit authorization. Current
    evidence edits are on isolated branch
    `codex/devops-staging-evidence-sync-20261127`; #268 is already merged and no
    production deployment has occurred. The original dirty checkout is preserved.

## Current merge and release gates

- Keep staging, release-staging, and staging-neon-preflight approvals
  independent. Self-review is now prevented for each protected staging
  environment. A deployment remains blocked until missing migration/release
  inputs are provisioned and a protected candidate run succeeds.
- Privately verify Render runtime/migration/Auth settings against the selected
  isolated Neon project and provision a new migration-only credential. Keep the
  release mapping attestation absent until then; do not treat this as merely
  awaiting review.
- Obtain the AI owner's approved representative holdout report and policy for
  the exact immutable provider/model. Historical English evaluation is not the
  current release-quality gate.
- Configure a supported image-backed Render path and production GitHub variables
  and credentials only after review. Build once, promote the same digests, and
  require exact-SHA production smoke and product acceptance before tagging.
- Rehearse application rollback and isolated restore; measure RTO/RPO, verify
  alert delivery and backup responder, and complete the DORA failure/recovery/
  rework records plus a comparable optimization study.
- Keep issue #153 **NO-GO** until each criterion is linked to current evidence.

The [2026-11-27 crosswalk](devops-rubric-readiness-2026-11-27.md) is the current
rubric view. The 10/10 result is not supported while the gates above remain
open.

### PR #268 follow-up — 2026-11-21 11:42 UTC

The next exact-head check on `e9451cc20928fefa7c0a6ded4803cebbad24ef42` passed Backend, Extension, migration preflight, Staging integration, workflow lint, dependency security/graph review, deterministic evaluation, and the Secretary report. Hosted staging preflight and Hosted staging were skipped. Required `Secretary staging` remains failed because the `needs-hosted-staging` label and exact-head hosted verification are absent. No current PR CodeQL result, Render deployment or authenticated CRUD was observed. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md) for run links. The release remains **NO-GO**; the descriptive DevOps evidence score remains 41/100.

### PR #268 retarget follow-up — 2026-11-21 11:57 UTC

PR #268 is now based on `main`; review branch head `77c0ed00e607c5580cedffadd031fe40ad71771b` includes the current `main` history. GitHub reports the PR open and mergeable, while the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. Exact-head CI passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security/graph review, deterministic evaluation, DevOps Secretary report and CodeQL. Hosted preflight/deployment were skipped; required `Secretary staging` remains failed because the hosted request label and exact-head hosted verification are absent. No Render deployment or authenticated hosted CRUD occurred. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md). Release remains **NO-GO** and the 41/100 descriptive evidence score is unchanged.

### PR #268 exact-head snapshot — 2026-11-21 12:02 UTC

Retargeted PR #268 head `1fa2e7827cfe84de425afcc7885743bd55b2a382` passed Backend, Extension, Staging integration, migration preflight, workflow lint, dependency security and graph review, deterministic evaluation, DevOps Secretary report, and all three CodeQL analyses. [CI run 44901642617](https://github.com/kendshhh/PhishLens/actions/runs/44901642617) completed at 12:02 UTC. Hosted staging preflight and Hosted staging were skipped. The required `Secretary staging` status failed because the `needs-hosted-staging` label and exact-head hosted verification were absent ([assessment 44901931269](https://github.com/kendshhh/PhishLens/actions/runs/44901931269)); no Render deployment or authenticated hosted CRUD occurred. GitHub reports the PR open and mergeable on `main`; the review decision remains `CHANGES_REQUESTED` pending collaborator re-review. The release remains **NO-GO**, and 41/100 is a descriptive evidence-progress score only. This documentation-only evidence update requires fresh exact-head CI before merge. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).

### PR #268 main-sync snapshot — 2026-11-21 12:14 UTC

PR #268 now includes current `main` through `31e86c7` in merge head `aee49fe5a11da37ed441464c80ad9a09e0b9dda8`. Exact-head CI run [44902645800](https://github.com/kendshhh/PhishLens/actions/runs/44902645800) passed Backend, Extension, Staging integration and migration preflight. Workflow lint [44902645811](https://github.com/kendshhh/PhishLens/actions/runs/44902645811), dependency security/graph [44902645851](https://github.com/kendshhh/PhishLens/actions/runs/44902645851), deterministic evaluation [44902645832](https://github.com/kendshhh/PhishLens/actions/runs/44902645832), and CodeQL [44902643383](https://github.com/kendshhh/PhishLens/actions/runs/44902643383) passed. The exact-head DevOps Secretary report was cancelled during the branch sync ([44902644757](https://github.com/kendshhh/PhishLens/actions/runs/44902644757)); the Secretary preview assessment reports required `Secretary staging` failure because the `needs-hosted-staging` label and exact-head hosted verification are absent ([44902874550](https://github.com/kendshhh/PhishLens/actions/runs/44902874550)). Hosted preflight/deployment were skipped; no Render deploy or authenticated CRUD occurred. GitHub shows PR #268 open, mergeable on `main`, with review decision `CHANGES_REQUESTED`. Release remains **NO-GO**; 41/100 is descriptive evidence progress, not completion. See the [dated evidence record](evidence/2026-11-21-staging-neon-auth-smoke.md).
