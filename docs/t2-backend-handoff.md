# T2 Backend Validation and AI Output Boundary — Draft Handoff

- Issue: #20
- Branch: `feat/20-backend-ai-boundary`
- Status: Locally implemented and tested; integration review remains.

## Endpoint boundaries

- `POST /analyses` returns an unsaved live analysis. It does not write a history record.
- `GET /api/analyses` continues to return `{"items": [...]}` for saved history. Its response and error formats have not changed.
- `/health` and `/ready` retain their existing behavior and response formats.

## Request contract for POST /analyses

The JSON request requires `text`, a nonblank string of at most 30,000 characters.

`subject` and `sender` are optional strings of at most 320 characters each. Empty or whitespace-only values become omitted (`None`) before the AI service runs. Nonblank values are preserved. `sender` is untrusted descriptive text, not an authenticated identity.

Extra JSON fields are rejected. Invalid requests receive HTTP 422 before the AI service or model is called.

## Successful live result

The response field is named `classification` and accepts `legitimate`, `spam`, or `phishing`.

Risk follows the classification: `legitimate` → `low`, `spam` → `medium`, and `phishing` → `high`. There is no `critical` rule for this live endpoint.

`confidence` is optional. Gemini does not provide a numeric confidence, so the field is omitted when unavailable; clients must not treat its absence as zero. The local model returns a number from 0 to 1. That number is an uncalibrated classifier score, not a measured probability that the verdict is correct.

Live evidence uses `evidence: [{"text": "...", "reason": "..."}]`. It is separate from saved history's `threat_indicators: [{"type": "...", "detail": "..."}]`. The backend validates the evidence structure and checks that quoted evidence occurs in the supplied email text after whitespace normalization.

The existing AI service and schemas from PR #26 remain the inference path. The smoke script also calls this shared service. Ordinary tests use fakes and do not load or download model weights.

## POST error contract

Only `POST /analyses` uses this new error envelope:

    {
      "error": {
        "code": "invalid_input",
        "message": "Invalid email input",
        "fields": [
          {"field": "text", "code": "blank"}
        ]
      }
    }

- HTTP 422: `invalid_input`. The `fields` array gives safe field names and short codes. Implemented field codes are `blank`, `required`, `too_long`, `invalid_type`, `unknown_field`, `malformed_json`, and `invalid`.
- HTTP 502: `inference_failed`. This includes invalid model output, unsupported evidence, Gemini HTTP 500/502/504 failures, and transport failures including timeouts. The fixed message is `Analysis failed`.
- HTTP 503: `analysis_unavailable`. This covers missing local models, configuration failure, recognized daily quota exhaustion, and Gemini HTTP 401/403/404/429/503 failures. Hosted availability failures use the shared `AnalysisUnavailableError` type. The fixed message is `Analysis temporarily unavailable`.

The 502 and 503 responses contain `code` and `message`, without `fields`. Submitted email text, credentials, provider exception text, and private model paths are not returned.

A distinct HTTP 504 response has not been implemented. Timeout classification and deadlines require a coordinated decision.

## Local verification

Run from the repository root:

    ./.venv/bin/python -m ruff check backend
    env -u RUN_DATABASE_TESTS ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider

Results on October 21, 2026: Ruff passed; 93 tests passed and 2 database tests skipped. Ten new endpoint regression cases exercise the actual Gemini provider and shared AI service with a mocked SDK client. They verify safe 503 responses for provider HTTP 401/403/404/429/503, and safe 502 responses for HTTP 500/502/504, transport timeouts, and connection failures. No network calls or model downloads are made by these tests.

These mocked tests verify contract behavior. They do not prove successful real-model inference, a live PostgreSQL read, or deployed extension behavior.

## Coordination before integration

- **Leyan / extension:** PR #53 is merged and supports `error.message` with a safe legacy `detail` fallback. Final staging and installed Chrome verification remain pending.
- **Wilberr / AI:** Re-review the typed availability mapping and new endpoint regression tests. Record real-model shared-service verification against the final integrated commit, including source SHA, model/revision, environment, synthetic cases, outputs, timings, and exit status.
- **Leyan and Wilberr:** Confirm the accepted Week 1 runtime scope. The client deadline remains 25 seconds, Gemini's configured HTTP timeout remains 30 seconds, and local inference has no enforced wall-clock deadline. These changes do not implement a compatible end-to-end deadline. Cold/unbounded local inference has not demonstrated completion within the client deadline.
- **Backend / DevOps:** Obtain successful required checks and staging HTTP verification for the final commit. Coordinate installed Chrome verification against that same deployed source and identified extension package before sign-off.
- **Week 2 boundary:** The proposed 15-second inference budget, 20-second server-operation target, and persistent-endpoint `504 analysis_timeout` are separate work. They are not implemented by this Week 1 PR.
