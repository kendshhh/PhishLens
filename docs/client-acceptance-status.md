# Client acceptance status

Audited November 8, 2026. Source: main ec234fe165900bce4d691d79b5da56a85a1b9b19,
plus the two loopback verifier files in this change. Backend Python sources, api.js and
report-client.js in the test snapshot were checked against Git blob hashes from that revision.
This record addresses #128, #135, #140, #145 and #150. A task's preparation is distinct from
an accepted release demonstration.

## Completed implementation and checks

- PR #155 merged the API reference corrections and integration audit.
- Client/unit/local HTTP verification: 231 extension tests and lint passed in the user checkout
  before the frontend continuation. The later PR #156 fix snapshot passed 253 extension tests,
  two preview-cleanup tests, ESLint and Ruff; those belong to that PR and its recorded source.
- Backend local verification: 244 passed, 38 skipped on the documented main-based test snapshot
  with PR #121's test overlay. Skipped PostgreSQL/optional tests are not passes.
- Four API JSON examples validated against the backend schemas. Existing api-reference tests
  replay create, detail/list, patch and empty delete through the actual client with injected fetch.
- This change adds an actual loopback HTTP replay between the JavaScript client/helper and the
  FastAPI saved-create router. It does not replace PostgreSQL or provider acceptance.

## Cross-stack error replay

Run from the repository root with backend development dependencies installed:

```text
python -m scripts.verify_client_errors
```

The Python harness binds an ephemeral 127.0.0.1 socket and runs the existing FastAPI app. The
JavaScript runner verifies a per-run handshake before any POST, refusing an unrelated local server.
No external target is used. Only the
saved-create configuration, idempotency lookup and inference/persistence service are substituted.
The production route performs request validation and maps the controlled exceptions to its normal
safe responses. Node uses createAnalysisClient and saveAnalysisAndRefresh over actual HTTP.

| Scenario | Observed status | Client verification |
|---|---|---|
| Conflicting idempotency key | 409 | Original status, readable message, input and request key retained |
| Blank body | 422 | Real FastAPI validation error retained; no refresh |
| Unexpected service exception | 500 | Safe fallback response; exception detail withheld |
| Invalid/failed provider result | 502 | Rejection, preserved input/key; no successful empty history |
| Unavailable provider | 503 | Rejection; explicit retry retains the automatic request key |
| Expired operation | 504 | Controlled timeout response; no automatic POST retry |

Actual result: all six status checks passed. Exactly eight POST requests were observed: six
cases and two caller-initiated unavailable retries. No detail/history GET, automatic retry,
external provider call, database connection or external record write occurred. The loopback
server shut down after the check. Both verifier files passed their applicable lint checks.
A deliberately wrong handshake was also rejected before any POST.

This checks the existing error boundary, not actual quota exhaustion, remote provider termination,
PostgreSQL rollback or deployed-browser rendering. Earlier local process tests separately verify
worker termination and recovery; they do not constitute a hosted failure drill.

## Task map

| Issue | Work completed | Remaining evidence / responsible boundary |
|---|---|---|
| #128 integration audit | API routes, ownership, CRUD, refresh, provenance, errors and retries mapped; gaps recorded here and in client-integration-audit.md | Review this refresh. An audit identifies gaps; it does not claim the gaps are resolved. |
| #135 client resilience | Target/redirect guards, malformed/network handling, retry keys and safe errors tested; actual FastAPI statuses replayed above | Review/CI on these files; frontend owner verifies any candidate-specific UI states; backend/AI owners control hosted failure drills. |
| #140 API reference | Requests, responses, limits, errors, optional token injection and synthetic ownership documented; examples and error replay tested | Compare with the agreed deployed candidate and record owner acceptance before claiming final live agreement. |
| #145 exact candidate | Replay/cleanup procedure and evidence fields prepared; historical connected run identified below | DevOps must designate accepted source/package/model and synthetic target; replay that exact candidate with request/status/cleanup evidence. |
| #150 demonstration | Full journey sequence and API/error explanations prepared in release-verification.md | Demonstrate the accepted deployed package/model; record actual results/questions. No demo attendance or release is inferred. |

## Evidence that must not be lost or overstated

PR #156 includes docs/evidence/frontend-staging-crud-2026-11-07.md. It records a successful
connected CRUD/reopen/delete journey on backend 0fcc747725512df13ba8ae0900b6080591425928
using local, then-uncommitted frontend edits based on 9f5a1ff2b1c5a9624cb22f6ecf08f9e082ad9054.
Its synthetic record was cleaned up and its local controller digest is recorded. This supersedes
blanket statements that no connected UI CRUD run exists. It is historical evidence, not final
current-head acceptance; native right-click, redeploy persistence, authentication and complete
local-LLM review remain outside that run. Do not repeat its proven steps unless the final-candidate
identity or changed behavior requires a new run.

The November 7 run #593 log recorded real TF-IDF saved persistence/cleanup, while its packaged
browser suite used a different local synthetic API. Those two checks cannot be combined into
an invented installed-Chrome/deployed-database run.

## Current release boundaries

At this audit the repository has no GitHub release. PR #156 remains open at f2b5edb with corrected
preview cleanup and report-library visibility; its candidate is not designated as the accepted
release. PR #157's opt-in Neon JWT integration is separate, unmerged work: token injection alone
does not authenticate the current shared-demo routes or isolate real users.

The latest DevOps issue updates report the private-repository branch-rule enforcement gap,
unverified production health/SHA, and staging replacement between PRs. Keep these owner-reported
limitations explicit; passing component CI does not establish protected main or production readiness.
Do not change approval rules, grant access, run shared failure drills or publish a release to fill
an evidence gap.

For final replay record full backend/package/model identities, approved synthetic target, browser
version, one create and returned ID, list/detail, notes/feedback edit plus reread/reopen, and delete
plus 404/list/reopen absence. Preserve request keys for ambiguous outcomes. Use only run-owned data.
The separate Week 1 subject/result change/restoration and any required redeploy/reread still need
their own exact-scope evidence; a notes edit alone does not prove either.
