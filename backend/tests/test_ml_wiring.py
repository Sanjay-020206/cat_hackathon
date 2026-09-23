"""Confirms Model A (anomaly) and Model B (ETA) are actually wired into live endpoints,
not just unit-testable in isolation (a gap found after Phase 3: /predictions returned a
static placeholder and no endpoint ever called the trained models)."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.ml import registry


def test_predictions_endpoint_uses_real_eta_model_not_placeholder():
    with TestClient(app) as client:
        tasks = client.get("/tasks").json()
        task_id = tasks[0]["task_id"]

        resp = client.get(f"/predictions/{task_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "note" not in body  # placeholder response included a "note" field
        assert body["confidence"] is not None
        assert 0.0 <= body["confidence"] <= 1.0
        assert isinstance(body["explanation"], list)


def test_predictions_endpoint_falls_back_gracefully_on_model_failure():
    with TestClient(app) as client:
        tasks = client.get("/tasks").json()
        task_id = tasks[0]["task_id"]

        with patch("app.routers.predictions.get_eta_model", side_effect=RuntimeError("model corrupted")):
            resp = client.get(f"/predictions/{task_id}")
            assert resp.status_code == 200
            body = resp.json()
            assert "note" in body
            assert body["predicted_duration"] == body["original_estimated_time"]


def test_predictions_endpoint_unknown_task_404():
    with TestClient(app) as client:
        resp = client.get("/predictions/NOT_A_TASK")
        assert resp.status_code == 404


def test_recommendation_endpoint_includes_real_ml_anomaly_score():
    with TestClient(app) as client:
        machines = client.get("/machines").json()
        machine_id = machines[0]["machine_id"]

        resp = client.get(f"/recommendations/{machine_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "ml_anomaly" in body
        if body["ml_anomaly"] is not None:
            assert "anomaly_flag" in body["ml_anomaly"]
            assert "anomaly_score" in body["ml_anomaly"]


def test_recommendation_endpoint_degrades_gracefully_if_anomaly_model_fails():
    with TestClient(app) as client:
        machines = client.get("/machines").json()
        machine_id = machines[0]["machine_id"]

        with patch("app.routers.recommendations.get_anomaly_model", side_effect=RuntimeError("corrupted")):
            resp = client.get(f"/recommendations/{machine_id}")
            assert resp.status_code == 200
            assert resp.json()["ml_anomaly"] is None


def test_live_websocket_recommendation_includes_ml_anomaly():
    with TestClient(app) as client:
        client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.02})
        try:
            with client.websocket_connect("/ws/telemetry") as ws:
                for _ in range(10):
                    msg = ws.receive_json()
                    if msg.get("type") == "status":
                        continue
                    rec = msg.get("recommendation")
                    assert rec is not None
                    assert "ml_anomaly" in rec
                    break
        finally:
            client.post("/simulation/stop")


def test_registry_lazily_trains_model_if_artifact_missing(tmp_path, monkeypatch):
    registry.reset()
    fake_path = str(tmp_path / "does_not_exist.joblib")
    monkeypatch.setattr("app.ml.anomaly.ARTIFACT_PATH", fake_path)
    model = registry.get_anomaly_model()
    assert model is not None
    registry.reset()
