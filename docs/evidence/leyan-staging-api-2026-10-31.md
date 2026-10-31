# Leyan: staging API verification, October 31, 2026

Related: #44, #45, #87, #98, PR #103. API evidence only; no Chrome or real-model claim.

## Identity and target

- Run: 2026-10-31 06:56:39–06:56:55 UTC (14:56 GMT+8).
- Origin: https://phishlens-staging.onrender.com
- Client/backend source: 4127dd14d3dc5e28e56f874775be84b95d8a57b1.
- Read-only /version: HTTP 200, exact source above, environment staging.
- /ready: HTTP 200, ready, database connected.
- Isolation basis: Kendra's maintained docs/devops/staging.md identifies Neon
  pr-58-staging/phishlens_dev with a restricted app role and separate migration role;
  protected Hosted staging and Secretary staging passed for this source.
- The verifier additionally guards origin, environment, exact SHA, readiness and redirects
  before writes. No database credentials were read or included in evidence.
- The saved-report verifier included local follow-up changes for Trixia review 5721676032:
  compare history evidence/explanation, require new-report mock/real mode and provider
  provenance consistent with that mode. Those follow-up edits were not committed at run time.
  They must be tied to the eventual committed source; this is not evidence for untested future edits.

## Commands and actual results

The imported functions used the same guard and arguments as these CLI commands:

```text
node scripts/verify_saved_report.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha 4127dd14d3dc5e28e56f874775be84b95d8a57b1 --allow-writes
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha 4127dd14d3dc5e28e56f874775be84b95d8a57b1 --allow-writes
```

Actual invocation was outputs/run-live-api-2026-10-31.mjs in the isolated Codex workspace;
it called verifySavedReport and verifyCrud sequentially, wrote local JSON evidence, and exited 0.

| Check | Actual result |
|---|---|
| Saved report | PASS: one create, server-returned ID, detail/history reads, shared-field equality, mock mode and matching provenance. The mock staging response used empty threat_indicators arrays; this run does not establish nonempty evidence retention. |
| Saved-report cleanup | PASS: record 710d3c2e-4ff1-4a95-9b9e-acf8a59cce45 deleted; subsequent detail returned 404 |
| CRUD | PASS: create, list/detail, notes/feedback update, reread, note clearing, delete, final 404 |
| CRUD cleanup | PASS: record 198315f9-fa8d-4d9d-ad92-51fb82d55e2d deleted and confirmed absent |

Only these newly created synthetic records were changed. No production writes, seeded subject
edits, environment changes, deployment actions or GitHub posts were performed.

## Local regression checks

### Controlled nonempty-evidence follow-up

The added test `controlled HTTP replay retains nonempty evidence and explanation across create, detail and history`
uses the actual client and verifier against a local in-memory HTTP server. It supplies two
nonempty evidence items (type, quote and detail) plus a nonempty explanation, checks the
create/detail/history path, and confirms synthetic cleanup. Existing negative tests reject
dropped or changed history evidence and explanation.

This is controlled fixture evidence only. It does not upgrade the earlier empty-array staging
run to real-provider or nonempty PostgreSQL evidence. A controlled real-backend nonempty-evidence
run remains pending with Trixia; staging writes remain on hold until the intended SHA and
isolated Neon target are confirmed.

Follow-up verification against PR #103 source 9e5ffaeaa1d3de1b10c16edaabc2f60f8e2b3de4
plus these test/documentation edits: 171 extension tests passed, 0 failed/skipped;
extension JavaScript ESLint passed. The following 169-test result is the earlier baseline.

With the follow-up validation changes:
- node --test extension/tests/*.test.mjs: 169 passed, 0 failed, 0 skipped.
- Extension JavaScript ESLint: passed.
- The new tests reject dropped/changed history evidence or explanation, legacy/null mode,
  missing/null/empty provenance, unknown or mismatched provider modes. Synthetic valid
  real/local and real/gemini cases pass; these are fixtures, not provider inference evidence.

## Still pending

- Verifier validation changes were committed in 640fa86. Commit/push the controlled
  nonempty-evidence test/documentation follow-up, obtain Trixia re-review and fresh required CI.
- Andrei's exact-package Chrome run, persistence after reopening, deletion after reopening,
  and redacted Network evidence.
- Week 1 changed-subject display and restoration, remaining browser-state evidence and reviews.
- Controlled actual-backend timeout/unavailable/invalid-output/database fault mapping.
- Real-provider/model acceptance where required. This run used mock AI.
- Board/sprint-log reconciliation and revision-linked post-merge delivery.
