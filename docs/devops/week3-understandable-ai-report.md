# Issue #97 — understandable AI report

Task: S3-A1 / W3-D2-Andrei

Branch: `feat/97-understandable-ai-report`

Owner: Andrei (`JupitraxNeptuna`)

Reviewer: Leyan (`inaki3023`); backup: Trixia (`xxTrixia`)

## Implementation status

The popup report form now uses the existing `saveAnalysisAndRefresh` composition and the injected five-method API client. It renders saved classification, confidence with an uncertainty note, validated indicators, explanation, and the backend's available provider/model metadata. Mock, provider-backed, and unknown provenance remain distinct. A missing classification is shown as not analyzed; no verdict is inferred from missing confidence or explanation.

Loading, validation, timeout, unavailable, malformed response, and partial refresh states have separate messages. Failed analysis keeps the form input. A failed history refresh preserves the report and existing history and exposes a retry action. Report fields and indicators are assigned as text, not HTML.

## Verification evidence

These checks are local. They do not establish connected-browser or deployed-provider behavior.

| Command | Result | Evidence type |
|---|---|---|
| `node extension/tests/popup.test.mjs` | PASS — 27 tests | UI states use explicit result fixtures and the development-only in-memory CRUD client |
| `node extension/tests/report-client.test.mjs` | PASS — 12 tests | Injected fake client; tests the existing #87 composition |
| `node extension/tests/report-client-http.test.mjs` | PASS — 3 tests | Production API client against a local synthetic HTTP server; not a deployed API or AI provider |
| `node extension/tests/api.test.mjs` | PASS — 20 tests | API validation and response handling with controlled fetch fixtures |
| `npm run lint` | PASS | ESLint on `extension/js/` |
| `npm run validate` | PASS | Extension manifest and required-file validation |

The UI provenance examples, including the model/provider strings in tests, are synthetic fixtures. The local HTTP server returns synthetic records. None of these results proves real-provider provenance, deployed API behavior, or installed Chrome acceptance.

## Integration still pending

Coordinate any response-contract changes with #90 and failure semantics with #96. Verify the exact PR head with the staging-connected extension and a real provider-backed result when available. Track installed-browser flows and revision-linked evidence in #91. Fixtures and local HTTP responses do not satisfy that integration check.
