# DevOps rubric readiness — 2026-11-27 08:22 UTC

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
| Pipeline design and coverage | 15 | **Partial.** CI covers backend, extension, migration source, security, CodeQL, workflow lint, deterministic AI checks, and a trusted staging controller. | On integrated PR #268 SHA `9039d1a`, CI Staging integration failed because a test imported an undefined `ROOT`; the correction is in this PR update and needs fresh exact-head CI. Production image promotion and automatic exact-SHA post-deploy acceptance are not live. |
| Automation and quality gates | 10 | **Partial.** Main has eight required contexts, strict checks and independent review requirements in the latest captured settings. The trusted controller fails closed; Neon preflight passed for `9039d1a`. | The new SHA did not pass its first staging integration run, and its `Secretary staging` status failed accordingly. The controlled failure-to-block-merge experiment is not evidenced. Fresh checks and reviewer approval are required after the fix. |
| Optimization with measured results | 20 | **Partial.** The reproducible 28-day report records a 3.66-minute merge-to-live proxy median (`60/142` matched), 63 successful deploy records, and CI median 66 seconds (`115/117` successful). | No comparable before/after result establishes a downward trend in end-to-end pipeline time and failure rate. Change failure rate, failed-deployment restore time, and deployment rework are not measured; no score is inferred from unknowns. |
| Environments and secrets | 10 | **Partial.** GitHub staging credentials are isolated by protected environments; the successful 554fd run verified the isolated Neon branch through real staging acceptance without exposing values. | Render production and staging remain Git-backed; same-digest deployment is absent. Current release-promotion migration credential/config attestations remain incomplete. Recheck the masked Render-to-Neon/Auth mapping for the integrated head. |
| AI-aware pipeline practices | 10 | **Partial.** Deterministic AI regression checks pass in CI. The hosted acceptance record explicitly marks quality blocked when no approval is supplied. | The policy is pending. No approved, representative holdout report bound to the exact release model exists; historical English evaluation is advisory only. Current model/provider acceptance and durable budget/alert evidence are missing. |
| Release and rollback | 10 | **Partial / below Excellent.** Versioned manifest, gated workflow, staged artifact checks, and rollback documentation are implemented in the candidate. Production Auto Deploy is off. | Render is not image-backed; no identical backend digest was promoted, no production tag/release/changelog exists, and no current-schema-compatible production rollback has been rehearsed. |
| Reliability and incident handling | 10 | **Partial.** Isolated staging CRUD passed for SHA `554fd223`; CI and recovery/runbook controls exist. | This does not demonstrate the integrated SHA or production availability. Current alert delivery, named backup responder, alert-to-recovery drill, application rollback, restore, and measured RTO/RPO are not proven. |
| Metrics, documentation, and reporting | 10 | **Partial.** Dated DORA source/report, current PR integration record, and redacted exact-SHA staging evidence are published. Unknown values remain explicitly unknown. | CFR, restore time, rework, comparable end-to-end improvement, and a full current weekly/sprint metric log remain unmeasured. |
| Live performance | 5 | **Partial.** Protected staging Auth/CRUD and extension UX passed on `554fd223` with ZIP SHA-256 `7d7082e1e1bc5f3c0fd0c89d8e1d85bb4ec0b3180cd19602cd87d322b955dccd`. | That run is stale for integrated `9039d1a`; its preflight passed, but CI integration failed before hosted acceptance. No approved AI result or production journey/performance demonstration exists. |

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
- Trusted run [45958860400](https://github.com/kendshhh/PhishLens/actions/runs/45958860400)
  passed on PR #268 SHA `554fd223ec98852acb12ebca01812530a84fde2d`, with backend
  and deployed SHA matching, extension ZIP SHA-256
  `7d7082e1e1bc5f3c0fd0c89d8e1d85bb4ec0b3180cd19602cd87d322b955dccd`, Neon
  project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`, and migration
  revision `0005_ai_request_quota`. It passed sign-in, persistent CRUD, reload,
  ownership/isolation, cleanup, and extension UX. AI quality was blocked and
  backend image digest was absent.
- Current integrated #268 head `9039d1a490d283cc7bcca9243aa02b705036a7dd`
  passed trusted Neon preflight [45963430015](https://github.com/kendshhh/PhishLens/actions/runs/45963430015).
  Its first CI run [45963431013](https://github.com/kendshhh/PhishLens/actions/runs/45963431013)
  failed one test import (`ROOT` undefined), causing `Secretary staging` to
  fail. The issue is fixed in this PR update, but the next exact-head checks and
  protected Auth/CRUD run have not completed. No acceptance is claimed for
  `9039d1a` or its successor until then.

The current dependency and merge-tree evidence is in the
[PR alignment record](pr-alignment-2026-11-27.md).

## Required closure evidence

1. Re-run CI on the corrected integrated #268 head, then obtain xxTrixia's
   approval for that exact protected staging run. Reject or ignore stale heads.
2. Reconfirm the isolated Neon/Render runtime mapping and least-privilege
   migration settings without publishing values.
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
