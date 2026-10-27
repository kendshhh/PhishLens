import pytest
from pydantic import ValidationError

from backend.app.analysis_schemas import (
    CreateSavedAnalysis,
    UpdateSavedAnalysis,
)


def test_create_accepts_omitted_subject():
    request = CreateSavedAnalysis.model_validate(
        {"body": "Synthetic email body"}
    )

    assert request.subject == ""
    assert request.body == "Synthetic email body"


@pytest.mark.parametrize(
    "payload",
    [
        {"body": ""},
        {"body": " \n "},
        {"body": "x" * 30_001},
        {"subject": "x" * 321, "body": "Synthetic body"},
        {"body": "Synthetic body", "user_id": "browser-selected-user"},
        {"body": "Synthetic body", "prediction": "legitimate"},
    ],
)
def test_create_rejects_invalid_or_browser_owned_fields(payload):
    with pytest.raises(ValidationError):
        CreateSavedAnalysis.model_validate(payload)


def test_patch_requires_a_field():
    with pytest.raises(ValidationError):
        UpdateSavedAnalysis.model_validate({})


def test_patch_accepts_explicit_null_notes():
    patch = UpdateSavedAnalysis.model_validate({"notes": None})

    assert "notes" in patch.model_fields_set
    assert patch.notes is None


def test_patch_rejects_verdict_changes():
    with pytest.raises(ValidationError):
        UpdateSavedAnalysis.model_validate(
            {"prediction": "legitimate"}
        )