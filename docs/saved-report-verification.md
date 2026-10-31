# Saved-report verification (Issue #98)

Owner: Leyan. Related tasks: #87 (component), #44/#45 (Week 2), #7/#23 (Week 1).
Prepared against main 82abb90904d079912d6d91faa470724947da8078 on October 31, 2026.

## Local replay

Run from the repository root:

```powershell
node --test extension/tests/*.test.mjs
npm.cmd run lint
```

Actual local result with this change: 153 tests passed, 0 failed/skipped; extension JavaScript lint passed.
The 11 new verifier tests use an in-memory loopback HTTP server and the actual API client.
They cover identity/write guards, returned-ID refresh, nullable fields/provenance, HTTP 422/500/502/503/504,
malformed JSON, failed refresh cleanup and cleanup failure reporting. Existing component tests also cover
timeout/network errors and explicit idempotent recovery. No real database, model or installed browser
was used for these results. Do not describe a synthetic HTTP 500 as an injected real database failure.

## Protected staging replay

First record the environment owner's current confirmation that Render staging points to the isolated
synthetic database. Confirm the intended backend SHA and matching extension artifact; a database name
or a healthy /ready response alone cannot establish the Neon branch. Shared staging can change.

```powershell
node scripts/verify_saved_report.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha CONFIRMED_FULL_BACKEND_SHA --allow-writes
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha CONFIRMED_FULL_BACKEND_SHA --allow-writes
```

Replace the placeholder with the identified 40-character live backend SHA.
Both commands refuse production, arbitrary hosts, redirects, missing opt-in, mismatched identity and
unready databases. The first reuses the existing target guard and calls saveAnalysisAndRefresh once.
It checks returned ID, detail/history fields, evidence and provenance, then deletes only its confirmed
created record and requires a detail 404. The second exercises existing edit/clear/delete CRUD.
These commands may run backend inference; use the agreed test mode and resource budget.

Neither command is claimed as run against staging in this change. Retain actual JSON output, client
source SHA, backend SHA, CI/deploy URL, environment confirmation and UTC time when run.

## Failures and cleanup

A refresh error fails acceptance even when creation succeeded. The verifier still attempts cleanup
for a confirmed saved ID. Cleanup failure reports that ID and fails; ask the environment owner to
inspect/remove only that synthetic row and record the result.

If a POST response is lost or malformed, a row may exist without a confirmed ID. The client exposes an
idempotencyKey with the error. Do not rerun the whole command assuming that clears the uncertain write:
a new run generates a new input and key. Record the original key and request context privately, and
coordinate recovery using the identical input/key or owner inspection. This script never automatically
retries or deletes records discovered through unrelated history.

## Remaining Week 1–3 acceptance

- Week 1 #7/#23: agreed synthetic subject change, display the changed database value, restore it and
  verify restoration; capture loading/empty/request-failure/malformed states. Label browser response
  overrides as substitutes. Use only the identified isolated record; no production or shared-seed
  edits without the agreed owner procedure.
- Week 2 #44/#45: record the real PostgreSQL/API replay, Andrei's UI/client composition and actual
  installed-package CRUD with notes/feedback surviving reopen and deletion remaining absent.
- Week 3 #87/#98: connect the saved-report component to the actual UI/backend, record mode/provenance,
  real provider evidence where required, and controlled backend timeout/unavailable/invalid-output/DB
  failure mapping. Synthetic status tests do not complete real fault injection.
- All weeks: reconcile required owner reviews, source/CI/deployment identities and board/sprint evidence.

Andrei owns UI rendering; Trixia owns storage, authentication and controlled backend faults; Kendra owns
protected environment/package identities; Wilberr owns real-model setup/evaluation. Authentication and
new local-scanner work are separate changes, not prerequisites to invent for an already agreed baseline.

Do not close these tasks from local tests alone. No GitHub issue, PR, board, deployment or shared local
checkout was modified while preparing this patch.
