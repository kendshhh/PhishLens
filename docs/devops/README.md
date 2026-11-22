# DevOps evidence and release records

**Current as of November 22, 2026. Release decision: NO-GO.** This index names
the current evidence set and its limits. Historical records stay dated and
retain their original findings; successor links may be added, but do not treat old
service IDs, workflow settings or deployment observations as current.

## Current source of truth

- [Live verification record (November 22, 2026)](release-record-2026-11-22.md):
  rechecked endpoint identities, current staging target/protection state,
  Render deploy history, and the open release gates.
- [Release record](release-record-2026-11-21.md): candidate identities,
  decision, exact blockers and next acceptance evidence.
- [Environment and secret map](environment-map-2026-11-21.md): service and
  database targets, non-secret settings, and unverified secret/mapping controls.
- [Readiness scorecard](release-readiness-scorecard-2026-11-21.md): seven
  release areas, evidence needed for a full pass, and scoring status.
- [Workflow alignment addendum](workflow-alignment-2026-11-21.md): local
  authenticated staging and version-pin changes, local verification, sync
  state, and the approval-dependent next steps. It does not claim a hosted
  acceptance pass.
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
   documentation refresh performs none of those actions.

## Before proposing merge or release

- Reconcile this working tree with latest `main` and review all existing user
  changes; no branch synchronization, commit, push or merge was performed as
  part of this audit.
- Land the authenticated staging smoke correction in the trusted workflow path;
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
