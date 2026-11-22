# Release verification record — 2026-11-22

## Decision

**NO-GO.** This record captures read-only checks on November 22 and a later same-day follow-up. It does not authorize deployment or claim product acceptance. No staging CRUD, account creation, migration, rollback, restore, or deployment was run. Production probes were GET-only. No credentials or connection strings were read into this record.

### Later same-day environment and recovery follow-up

This follow-up supersedes earlier staging-target, deployment, protection, and recovery statements below where they conflict. Render and Neon service/project metadata were cross-checked read-only. GitHub environment values and environment protection details below are from the supplied read-only settings review and were not independently queried in this pass. No secret values or product rows were accessed.

- GitHub `main` advanced after the initial 561c19d snapshot to [`f957cd3d22651ac3b6721a4d16dffba27fb6ee40`](https://github.com/kendshhh/PhishLens/commit/f957cd3d22651ac3b6721a4d16dffba27fb6ee40) (PR #278, merged at 2026-11-22 06:00 UTC). Backend, extension, workflow lint, dependency security, CodeQL, and deterministic AI checks passed. The Secretary `preview` job was skipped on the main push. The scheduled [production SHA/health run 45001981909](https://github.com/kendshhh/PhishLens/actions/runs/45001981909) failed at 08:15 UTC in “Compare public production endpoints with main”; production remains on `811980c`, not current `main`.
- PR #266 is still open at head `c6dffaea8c402eacac637e6d2d927faaaf37833f`, based on the now-stale `561c19d` main. Its latest [Hosted staging run 44982062694](https://github.com/kendshhh/PhishLens/actions/runs/44982062694) failed the exact database/Auth mapping preflight; deploy and authenticated CRUD acceptance were skipped. PR #251 is open at head `c3b42eb3414cf5b9c22bca46eed59a59ba21a987`, based on current `f957cd3`; its [Hosted staging run 44993222341](https://github.com/kendshhh/PhishLens/actions/runs/44993222341) failed the same mapping preflight, so deployment and CRUD were skipped. Neither PR passes product acceptance.
- Render metadata reports staging service `srv-db92irlg1s2s739404i0` on Git branch `main`, using native Python and `python scripts/start_staging.py`, with Auto-Deploy off. The latest live deployment is `dep-dc14umnf3r2c73bl1c20` at full SHA `6b6b83d5ef261e10e4312a78b5e2f3953b0e36ec`; later attempts on `561c19da40165d7994d86232af63059a288b4ac2` failed or were canceled. `/version` did not return before the later probe timed out, so the running identity is deployment-metadata evidence, not a current endpoint confirmation.
- Neon metadata confirms PR251 project `phishlens-staging-pr251-isolated` (`ancient-brook-17208049`) and ready default `staging-root` branch (`br-rough-sea-a1l6ehi1`) are separate from production. Its project settings have public connections enabled and no IP allowlist. The supplied catalog review reports `phishlens_dev` has no public tables or Alembic history, so it is not ready for app acceptance.
- The supplied current GitHub environment review says staging currently targets existing project `hidden-shadow-38533062`, branch `br-broad-feather-b3261w7l`; production targets `patient-bird-25428852`. This corrects the earlier claim that staging and production environment values named the same project. PR251's `ancient-brook` project is not selected. Render does not expose variable values, so the effective runtime and migration URLs, roles, and Auth endpoint remain unmatched to the service.
- The local checkout's `scripts/start_staging.py` pins `ep-soft-fog-b3orfa8a`; the supplied deployed-source review says SHA `6b6b83d` uses environment-provided mapping values. This source/configuration drift must be reconciled against the owner-approved project and branch before changing the pin or deploying.
- The supplied settings review reports that staging permits self-review and includes stale `refs/pull/33/merge`; production blocks self-review but permits admin bypass and has only `inaki3023` as reviewer, with no production environment secrets or variables. The active `main` ruleset still requires Backend checks, Extension checks, Staging integration, and Secretary staging plus one approval. These controls do not yet establish an independent, non-bypassable release approval.
- No automatic Neon snapshot schedule is reported. The manual recovery snapshot and restored drill branch expire November 27, 2026; the drill is small-sample evidence, not measured service RTO/RPO. Render `notifyOnFail=default` is not proof of an alert route or tested delivery.
- Promotion is not image-based: staging is a native Python service, and the main workflow has no Docker/GHCR backend image build or digest promotion. The extension ZIP check is not backend artifact provenance. No same-digest staging-to-production path is evidenced.

## Candidate and deployment identity

| Gate | Status | Evidence |
|---|---|---|
| Eligible reviewed PR candidate | **Open** | None of the current release/staging PRs inspected is an updated, independently approved candidate. The local workspace remains dirty and is not a candidate. |
| PR #266 release workflow candidate | **Fail / not selected** | PR [#266](https://github.com/kendshhh/PhishLens/pull/266) is open at head `c6dffaea8c402eacac637e6d2d927faaaf37833f`, based on `561c19da40165d7994d86232af63059a288b4ac2`, now behind current `main` `f957cd3d22651ac3b6721a4d16dffba27fb6ee40`. Its latest [CI run 44982062694](https://github.com/kendshhh/PhishLens/actions/runs/44982062694) failed exact Render staging Auth/database mapping before deployment; deploy and authenticated acceptance were skipped. Earlier attempt [44930164084](https://github.com/kendshhh/PhishLens/actions/runs/44930164084) timed out at sign-in and did not pass dependent CRUD, persistence, isolation, cleanup, or UX checks. |
| PR #251 Auth candidate | **Fail / not selected** | PR [#251](https://github.com/kendshhh/PhishLens/pull/251) is open at head `c3b42eb3414cf5b9c22bca46eed59a59ba21a987`, based on current `main` `f957cd3d22651ac3b6721a4d16dffba27fb6ee40`. In [CI run 44993222341](https://github.com/kendshhh/PhishLens/actions/runs/44993222341), Hosted staging failed while verifying Render staging Auth mode and exact database mapping; deployment and authenticated product checks were skipped. |
| Latest host/allowlist gate | **Fail before deployment** | PR #270 head `b9dc2361d9045e86252725a8cc5f20a621c7903c` failed in [CI run 44933763538](https://github.com/kendshhh/PhishLens/actions/runs/44933763538) at `scripts/deploy_staging.py`: `Staging database host/name does not match the isolated allowlist`. Product steps were skipped. Keep this guard in place until the authorized owner confirms the intended target and roles. |
| Other current staging candidate | **Fail / not selected** | PR #268 head `959dbd4532a110557233a5425fee5a48c11244c5` is not mergeable and its exact-head CI run [44911243336](https://github.com/kendshhh/PhishLens/actions/runs/44911243336) failed. It is not a reviewed acceptance candidate. |
| Current staging deployment | **Pass (deploy metadata only)** | Later Render metadata reports `dep-dc14umnf3r2c73bl1c20` live at SHA `6b6b83d5ef261e10e4312a78b5e2f3953b0e36ec`; Auto-Deploy is off. The earlier `561c19d` deployment was superseded. Later `/version` timed out, so live endpoint identity and product acceptance are not verified. |
| Reported sign-in failure | **Fail (unlinked report)** | The November 21 workspace note reports the latest product acceptance attempt failed at sign-in, so CRUD, persistence, isolation, cleanup, and extension UX did not pass. That note has no run URL or tested SHA; it cannot be bound to a current candidate. |

## Live staging probes

Initial November 22, 2026 probes, taken before the later staging deployment. They are historical observations, not evidence about the current live staging runtime.

| Probe | Status | Result |
|---|---|---|
| `GET /version` | **Pass (superseded observation)** | At the earlier probe, HTTP 200 reported `environment=staging`; commit `561c19da40165d7994d86232af63059a288b4ac2`. A later request after the `6b6b83d` deploy timed out. |
| `GET /health` | **Pass (live endpoint only)** | HTTP 200; status `ok`; service `phishlens-api`. |
| `GET /ready` | **Pass (live endpoint only)** | HTTP 200; `ready`; database `connected`. This does not identify the Neon project, branch, or role. |
| `GET /model-info` | **Pass (superseded identity observation)** | The earlier endpoint returned HTTP 200 with provider `tfidf`, model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`, and alert threshold `0.8871260470833809`. This is not a probe of the later `6b6b83d` deployment. The approved historical English v12a study meets only its scoped advisory thresholds (95% phishing recall, 0.1% legitimate false-positive rate, and 1,200/1,200 valid outputs; see [study evidence](../ai/sprint-4-release-evidence.md)). Contemporary-source qualification, explanation review, and candidate-level model/provider acceptance remain **Open**. |
| Anonymous `GET /api/analyses` | **Pass (protection behavior only)** | HTTP 401 with `WWW-Authenticate: Bearer`. This does not establish authenticated history or CRUD. |

## Staging target, roles, and Auth

| Gate | Status | Evidence |
|---|---|---|
| GitHub target agrees with the checked-out startup pin | **Fail / source drift** | The local `scripts/start_staging.py` pins `ep-soft-fog-b3orfa8a`; the supplied deployed-source review says live SHA `6b6b83d` uses environment-provided mapping. Current GitHub staging values are reported to point at `hidden-shadow-38533062` / `br-broad-feather-b3261w7l`, while production points at `patient-bird-25428852`. Render does not expose the values, so no complete service-to-Neon match is proven. |
| Approved isolated staging target | **Open / not selected** | Existing staging and production projects are separate per the supplied GitHub value review; however, the effective Render target is not independently matched. PR251 project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, is not selected by current staging values. Neon metadata confirms it exists and its branch is ready; the supplied catalog check reports `phishlens_dev` has zero public tables and no Alembic revision. Do not deploy to or migrate either target until the owner confirms which project/branch is intended. |
| Runtime and migration roles/schema | **Open** | The supplied PR251 catalog review reports `phishlens_staging_app` can connect and use `public` but cannot create there, is not elevated, and is not a member of `neondb_owner`; with no tables/Alembic history, grants and migration state cannot be validated. On existing `hidden-shadow`, the supplied review found `users` SELECT/INSERT/UPDATE/DELETE plus `alembic_version` read for the app role, broader than the earlier least-privilege expectation. Render does not reveal whether either mapping is active. |
| Auth and test identities | **Open** | The supplied PR251 review reports a Neon Auth URL/JWKS under `ancient-brook` with the staging Render origin trusted and email/password verification enabled; this differs from the existing `phishlens-staging` Auth endpoint under `hidden-shadow`. Current service-to-Auth mapping, A/B account distinctness, synthetic status, and verification status remain unverified. No account was created or used. |
| Migration revision | **Open** | No migration preflight ran for an eligible candidate. The November 21 migration revision is historical and is not asserted for this deploy. |

## GitHub protection and trusted workflow

| Gate | Status | Evidence |
|---|---|---|
| Staging independent review | **Fail** | The supplied settings review reports staging reviewers `EnviousCoal` and `kendshhh`, but self-review is allowed. Required review is not independent until that setting is corrected and verified. |
| Production approval and bypass | **Fail** | The supplied settings review reports self-review is blocked but admin bypass is enabled, only `inaki3023` is a reviewer, and the production environment has no secrets or variables. This is not a fully enforced independent approval path. |
| Deployment branch rules | **Fail** | The supplied staging allowlist includes `main`, `refs/pull/*/merge`, and stale `refs/pull/33/merge`. Confirm intended refs and remove the stale entry before using this environment as a release gate. |
| A/B protected secret names | **Pass (names only)** | `STAGING_AUTH_USER_A_EMAIL`, `STAGING_AUTH_USER_A_PASSWORD`, `STAGING_AUTH_USER_B_EMAIL`, and `STAGING_AUTH_USER_B_PASSWORD` are present. Values were not inspected or recorded; account properties remain **Open**. |
| Effective `main` rules | **Partial** | The supplied current review reports one approval and four required checks: `Backend checks`, `Extension checks`, `Staging integration`, and `Secretary staging`. Earlier ruleset metadata showed the same contexts. Classic branch-protection details remain inaccessible through the connected GitHub integration; independent approval at deployment environments is separately incomplete as noted above. |
| Trusted staging workflow | **Fail / not ready** | GitHub `main` still contains the legacy hosted path: trusted `staging_smoke.mjs` plus a `verify_crud.mjs --allow-writes` step without the A/B Auth credentials in that job's environment. The newer local/candidate workflow is not the trusted default-branch controller. Do not trigger hosted staging until the reviewed controller and Auth path are reconciled. |
| Same backend artifact promoted by digest | **Fail** | Render staging is a native Python service and the main workflow has no backend Docker/GHCR image build or immutable digest promotion. Extension ZIP verification against a staging SHA does not prove backend image identity. |

## Render auto-deploy reconciliation

| Gate | Status | Evidence |
|---|---|---|
| Production Auto-Deploy history | **Pass (setting off; current SHA behind main)** | Render metadata currently reports Auto-Deploy off. The latest live deploy is `dep-dc1716etlv9c73b8nl0g`, SHA `811980c2cbf70d9957146bf329627f0826a018f1`, trigger `service_updated`; the earlier `new_commit` deployment `dep-dc07rs67bikc73fjgjq0` of the same SHA is deactivated. Production remains behind current `main` `f957cd3`; the scheduled production SHA/health check failed. No production deploy was triggered during this review. |

## Production read-only probes

| Probe | Status | Result |
|---|---|---|
| `GET /version` | **Pass on earlier probe; deployment identity reconfirmed** | Earlier warm retry returned HTTP 200, `environment=production`, SHA `811980c2cbf70d9957146bf329627f0826a018f1`. Later Render deploy metadata still reports that SHA live; no later endpoint probe was made. |
| `GET /health`, `GET /ready` | **Pass** | Both returned HTTP 200; readiness reported the database connected. |
| `GET /model-info` | **Pass (disabled mode)** | HTTP 200; `provider_mode=disabled`, `analysis_enabled=false`, and TF-IDF/local-review support disabled. No inference was run. |
| Anonymous `GET /api/analyses` | **Open** | Read-only response was HTTP 200 with an existing item. No write was made. The production owner should confirm whether anonymous saved-report listing is intended. |

## Recovery and alert follow-up

| Gate | Status | Evidence |
|---|---|---|
| Scheduled recovery points | **Fail / absent** | The supplied account review found no automatic Neon snapshot schedule for current production or staging. One manual snapshot and its isolated restored branch expire November 27, 2026. |
| Restore objectives | **Open** | The prior isolated restore covers a small dataset only. Service RTO and recoverable-point age/RPO were not measured; do not report the branch-ready time as application recovery time. |
| Alert delivery | **Open** | Render reports `notifyOnFail=default`; no verified recipient/channel or controlled alert-delivery drill is recorded. |

## Package, browser, and data cleanup

| Gate | Status | Evidence |
|---|---|---|
| Extension package for exact candidate | **Open** | No eligible candidate package or package SHA-256 was produced. |
| Installed Chrome acceptance | **Open** | No package from the deployed candidate was installed; Chrome version and browser result are unrecorded. Automated package checks would not replace this acceptance. |
| Authenticated CRUD, fresh-client persistence, cross-user denial, and failure handling | **Open** | No staging writes or test accounts were used. These checks remain unrun pending owner target/role confirmation and an approved exact candidate. |
| Cleanup | **Open** | No test records were created, so no acceptance cleanup result is claimed. |

## Required next evidence

1. Have the staging/database owner decide whether the intended target is the existing `hidden-shadow` project or PR251's `ancient-brook` project. For `ancient-brook`, provision and verify schema/migrations and grants before it can host the app; do not infer readiness from the root branch being ready.
2. Privately compare the Render runtime and migration host/database/role identities, Auth endpoint, Neon project/branch IDs, and startup allowlist. Bind project and branch identity to the same verified host; record only masked identities and read-only catalog results.
3. Reconcile the local pinned `ep-soft-fog` startup code with the reviewed deployed-source behavior only after the owner approves the target. Keep staging separate from production.
4. Have the environment owner prevent staging self-review, remove stale `refs/pull/33/merge`, and close the production admin-bypass path with at least one backup independent reviewer. Verify saved settings and distinct verified synthetic A/B accounts without exposing values.
5. Implement and review a backend image build with source provenance and SBOM, then deploy one immutable digest to staging and production; preserve the extension ZIP digest and bind both artifacts in a manifest.
6. Select an updated independently reviewed PR, record its head and merge-candidate SHA, reconcile the trusted workflow, and run migration preflight before any staging deployment or CRUD.
7. On that one candidate, finish A/B sign-in, CRUD, fresh-client persistence, cross-user denial, failure handling, cleanup, post-run identity probes, and installed Chrome acceptance. Then rehearse application rollback and isolated restore, measure RTO/RPO, configure and test alert routing, and only then consider release approval.

Keep release issue #153 **NO-GO** until every required gate passes on one candidate and its evidence is reviewed.
