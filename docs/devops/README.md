# DevOps evidence and release records

**Current as of November 21, 2026. Release decision: NO-GO.** This index names
the current evidence set and its limits. Historical records stay dated and
retain their original findings; successor links may be added, but do not treat old
service IDs, workflow settings or deployment observations as current.

The staging smoke and CI guard implementation is on review branch
`codex/devops-staging-closeout-20261121`, implementation commit
`a80b95e146cd03a96ffca156ccfe5721ac871b68`. PR #268's latest application/test
commit is `d27eaa07a28173c485d19f44524a88e71515fc10`. Its CI and local staging passed,
and the direct GET-only smoke passed, but Hosted staging was skipped and no
Render deployment occurred. It is not merged or verified by a hosted workflow
run.

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
