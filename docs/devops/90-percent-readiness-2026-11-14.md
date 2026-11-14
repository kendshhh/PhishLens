# Release readiness blockers — 2026-11-14

This is a revision-linked DevOps handoff for the work that can move release
readiness forward. It is not a course grade or a claim that the project is 90%
complete. Issue closure counts are tracking data, not a weighted completion
score.

## Current repository snapshot

- GitHub repository: `kendshhh/PhishLens`, public visibility is intended.
- Current `main`: `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8`.
- Issues: 24 closed and 40 open out of 64 (37.5% raw issue closure).
- Current open PRs are #107, #156, #202, #208, and #209. PRs #206 and #207
  have merged into `feat/96-bounded-inference`; neither merged into `main`.
  Current #107 head is `81b13485d0e773a0f9301a8453a5eb83b16ea8e3`. Backend,
  Extension, Migration source preflight, Staging integration, Workflow lint,
  CodeQL, Dependency security, Dependency graph review, and Deterministic AI
  evaluation pass. Hosted staging, Hosted staging preflight, and the Issue 90
  read-only staging package check were skipped; the Secretary staging check
  reported that hosted staging was not requested. The latest submitted #107
  review is `CHANGES_REQUESTED` from EnviousCoal, who remains the requested
  reviewer.
- [PR #196](https://github.com/kendshhh/PhishLens/pull/196) merged as
  `591a2beaafcc4cc3706d176f8c79f2ffde300e89`. Its deterministic AI workflow,
  fail-closed saved-analysis spend policy, and 40-case TF-IDF development run
  are in `main`. The development run is not a held-out quality evaluation;
  its reported phishing recall was 3/16 (18.75%). The configurable dollar
  estimate is not a provider-side or account-wide quota.
- [PR #198](https://github.com/kendshhh/PhishLens/pull/198) merged as
  `6e92f99af0209dfb62dfcea8c131ce4f53cbde19`. Its exact-SHA production smoke
  is manual. The latest recorded run checked production SHA
  `591a2beaafcc4cc3706d176f8c79f2ffde300e89`, then failed closed because
  `provider_mode=unavailable`; it sent zero analysis requests, made zero
  provider calls, and made zero database writes. A separate read-only probe on
  November 14 now confirms production `/version` reports current `main`
  `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8`; `/health` was `ok`, `/ready` was
  `ready` with database `connected`, and `/model-info` still reported
  `provider_mode=unavailable`. Current `main` is live and ready, but production
  AI behavior remains unavailable and no changed-feature CRUD acceptance is
  established by these endpoints.

  The same read-only probe found staging at
  `cd913b5c7c7cf6796b4cdb12a854c709a173a12f`, with `environment=staging`,
  healthy/readiness responses, `provider_mode=tfidf`, and model SHA-256
  `a2f13c256dd46c3267263d8fde8f4f822206c5b0ceda96658713e2523a7f9559c`.
  These GET checks made no application write or paid provider request. Neither
  `/ready` response identifies its Neon branch/database.

## Highest-value remaining work

| Work | Owner / reviewer | Evidence needed to call it complete | Can a code-only PR finish it? |
| --- | --- | --- | --- |
| [#92 held-out evaluation](https://github.com/kendshhh/PhishLens/issues/92) | Wilberr (`EnviousCoal`), with team review | Rights/provenance, reviewed labels, frozen split and overlap report, pinned model/preprocessing, complete results and an owner decision | No. It requires approved data and human review. |
| [#94 provider smoke and spend controls](https://github.com/kendshhh/PhishLens/issues/94) | Kendra (`kendshhh`) and Wilberr | Approved provider/model and provider quota or durable shared budget, then one bounded synthetic smoke and redacted result | No. The merged per-run estimate does not establish provider quota. |
| [#95 AI failure and recovery drill](https://github.com/kendshhh/PhishLens/issues/95) | Kendra; Wilberr review | Approved protected-staging failure matrix, exact revisions, simulated/live labels, measured detection/recovery, stop and rollback evidence | No. A staging window and owner approval are prerequisites. |
| [#37 environment identity](https://github.com/kendshhh/PhishLens/issues/37) and [#133 controls](https://github.com/kendshhh/PhishLens/issues/133) | Kendra | Fresh, read-only Render-to-Neon target mapping for staging and production; readiness alone proves connectivity, not database identity | No. Current service and health identities are refreshed, but the service-to-Neon mapping and effective secret scopes remain unavailable from read-only metadata. |
| [#143](https://github.com/kendshhh/PhishLens/issues/143) candidate; [#153](https://github.com/kendshhh/PhishLens/issues/153) release gate | Kendra and the team | Reviewed candidate SHA, exact live SHA, successful changed-feature smoke, approved SLI/SLO, clean backup restore with RPO/RTO, tag/changelog | No. These require deployment and team acceptance evidence. |
| [#41 participant records](https://github.com/kendshhh/PhishLens/issues/41) and [#148 closeout](https://github.com/kendshhh/PhishLens/issues/148) | Whole team; Kendra records | Actual dated standup, retrospective, consultation and attendance evidence | No. Records must come from participants; they must not be reconstructed. |

## Order for tonight

1. PRs #206 and #207 have already merged into the protected
   `feat/96-bounded-inference` branch. On #107 head
   `81b13485d0e773a0f9301a8453a5eb83b16ea8e3`, Backend, Extension, Migration
   source preflight, Staging integration, Workflow lint, CodeQL, Dependency
   security, Dependency graph review, and Deterministic AI evaluation pass;
   Hosted staging, Hosted staging preflight, and the Issue 90 read-only staging
   package check were skipped. The latest submitted reviewer decision is
   `CHANGES_REQUESTED`; EnviousCoal is still the requested reviewer. Obtain a
   fresh reviewer decision before treating #107 as ready to merge. Do not count
   the feature branch as merged to `main` or as current staging acceptance.
2. Before any staging write or promotion, have the environment owner verify the
   selected SHA and exact Neon target read-only; then run one approved synthetic
   acceptance flow and clean it up.
3. Keep the held-out evaluation, provider quota, failure drill, restore target,
   and participant records open until the named owners supply their evidence.
4. Run the production smoke against the exact deployed SHA after the provider
   configuration is corrected and reviewed. Do not mark it successful from
   `/ready` alone.

This report organizes the remaining work; it does not close any of these issues
or claim that the required external evidence has been produced.
