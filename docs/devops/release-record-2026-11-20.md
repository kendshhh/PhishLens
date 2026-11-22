# Release record — 2026-11-20

> Historical snapshot. Service identities and control-plane observations were
> refreshed on November 21 in the
> [current release record](release-record-2026-11-21.md). Preserve this file as
> the November 20 evidence; do not use it as current deployment state.

## Decision

**NO-GO.** This record fixes the product scope and captures the identities
observed during the November 20 audit. It is not approval to deploy or a claim
that application acceptance is complete.

## Release scope

The intended CSP221A product is the **PhishLens Chrome Manifest V3 extension,
backed by the PhishLens FastAPI service on Render and PostgreSQL/Auth on Neon**.
The `https://csp221a.vercel.app/` address is the CSP221A course guide, not the
PhishLens product release URL. Remove it from product-release links while
retaining it where the course guide itself is referenced.

The historical web-app note was reconciled in
[issue #153](https://github.com/kendshhh/PhishLens/issues/153): PR #244 was a
short-lived experiment and PR #253 records that the conversion was abandoned.
The issue and this record now agree that Chrome is the release target. The
instructor's confirmation that the extension satisfies the frontend requirement
is still pending; no instructor decision is claimed.
The draft seven-area evidence map and scoring rule are in the
[release readiness scorecard](release-readiness-scorecard-2026-11-20.md);
weights still need team/instructor agreement, so no completion percentage is
reported.

## Observed candidate identities

| Component | Observed identity | Acceptance state |
|---|---|---|
| GitHub source | `main` at [`16f955321caf5dc368181be7ce5c00643750545d`](https://github.com/kendshhh/PhishLens/commit/16f955321caf5dc368181be7ce5c00643750545d), merged PR #255 | EnviousCoal approved PR #255; its reported CI passed and Render deployed the same SHA via `new_commit`. Hosted staging was skipped; this is pipeline evidence for a DevOps change, not product acceptance. No release tag exists. |
| Production API | Render reports live deploy `dep-dc03j4sipgvc738ueieg`, source SHA `16f955321caf5dc368181be7ce5c00643750545d` | Deployment identity/state verified in Render. Current exact-SHA feature smoke is not established. The last recorded `/model-info` result on prior SHA `60641f3` was `provider_mode=unavailable`; direct endpoint checks for the new deploy were blocked by a Cloudflare challenge in this audit. |
| Staging API | Render reports live deploy `dep-dc018hlg1s2s73dtalng`, source SHA `d6612c258f289b3a45d8229e4a4803cac75a91ee` | Health/readiness and bounded preflight passed for this exact SHA; staging is not the production SHA. |
| Staging extension package | `PhishLens-Staging-Auth-Extension.zip`, source SHA `d6612c258f289b3a45d8229e4a4803cac75a91ee`, ZIP SHA-256 `23f4178334009493b4639114d53439493f07a0991468a4a267a37763c2047285`; sidecar SHA-256 `73b348817d4062e4c2044283dd8d8a79f04ee5c2c67c49ad952d6563096df3ac` | Hashes and source identity are recorded in PR #251. Staging-only manifest; `trusted_chrome_origin=null`; installed acceptance is pending. |
| AI model | Staging PR #251 preflight reports TF-IDF; the deployed model artifact SHA recorded for staging is `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` | Staging identity only. Production model status on SHA `16f9553` still needs an exact-SHA probe; no broad release-quality acceptance is claimed. |
| Auth mode | PR #251 exact-head bounded preflight records `REPORT_AUTH_MODE=neon`; anonymous saved-report request returned `401 Bearer` | Auth configuration is identified for preflight, but live sign-in and authenticated saved-report acceptance are pending. |
| Neon target | PR #251 preflight records Neon project `patient-bird-25428852`, branch `pr-58-staging` (`br-delicate-paper-b381z98i`), report DB `phishlens_dev`, runtime role `phishlens_staging_app`, Auth DB `neondb` | This is a staging preflight target, not permission to write. Private Render-to-Neon mapping and role/grant verification remain required before staging writes. |

### Candidate selection status

The `d6612c2` backend plus the exact-head PR #251 ZIP is the identified
**staging verification candidate** for the Auth journey. It is not the final
release candidate: PR #250's AI-integrated extension head is a different SHA
(`57fa2d55614f9f95e9263d584151481483929613`) and no exact package built from a
single reviewed, integrated source/backend/model/Auth tuple has been selected.
The first release-gate action is to consolidate and review the intended changes,
then build and record one package from that exact source. Do not substitute the
PR #251 staging ZIP for the separate PR #250 candidate.

## Required release evidence

- [x] Reconcile issue #153 with the Chrome extension scope; instructor confirmation of the frontend requirement remains pending.
- [x] Produce and record a staging extension package with exact source SHA and ZIP SHA-256; installed acceptance and its pairing with the integrated release candidate remain pending.
- [ ] Record the exact backend SHA, model/provider identity, Auth mode and verified Neon branch mapping for that package.
- [ ] Pass authenticated staging sign-in and saved-report create/list/read/update/delete, persistence, ownership/isolation, failure-state and cleanup checks on that same pair.
- [ ] Pass the approved AI quality evaluation on the intended, reviewed evaluation cohort; retain model/data provenance and results.
- [ ] Verify the effective required GitHub checks and independent approval using a current PR.
- [ ] Run exact-SHA deployment smoke after the approved release; retain health, readiness, version, provider and user-flow evidence.
- [ ] Rehearse application rollback to a schema/config-compatible target and separately restore Neon data into an isolated branch; record measured RTO/RPO and data-loss window.
- [ ] Publish a versioned release and changelog only after all preceding evidence passes.

The current release issue remains the source for team sign-off. Update this
record only with evidence tied to exact component identities; a planned action,
green unrelated check or skipped deployment job does not satisfy an item.
