# Leyan: Week 4 audit and acceptance runbook

Planning source: Daily Tasks PDF, Week 4 — Final, W4-D1-Leyan through W4-D5-Leyan.
Dates remain TBD and the schedule is proposed. No issue, board status, release or demo completion is implied.
Baseline: main b8015961b6f31bdeaea62820b313f339b587d5f1, November 2, 2026.

## Task map

| Task | Assigned work | Prepared here | Completion still needed |
|---|---|---|---|
| D1, P0 | Audit real CRUD, refresh/redeploy persistence, provenance, HTTP errors and duplicate behavior; record missing connections | Source/evidence gap audit below | Exact release API/browser evidence and owner resolution |
| D2, P1 | Verify loading, network/malformed behavior, duplicate prevention, retry safety; sync contract docs | Redirect rejection, nonblank HTTP fallback, regression tests and current reference | Review/CI and identified connected/browser checks |
| D3, P1 | Endpoint/request/response/error examples, setup, trace examples through tests, document synthetic identity | API reference, replayable examples and client/schema validation | Backend/UI owner agreement and comparison with chosen deployed candidate |
| D4, P0 | Exact-candidate create/list/detail/update/delete/analyze/save/reread; capture failures and identity | Run sequence and evidence fields below | Approved target, exact SHA/package and actual replay |
| D5, P0 | Deployed extension user journey; explain API/error behavior | Demonstration sequence and explanations below | Actual final package/model/backend demonstration and sign-off |

## D1 source and evidence audit

| Boundary | Reviewed evidence | Gap / next owner |
|---|---|---|
| History and CRUD | Saved routers, schemas and five-method api.js client at baseline | Leyan/Trixia: replay on final candidate; Andrei: prove connected UI |
| Database persistence | Historical October 31 staging CRUD on 4127dd1, documented in PR #103 | Not refresh/redeploy proof for the current candidate; Kendra/Trixia identify safe target and compatible source |
| Refresh | saveAnalysisAndRefresh retains confirmed creation and exposes partial refresh errors; local tests exist | Andrei/Leyan: install exact UI and observe refresh/reopen behavior |
| Provenance | Detail supports mode/provenance; list contains summary fields; nullable confidence remains readable | Trixia/Wilberr: real-provider model identity and nonempty persistence evidence |
| HTTP errors | Client preserves status and readable saved detail; malformed/network failures reject | Blank messages and HTTP redirects reproduced and fixed here; real backend fault injection still owner-dependent |
| Duplicate behavior | Same-input uncertain create keeps key, no automatic retry; explicit retry can reuse original key | Local timed-out POST/retry checked; final environment/backend retry acceptance still pending |
| Authentication | Current saved routes derive a fixed synthetic demo owner | Trixia/Andrei/Leyan: separate auth contract; no real-user isolation claim |
| Candidate drift | PR #103 verification is separate from main; #99 local-analysis workflow is a different unmerged candidate at audit time | Freeze exact accepted client/backend/model revisions before final acceptance |

No new staging write was performed. The team's hold on record-changing actions remains in force until
the intended live SHA and isolated Neon target are confirmed. An earlier passed run is dated evidence,
not current environment confirmation.

## D2/D3 verification record

- Reproduced five failures before the fix: blank/whitespace HTTP messages and followed redirects
  for legacy history, CRUD list and persistent create.
- Redirects now reject before the destination is called; blank detail falls back to readable HTTP status.
- A real local HTTP timeout test checks one POST, retained idempotency key, explicit same-key retry,
  and unchanged input. It uses a disposable synthetic server, not PostgreSQL.
- Full baseline extension suite plus Week 4 work: 151 passed, 0 failed/skipped.
- API example create, patch, detail and list validate against the actual backend Pydantic schemas.
- New API-reference tests replay the JSON examples through the actual client.
- UI loading/empty/malformed rendering remains Andrei-owned; earlier local UI tests are not browser proof.

