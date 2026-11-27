# Exact-head hosted staging acceptance — PR #306

- Trusted controller: [run 45999893591](https://github.com/kendshhh/PhishLens/actions/runs/45999893591), completed 2026-11-27 12:40 UTC.
- Candidate source and backend SHA: `131d282222361a6d29601f90a2930445ee4a61cf`.
- Extension package SHA-256: `376b26a4de0307c00b331d2e66ea4caf363ab8347c8a037df83e1a8b22ffeb08`; independently re-hashed after downloading the workflow artifact.
- Staging service: `https://phishlens-staging.onrender.com`; isolated Neon project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`; migration `0005_ai_request_quota`; Neon Auth enabled.
- Staging `/version` at 14:33 UTC returned the exact accepted SHA; `/health` and `/ready` returned 200 and the database was connected.
- Redacted machine-readable summary: [`2026-11-27-staging-acceptance-131d282.json`](2026-11-27-staging-acceptance-131d282.json).

## Passed checks

The trusted workflow passed candidate inspection, isolated Neon validation, exact-SHA staging deployment, authenticated extension and CRUD acceptance, and the required `Secretary staging` status. The downloaded package SHA-256 matched the workflow evidence.

The exact package was installed and the flow passed sign-in, create, list, read, update, delete, persistence after reload, two-account data isolation, ownership checks, cleanup (zero pending records), and rejection of anonymous saved-report history access. The extension passed loading, success, authentication-failure, API-error, and timeout states. The run recorded zero production API, Auth, or write requests.

## Limits

This closes the product-path acceptance gap for the tested candidate. The current `main` commit is `fd23b186ad85f9d33e7f80dec03f09d9b7005403`; its application/runtime files match the accepted candidate tree, while subsequent changes are documentation/schema-guide files. `main` itself was not deployed or rebuilt as this exact candidate, and the ZIP still embeds the accepted PR SHA. A release build must bind fresh exact-main provenance.

AI quality remains **BLOCKED** (`approval_not_provided`) for TF-IDF revision `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`. The backend image digest is null; Render is Git-backed, so same-image promotion is not established. Production was not deployed, no release tag was created, and the release remains **NO-GO**. GitHub's workflow artifact expires 2026-12-04; the ZIP was not committed or published to durable release storage.
