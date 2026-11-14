# Kendra DevOps status: Sprints 1–3

**Snapshot date:** 2026-11-14

**GitHub `main` at this refresh:** `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8`

**Late-day refresh:** PRs [#196](https://github.com/kendshhh/PhishLens/pull/196)
and [#198](https://github.com/kendshhh/PhishLens/pull/198) are merged. See the
[current release-readiness handoff](90-percent-readiness-2026-11-14.md) for
remaining blockers and owners. The detailed sections below preserve earlier
same-day observations; newer facts in the handoff supersede them.

**Open related PRs:** [#107](https://github.com/kendshhh/PhishLens/pull/107),
[#156](https://github.com/kendshhh/PhishLens/pull/156),
[#202](https://github.com/kendshhh/PhishLens/pull/202),
[#208](https://github.com/kendshhh/PhishLens/pull/208),
[#209](https://github.com/kendshhh/PhishLens/pull/209)

PRs [#206](https://github.com/kendshhh/PhishLens/pull/206) and
[#207](https://github.com/kendshhh/PhishLens/pull/207) merged into the protected
`feat/96-bounded-inference` branch; they did not merge that branch into `main`.
The current #107 head is `81b13485d0e773a0f9301a8453a5eb83b16ea8e3`. Its
automated checks pass, hosted staging checks were skipped, and reviewer
re-approval is still required.

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
| Sprint 2 | #36, #38, #39, and #40 are closed; #37 and #41 are open. Merged PR #189 publishes the Sprint 2 handoff with historical CRUD evidence. | Hosted acceptance remains on hold pending selected backend, database, and authentication confirmation. Current Render-to-Neon mapping and effective key scopes, participant-sourced standups/retro/consultation, and reliable end-to-end optimization remain open. |
| Sprint 3 | Deterministic contract/failure tests and the manual-only provider-smoke workflow are merged from PR #104. PR #196 is now merged and adds deterministic AI evaluation plus fail-closed saved-analysis spend policy. #92–#95 remain open. | AI-owner thresholds, held-out evaluation, provider-side quota, a successful production behavior smoke, and the protected-staging AI failure/recovery drill remain open. |

## Sprint 1 — repository, architecture, walking skeleton

### Delivered in the repository

- [#9](https://github.com/kendshhh/PhishLens/issues/9) and
  [#24](https://github.com/kendshhh/PhishLens/issues/24) are closed. Main
  protection, backend/extension checks, PostgreSQL migration/seed checks,
  extension validation/package artifacts, and Render deployment after main CI
  are implemented.
- [The architecture map](../architecture.md) and
  [ADR-0001](../adr/0001-application-and-deployment-architecture.md) record
  the implemented modular API plus browser-extension architecture. The record does
  not fabricate team or instructor approval.
- Merged [PR #192](https://github.com/kendshhh/PhishLens/pull/192) adds synthetic
  browser acceptance cases using isolated API/provider fixtures. It does not
  establish connected staging persistence or a live-provider result. Merged
  [PR #193](https://github.com/kendshhh/PhishLens/pull/193) prepares a guarded
  two-account Neon Auth acceptance procedure; it made no live Auth calls or
  hosted writes.
- `.env.example` is checked in and `.env` is ignored. The repository-process
  record includes a 499-commit history scan with no recognized secrets. It also
  records personal-provider email identities in commit metadata; the owner chose
  to preserve that attribution. This is not a clean-history claim, so the guide's
  clean-history criterion remains unmet if it includes author/committer identity.

### Still needed for course-level acceptance

- Run an exact-current-SHA installed-Chrome flow that shows the actual API
  request/response, saved record, changed-record read, and cleanup. Historical
  package/browser identity and `/ready` are not substitutes for this.
- The latest recorded exact-SHA production smoke checked
  `591a2beaafcc4cc3706d176f8c79f2ffde300e89`, not the current `main` SHA above.
  It verified health/readiness but stopped before inference because
  `/model-info` reported `provider_mode=unavailable`; production AI behavior on
  current `main` remains unproven.
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
  database mapping remain unverified. A fresh November 14 read-only probe
  reported production `/version` at `ddc0ab16d5cdee97d88de2cd2b899e6ee6ba2213`
  with `provider_mode=unavailable`, and staging at
  `dcd234e0e012e1a869e182e64d34728343d17637` with `provider_mode=tfidf`.
  Both `/health` and `/ready` returned HTTP 200; readiness said the database was
  connected but does not establish the branch/database target. The name `phishlens_dev`
  exists on multiple branches, and `/ready` only establishes a working database
  connection. Read-only Render metadata identifies `phishlens-api` and
  `phishlens-staging`, both on `main`; production auto-deploys after checks and
  staging auto-deploy is off. The connector did not return an environment-variable
  inventory, so it did not establish either database target or effective Render
  API-key scopes. The
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
  mock-provider CI gate exists from merged PR #104. Merged PR #196 adds
  evaluation on AI logic/prompt/model-setting changes. The AI owner has not
  approved a quality baseline or blocking threshold. Keep the separate
  [held-out evaluation #92](https://github.com/kendshhh/PhishLens/issues/92)
  open.
- PR #196's 40-case `synthetic-v1` TF-IDF development result is 65% binary
  accuracy, 18.75% phishing recall (3/16), and 6.25% legitimate false-positive
  rate. It is a regression-development set, not a held-out test or release
  threshold. The run made zero provider calls.
- [#94](https://github.com/kendshhh/PhishLens/issues/94): the provider smoke is
  manual-only and guarded. The course guide's scheduled live-smoke criterion is
  not met. Owner-approved provider/model selection, staging
  identity/approval, provider-side quota or shared durable budget, and a redacted
  real-provider run are absent. PR #196's dollar calculation is a configurable
  estimate, not a quota or account-wide spend cap. Keep production Gemini
  disabled without a real quota/shared limit.
- [#95](https://github.com/kendshhh/PhishLens/issues/95): required deterministic
  and simulated failure cases exist. No owner-approved protected-staging
  provider/AI failure matrix has been run; the earlier app rollback is not an AI
  recovery measurement.
- Merged PR #198's exact-SHA production smoke failed closed before analysis
  because production reported `provider_mode=unavailable`. On the recorded SHA
  `591a2beaafcc4cc3706d176f8c79f2ffde300e89`, it made zero analysis requests,
  writes, or paid calls. This run does not prove current `main`
  `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8` is live or behavior-accepted.
- There is no verified deploy-ended Render event or approved hook for an
  immediate changed-feature smoke after every production deployment. Team
  approval is still needed for the production SLI/SLO and backup-restore RPO/RTO;
  no end-to-end restore acceptance is established.

## Next actions and required evidence

| Action | Required evidence / dependency |
| --- | --- |
| Refresh PR #107 path | #206 and #207 are approved, clean PRs into `feat/96-bounded-inference`; merge them only through the protected branch process, then refresh #107 checks and required reviewer approval. |
| Correct production provider mode | Render owner must inspect and review the production configuration change; rerun PR #198's exact-SHA smoke and verify changed behavior before claiming AI acceptance. |
| Resolve #37 environment verification | Authorized read-only Render configuration check identifying the production and staging Neon branch/database; verify effective external key scopes. Do not expose values. |
| Complete #41 | Real participant-sourced standups, retro, consultation attendance, decisions, and technical explanations. |
| Complete #92–#95 | AI-owner-approved criteria/data/provider/quota and bounded failure matrix; exact revisions, no-retry behavior, redacted reports, detection and recovery timing. |
| Agree reliability targets | Team-approved SLI/SLO, backup restore procedure, and RPO/RTO before claiming final release readiness. |
| Reconcile dependency alert state | The current GitHub API still reports 12 open high `pyasn1` alerts and 3 open medium `opentelemetry-api` alerts, although all three default-branch requirements lockfiles pin patched `pyasn1==0.6.5`. Confirm the dependency graph/alert refresh and retain the findings until GitHub closes them; do not dismiss them merely to clear the dashboard. |

No production writes, provider calls, grant changes, or issue closures were
performed for this documentation update. GitHub ran the required PR checks;
Hosted staging and its preflight were skipped. No tests were run manually.

## Named handoff for remaining work

These assignments follow the repository role map and current issue ownership.
They are proposed handoffs; they do not claim that the named people are
available, have accepted a new deadline, or have completed the work.

| Person | Role-based next work | Completion evidence |
| --- | --- | --- |
| Kendra (`kendshhh`) | DevOps: keep this PR current with `main`; verify Render-to-Neon targets and effective key scopes; coordinate the exact reviewed staging candidate; refresh DORA and release evidence. | Current source/deployed SHA, redacted target mapping, exact-SHA run, updated metrics and evidence links. |
| Wilberr (`EnviousCoal`) | AI owner: approve held-out protocol, data provenance/freeze, model decision and blocking threshold; decide provider/model and quota with Kendra before any paid request. | Reviewed evaluation protocol and, only after budget approval, a redacted bounded provider report. |
| Trixia (`xxTrixia`) | Backend: confirm the isolated staging database/role and failure matrix; re-review saved-analysis spend guarding and persistence behavior. | Read-only target/role evidence, reviewed failure expectations, and PR review. |
| Leyan (`inaki3023`) | Fullstack: run the API/client saved-report flow on the agreed staging SHA, including a fresh reread. | Source-bound create/read/edit/reread/delete/cleanup evidence and review. |
| Andrei (`JupitraxNeptuna`) | Frontend: install the matching extension package and verify connected Chrome CRUD and visible failure states. | Browser run sheet/screenshots tied to extension and backend SHAs. |
| Whole team | Hold a real review/rehearsal and record attendance, decisions, blockers and owners. Do not backdate a new meeting as a missing Sprint 2 event. | Dated participant-sourced notes. Historical standups and retro remain open unless contemporaneous evidence is supplied. |

Related open work: #37, #41, #42, #45, #87, #91, #92, #93, #94, #95, #96,
#98, and #153. These references do not close those acceptance gates.
