"""Integration regressions, not new held-out benchmark measurements."""

import json
import math
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient
import pytest

from backend.ai.service import AIService
from backend.ai.tfidf_provider import MODEL_SHA256, TfidfProvider, prepare_plain, score_text
from backend.app import main
from backend.app.analysis_deadlines import AnalysisDeadline
from backend.app.analysis_execution import run_saved_inference
from backend.app.analysis_mapping import build_saved_analysis_fields

ROOT = Path(__file__).resolve().parents[2]


def test_server_scores_body_only_and_keeps_verified_original_quotes():
    provider = AIService(TfidfProvider())
    body = "Please review the meeting agenda. Do not share your password."
    first = provider.analyze_email(subject=None, sender=None, body=body)
    second = provider.analyze_email(subject="URGENT account suspended", sender="fake@example.test", body=body)
    assert first.raw_margin == second.raw_margin
    assert first.model_revision == MODEL_SHA256
    assert first.confidence is None
    assert math.isclose(first.alert_threshold_score, .887126047083381, abs_tol=1e-14)
    assert first.model_alert is (first.raw_margin >= 0)
    for item in first.evidence:
        assert item.text in body
        assert "not proof" in item.reason
    fields = build_saved_analysis_fields(first, mode="tfidf", subject="Title", body=body)
    assert fields["analysis_mode"] == "real"
    assert fields["analysis_provenance"]["phishing_score"] == first.phishing_score


@pytest.mark.parametrize("body", ["", "  ", "🔒⚠️", "<html>meeting</html>", "x" * 30001])
def test_invalid_or_unscorable_input_is_not_a_safe_verdict(body):
    with pytest.raises(RuntimeError):
        score_text(body)


def test_browser_python_arithmetic_parity_on_software_fixtures():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node needed for cross-runtime parity")
    inputs = [
        "Please review the project meeting agenda.",
        "Verify your password now at https://accounts.example.test/login or access will be suspended.",
        "Your code is 123456. Do not share it. Contact qa@example.test.",
        "Team\u0085meeting\u001cagenda\u00a0tomorrow — café 東京 ١٢٣٤٥٦.",
        "İSTANBUL meeting tomorrow with team.",
        "Meeting agenda " + "a" * 2500 + " the final agenda",
        "🔒 Your reference 1234567890. Call +1 (202) 555-0142.",
    ]
    program = """
import {readFileSync} from 'node:fs';
import {analyze} from './extension/ai/core.mjs';
const a=JSON.parse(readFileSync('extension/ai/tfidf_v12a.json'));
const c=JSON.parse(readFileSync('extension/ai/contract.json'));
let data='';for await(const s of process.stdin)data+=s;
console.log(JSON.stringify(JSON.parse(data).map(text=>analyze({text},a,c))));
"""
    completed = subprocess.run([node, "--input-type=module", "-e", program], cwd=ROOT,
                               input=json.dumps(inputs), capture_output=True, text=True, check=True)
    for body, js in zip(inputs, json.loads(completed.stdout), strict=True):
        py = score_text(body)
        assert py["text"] == js["analysis_text"]
        assert py["input_truncated"] == js["input_truncated"]
        assert math.isclose(py["raw_margin"], js["raw_margin"], abs_tol=1e-12)
        assert math.isclose(py["score"], js["score"], abs_tol=1e-12)
        assert py["alert"] == js["alert"]


def test_frozen_core_failure_does_not_leak_private_data():
    # Unsupported HTML is a rejected input, not an instruction to the classifier.
    with pytest.raises(RuntimeError):
        TfidfProvider().analyze(json.dumps({"body": "<script>private</script>"}))


def test_model_info_requires_no_database(monkeypatch):
    monkeypatch.setattr(main, "get_ai_config", lambda: ("tfidf", None, None))
    with TestClient(main.app) as client:
        info = client.get("/model-info").json()
    assert info["accepts_tfidf_reports"] is True
    assert info["model_sha256"] == MODEL_SHA256


def test_stateless_api_uses_selected_model_and_never_reports_class_certainty(monkeypatch):
    monkeypatch.setattr(main, "get_ai_config", lambda: ("tfidf", None, None))
    main._get_cached_ai_service.cache_clear()
    try:
        with TestClient(main.app) as client:
            response = client.post("/analyses", json={"text": "Please review the team meeting agenda."})
        assert response.status_code == 200
        result = response.json()
        assert result["mode"] == "tfidf"
        assert result["model_revision"] == MODEL_SHA256
        assert "confidence" not in result
        assert 0 <= result["phishing_score"] <= 1
        assert result["model_alert"] == (result["raw_margin"] >= 0)
    finally:
        main._get_cached_ai_service.cache_clear()


def test_save_header_refuses_mock_before_touching_database(monkeypatch):
    from backend.app.routers import saved_create

    monkeypatch.setattr(saved_create, "get_ai_config", lambda: ("mock", None, None))
    def no_database():
        pytest.fail("Incompatible model must be rejected before database access")
    monkeypatch.setattr(saved_create, "get_database_url", no_database)
    with TestClient(main.app) as client:
        response = client.post("/api/analyses", json={"body": "Meeting agenda"},
                               headers={"X-PhishLens-Model": MODEL_SHA256})
    assert response.status_code == 503
    assert response.json()["code"] == "analysis_unavailable"


def test_tfidf_saved_worker_runs_in_supervised_process_without_database():
    result = run_saved_inference(subject="Title", body="Please review the meeting agenda.",
                                 mode="tfidf", api_key=None, model=None,
                                 deadline=AnalysisDeadline.start())
    assert result.model_revision == MODEL_SHA256
    assert result.phishing_score is not None
