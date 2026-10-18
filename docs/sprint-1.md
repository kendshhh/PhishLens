# Sprint 1 Log

## Consultation

October 15, 2026

## Goal

Deliver a deployed walking skeleton:
Chrome extension → FastAPI → PostgreSQL.

Establish PR checks and automatic deployment.
Demonstrate one actual AI inference call through backend code.

## Ownership

| Member | Task |
|---|---|
| Kendra | Repository workflow, Neon, CI/CD and deployment |
| Trixia | Database schema, migrations and backend foundation |
| Andrei | Extension shell and UI states |
| Leyan | History API/UI integration |
| Wilberr | DistilBERT inference adapter and verification |

## Progress

### October 19 integration follow-up

Extension analysis and history now share `extension/js/config.js`. The staging
package replaces that origin for both features and grants only staging host
permission. Local verification passed 18 extension tests, configured ESLint,
manifest validation, background syntax, and staging archive/configuration checks.
These changes are local and have not been deployed.

Render reported staging deployment `dep-dbaehj5g1s2s73bqcs80` live at commit
`fc0741a100c15b898ca18d2a6ede169c367fe9da`. A synthetic hosted analysis returned
HTTP 200 in 3.44 seconds with `mode: mock`; this is not real AI inference evidence.
Initial health/readiness requests timed out. Installed-Chrome acceptance remains
pending: browser automation cannot claim the Chrome extensions management tab.
See [staging notes](devops/staging.md) for the current acceptance limits.

Recorded October 14, 2026. This is a verified progress snapshot, not a
reconstructed team standup or a claim about unpushed teammate work.

- Repository setup: reviewed PRs #2 and #4 merged; roles and workflow documented.
- Pipeline design: PIPELINE.md documents triggers, checks, deploy handoff and limits.
- Neon: production and development branches exist. The production branch's
  phishlens_dev database also contains migration 0001_initial_schema and demo data
  (user dashboard evidence). Do not infer environment from database name alone.
- Backend/schema: PR #10 merged. PR #14 consolidated dependencies and added
  migration/repeated-seed CI checks. PR #15 added seed relationship assertions.
- Readiness: merged main 2a70ad3 has a passing CI run; deployed /ready independently
  returned HTTP 200 and database connected. This checks SELECT 1, not CRUD.
- Automated CI/CD: backend PR/main checks and checked-main automatic deployments
  verified. Review protection and intentional failure/repair evidence recorded.
- Public deployment: https://phishlens-api-ocvt.onrender.com/health responds HTTP 200.
- Recovery: rollback succeeded; first restoration failed and retry succeeded.
  See devops/incidents.md. Exact complete restoration duration remains unknown.
- Extension and history UI: absent from inspected merged tree; owners must provide
  runnable components to complete the deployed walking skeleton and its build checks.
- AI inference: adapter/real backend call absent from inspected merged tree; Wilberr
  and Trixia must supply the smoke evidence. Approval of the design is not execution.

Evidence: [CI metrics](devops/metrics.md), [runbook](devops/runbook.md),
[pipeline](../PIPELINE.md), [CI/CD issue #9](https://github.com/kendshhh/PhishLens/issues/9).

## Standups

### October 13, 2026

For each member, record:

- Done:
- Next:
- Blocked:
- Issue/PR links:

## Risks and Dependencies

- Backend deployment, migration/seed CI and public database readiness are verified.
- The largest Week 1 delivery gap is the frontend reading a real saved analysis
  through the deployed API; Leyan and Andrei own the implementation, Kendra the
  associated build checks and deployment verification.
- The actual backend model smoke is still needed from Wilberr/Trixia.
- Production and development both contain a database named phishlens_dev. Confirm
  the branch privately when configuring connections; the seed name guard alone
  does not establish non-production isolation.
- Model checkpoint and hosting capacity need verification.

The instructor requires install, lint and build on PRs. Python compilation checks
syntax but does not complete the missing extension build/package requirement.
Do not mark the whole walking skeleton complete from /health or /ready alone.

Update these risks as work progresses.

## Retrospective

Complete with the team before Consultation 1. The following are evidence-backed
discussion prompts, not a fabricated retrospective agreed by absent members.

- What went well: reviewed commits produced passing backend/database CI and
  automatic deployment; a deliberate failing test demonstrated the gate.
- What did not go well: recovery hit a restoration timeout with no confirmed
  cause, and the frontend/model walking-skeleton handoffs remain incomplete.
- Proposed change for next sprint: each developer supplies a small runnable PR
  and exact check commands early; verify the whole deployed slice before polish.
- Team confirmation and additional member observations: pending.
