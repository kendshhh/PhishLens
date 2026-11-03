"""Software contract and parity checks; no real LLM or accuracy claims here."""
import copy

import pytest
from pydantic import ValidationError

from backend.ai.live_review import (
    JUDGE_ID,
    JUDGE_REVISION,
    auxiliary_checks,
    review_request_sha,
    validate_local_review,
)
from backend.ai.service import AIService
from backend.ai.tfidf_provider import TfidfProvider
from backend.app.analysis_schemas import CreateSavedAnalysis, LocalReviewReport

BODY = "Team meeting tomorrow at ten. Thank you."


def payload():
    primary = AIService(TfidfProvider()).analyze_email(subject=None, sender=None, body=BODY)
    checks = [{"kind": "tfidf", "model_id": primary.model, "sha256": primary.model_revision,
               "raw_margin": primary.raw_margin, "score": primary.phishing_score,
               "threshold_score": primary.alert_threshold_score, "cutoff": 0,
               "alert": primary.model_alert, "valid": True}, *auxiliary_checks(BODY)]
    # A manually specified audit is only a schema fixture, never a claimed model result.
    judge = {"valid": True, "audit": "supported", "quote": "Team meeting tomorrow at ten.",
             "reason_code": "protective_or_routine_context", "missing_context": False,
             "model_id": JUDGE_ID, "model_revision": JUDGE_REVISION, "prompt_version": "phishlens-live-judge-1"}
    released = all(c["alert"] == primary.model_alert for c in checks)
    return primary, {"version": "phishlens-live-review-1", "status": "released" if released else "uncertain",
                     "primary_alert": primary.model_alert, "judge": judge, "reevaluators": checks}


def test_server_replays_all_classifiers_and_attributes_llm_to_browser():
    primary, raw = payload()
    result = validate_local_review(LocalReviewReport.model_validate(raw), primary, BODY)
    assert result["server_quote_checked"] is True
    assert len(result["server_replayed_classifiers"]) == 3
    assert result["origin"] == "browser_reported_LLM_audit_not_server_LLM_inference"


@pytest.mark.parametrize("field,value", [("score", .999), ("raw_margin", 99.), ("sha256", "a" * 64)])
def test_altered_client_numbers_or_model_identity_are_rejected(field, value):
    primary, raw = payload(); raw["reevaluators"][1][field] = value
    with pytest.raises(ValueError):
        validate_local_review(LocalReviewReport.model_validate(raw), primary, BODY)


def test_unsupported_judge_quote_is_rejected():
    primary, raw = payload(); raw["judge"]["quote"] = "This quote was never in the email."
    with pytest.raises(ValueError):
        validate_local_review(LocalReviewReport.model_validate(raw), primary, BODY)


def test_missing_judge_is_saved_as_uncertain_and_not_invented_as_valid():
    primary, raw = payload(); raw["judge"] = {"valid": False, "code": "judge_timeout"}; raw["status"] = "uncertain"
    result = validate_local_review(LocalReviewReport.model_validate(raw), primary, BODY)
    assert result["status"] == "uncertain"
    assert result["server_quote_checked"] is False


def test_client_review_is_bounded_and_does_not_authorize_client_prediction():
    _, raw = payload()
    request = CreateSavedAnalysis(body=BODY, local_review=raw)
    assert request.local_review is not None
    with pytest.raises(ValidationError):
        CreateSavedAnalysis(body=BODY, local_review=raw, prediction="legitimate")
    assert "local_review" not in CreateSavedAnalysis(body=BODY).model_dump()


def test_review_request_digest_changes_for_another_audit():
    _, raw = payload(); modified = copy.deepcopy(raw)
    modified["judge"] = {"valid": False, "code": "judge_timeout"}; modified["status"] = "uncertain"
    assert review_request_sha(LocalReviewReport.model_validate(raw)) != review_request_sha(LocalReviewReport.model_validate(modified))
