"""Phase 8: optional local LLM explanation, with mandatory template fallback (spec
sections 35-36). Tests cover both paths -- Ollama unreachable (fallback) and Ollama
serving a real local model (LLM path) -- and require neither to crash the API.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.context import llm_explain
from app.context.llm_explain import explain_with_fallback, generate_natural_language, is_available
from app.main import app

SAMPLE_EXPLANATION = {
    "detection": "Operational risk is increasing (elevated).",
    "evidence": "Contributing factors: cycle time deviation from baseline of 23%; 2 proximity event(s).",
    "explanation": "Current risk score is 0.52 (Elevated), driven primarily by safety conditions.",
    "recommendation": "Reposition before continuing excavation.",
    "priority": "High",
    "confidence": 0.84,
    "source": "template",
}


def test_is_available_false_when_ollama_unreachable():
    with patch("app.context.llm_explain.urllib.request.urlopen", side_effect=OSError("connection refused")):
        assert is_available() is False


def test_generate_natural_language_returns_none_on_connection_error():
    with patch("app.context.llm_explain.urllib.request.urlopen", side_effect=OSError("connection refused")):
        result = generate_natural_language(SAMPLE_EXPLANATION)
        assert result is None


def test_explain_with_fallback_uses_template_when_ollama_unavailable():
    with patch("app.context.llm_explain.is_available", return_value=False):
        result = explain_with_fallback(SAMPLE_EXPLANATION)
        assert result["source"] == "template"
        assert "Reposition before continuing excavation." in result["narrative"]
        # original fields preserved
        assert result["detection"] == SAMPLE_EXPLANATION["detection"]


def test_explain_with_fallback_does_not_raise_on_malformed_llm_response():
    with patch("app.context.llm_explain.is_available", return_value=True), patch(
        "app.context.llm_explain.generate_natural_language", return_value=None
    ):
        result = explain_with_fallback(SAMPLE_EXPLANATION)
        assert result["source"] == "template"


def test_explain_with_fallback_uses_llm_text_when_available():
    with patch("app.context.llm_explain.is_available", return_value=True), patch(
        "app.context.llm_explain.generate_natural_language", return_value="Risk is rising; reposition now."
    ):
        result = explain_with_fallback(SAMPLE_EXPLANATION)
        assert result["source"] == "llm"
        assert result["narrative"] == "Risk is rising; reposition now."


def test_recommendation_endpoint_works_without_narrative_flag():
    """Default path must have zero Ollama dependency and never call it."""
    with patch.object(llm_explain, "is_available") as mock_available:
        with TestClient(app) as client:
            machines = client.get("/machines").json()
            machine_id = machines[0]["machine_id"]
            resp = client.get(f"/recommendations/{machine_id}")
            assert resp.status_code == 200
            assert "narrative" not in resp.json()["explanation"]
        mock_available.assert_not_called()


def test_recommendation_endpoint_with_narrative_falls_back_gracefully_if_ollama_down():
    with patch("app.context.llm_explain.is_available", return_value=False):
        with TestClient(app) as client:
            machines = client.get("/machines").json()
            machine_id = machines[0]["machine_id"]
            resp = client.get(f"/recommendations/{machine_id}", params={"narrative": True})
            assert resp.status_code == 200
            body = resp.json()
            assert body["explanation"]["source"] == "template"
            assert "narrative" in body["explanation"]


def test_recommendation_endpoint_with_narrative_uses_real_ollama_if_running():
    """Only meaningful if Ollama is actually running locally with a pulled model; skips
    gracefully (asserts fallback shape) if not, since Ollama must remain optional."""
    with TestClient(app) as client:
        machines = client.get("/machines").json()
        machine_id = machines[0]["machine_id"]
        resp = client.get(f"/recommendations/{machine_id}", params={"narrative": True})
        assert resp.status_code == 200
        body = resp.json()
        assert body["explanation"]["source"] in ("llm", "template")
        assert len(body["explanation"]["narrative"]) > 0
