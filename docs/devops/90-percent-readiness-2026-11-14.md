# Release readiness blockers — 2026-11-14

This is a revision-linked DevOps handoff for the work that can move release
readiness forward. It is not a course grade or a claim that the project is 90%
complete. Issue closure counts are tracking data, not a weighted completion
score.

## Current repository snapshot

- GitHub repository: `kendshhh/PhishLens`, public visibility is intended.
- Current `main`: `e6d0fd01fb7e74587c20bc420e16c453ad5f7ef8`.
- Issues: 24 closed and 40 open out of 64 (37.5% raw issue closure).
- Five other pull requests were open when this snapshot was captured, before
  this handoff PR (#208) was opened. #206 and #207 are approved, clean follow-ups
  into `feat/96-bounded-inference`; they are not merges to `main`. #107 remains
  behind `main` with changes requested. #156 is dirty with changes requested,
  and #202 is blocked with changes requested.
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
  provider calls, and made zero database writes. That run does not prove the
  current `main` SHA above is live or that AI behavior works in production.

## Highest-value remaining work

| Work | Owner / reviewer | Evidence needed to call it complete | Can a code-only PR finish it? |
| --- | --- | --- | --- |
| [#92 held-out evaluation](https://github.com/kendshhh/PhishLens/issues/92) | Wilberr (`EnviousCoal`), with team review | Rights/provenance, reviewed labels, frozen split and overlap report, pinned model/preprocessing, complete results and an owner decision | No. It requires approved data and human review. |
| [#94 provider smoke and spend controls](https://github.com/kendshhh/PhishLens/issues/94) | Kendra (`kendshhh`) and Wilberr | Approved provider/model and provider quota or durable shared budget, then one bounded synthetic smoke and redacted result | No. The merged per-run estimate does not establish provider quota. |
| [#95 AI failure and recovery drill](https://github.com/kendshhh/PhishLens/issues/95) | Kendra; Wilberr review | Approved protected-staging failure matrix, exact revisions, simulated/live labels, measured detection/recovery, stop and rollback evidence | No. A staging window and owner approval are prerequisites. |
| [#37 environment identity](https://github.com/kendshhh/PhishLens/issues/37) and [#133 controls](https://github.com/kendshhh/PhishLens/issues/133) | Kendra | Fresh, read-only Render-to-Neon target mapping for staging and production; readiness alone proves connectivity, not database identity | No. It requires current host configuration evidence. |
| [#143 candidate and #153 release gate](https://github.com/kendshhh/PhishLens/issues/153) | Kendra and the team | Reviewed candidate SHA, exact live SHA, successful changed-feature smoke, approved SLI/SLO, clean backup restore with RPO/RTO, tag/changelog | No. These require deployment and team acceptance evidence. |
| [#41 participant records](https://github.com/kendshhh/PhishLens/issues/41) and [#148 closeout](https://github.com/kendshhh/PhishLens/issues/148) | Whole team; Kendra records | Actual dated standup, retrospective, consultation and attendance evidence | No. Records must come from participants; they must not be reconstructed. |

## Order for tonight

1. Reconcile PRs #206/#207 on the protected feature branch, then refresh #107
   checks and obtain its required reviewer decision. Do not count those branch
   PRs as merged to `main` until they are.
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
