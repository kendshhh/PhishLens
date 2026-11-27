# AI failure-test crosswalk — 2026-11-23

This crosswalk maps the Module 6 failure examples from *Engineering AI-Native
Products.pdf* to PhishLens tests. Provider calls in these tests are mocked.
The current product analyzes supplied email content and has no retrieval or RAG
subsystem; the PDF's “nothing retrieved” case is therefore recorded as an
architecture applicability decision rather than claimed as a retrieval test.

| PDF failure case | Test evidence | Result and scope |
|---|---|---|
| Timeout | `backend/tests/test_provider_error_contract.py::test_transport_failure_retains_safe_502_contract[ReadTimeout]`; `backend/tests/test_analysis_worker_timeout_classification.py::test_typed_provider_timeout_is_classified_for_saved_analysis`; `backend/tests/test_provider_error_contract.py::test_provider_status_has_safe_endpoint_contract` (upstream HTTP 504 remains a sanitized 502 provider failure) | A client-side `httpx.ReadTimeout` becomes 504 with a five-second `Retry-After` and a safe body; saved-analysis worker classifies the typed timeout. |
| Rate limited | `backend/tests/test_ai_api.py::test_ai_request_quota_rejection_stops_before_inference`; `backend/tests/test_provider_error_contract.py::test_provider_status_has_safe_endpoint_contract` (provider 429 case) | The app quota returns 429 with `Retry-After` before inference. An upstream provider 429 is separately treated as unavailable (503) to avoid confusing an upstream quota with this user's quota. |
| Provider failure | `backend/tests/test_ai_api.py::test_analysis_endpoint_reports_provider_failure`; `backend/tests/test_safe_errors.py::test_provider_failure_does_not_expose_private_details` | 502 safe failure; private provider details are not returned. |
| Invalid JSON | `backend/tests/test_ai_providers.py::test_bad_google_output_is_not_a_safe_verdict` (`"not json"` case) | Rejected as controlled invalid analysis; no verdict is created. |
| Wrong output shape | `backend/tests/test_ai_service.py::test_malformed_provider_contract_is_a_controlled_failure`; `backend/tests/test_output_boundary.py::test_invalid_model_output_never_becomes_a_verdict` | Missing/invalid fields and unsupported values fail validation; response contains no model verdict. |
| Business rule broken | `backend/tests/test_ai_service.py::test_invented_evidence_fails_instead_of_becoming_a_valid_report`; `backend/tests/test_analysis_mapping.py::test_rejects_evidence_not_found_in_email` | Evidence not present in the supplied email is rejected. |
| Nothing retrieved | `backend/tests/test_ai_api.py::test_oversized_and_malformed_requests_never_invoke_ai` (empty text case) and `backend/tests/test_ai_service.py::test_invalid_input_never_reaches_provider` (empty-body case) | Empty supplied input is rejected with 422 before provider use. PhishLens has no retrieval call, so an empty retrieval result is not a current product path. Keep this case N/A only while the architecture remains non-RAG; obtain course-owner acceptance if required. |
| Oversized input | `backend/tests/test_ai_api.py::test_oversized_and_malformed_requests_never_invoke_ai`; `backend/tests/test_ai_service.py::test_invalid_input_never_reaches_provider` | 30,001-character body is rejected before AI invocation. |

The tests assert response status, error schema, validation rules, output
properties, provenance, or evidence grounding. They do not assert exact model
wording. The focused mocked suite is run with the commands recorded in the
current audit; no paid provider calls are part of this crosswalk.
