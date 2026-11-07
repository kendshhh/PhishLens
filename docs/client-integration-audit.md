# Client integration audit

Checked November 7, 2026 against main `6ce3b5066c845dc70e7ad0c318cbba3c083ca041`.
Tracks #128, #135 and #140, with acceptance carryover in #7, #23, #44, #45, #87 and #98.
This audit reconciles existing evidence; it does not record a new deployment or external write.

## Verified evidence

### Protected staging API

[Run #593](https://github.com/kendshhh/PhishLens/actions/runs/42321395893)
passed for PR #154 head `331a5a9a34f84fda47a32e22195444705a8376a5`, testing merge
`c6cc12ae9f61b43684ef5a037712761ef7b271cd`.

The [Hosted staging log](https://github.com/kendshhh/PhishLens/actions/runs/42321395893/job/128247287511)
records exact-source/migration/private-target preflight, health/readiness and seeded history through
the extension client. At 03:23:18 UTC it reports saved-report CRUD passed and cleanedUp true for
synthetic ID `b71843ad-1f8f-4ff0-969b-7d81418ad4d7`.

The actual result is analysisMode real, providerMode tfidf, model word_plus_char_wb_C1p0,
revision `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
Descriptions of this run as mock-only conflict with the raw job result. This establishes scoped
non-mock TF-IDF persistence, not a Gemini request, a successful local Llama review, a quality
benchmark, a live failure drill or the final installed-Chrome journey.

[Staging artifact](https://github.com/kendshhh/PhishLens/actions/runs/42321395893/artifacts/13558364524)
has enclosing archive SHA-256 `babb1da968da13353ca609939331a24965571937eddc15c246ed3423c5a6b06d`.
That is the GitHub artifact digest, not the nested extension ZIP digest. Recheck live identity before
using any package: shared staging may have changed after the run.

### Packaged browser checks

The [Extension checks job](https://github.com/kendshhh/PhishLens/actions/runs/42321395893/job/128246543776)
passed npm run test:browser and uploaded
[Extension-Browser-Acceptance](https://github.com/kendshhh/PhishLens/actions/runs/42321395893/artifacts/13552393921).
The inspected scripts/browser_acceptance.mjs unpacks the package into a disposable browser profile,
redirects its API origin and host permission to a local in-memory server, and adds a test-only delayed
completion hook for the production Clear handler.

Its six scenarios cover history rendering, local result or readable error, Clear/stale completion,
create/view, edit/delete, and empty/history-error presentation. These are useful browser checks,
but their synthetic API does not prove that the installed popup works with deployed PostgreSQL.
The script does not test popup reopen persistence, malformed history in the browser, backend
redeployment persistence, or actual provider/storage failures. No new screenshots were inspected here.

### Current client checks

An isolated source snapshot from the main revision above ran 11 client-focused test files:
api-reference, api, client-resilience, client-session, crud-http, crud-target, crud, report-client-http,
report-client, report-failures-http, and saved-report-verifier.

Command: node --test extension/tests/*.test.mjs from that scoped snapshot.
Result: 169 passed, 0 failed, 0 skipped. This is a client subset, not the full repository suite.
Tests use injected responses or disposable loopback HTTP servers. They cover status/error mapping,
malformed data, retry keys, redirect/target guards, session-token injection, nullable legacy values,
saved evidence/provenance retention and cleanup handling. No external writes or providers were used.

The four documented JSON examples (create, patch, detail and list) also validated against the
actual backend/app/analysis_schemas.py from the same main revision using Pydantic. This is schema
validation, not a live endpoint replay.

## Remaining work and owners

| Boundary | Existing evidence | Remaining acceptance / owner |
|---|---|---|
| Week 1 changed history (#7/#23) | Historical real history display; client record validation | Trixia coordinates a safe synthetic subject/result change and restoration; Andrei/Leyan capture the changed displayed value and required owner sign-offs. A notes-only edit is not equivalent. |
| Week 2 CRUD (#44/#45) | Historical PostgreSQL replay plus later TF-IDF staging API success | Andrei/Trixia execute the matched installed-Chrome create/view/edit/reread/delete/reopen sequence; Leyan reviews client/API evidence. |
| Week 3 saved flow (#87/#98) | Merged helper/verifier; local failure cases; real TF-IDF staging save | Compare returned ID, evidence/provenance and refresh in the connected UI; Trixia/Wilberr provide controlled backend failure evidence. |
| API resilience (#135) | Client subset passes; synthetic browser empty/error states | Controlled real-server timeout/unavailable/invalid-output/storage errors, no false success or duplicate save; UI evidence remains Andrei/Leyan-owned. |
| API reference (#140) | Examples replay through actual client; current source/schema inspection | Compare documented examples with chosen deployment; record owner agreement and live statuses before closure. |
| Candidate acceptance (#145) | Guarded staging/API and synthetic browser results | Kendra identifies the exact candidate/package/isolated target; record integrated journey and cleanup, including any agreed redeploy/reread. |
| Final demo (#150) | Demo sequence prepared in release-verification.md | Demonstrate the actual accepted backend/model/package; record real results/questions and limitations. |
| Authentication | PR #125 merged optional token getter and safe session errors | Trixia/Kendra confirm supported Neon configuration; Andrei confirms UI branch; then wire acquisition/refresh/sign-out and verify per-user ownership/cross-user denial. |

PRs #99, #103, #106 and #125 are merged. Former open-review notes are historical, not new coding
requirements. PR #61 still explicitly lists installed-Chrome CRUD/reopen/Network evidence as incomplete;
its automated report does not replace that manual evidence. The audit covers source and recorded runs;
it does not establish today's live staging identity or authorize fault injection.

## One coordinated acceptance run

1. Record exact client/backend/package/model identities, isolated target and the agreed synthetic-write window.
2. Create once, read the returned ID in detail/history and compare evidence, explanation, mode and provenance.
3. Edit notes/feedback, reread, close/reopen and confirm persistence. Capture methods/statuses without tokens.
4. Delete only this run's record, confirm 404/list absence and reopen to verify it stays absent.
5. With owner-controlled fault setup, check readable failures and preserved input/key without automatic POST retry.
6. Record the separate Week 1 subject/result change/restoration and any agreed redeploy/reread.
7. Attach dated results to the relevant issues, then reconcile their checkboxes and board status.

One well-identified run can supply evidence to several tasks. Keep any unsupported scenario open;
do not repeat tests merely because the same boundary appears in multiple sprint issues.
