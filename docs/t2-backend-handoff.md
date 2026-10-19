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
- HTTP 502: `inference_failed`. This includes invalid model output, unsupported evidence, and inference failures. The fixed message is `Analysis failed`.
- HTTP 503: `analysis_unavailable`. This covers missing local model files, configuration failure, and recognized daily provider quota exhaustion. The fixed message is `Analysis temporarily unavailable`.

The 502 and 503 responses contain `code` and `message`, without `fields`. Submitted email text, credentials, provider exception text, and private model paths are not returned.

A distinct HTTP 504 response has not been implemented. Timeout classification and deadlines require a coordinated decision.

## Local verification

Run from the repository root:

    ./.venv/bin/python -m ruff check backend
    env -u RUN_DATABASE_TESTS ./.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider

Results on October 20, 2026: Ruff passed; 83 tests passed and 2 database tests skipped. Tests cover blank and oversized input, optional blank fields, safe errors, missing local model files, invalid labels and confidence, unsupported evidence, and no successful verdict after failure.

These mocked tests verify contract behavior. They do not prove successful real-model inference, a live PostgreSQL read, or deployed extension behavior.

## Coordination before integration

- **Leyan / extension:** `extension/background.js` currently reads `errorBody.detail` for POST failures. Update it to read the new `error.message` and retain a safe fallback. Confirm that successful live results remain separate from history records. Do not change `GET /api/analyses`.
- **Wilberr / AI:** Review the status and code choices, particularly unavailable hosted models versus general inference failure. Confirm a real-model smoke run through the shared service and record its result. Evidence and confidence display remain client integration work.
- **Leyan and Wilberr:** Agree on compatible time limits. The extension currently stops waiting after 25 seconds, while the Gemini client is configured for 30 seconds and local cold inference has been observed taking longer. Decide whether a distinct provider timeout should return HTTP 504.
- **Backend / DevOps:** Review this branch and applicable CI results before merging. Record any deployment verification separately. No hosted production behavior is claimed by the local test results.