See [API reference](api-reference.md) and [synthetic fixtures](examples/saved-api.json).
Use node --test extension/tests/*.test.mjs and npm.cmd run lint from the project root.
No AI weights, real-provider calls or external database are needed for these local checks.

## D4 candidate run record

Do not fill PASS before actually observing the behavior.

| Identity field | Record at run time |
|---|---|
| Client and backend full source SHA | Pending |
| CI run / protected deployment link | Pending |
| Package/artifact link, digest and version | Pending |
| /version environment and commit | Pending |
| Owner-confirmed isolated Neon target | Pending; never record credentials |
| API origin / browser version | Pending |
| Provider mode / model revision | Pending; distinguish mock and real |
| Unique synthetic IDs / cleanup outcome | Pending |

Run sequence after the target and any writes are authorized:

1. Query /version and /ready; stop on a mismatched SHA/environment or unready database.
2. Create one uniquely named synthetic analysis through the saved API. Record POST 201 and returned ID.
3. List and read that ID. Compare subject/body, prediction, confidence, risk, evidence, explanation,
   mode and detail provenance. New results require a concrete label; old nullable history stays readable.
4. Edit notes/feedback. Reread through API, close/reopen the popup and verify persistence.
5. If a compatible redeploy is part of the agreed acceptance, have Kendra coordinate it, then reread
   the same ID. Never infer survival from a successful build or health endpoint.
6. Delete only the created row. Confirm detail 404 and absence from list and reopened popup.
7. Analyze a synthetic selection using the agreed unsaved flow. Record success/result or controlled
   failure; a mock result is not real-model acceptance.
8. Exercise the persistent analyze-and-save path once with body:selectedText and absent subject.
   Do not call both inference endpoints expecting one inference. Display its returned saved record,
   refresh detail/history, then clean up only that run's row.
9. With Trixia's agreed safe fault setup, verify unavailable, timeout, invalid output and storage
   failures. Preserve input; show readable errors; do not present empty success or silently retry POST.
10. Record redacted Network methods/statuses, expected/actual UI behavior, remaining defects and owners.

Reuse scripts/verify_crud.mjs for guarded CRUD. scripts/verify_saved_report.mjs belongs to PR #103;
use the exact reviewed source when available and record any separate verifier revision.
Do not imply this Week 4 main-based branch already includes or delivers #103.

For a lost acknowledgement, keep the identical request/key and coordinate recovery rather than
rerunning a new command with a new subject/key. If cleanup is uncertain, retain that exact synthetic
ID for the owner. Do not delete unrelated history or seeded records to manufacture an empty state.

## D5 demonstration and explanation

Use Andrei's exact installed candidate and a verified demo API, not a production ZIP against staging.
The final demonstration must use actual backend data/model in the accepted scope; fixture-only work
cannot satisfy this task.

1. State environment, package/source/backend/model identity and any limitation before the demo.
2. Analyze synthetic content; explain what is model output versus backend risk mapping.
3. Save once using the agreed persistent flow, then show the returned ID in detail and history.
4. Edit notes/feedback, reopen/refresh and show they persist.
5. Delete the synthetic row; reopen and show it is absent.
6. Show one controlled failure/recovery without a false safe verdict or duplicate save.
7. Explain these boundaries:
   - The extension calls FastAPI; it never receives Neon credentials.
   - An unsaved result and a persistent report use different routes/request fields.
   - The backend chooses owner and validates/stores the verdict; demo identity is not authentication.
   - Null confidence is unavailable confidence, not zero or an invented model score.
   - A timeout can follow a successful commit; retain the idempotency key for an explicit retry.
   - 204 DELETE has no JSON body; errors reject and must stay visible in the UI.

Record actual attendees/questions/results only after the demonstration. Keep missing acceptance
explicit and assigned. No release tag, meeting, instructor approval or measured performance is invented.

## Publishing and ownership

Keep Week 4 work on a new task branch from updated main, separate from PR #103.
No dedicated Leyan Week 4 issue was found at audit time; prepare the task issue and obtain the team
scope/date agreement before presenting this proposed schedule as committed.
Trixia reviews API/client contract; Andrei reviews client/UI composition. Kendra owns delivery targets,
and Wilberr owns real model/evaluation evidence. No backend, UI, migration or workflow files were edited.
