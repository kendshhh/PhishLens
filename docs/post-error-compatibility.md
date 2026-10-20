# Live POST error compatibility

Related: backend PR #50 and issue #20. This extension fix can merge before or together with #50 because it supports both response formats.

POST /analyses failure message priority:
1. Nonblank string error.message from the structured error envelope.
2. Nonblank string detail from older backend responses.
3. Generic HTTP status message.

Non-JSON failures retain the existing readable HTTP error. Tests exercise 422 invalid_input, 502 inference_failed, and 503 analysis_unavailable through the actual background worker test harness. They check the error state, null result, error badge, and legacy compatibility. Existing Clear, stale-request, and timeout tests still pass.

Local verification on an isolated copy of main c350131 plus these files:
- node --test extension/tests/*.test.mjs: 32 passed, 0 failed.
- ESLint extension/js/ and extension/background.js: passed.

Fixtures match the documented error envelopes at backend PR #50 commit 5e80b5d. This is client fixture verification, not a claim of deployed/backend joint acceptance. Trixia/Wilberr still need a combined integration check.

Live POST results remain in Chrome session state and do not create saved-history records. GET /api/analyses and the Week 2 CRUD factory are untouched by this PR.

The client deadline remains 25 seconds. Provider/local processing limits and any distinct 504 behavior remain pending agreement with Wilberr and Trixia. This PR does not settle or change those limits. No backend, main.py, database, popup layout, CI, or production deployment changes are included.
