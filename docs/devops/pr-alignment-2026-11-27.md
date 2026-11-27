# Coordinated release PR alignment — 2026-11-27 11:00 UTC

This snapshot is based on current GitHub PR metadata and a full filename inventory
for all 16 open PRs at 11:00 UTC; #282 checks were refreshed at 10:48 UTC. The machine-readable record is
[evidence/open-pr-alignment-2026-11-27.json](evidence/open-pr-alignment-2026-11-27.json).
It records full head/base SHAs, current base-branch tips, authors, review decisions,
labels, changed files, explicit PR references, and database-migration paths. The
inventory is metadata only; it does not read secret values or database contents.
`main` is `88156d479d19eb0b8018ab76aa3170eb60079765`.

## Coordinated release history

| PR | Current state | Exact identity and result | Migration / action |
|---|---|---|---|
| [#268](https://github.com/kendshhh/PhishLens/pull/268) | Merged 2026-11-27 08:44 UTC | Reviewed head `d77491d8fd91252190755714df8e5fa475e9c13b` merged as main `88156d479d19eb0b8018ab76aa3170eb60079765`; merge tree `89a3b3e0701629497c4f1f14e756f26ca98a10c7` equals the accepted candidate tree. | No DB migration files. Trusted staging run `45966647832` passed the exact extension/backend Auth and persistent CRUD journey on isolated Neon revision `0005_ai_request_quota`. Model approval was blocked; no image digest was produced. |
| [#281](https://github.com/kendshhh/PhishLens/pull/281) | Closed, unmerged | Its intended release-gate work was integrated through #268. Current PR has no open diff; its closed description is historical and stale. | Do not merge or reopen the old head. Reopen only for a new unique change and fresh review. |
| [#282](https://github.com/kendshhh/PhishLens/pull/282) | Open, changes requested | Current head `27118fc610f2c01fd11a472e0939f6dc74cbe130`, base is current main `88156d479d19eb0b8018ab76aa3170eb60079765`; one changed file: `docs/devops/pr282-integration-2026-11-27.md`. | No migration or runtime code. Exact-head Backend, Extension, Staging integration, migration source preflight, CodeQL, dependency security, AI evaluation, dependency graph review, and workflow lint passed. `verify-neon` and Issue 90 are skipped by docs-only conditions; Secretary staging explicitly reports N/A. No hosted product acceptance is requested. Review remains changes requested. |

PR #282's previous runtime and quota work is already in #268/main. It is
incorrect to describe the current #282 diff as the old 101-file runtime change.
The `needs-hosted-staging` label is no longer appropriate for this documentation-only
head and should not trigger a hosted deploy.

## All open PRs

Base `recorded SHA → current branch tip` reveals whether a PR is based on the
latest tip of its target branch. A child stacked on another open branch is
intentionally based on that branch's current head and is not called stale merely
because it differs from `main`. “Explicit PR references” are text references from
PR descriptions, not proof of a dependency by themselves.

| PR | Review | Base branch @ recorded SHA → current tip | Head branch @ SHA | Explicit PR references | Diff / DB migrations | Description, overlap, and safe action |
|---|---|---|---|---|---|---|
| [#303](https://github.com/kendshhh/PhishLens/pull/303) | REVIEW_REQUIRED | `main` @ `88156d479d19eb0b8018ab76aa3170eb60079765` → `88156d479d19eb0b8018ab76aa3170eb60079765` | `codex/local-rag-review` @ `06bf7323d8e6983041d94e45bd2e7e97027470c5` | — | 64 files; migrations: none | Independent main PR; shares 58 changed paths with #293 and 28 with #294, plus smaller UI overlap with #298 and #250. Not a declared stack; owners must resolve overlap before either candidate merges. |
| [#298](https://github.com/kendshhh/PhishLens/pull/298) | APPROVED | `phishlens-ui-scan` @ `6056419bae22507a4dd922feb19185e5d7c97d9a` → `6056419bae22507a4dd922feb19185e5d7c97d9a` | `feat/sidebar-ui-andrei` @ `1717724e3005ff62ed2f8a00f69d651d9972cd4b` | — | 3 files; migrations: none | Intentional child of #293: its base branch is exactly #293 head. Keep the stack and land/validate parent first; 2 shared popup paths require final-tree review. |
| [#294](https://github.com/kendshhh/PhishLens/pull/294) | review state not reported | `codex/release-gates-20261121` @ `2a9769738424fc1a4c112d606e81e48d7342963f` → `fcc81d08962a493b489a1c73ebeff34a6d361e77` (stale base) | `codex/pr269-context-model-20261125` @ `75e2162309cedf0341bbcc0831bc35ebf8007ad6` | #266 | 29 files; migrations: none | PR body identifies #266 as prerequisite; base branch `codex/release-gates-20261121` is the merged #266 line, but recorded base SHA is behind its current tip. 28 shared paths with #293/#303 need owner-agreed integration order. |
| [#293](https://github.com/kendshhh/PhishLens/pull/293) | CHANGES_REQUESTED | `main` @ `28f136894ac0c220fc370feb926da335472b283d` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `phishlens-ui-scan` @ `6056419bae22507a4dd922feb19185e5d7c97d9a` | — | 58 files; migrations: none | Main base is stale. Parent of intentionally stacked #298. Shares 28 files with #294 and 58 with #303; compare combined AI/UI tree before merge. |
| [#291](https://github.com/kendshhh/PhishLens/pull/291) | APPROVED | `feature/extension-auth-main-sync` @ `71694c8283c831783a56f312b8f9bada098780d3` → `71694c8283c831783a56f312b8f9bada098780d3` | `codex/pr290-sqlalchemy-trusted-bump` @ `2c1cb07ee1365a8143438185505702a23a5f0adc` | #251 | 3 files; migrations: none | Intentional dependency branch based on merged #251. Duplicates all 3 SQLAlchemy requirement files changed by #290; select one canonical update. |
| [#290](https://github.com/kendshhh/PhishLens/pull/290) | APPROVED | `main` @ `d00c6d97729a76cf0af0e53e84faea201d109a42` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/pip/backend/sqlalchemy-2.1.9` @ `fca8651c52f6238116d08c338c398fc9dc01a085` | #251 | 3 files; migrations: none | Dependabot SQLAlchemy 2.1.9 update; base is stale and duplicates #291 across all 3 requirement files. Select one, refresh lock/constraints, then validate. |
| [#289](https://github.com/kendshhh/PhishLens/pull/289) | APPROVED | `main` @ `d00c6d97729a76cf0af0e53e84faea201d109a42` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/pip/backend/ruff-0.17.6` @ `eff625905dd80afa9de6b5f28d18af3410883341` | — | 1 files; migrations: none | Dependabot Ruff update; base is stale. Rebase/update and rerun checks before merge. |
| [#288](https://github.com/kendshhh/PhishLens/pull/288) | CHANGES_REQUESTED | `main` @ `d00c6d97729a76cf0af0e53e84faea201d109a42` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/pip/backend/fastapi-0.165.0` @ `eac134ddd1a166f38d99eaeb54e25d9fc51862b9` | — | 3 files; migrations: none | Dependabot FastAPI update; base is stale and overlaps shared Python requirement files with #290/#291/#242. Integrate dependency updates serially. |
| [#287](https://github.com/kendshhh/PhishLens/pull/287) | CHANGES_REQUESTED | `main` @ `d00c6d97729a76cf0af0e53e84faea201d109a42` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/pip/backend/httpx2-2.16.2` @ `80938bc9f2a15802060b6f4d5cbf52ad95fb0608` | — | 2 files; migrations: none | Dependabot httpx2 update; base is stale and overlaps development requirement/lockfile paths. Integrate serially. |
| [#286](https://github.com/kendshhh/PhishLens/pull/286) | CHANGES_REQUESTED | `main` @ `d00c6d97729a76cf0af0e53e84faea201d109a42` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/npm_and_yarn/eslint-10.15.0` @ `e8c5143bb3d81b510f3dbe61536f9912235697b1` | — | 2 files; migrations: none | Dependabot ESLint update; base is stale and overlaps package.json/package-lock with #285 and #237. Re-resolve lockfile after each chosen update. |
| [#285](https://github.com/kendshhh/PhishLens/pull/285) | CHANGES_REQUESTED | `main` @ `d00c6d97729a76cf0af0e53e84faea201d109a42` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/npm_and_yarn/playwright-1.65.1` @ `be5a94e7ff3d7b52d791bf2365978850f89c81e1` | — | 2 files; migrations: none | Dependabot Playwright update; base is stale and overlaps package.json/package-lock with #286 and #237. Re-resolve lockfile after each chosen update. |
| [#282](https://github.com/kendshhh/PhishLens/pull/282) | CHANGES_REQUESTED | `main` @ `88156d479d19eb0b8018ab76aa3170eb60079765` → `88156d479d19eb0b8018ab76aa3170eb60079765` | `codex/devops-evidence-go-20261123` @ `27118fc610f2c01fd11a472e0939f6dc74cbe130` | #268 | 1 file; migrations: none | Documentation-only integration record. Exact-head applicable checks passed; `verify-neon` and Issue 90 were skipped, Secretary staging is explicit N/A, and no hosted deploy or product acceptance ran. Review remains changes requested. |
| [#280](https://github.com/kendshhh/PhishLens/pull/280) | CHANGES_REQUESTED | `main` @ `0338ad163a4892987a6a682aed29b95c22c322da` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `codex/staging-auth-bridge-route` @ `42738d749068d8e853236bd6217c89cce47481f1` | #251 | 4 files; migrations: none | Main base is stale. Auth bridge files overlap changes already integrated in #268 and #282 historical code; compare current diff against main before deciding whether any unique fix remains. |
| [#250](https://github.com/kendshhh/PhishLens/pull/250) | CHANGES_REQUESTED | `main` @ `c06fb974ead1df1feacfcad0e8d507167274ff84` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `codex/sprint4-extension-20261119` @ `992a82a6ae0b22c9b49cc74700c1ba6971e6a471` | — | 8 files; migrations: none | Main base is stale; 3 extension/auth/browser files overlap #293/#303. Compare against current main and confirm unique remaining scope with its owner. |
| [#242](https://github.com/kendshhh/PhishLens/pull/242) | CHANGES_REQUESTED | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/pip/backend/google-genai-3.3.0` @ `b4be7286ce1a54c15b4c6036ed20de063c1ddaa9` | — | 4 files; migrations: none | Dependabot google-genai update is stale and overlaps Python requirement files with #288-#291. Earlier release records mark Gemini retired; confirm the dependency is still used before merge. |
| [#237](https://github.com/kendshhh/PhishLens/pull/237) | APPROVED | `main` @ `11f72ad3de1a3d39a24ce1f5cea45f2f0262a5d0` → `88156d479d19eb0b8018ab76aa3170eb60079765` (stale base) | `dependabot/npm_and_yarn/better-auth-1.7.23` @ `399bdcbde04fabc018d3bce89163cc681536ea73` | — | 4 files; migrations: none | Dependabot Better Auth update is stale and overlaps package lock paths with #285/#286. Integrate one lockfile change at a time. |

## Dependency, overlap, and merge-order findings

- **Intentional stack:** #298 is based on #293's exact current head. Preserve the
  stack; finish and merge/close the parent according to owner review first, then
  validate #298 against the resulting parent. Their two shared UI paths need a
  combined diff review.
- **Unresolved AI/UI overlap:** #293 and #294 share 28 changed paths. #303 is
  based on current `main`, not either PR, yet shares 58 paths with #293 and 28
  with #294. #303 also overlaps #250/#298 on extension UI paths. This could be
  copied, superseding, or parallel work; metadata cannot decide intent. The
  authors should identify one integration order, compare actual blob contents,
  preserve unique changes, then run exact-head checks on the combined tree.
- **Duplicate SQLAlchemy update:** #290 and #291 both change the same three
  requirements files to SQLAlchemy 2.1.9. #291 is based on the merged #251
  branch; #290 targets main on an older base. Select a single canonical PR,
  regenerate constraints/lockfiles once, and run backend/security checks. Do not
  merge both.
- **Shared dependency locks:** #288/#242 share the backend requirement files;
  #285/#286/#237 share npm package/lock files. Refresh and validate these updates
  serially so one lockfile resolution does not overwrite another. Confirm Gemini
  is still used before considering #242.
- **Stale targets:** Every open PR whose base is `main` at a SHA older than
  `88156d47` needs an owner decision to refresh/rebase, close as
  superseded, or keep intentionally stacked. Do not rewrite a branch or retarget
  a PR solely for cosmetic graph simplicity.
- **Superseded scope:** #280 and #250 overlap authentication/extension paths
  already changed on main. Their owners should compare current diffs with main
  and identify any unique remaining changes before requesting review.

## Migration graph and environment mapping

The current machine-readable inventory found **zero database migration files in
all 16 open PR diffs**. The `backend/ai/schemas.py` path, when
present, is an API/model schema rather than an Alembic database revision. The
accepted #268 candidate applied no production migration and reported staging
revision `0005_ai_request_quota` on the isolated PR251-approved Neon project and
branch. No migration graph divergence is introduced by the open PR set. The
current cross-PR sources of environment drift are instead deployment settings
and missing release credentials/configuration, documented in the
[environment map](environment-map-2026-11-27.md) and
[controlled release record](controlled-release.md).

The current environment map shows staging reviewer self-review prevented on
`staging`, `release-staging`, and `staging-neon-preflight`; their `main`-only
ref policies and reviewer lists were preserved. Classic branch protection and
active ruleset #27733591 agree on eight strict required checks. No deliberately
failing required-check experiment has been run, so merge-blocking behavior is
not demonstrated by a negative test.

## Release status

The latest evidence does not support 10/10 or GO. Exact candidate product
acceptance passed in isolated staging, but model-quality approval, live current
staging identity, same-image staging-to-production promotion, production exact-SHA
acceptance, release tag/changelog, current-compatible rollback, measured database
restore/RTO/RPO, alert delivery, and a comparable optimization result are still
open. Keep issue #153 **NO-GO** and do not claim these gaps as completed by a
green CI check or documentation update.
