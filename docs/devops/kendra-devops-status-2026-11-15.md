# Kendra DevOps status — Sprints 1–3 — 2026-11-15

This is the current evidence snapshot for Kendra's DevOps work. It separates
merged repository controls, staging evidence, production state, and items that
need decisions or records from other people. It is not a course grade or a
weighted project-completion percentage.

## Current repository and controls

- Repository `kendshhh/PhishLens` is public; the owner has confirmed that public visibility is intended.
- Current `main`: `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` (PR #215).
- Issue tracker: 30 closed and 34 open of 64 total (46.9% raw closure, not a project-progress score). Issue #133 is closed after the documented control evidence was merged.
- Main ruleset `26782191` is active and requires 11 contexts, including deterministic AI evaluation, dependency security, and dependency graph review.
- Current-main push runs for CI, Workflow lint, and Dependency security completed successfully: [CI #43610239369](https://github.com/kendshhh/PhishLens/actions/runs/43610239369), [Workflow lint #43610239268](https://github.com/kendshhh/PhishLens/actions/runs/43610239268), and [Dependency security #43610239226](https://github.com/kendshhh/PhishLens/actions/runs/43610239226). The [AI evaluation workflow #43610239261](https://github.com/kendshhh/PhishLens/actions/runs/43610239261) completed with its evaluation job skipped because this change did not touch AI paths; it made no paid provider request.
- The 40-case TF-IDF result remains a development regression signal only. It is not held-out quality evidence and has no AI-owner-approved blocking threshold. See [issue #92](https://github.com/kendshhh/PhishLens/issues/92) and [issue #93](https://github.com/kendshhh/PhishLens/issues/93).

## Security history scan — 2026-11-15

Gitleaks v8.30.1 scanned all local Git refs (607 commits, about 21.22 MB). It
reported seven `generic-api-key` findings in historical package-identity JSON
files under `docs/frontend/issue-131`, `issue-136`, and `issue-141`. Review of
the redacted matches and JSON structure showed these are SHA-256 file digests
whose asset path is `js/api.js`, not credentials. All twelve changed/added files
scanned separately with zero findings. No repository history was rewritten and
no finding was suppressed. This is heuristic secret scanning, not proof that
every kind of sensitive information is absent.

## Staging: current-main acceptance passed

Staging now serves the exact current-main SHA after PR #215. The verified
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
also failed because production did not match current `main`.

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
| [#92](https://github.com/kendshhh/PhishLens/issues/92) and [#93](https://github.com/kendshhh/PhishLens/issues/93) | Frozen, approved held-out evaluation and AI-owner decision on deterministic thresholds. | Requires approved data and AI-owner review. The 40-case development set cannot substitute. |
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
- Deterministic AI evaluation on AI-related changes and the saved-analysis fail-closed spend guard were merged in PR #196; the deterministic check is required by the main ruleset.
- Dependency security is a required main check.
- This refresh records the current-main staging acceptance and the observed production blocker. Issue #133 is closed; the remaining issues above are left open because their acceptance requires evidence or owner/team decisions not present here.
