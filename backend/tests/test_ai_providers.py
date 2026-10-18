import json
import sys
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from google.genai import errors

from backend.ai import gemini_provider
from backend.ai.local_provider import EXPECTED_LABELS, MODEL_REVISION, LocalProvider
from backend.ai.service import AIService
from backend.core import config


@pytest.mark.parametrize("mode", ["mock", "local"])
def test_offline_modes_need_no_google_credentials(monkeypatch, mode):
    monkeypatch.setattr(config, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("AI_MODE", mode)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert config.get_ai_config() == (mode, None, None)


@pytest.mark.parametrize("mode, key, model, message", [
    ("unknown", "", "", "AI_MODE must be"),
    ("gemini", "", "gemini-test", "GEMINI_API_KEY is required"),
    ("gemini", "synthetic-key", "", "GEMINI_MODEL is required"),
])
def test_invalid_ai_configuration_fails_explicitly(monkeypatch, mode, key, model, message):
    monkeypatch.setattr(config, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("AI_MODE", mode)
    monkeypatch.setenv("GEMINI_API_KEY", key)
    monkeypatch.setenv("GEMINI_MODEL", model)
    with pytest.raises(RuntimeError, match=message):
        config.get_ai_config()


@pytest.fixture
def google_client(monkeypatch):
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps({
        "classification": "legitimate", "tactics": [], "evidence": [], "recommendations": [],
    }))
    constructor = Mock(return_value=client)
    monkeypatch.setattr(gemini_provider.genai, "Client", constructor)
    return client, constructor


def test_gemini_uses_raw_json_schema_with_bounded_single_attempt(google_client):
    client, constructor = google_client
    provider = gemini_provider.GeminiProvider(api_key="synthetic-key", model="gemini-3.1-flash-lite")
    result = provider.analyze('{"body":"Hello"}')
    config = client.models.generate_content.call_args.kwargs["config"]
    assert config.response_json_schema["additionalProperties"] is False
    assert config.response_schema is None
    assert config.max_output_tokens == 2048
    assert constructor.call_args.kwargs["http_options"].timeout == 30_000
    assert constructor.call_args.kwargs["http_options"].retry_options.attempts == 1
    assert result.confidence is None
    assert result.model == "gemini-3.1-flash-lite"
    assert result.explanation_source == "model"
    provider.close()
    client.close.assert_called_once()


def test_gemma_uses_explicit_prompt_schema_instead_of_unsupported_json_mode(google_client):
    client, _ = google_client
    provider = gemini_provider.GeminiProvider(api_key="synthetic-key", model="gemma-4-31b-it")
    provider.analyze('{"body":"Hello"}')
    call = client.models.generate_content.call_args.kwargs
    assert call["config"].response_json_schema is None
    assert call["config"].response_mime_type is None
    assert '"classification"' in call["contents"]


@pytest.mark.parametrize("text", [None, "", "not json", '{"classification":"safe"}', '{"classification":"phishing","confidence":0.99}'])
def test_bad_google_output_is_not_a_safe_verdict(google_client, text):
    client, _ = google_client
    client.models.generate_content.return_value = SimpleNamespace(text=text)
    provider = gemini_provider.GeminiProvider(api_key="synthetic-key", model="gemini-test")
    with pytest.raises(RuntimeError, match="empty response|invalid analysis"):
        provider.analyze("Test")


@pytest.mark.parametrize("code", [400, 401, 403, 404, 429, 500, 503])
def test_google_errors_do_not_expose_provider_details(google_client, code):
    client, _ = google_client
    client.models.generate_content.side_effect = errors.APIError(
        code=code, response_json={"error": {"message": "private provider details"}},
    )
    provider = gemini_provider.GeminiProvider(api_key="synthetic-key", model="gemini-test")
    with pytest.raises(RuntimeError) as exc:
        provider.analyze("Test")
    assert "private" not in str(exc.value)
    assert str(code) in str(exc.value)


def test_network_timeout_is_a_controlled_failure(google_client):
    client, _ = google_client
    client.models.generate_content.side_effect = httpx.ReadTimeout("private transport detail")
    provider = gemini_provider.GeminiProvider(api_key="synthetic-key", model="gemini-test")
    with pytest.raises(RuntimeError, match="connection failed or timed out"):
        provider.analyze("Test")


def test_daily_quota_is_distinct_from_a_temporary_rate_limit(google_client):
    client, _ = google_client
    client.models.generate_content.side_effect = errors.APIError(
        code=429, response_json={"error": {"message": "private quota details", "details": [
            {"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier", "quotaValue": "20"}]},
        ]}},
    )
    provider = gemini_provider.GeminiProvider(api_key="synthetic-key", model="gemini-test")
    with pytest.raises(gemini_provider.DailyQuotaExceeded, match="daily request quota") as exc:
        provider.analyze("Test")
    assert "private" not in str(exc.value)
    assert "20" not in str(exc.value)


