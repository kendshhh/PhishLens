# Release record — 2026-11-21

## Decision

**NO-GO.** This is a read-only evidence refresh as of November 21, 2026
(Asia/Manila). It records current repository and Render identities; it is not a
deployment authorization or a product acceptance sign-off.

## Release scope

The intended deliverable is the locally installed Chrome Manifest V3 PhishLens
extension, backed by the FastAPI service on Render and PostgreSQL/Auth on Neon.
Issue [#153](https://github.com/kendshhh/PhishLens/issues/153) now states this
scope and points to the retired Vercel experiment in issues #244/#248. The
CSP221A course guide is not the PhishLens product URL.

## Observed identities

| Component | Current identity | What the evidence proves |
|---|---|---|
| Repository | GitHub main at [811980c2cbf70d9957146bf329627f0826a018f1](https://github.com/kendshhh/PhishLens/commit/811980c2cbf70d9957146bf329627f0826a018f1), PR #264 | Main commit and code identity. No release tag or GitHub Release is published. |
| Production API | Render deploy [dep-dc07rs67bikc73fjgjq0](https://dashboard.render.com/web/srv-db7eap25b2lc73fkelpg/deploys/dep-dc07rs67bikc73fjgjq0), source SHA 811980c2cbf70d9957146bf329627f0826a018f1, Live | Deployed from main at 17:05:52–17:07:13 UTC on November 20. The scheduled [drift run 44812619162](https://github.com/kendshhh/PhishLens/actions/runs/44812619162) passed exact-SHA, health and readiness checks. It does not verify model state, Auth, CRUD or the extension journey. Production auto-deploy remains enabled on main when checks pass. |
| Staging API | Render deploy [dep-dc07s1cipgvc73dh0150](https://dashboard.render.com/web/srv-db92irlg1s2s739404i0/deploys/dep-dc07s1cipgvc73dh0150), source SHA 811980c2cbf70d9957146bf329627f0826a018f1, Live | Manually deployed at 17:06:14–17:07:30 UTC on November 20. It matches the production source SHA, but no current authenticated acceptance run is attached to it. Staging auto-deploy is off. |
| Extension build | PhishLens-Extension artifact ID 14651606496 from [CI run 44779598624](https://github.com/kendshhh/PhishLens/actions/runs/44779598624); source SHA 811980c2cbf70d9957146bf329627f0826a018f1; archive digest sha256:8f07bf6fd9e5844ee541b4c13439cd32b57d231ca8c297bbd5513346bc17244d; expires November 27 | CI artifact is tied to current main. This is the GitHub archive digest, not a separately verified ZIP SHA-256. No accepted extension/backend/model manifest is published. |
| Browser acceptance evidence | Extension-Browser-Acceptance artifact ID 14652195937 from CI run 44779598624; digest sha256:e953b567b84d99f70182b5a7fb22eedc4f3876b467a804f27cdcfe2e745b6c1b; expires February 18, 2027 | Packaged browser checks ran for current main. This does not replace authenticated live staging acceptance. |
| Model/provider | The 40-case synthetic evaluation remains below release quality: 18.75% phishing recall (3/16), 6.25% legitimate false positives (1/16), and all eight spam cases classified as legitimate. | Production analysis was verified disabled on November 20. The current environment value was not reread on November 21, and no current model-info response was obtained. No approved production model/provider is evidenced. |
| Auth and database | Neon exposes production and staging branches; the exact Render-to-Neon mapping and current runtime Auth mode remain unverified. | The November 20 isolated snapshot restore checked schema and aggregate integrity, but does not establish application acceptance or measured RTO/RPO. |

## Current workflow evidence

The following runs for current main SHA 811980c succeeded:

- [CI 44779598624](https://github.com/kendshhh/PhishLens/actions/runs/44779598624)
- [Deterministic AI evaluation 44779598647](https://github.com/kendshhh/PhishLens/actions/runs/44779598647)
- [Workflow lint 44779598943](https://github.com/kendshhh/PhishLens/actions/runs/44779598943)
- [Dependency security 44779598600](https://github.com/kendshhh/PhishLens/actions/runs/44779598600)
- [CodeQL 44779598763](https://github.com/kendshhh/PhishLens/actions/runs/44779598763)
- [Scheduled Production drift 44812619162](https://github.com/kendshhh/PhishLens/actions/runs/44812619162)

The active CI ruleset [#27733591](https://github.com/kendshhh/PhishLens/rules/27733591)
requires Backend checks, Extension checks, Staging integration and Secretary
staging. Its strict status policy is false and it has no bypass actors. The
active approval ruleset [#26782191](https://github.com/kendshhh/PhishLens/rules/26782191)
requires one approval, dismisses stale reviews and resolves review threads, but
does not require the latest push to be approved. The classic branch-protection
endpoint returned 403 in this refresh. A November 20 read listed eight required
contexts; it is not current proof of the effective combined contract. No current
runtime PR demonstrates that a deliberately failing required check blocks
merge.

PR #257 made Secretary fail closed when Auth acceptance remains pending and
requires explicit Neon Auth mode for authenticated preview. PR #262 corrected
the backend-only staging skip. These changes improve status semantics, but the
effective current branch gate and runtime behavior still need a live PR
demonstration.

## Release evidence still required

- [ ] Complete authenticated staging sign-in and saved-report create/list/read/update/delete, persistence, ownership isolation, failure handling and cleanup on the current exact extension/backend pair.
- [ ] Publish the exact extension artifact, backend SHA, approved model identity, Auth mode and Neon branch in one accepted manifest.
- [ ] Review a representative held-out model cohort, approve numeric release thresholds and require failure below threshold. Keep production inference disabled until this passes.
- [ ] Reconcile the active ruleset with classic branch protection and prove current runtime-PR labels/skips, independent approval and failing-check merge block.
- [ ] Gate production on explicit release approval, stage then promote the same artifact, and run exact-SHA post-deploy acceptance.
- [ ] Rehearse rollback to a schema/config-compatible application release.
- [ ] Repeat an isolated database restore under representative conditions and measure service RTO and recoverable-point age against the approved ≤30-minute / ≤1-hour targets.
- [ ] Verify alert delivery and ownership, refresh user-flow performance/cost evidence, and publish a versioned release record only after the blockers pass.

## Migration and recovery limits

The November 15 disposable-PostgreSQL report records migration upgrades through
schema 0004 and 11 saved-report CRUD tests against that schema from a
pre-Neon-Auth backend revision. It does not prove rollback compatibility with
the current production predecessor and configuration.

The [November 20 Neon restore drill](recovery-drill-2026-11-20.md) restored a
manual snapshot into an isolated branch and matched schema and aggregate counts.
The Neon free plan blocks production branch protection and scheduled snapshots;
the snapshot and drill branch expire November 27. The measured one-second
provider restore-to-ready interval is not service RTO, and the recovered point
was not precise enough to establish RPO. Current app rollback is not rehearsed.

Update this record only when evidence is tied to exact deployed and packaged
identities. A successful health check, skipped job or planned action does not
close a release item.