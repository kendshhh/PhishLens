# Staging acceptance — 2026-11-14

## Target identity

- Render service: `phishlens-staging` (`srv-db92irlg1s2s739404i0`), linked to `main`.
- Live deployment: `dep-dbrsad3rjlhs73ce2gl0`, commit `8c02a7c86e8b2052d127b5a6a0422a5a80ffa9ea`.
- Render reported the deployment `live` at `2026-11-14T02:20:54Z`.
- `/version` returned HTTP 200 with that exact commit and `environment=staging`.
- Render's `STAGING_DATABASE_HOST` matched Neon endpoint `ep-soft-fog-b3orfa8a-pooler.c-4.ap-southeast-1.aws.neon.tech`, which Neon maps to branch `pr-58-staging` (`br-delicate-paper-b381z98i`) in project `patient-bird-25428852`, database `phishlens_dev`.
- The deployed startup guard validates that the runtime and migration URLs match the configured staging host and database and that the runtime uses the restricted staging role. No connection string or password is included here.

## Read-only preflight

At the live SHA above:

| Check | Result |
|---|---|
| `/version` | HTTP 200; staging; exact SHA matched |
| `/health` | HTTP 200; `status=ok` |
| `/ready` | HTTP 200; `status=ready`, database connected |
| `/model-info` | HTTP 200; `provider_mode=tfidf`, model SHA `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` |

## Synthetic feature acceptance and cleanup

Ran the repository's guarded CRUD verifier against the exact staging SHA:

```text
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com \
  --environment staging \
  --expected-sha 8c02a7c86e8b2052d127b5a6a0422a5a80ffa9ea \
  --allow-writes
```

Result: passed. The verifier created synthetic record `596fdeb7-58d0-4d82-8902-1382ec1848c0`, read it back, updated and cleared its notes, deleted it, and asserted that a subsequent detail read returned 404. Its `finally` cleanup also deletes the run's record if an earlier assertion fails. The report says `cleanedUp=true`.

The analysis used the deterministic TF-IDF provider. This acceptance made no Gemini/provider request, made no production write, and retained no user message. The existing seeded demo fixture was only read; the synthetic verifier record was deleted.

## Evidence limits

This is one staging CRUD acceptance run, not production proof, a quality
evaluation, or a load test. A production snapshot restore was attempted later,
but it changed Neon branch topology and did not meet safe restore acceptance;
its outcome is recorded in
[reliability-acceptance-2026-11-14.md](reliability-acceptance-2026-11-14.md).
An agreed RPO/RTO and a repeatable safe restore remain open.

## Current staging target recheck — 2026-11-14

An external/API-triggered Render deployment replaced the above main deployment
after that run. Render reports auto-deploy `off`, so this was not an automatic
deploy from the service's linked branch. The current staging service reports
commit `c3ce2fff382f01014b4a846755a4c6007f642ec6`, from
`test/47-verify-installed-browser-crud`; it is not `main` and is not the
release candidate represented by the earlier `8c02a7c` acceptance.

The Render service's configured staging host was previously inspected in the
Render dashboard and matched the Neon pooled host
`ep-soft-fog-b3orfa8a-pooler.c-4.ap-southeast-1.aws.neon.tech`. A fresh Neon
compute lookup maps that endpoint to branch `pr-58-staging`
(`br-delicate-paper-b381z98i`) in project `patient-bird-25428852`. This confirms
the target branch identity; the Render integration does not expose a separate
read-only environment-variable listing through its current connected API.

At the exact current SHA, read-only checks returned `/version` with the same
commit and `environment=staging`, `/health` HTTP 200, `/ready` HTTP 200 with
`database=connected`, and `/model-info` with provider `tfidf` and model SHA
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.

The guarded CRUD verifier was rerun with
`--expected-sha c3ce2fff382f01014b4a846755a4c6007f642ec6`. It passed create,
read, update, clear, delete, and post-delete 404 checks for synthetic record
`9856b33d-8e08-44de-97a1-d319cda04f5f`; the script reported
`cleanedUp=true`. The request used TF-IDF, made no paid provider request, and
made no production write. This proves the current feature branch's backend
CRUD behavior on the staging target. It does not prove main's current target or
the feature branch's browser-extension behavior.