def test_local_construction_does_not_import_or_load_weights():
    provider = LocalProvider()
    assert provider.model is None
    assert provider.tokenizer is None


def fake_local_modules(monkeypatch, labels=EXPECTED_LABELS):
    torch = Mock()
    model = Mock()
    model.config.model_type = "distilbert"
    model.config.id2label = labels
    torch.inference_mode = nullcontext
    transformers = SimpleNamespace(
        AutoTokenizer=Mock(), AutoModelForSequenceClassification=Mock(),
    )
    transformers.AutoModelForSequenceClassification.from_pretrained.return_value = model
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    return torch, transformers, model


def test_local_loading_is_pinned_offline_cased_and_uses_safetensors(monkeypatch, tmp_path):
    _, modules, _ = fake_local_modules(monkeypatch)
    provider = LocalProvider(cache_dir=tmp_path)
    provider._load()
    kwargs = modules.AutoModelForSequenceClassification.from_pretrained.call_args.kwargs
    assert kwargs["revision"] == MODEL_REVISION
    assert kwargs["local_files_only"] is True
    assert kwargs["trust_remote_code"] is False
    assert kwargs["use_safetensors"] is True
    assert modules.AutoTokenizer.from_pretrained.call_args.kwargs["do_lower_case"] is False


def test_local_label_mismatch_fails_instead_of_guessing(monkeypatch):
    fake_local_modules(monkeypatch, labels={0: "LABEL_0", 1: "LABEL_1"})
    with pytest.raises(RuntimeError, match="unexpected architecture or labels"):
        LocalProvider()._load()


def test_missing_local_weights_return_an_actionable_failure(monkeypatch):
    _, modules, _ = fake_local_modules(monkeypatch)
    modules.AutoTokenizer.from_pretrained.side_effect = OSError("private cache path")
    with pytest.raises(RuntimeError, match="Local AI is unavailable") as exc:
        LocalProvider()._load()
    assert "private" not in str(exc.value)


@pytest.mark.parametrize("url_length", [0, 1_999, 2_000, 2_001, 25_000])
def test_phishing_in_later_window_is_detected(monkeypatch, url_length):
    torch, modules, _ = fake_local_modules(monkeypatch)

    class Tensor:
        shape = (2, 512)

        def __getitem__(self, _key):
            return self

        def tolist(self):
            return [.02, .99]

    tokenizer = modules.AutoTokenizer.from_pretrained.return_value
    tokenizer.return_value = {"input_ids": Tensor(), "attention_mask": Tensor(), "overflow_to_sample_mapping": Tensor()}
    torch.softmax.return_value = Tensor()
    url = "https://example.test/" + "a" * (url_length - len("https://example.test/")) if url_length else ""
    body = "Benign newsletter. " * 100 + "Send your password now. " + url
    result = AIService(LocalProvider()).analyze_email(
        subject=None, sender=None, body=body,
    )
    if url_length:
        quote = next(item.text for item in result.evidence if item.text.startswith("https://"))
        assert quote == url[:2_000]
        assert quote in body
    assert result.classification == "phishing"
    assert result.confidence == .99
    assert result.windows_processed == 2
    assert result.input_truncated is False
    assert result.explanation_source == "rules"
    assert tokenizer.call_args.kwargs["return_overflowing_tokens"] is True
