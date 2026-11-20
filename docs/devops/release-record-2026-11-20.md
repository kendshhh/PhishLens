# Release record — 2026-11-20

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

This resolves the current local project documentation scope. The historical
web-app note in [issue #153](https://github.com/kendshhh/PhishLens/issues/153)
still needs an owner update so the project issue and this record agree.

## Observed candidate identities

| Component | Observed identity | Acceptance state |
|---|---|---|
| GitHub source | `main` at [`60641f32353c61a5b1f0dcfca1e0f5912afb76b3`](https://github.com/kendshhh/PhishLens/commit/60641f32353c61a5b1f0dcfca1e0f5912afb76b3) | Source identity verified; no release tag exists. |
| Production API | Render deploy `dep-dbvt8r0u01pc73b4siig`, source SHA `60641f32353c61a5b1f0dcfca1e0f5912afb76b3` | Health and DB readiness pass; `/model-info` reports `provider_mode=unavailable`; feature acceptance fails. |
| Staging API | Source SHA `d6612c258f289b3a45d8229e4a4803cac75a91ee` | Health and DB readiness pass; TF-IDF mode; not the production SHA. |
| Extension package | Artifact SHA-256 and installable package identity not recorded here | **NOT VERIFIED** as paired with either API SHA. |
| AI model | Staging reports TF-IDF model SHA `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` | Production reports no active provider; the model is not accepted for broad release. |
| Auth mode | Authenticated staging acceptance is still pending | **NOT VERIFIED**. |
| Neon target | Connected project exposes `production` and `pr-58-staging` branches | Exact Render-to-Neon mapping and runtime permissions require private owner verification. |

## Required release evidence

- [ ] Update issue #153 to remove or clearly close the historical web-app scope note.
- [ ] Produce one installable extension package and record its source SHA and ZIP SHA-256.
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
