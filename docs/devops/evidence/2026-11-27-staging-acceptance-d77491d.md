# Exact-head staging acceptance — PR #268

- Workflow run: [45966647832](https://github.com/kendshhh/PhishLens/actions/runs/45966647832)
- Candidate/backend source SHA: `d77491d8fd91252190755714df8e5fa475e9c13b`
- Extension ZIP SHA-256: `495d9bb7d3a222b103a30de819f6a0e7c8d4c9844e9120c24b9d6f4a4b47bdb7`
- Redacted staging report: [`2026-11-27-staging-acceptance-d77491d.json`](2026-11-27-staging-acceptance-d77491d.json)
- Report SHA-256: `C23277EBD293FE8C8DF8CF09B67093C9DD1CC8A405881118596C72C5BB0D5670`
- Extension package artifact SHA-256: `e3c97b23513ad25d5af54cdadf2227dfede621ead55f8a38dd9865682266bf05`
- Staging branch: Neon project `ancient-brook-17208049`, branch `br-rough-sea-a1l6ehi1`
- Migration revision: `0005_ai_request_quota`

## Result

The trusted controller passed exact-candidate inspection, isolated Neon
verification, staging deployment, authenticated extension acceptance, and the
required `Secretary staging` report. The staged backend `/version` and source
SHA matched the candidate. The built extension package was installed for the
acceptance run and its SHA-256 is bound above.

The run passed sign-in, create, list, read, update, delete, persistence after
reload, ownership checks, two-account isolation, and cleanup. It also passed
loading, success, authentication-failure, API-error, and timeout UI checks.
The anonymous saved-report request received HTTP 401 as required. Evidence
records zero production API, Auth, or write requests and zero unexpected
external requests.

## Limits

AI-quality acceptance is **BLOCKED** (`approval_not_provided`). The candidate
reports TF-IDF model revision
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`; this
staging CRUD pass does not approve its quality. The backend image digest is
`null`; Render still runs a Git-backed service, so same-digest production
promotion is not evidenced. This is staging evidence only: no production
deployment, production data access, release tag, or GO decision occurred.

The GitHub artifact is retained until 2026-12-04. The redacted JSON and this
record preserve the acceptance result beyond that artifact retention period;
the 14 MB extension ZIP itself is not committed and is not a durable release
artifact.
