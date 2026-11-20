# Kendra DevOps status — Sprints 1–3 — 2026-11-15

> Historical snapshot. Current delivery and release status is recorded in
> [PIPELINE.md](../../PIPELINE.md), refreshed November 20, 2026. This file
> preserves the November 15 evidence and must not be used as current service or
> branch-protection state.

This snapshot separates merged repository controls, staging evidence,
production state, and items that needed decisions or records from other people.
It is not a course grade or a weighted project-completion percentage.

## Current repository and controls

- GitHub reports 15 open Dependabot alerts: 12 high for `pyasn1` and 3 medium for `opentelemetry-api` across the three requirements manifests. Current `main` pins the patched versions `pyasn1==0.6.5` and `opentelemetry-api==1.45.2`; the alerts remain open and were not dismissed. Reconcile the dependency graph/alert state before calling them resolved.
- Repository `kendshhh/PhishLens` is public; the owner has confirmed that public visibility is intended.
- GitHub `main` at this refresh: `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c` (PR #231). The earlier `56fba3952b588d289cf539623f9b4149b03258fc` SHA is the PR #226 merge, not current main; PR #231 later removed the unused Vercel landing page. PR #224 added browser-acceptance checks/evidence for staging candidate `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f`; PR #221 audited documentation; PR #226 hardened the hosted-staging URL guard and added offline regression tests.
- Issue tracker: 30 closed and 34 open of 64 total (46.9% raw closure, not a project-progress score). Issue #133 is closed after the documented control evidence was merged.
- Main ruleset `26782191` is active and requires one approval plus six contexts: Backend checks, Extension checks, Staging integration, Workflow lint, CodeQL, and Dependency security. The API-visible ruleset does not list an AI evaluation context; an earlier PR checks view showed the separate `Deterministic AI Evaluation` context as Expected. The always-reported exact-name AI job is a change proposed by the unmerged PR #220 workflow revision, not a behavior yet merged to `main`. On PR branch head `b0a7591b4a04a7c553d18f9cbde5e3c8ba83353f`, the context succeeded in run 43717709615; its full evaluation passed and N/A step was skipped because the AI workflow itself changed. The unrelated-change N/A path and any classic branch-protection rule still need independent verification; the connected GitHub API cannot read classic branch-protection settings.
- Main push runs for application SHA `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` before PR #224 completed successfully: [CI #43610239369](https://github.com/kendshhh/PhishLens/actions/runs/43610239369), [Workflow lint #43610239268](https://github.com/kendshhh/PhishLens/actions/runs/43610239268), and [Dependency security #43610239226](https://github.com/kendshhh/PhishLens/actions/runs/43610239226). The [AI evaluation workflow #43610239261](https://github.com/kendshhh/PhishLens/actions/runs/43610239261) completed with its evaluation job skipped because this change did not touch AI paths; it made no paid provider request.
- The 40-case synthetic suite is development-only and has no numeric model-quality cutoff. The AI owner approved the zero-tolerance deterministic rule in [#93](https://github.com/kendshhh/PhishLens/issues/93#issuecomment-6891138424). The always-reported `Deterministic AI Evaluation` job is part of the unmerged PR #220 workflow revision; AI-related changes run its workload and unrelated changes report explicit N/A. On PR branch head `b0a7591b4a04a7c553d18f9cbde5e3c8ba83353f`, [run 43717709615](https://github.com/kendshhh/PhishLens/actions/runs/43717709615) passed the exact-name context and full 40-case evaluation; the N/A step was skipped because this PR changes the workflow. Verify the N/A path on a future unrelated-change PR. The API-visible main ruleset does not list AI evaluation, although a reviewed PR checks view showed the separate context as Expected; classic branch protection was not available through the connected API. Separately, [#92](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6891137984) accepts TF-IDF v12a for advisory screening only on the frozen English source-pair cohort, meeting its approved recall, legitimate-only false-positive, and valid-output criteria. Broader contemporary-source coverage remains open.

## Security history scan — 2026-11-15

Gitleaks v8.30.1 scanned all local Git refs (608 commits, about 21.22 MB). It
reported seven `generic-api-key` findings in historical package-identity JSON
files under `docs/frontend/issue-131`, `issue-136`, and `issue-141`. Review of
the redacted matches and JSON structure showed these are SHA-256 file digests
whose asset path is `js/api.js`, not credentials. All twelve changed/added files
scanned separately with zero findings. No repository history was rewritten and
no finding was suppressed. This is heuristic secret scanning, not proof that
every kind of sensitive information is absent.

## Staging: exact-SHA acceptance passed

The November 15 run recorded staging serving exact application SHA `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f`, which was main after PR #215 and before PR #224. PR #224 later advanced main to `c568b7a39a7abf3a99ed7aa318d490397d21bd30`, PR #221 to `bfa0d61040ea671a81317102f2de536cf86a9844`, PR #226 to `56fba3952b588d289cf539623f9b4149b03258fc`, and PR #231 to current snapshot `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c`. PR #226 includes the later hosted-staging URL identity guard fix; the recorded deployment and CRUD run predate and do not test that fix. The verified
Render-to-Neon staging mapping, health/readiness/model preflight, and one
synthetic CRUD create/read/update/delete/cleanup run are recorded in
[the November 15 staging acceptance](staging-acceptance-2026-11-15.md).
This closes the prior staging seed/target acceptance gap for this backend
staging run. It is not production acceptance or browser acceptance.

## Production: still blocked

The production Render service's latest live deploy is
`dep-dbs7h56q1p3s73eg2pvg`, source SHA
`205ec26f8b5d04104a6e8fdfa0c9efa490ecdf02`, finished
`2026-11-14T15:06:04Z`. It does not match current `main`.

Fresh read-only requests to production returned:

| Endpoint | Result |
| --- | --- |
| `/version` | HTTP 200; SHA `205ec26f8b5d04104a6e8fdfa0c9efa490ecdf02`; `environment=production` |
| `/health` | HTTP 200; `status=ok` |
| `/ready` | HTTP 200; database `connected` |
| `/model-info` | HTTP 200; `provider_mode=unavailable`, `accepts_tfidf_reports=false` |

The last result means production feature acceptance fails despite healthy
process/database checks. The [exact-SHA production smoke run #43610307606](https://github.com/kendshhh/PhishLens/actions/runs/43610307606)
failed closed at the provider preflight and made zero analysis requests, paid
provider calls, or database writes. The latest [production drift run
#43639445224](https://github.com/kendshhh/PhishLens/actions/runs/43639445224)
also failed because production did not match then-current `main` SHA `8c4795f`.

Do not report production acceptance or release completion from `/health` or
`/ready`. A Render deploy of current `main`, a working production provider
configuration, and a successful exact-SHA changed-behavior smoke are still
needed. The production smoke workflow is manual-only; no deploy-ended webhook
trigger is configured or verified. Render documents workspace webhooks as a
Pro-or-higher feature, but the current workspace plan is not exposed by the
connected read-only metadata. See [production smoke limitations](production-deploy-smoke.md)
and [Render's webhook documentation](https://render.com/docs/webhooks).

## Remaining evidence and owner decisions

| Issue | Remaining item | Why Kendra cannot close it from this evidence |
| --- | --- | --- |
| [#37](https://github.com/kendshhh/PhishLens/issues/37) | Verify production's Neon branch/database mapping, complete the credential-scope review, and record the commit-identity/history disposition. Staging endpoint mapping is now verified. | Render API access does not expose the values/scopes needed for complete production mapping and secret-scope verification; the history disposition requires an owner decision. |
| [#41](https://github.com/kendshhh/PhishLens/issues/41) | Actual standups, retrospective, consultation attendance, rehearsal, and participant explanations. | These must come from participants; commits and issue assignments are not meeting evidence. |
| [#92](https://github.com/kendshhh/PhishLens/issues/92) and [#93](https://github.com/kendshhh/PhishLens/issues/93) | For #92, apply the approved thresholds prospectively to a protocol-admitted contemporary bundle and broaden source coverage; the frozen cohort decision applies only to advisory use on its English source pair. For #93, verify the N/A status path on an unrelated change; full deterministic evaluation and exact-context reporting passed on PR #220. | The 40-case development suite has no numeric quality cutoff. Broader contemporary-source evaluation remains open; the ruleset API does not expose the classic protection view. |
| [#94](https://github.com/kendshhh/PhishLens/issues/94) | Provider/model approval, provider-side quota or durable shared spend control, and one bounded synthetic provider run. | No owner-approved quota or provider authorization is recorded; the per-run estimate is not an account-wide cap. No paid request was made. |
| [#95](https://github.com/kendshhh/PhishLens/issues/95) | Protected-staging AI failure matrix, measured detection/recovery, and accepted stop/rollback evidence. | Requires owner/reviewer-approved failure cases. Prior app rollback evidence is not an AI-provider failure drill. |
| [#143](https://github.com/kendshhh/PhishLens/issues/143) and [#153](https://github.com/kendshhh/PhishLens/issues/153) | Reviewed exact candidate deployed to production, changed-feature acceptance, approved SLI/SLO, and safe restore with agreed RPO/RTO. | Production is behind `main` and reports provider unavailable; no approved reliability targets or clean restore acceptance exist. |
| [#148](https://github.com/kendshhh/PhishLens/issues/148) | Release tag/changelog and actual team process records. | Release is not verified live; participant-sourced records are missing. |

Issue #129's final backlog freeze still needs team agreement. The GitHub CLI
authentication available to this session lacks the `read:project` scope, and
the connected GitHub tools expose no Projects board edit action. Board updates
could not be applied or verified through the available access.

## Delivery metrics

The [28-day metrics report](metrics.md) ends at `2026-11-14 03:12 UTC`; it was
not recomputed in this refresh. It records PR pipeline attempts `n=682` across
110 branches, main runs `n=86`, production deploys `n=69`, and 64 matched
merge-to-live samples out of 95 merged PR SHAs. Recovery time remains unknown
(`n=0`). The optimization comparison remains only `n=2` baseline and `n=2`
candidate backend-job samples; it does not support an end-to-end speedup claim.

## Kendra-owned work completed in the repository

- Current-main staging target protection was merged in PR #215.
- PR #196 added the path-filtered deterministic AI evaluation and saved-analysis fail-closed spend guard. The AI owner approved the #93 deterministic criteria. The unmerged PR #220 workflow revision now reports and passes the exact context with the full evaluation on an AI-related workflow change; verify the explicit N/A path on an unrelated change before closing #93.
- Dependency security is a required main check.
- This refresh records the current-main staging acceptance and the observed production blocker. Issue #133 is closed; the remaining issues above are left open because their acceptance requires evidence or owner/team decisions not present here.
