# Kendra DevOps status: Sprints 1–3

**Snapshot date:** 2026-11-14

**GitHub `main`:** `6068558a1903284fc80a6cbc07936a16a3598e1e`

**Open related PRs:** [#196](https://github.com/kendshhh/PhishLens/pull/196),
[#198](https://github.com/kendshhh/PhishLens/pull/198)

This is a current evidence crosswalk, not a claim that closed issue checkboxes
prove every course acceptance item. The course guide distinguishes a checked
pipeline from deployed product evidence, and requires measured delivery,
rollback, live acceptance, and AI-aware controls. The current board was refreshed
separately; this document does not change issue state or invent participant
records.

## Status at a glance

| Sprint | Repo / issue status | Remaining acceptance |
| --- | --- | --- |
| Sprint 1 | Issues #9 and #24 are closed. CI, merge protections, extension packaging, migrations, and automated deployment are present in the repository. This PR adds the missing architecture map and decision record. | Current integrated Chrome-to-API-to-PostgreSQL acceptance and backend inference on an identified live SHA are not evidenced. Closed issue status does not supply the missing Network, changed-record, teammate, or instructor evidence. |
| Sprint 2 | #36, #38, #39, and #40 are closed; #37 and #41 are open. CI/security controls and the 28-day metrics snapshot are documented. | Fresh Render-to-Neon mapping and encrypted Render key scopes, participant-sourced standups/retro/consultation, and a reliable end-to-end optimization result remain open. |
| Sprint 3 | Deterministic contract/failure tests and the manual-only provider-smoke workflow are merged from PR #104. #92–#95 remain open. PR #196 adds deterministic evaluation and saved-route spend protection but is not merged. | AI-owner thresholds, held-out evaluation, approved provider/quota, a real provider smoke, and the protected-staging AI failure/recovery drill remain open. |

## Sprint 1 — repository, architecture, walking skeleton

### Delivered in the repository

- [#9](https://github.com/kendshhh/PhishLens/issues/9) and
  [#24](https://github.com/kendshhh/PhishLens/issues/24) are closed. Main
  protection, backend/extension checks, PostgreSQL migration/seed checks,
  extension validation/package artifacts, and Render deployment after main CI
  are implemented.
- This branch adds [the architecture map](../architecture.md) and
  [ADR-0001](../adr/0001-application-and-deployment-architecture.md), recording
  the implemented modular API plus browser-extension architecture. The record does
  not fabricate team or instructor approval.
- Merged [PR #192](https://github.com/kendshhh/PhishLens/pull/192) adds synthetic
  browser acceptance cases using isolated API/provider fixtures. It does not
  establish connected staging persistence or a live-provider result. Merged
  [PR #193](https://github.com/kendshhh/PhishLens/pull/193) prepares a guarded
  two-account Neon Auth acceptance procedure; it made no live Auth calls or
  hosted writes.
- `.env.example` is checked in and `.env` is ignored. The repository-process
  record includes a 499-commit history scan with no recognized secrets, while
  also preserving the known personal-provider commit-email attribution finding.

### Still needed for course-level acceptance

- Run an exact-current-SHA installed-Chrome flow that shows the actual API
  request/response, saved record, changed-record read, and cleanup. Historical
  package/browser identity and `/ready` are not substitutes for this.
- Record a successful backend AI inference on an identified deployed revision.
  PR #198's November 14 production smoke stopped before analysis because
  `/model-info` reported `provider_mode=unavailable`. That probe preceded the
  later main advance to `6068558`; production identity was not rechecked after
  that merge in this closeout.
- Attach the actual required teammate/instructor acceptance evidence. Issue
  closure alone is not the evidence.

## Sprint 2 — environments, delivery metrics, team evidence

### Delivered in the repository

- #38 PostgreSQL CI coverage and #39 checked-main automatic delivery are closed.
- #40 is closed. The current 28-day snapshot is in
  [metrics.md](metrics.md), backed by run/deploy exports. It reports PR and main
  pipeline times, success rates, deploy counts, merge-to-live, failed deploys,
  recovery sample size, and the change/effect limitations.
- PR #197 merged as `76551f68ff7dc02971cf127fa82f1f35e79cc2ab`. The active
  `main` ruleset requires `Backend checks`, `Extension checks`, `Migration source
  preflight`, `Staging integration`, `Workflow lint`, `CodeQL`, `Hosted staging
  preflight`, `Hosted staging`, `Dependency security`, and `Dependency graph
  review (GitHub Advanced Security)`. This is a read of current ruleset 26782191.
- A read-only Neon inspection of the current `production` branch found
  `phishlens_dev_app` on database `phishlens_dev` with database CONNECT, public
  schema USAGE, no database/schema CREATE, no elevated role membership, and only
  SELECT/INSERT/UPDATE/DELETE on `users` and `analyzed_emails`. It had no
  privileges on `alembic_version`; all three tables are owned by `neondb_owner`.
  The same role can connect to the separate `neondb` database but has no public
  tables there.

### Still open

- [#37](https://github.com/kendshhh/PhishLens/issues/37): the Neon role grant
  state is now read-only verified, but the live Render `DATABASE_URL` branch and
  database mapping was not read or freshly confirmed. The name `phishlens_dev`
  exists on multiple branches, and `/ready` only establishes a working database
  connection. Render API-key internal scopes also remain unknown; the
  `production-observer` environment has administrator bypass enabled. Do not run
  hosted writes or promotion until the target is verified.
- [#41](https://github.com/kendshhh/PhishLens/issues/41): the repository still
  lacks participant-sourced async standups, a retrospective, whole-team
  rehearsal/attendance, and exact instructor feedback. These cannot be recreated
  from commits or issue assignments.
- The refreshed 28-day snapshot has PR wall time mean 175.87 minutes / median
  4.58 / p90 205.08 (`n=682` attempts across 110 head branches); PR success is
  82.14% excluding cancellations and 75.51% including them. Main wall time is
  mean 1.39 / median 1.18 / p90 1.92 minutes (`n=86`, 100% success). Render has
  69 deploy records (`n=69`, 0 failed statuses); 64 of 95 merged PR SHAs matched
  a deploy for merge-to-live (mean 4.40, median 3.42, p90 5.47 minutes). Recovery
  is unknown (`n=0`). The uv comparison is only `n=2` baseline and `n=2`
  candidate Backend-job samples; no equivalent end-to-end speedup is established.

## Sprint 3 — AI-aware pipeline, evaluation, spend, failure handling

- [#93](https://github.com/kendshhh/PhishLens/issues/93): the deterministic
  mock-provider CI gate exists from merged PR #104. PR #196 adds evaluation on
  AI logic/prompt/model-setting changes, but remains open. The AI owner has not
  approved a quality baseline or blocking threshold. Keep the separate
  [held-out evaluation #92](https://github.com/kendshhh/PhishLens/issues/92)
  open.
- PR #196's 40-case `synthetic-v1` TF-IDF development result is 65% binary
  accuracy, 18.75% phishing recall (3/16), and 6.25% legitimate false-positive
  rate. It is a regression-development set, not a held-out test or release
  threshold. The run made zero provider calls.
- [#94](https://github.com/kendshhh/PhishLens/issues/94): the provider smoke is
  manual-only and guarded. Owner-approved provider/model selection, staging
  identity/approval, provider-side quota or shared durable budget, and a redacted
  real-provider run are absent. PR #196's dollar calculation is a configurable
  estimate, not a quota or account-wide spend cap. Keep production Gemini
  disabled without a real quota/shared limit.
- [#95](https://github.com/kendshhh/PhishLens/issues/95): required deterministic
  and simulated failure cases exist. No owner-approved protected-staging
  provider/AI failure matrix has been run; the earlier app rollback is not an AI
  recovery measurement.
- PR #198's exact-SHA production smoke failed closed before analysis because the
  production model mode was unavailable at the time of that probe. It made zero
  analysis requests, writes, or paid calls. Its staging CRUD result used a
  test-branch SHA, not current `main`. Production identity was not rechecked
  after main advanced to `6068558`.
- There is no verified deploy-ended Render event or approved hook for an
  immediate changed-feature smoke after every production deployment. Team
  approval is still needed for the production SLI/SLO and backup-restore RPO/RTO;
  no end-to-end restore acceptance is established.

## Next actions and required evidence

| Action | Required evidence / dependency |
| --- | --- |
| Review and merge PR #196 | Exact-head required checks and reviewer acceptance; keep numeric model threshold pending until AI-owner decision and held-out data. |
| Review and merge PR #198 | Exact-head CI plus decision on a supported production post-deploy trigger; do not describe manual dispatch as an automatic smoke. |
| Resolve #37 environment verification | Authorized read-only Render configuration check identifying the production and staging Neon branch/database; verify effective external key scopes. Do not expose values. |
| Complete #41 | Real participant-sourced standups, retro, consultation attendance, decisions, and technical explanations. |
| Complete #92–#95 | AI-owner-approved criteria/data/provider/quota and bounded failure matrix; exact revisions, no-retry behavior, redacted reports, detection and recovery timing. |
| Agree reliability targets | Team-approved SLI/SLO, backup restore procedure, and RPO/RTO before claiming final release readiness. |
| Reconcile dependency alert state | GitHub currently reports 12 open high `pyasn1` alerts and 3 open medium `opentelemetry-api` alerts, although all three default-branch requirements lockfiles pin patched `pyasn1==0.6.5`. Confirm the dependency graph/alert refresh and retain the findings until GitHub closes them; do not dismiss them merely to clear the dashboard. |

No production writes, provider calls, grant changes, or issue closures were
performed for this documentation update. GitHub ran the required PR checks;
Hosted staging and its preflight were skipped. No tests were run manually.
