# DevOps rubric readiness — 2026-11-27 07:48 UTC

## Decision

**A 10/10 (100/100) is not supported. Release remains NO-GO.** This crosswalk
uses the 100-point rubric supplied by the project owner. It records current
evidence and gaps; it does not convert qualitative bands into invented partial
points. The rubric gives criterion maxima and broad bands, but does not define
how to score the gaps between bands or how to award partial points within a
criterion.

## Criterion crosswalk

| Rubric criterion | Max | Current evidence | Gap to Excellent |
|---|---:|---|---|
| Pipeline design and coverage | 15 | **Partial.** Backend, extension, integration, migration, security, CodeQL, AI evaluation, workflow lint, staging acceptance, and production promotion stages are represented. Current PR #281 checks pass except protected staging is still waiting. | The controlled image promotion and production post-deploy user-flow verification are not live. Justification and current flow are documented in `PIPELINE.md`, but staging/production do not yet use the same immutable backend artifact. |
| Automation and quality gates | 10 | **Partial.** Main classic protection and active ruleset currently agree on eight required contexts, strict up-to-date checks, one approval, stale-review dismissal, and latest-push approval. Admin bypass is off. The staging label is present on PR #281. | A deliberately failing required check has not been demonstrated to block merge in a controlled test. Production promotion still requires an explicit workflow dispatch and external environment approval; the path is not yet proven end to end. |
| Optimization with measured results | 20 | **Partial.** The current 28-day DORA report is reproducible. Merge-to-live median is 3.66 minutes (`n=60` exact SHA matches of 142 merged PRs); deployment frequency is 63 successful records / 28 days; main-CI median is 66 seconds (`n=117`, 115 pass, 2 fail). Prior backend-job optimization comparisons are recorded. | No current like-for-like end-to-end optimization demonstrates a downward pipeline-time and failure-rate trend. Change fail rate, failed-deployment recovery, and rework are not measured. Prior small samples do not establish a dependable system-wide improvement. |
| Environments and secrets | 10 | **Partial.** GitHub staging environments require xxTrixia, prevent self-review and admin bypass, and allow `main` only. Production uses a separate protected GitHub environment and independent reviewer. No secret values are in this evidence. | Render-to-Neon runtime/migration/Auth mapping and migration credential are not verified. Render production and staging are Git-backed Python services; Render's Production environment metadata is unprotected. The public API allowlist is `0.0.0.0/0` by design; it does not demonstrate deploy-credential exposure. Review platform access controls without disrupting the client-facing API. |
| AI-aware pipeline practices | 10 | **Partial.** Mocked AI checks and deterministic AI evaluation run in CI. Staging acceptance correctly reports AI quality as blocked when approval evidence is absent. | The policy remains pending; the representative held-out report and approved thresholds are missing. Production analysis is disabled. A scheduled live provider smoke and shared durable spend/rate limits are not verified. The historical English cohort is advisory only. |
| Release and rollback | 10 | **Partial / below Excellent.** A controlled release workflow, manifest validation, protected approval checks, and rollback documentation exist in the PR/repository. No production release was made. | No versioned release/tag/changelog exists. PR #281 promotion is unmerged and blocked on staging credentials, mapping attestation, AI approval, and image-backed Render configuration. A rollback compatible with current production schema/config has not been rehearsed. |
| Reliability and incident handling | 10 | **Partial.** The sampled main CI success share is 115/117 (98.29%); runbooks and incident records exist. | Two sampled CI failures remain in the rate; 15 existing Dependabot alerts (12 high, 3 moderate) were reported by GitHub. Current alert delivery, named backup responder, alert-to-recovery exercise, production rollback, and measured RTO/RPO are not demonstrated. The isolated Nov 20 restore does not prove current service recovery. |
| Metrics, documentation, and reporting | 10 | **Partial.** A dated DORA 4+1 source snapshot and generated report are published with sample counts and limits; pipeline, release, environment, and recovery documents exist. | Change fail rate, recovery time, and rework classifications remain unmeasured; current weekly/sprint completeness and a comparable optimization result are not established. Historical records remain explicitly dated. |
| Live performance | 5 | **Partial / below Excellent.** Historical exact-head staging acceptance on PR #268 and #282 verified persistent CRUD, account isolation, and extension UX. | Those runs are not current for the latest heads. Current #268/#282 have no exact-head Auth/CRUD acceptance; #281's current protected preflight is waiting and its trusted controller failed closed. There is no approved AI result or production promotion. On Nov 27, `/model-info` returned HTTP 200 with analysis disabled, while `/health`, `/ready`, and `/version` timed out after 15 seconds from this client. No current production journey/performance demonstration is available. |

## Exact staging evidence

- Historical PR #268 head `63b000e17631f9514d8763c4c88d054cbcfc2e24` passed run
  [45950870589](https://github.com/kendshhh/PhishLens/actions/runs/45950870589).
  Backend source SHA matched; extension ZIP SHA-256 was
  `f1ec77033373fde07cb4bd2fc45c34ea3e530fae6b2afc3d3e9176d3483d56b4`.
- Historical PR #282 head `7551e4077e4f71f2768a3d090b7ce437d727eb60` passed run
  [45949708542](https://github.com/kendshhh/PhishLens/actions/runs/45949708542).
  Backend source SHA matched; extension ZIP SHA-256 was
  `d1225eb823f6453ddd6b0c90778759c663ad9a4831b61c2138ed0d7e39087c01`.
- Both runs verified sign-in, create/list/read/update/delete, reload
  persistence, ownership, user isolation, cleanup, and loading/success/auth/API/
  timeout UI states against isolated Neon branch `br-rough-sea-a1l6ehi1`. Both
  report `backend_image_digest: null`, `ai_quality_status: blocked`, and
  `release_decision: no-go`. They are exact candidate acceptance evidence, not
  a production release.
- Current PR #268 head `554fd223ec98852acb12ebca01812530a84fde2d` and #282 head
  `3131dae6f09c30b267ca4aa7b864694a44fd744c` pass CI and Neon preflight but
  have no current hosted Auth/CRUD acceptance. Current PR #281 head
  `27859a31674f99f17a5e26454104b3e6719493a7` passes source/local checks; its
  Neon preflight is waiting for protected approval, and trusted controller run
  `45957149389` failed closed for lack of an exact-head preflight attestation.
  No acceptance is claimed for the current #281 head.

The current dependency and merge-tree evidence is in the
[PR alignment record](pr-alignment-2026-11-27.md).

## Required closure evidence

1. Complete exact-head protected staging for PR #281 only after the reviewer
   approves the current run and the mapping/migration credentials pass
   preflight. Keep stale runs rejected.
2. Privately verify Render runtime, migration, Neon project/branch/database,
   app/migration roles, and Auth endpoint; provision a fresh least-privilege
   migration credential. Do not publish values.
3. Obtain AI owner approval for the policy and representative holdout report;
   require the exact provider/model identity and quality status before release.
4. Configure a supported immutable image deployment for Render, promote the
   same backend digest and extension ZIP, then require exact-SHA production
   smoke and product acceptance before creating a tag/release.
5. Harden Render production access through the service owner’s reviewed change;
   exercise current-compatible application rollback and isolated data restore.
   Record alert delivery, backup responder, and measured RTO/RPO.
6. Link incident/rework classifications to deployment SHAs and run a
   like-for-like optimization study with adequate samples. Keep metrics marked
   “not measured” until authoritative records exist.

The full current metrics and source methodology are in
[the DORA report](dora-report-2026-11-27.md); current service observations are
in [metrics.md](metrics.md); release workflow state is in
[controlled-release.md](controlled-release.md).
