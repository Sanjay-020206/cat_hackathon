"""Phase 11: reliability tests (spec section 44 rules + section 11 fault list).

Injects the specific failure modes the spec calls out -- no internet/Ollama, WebSocket
interruption, missing/invalid telemetry, ML failure, DB query failure -- and asserts the
core application keeps functioning (never a hard crash of the whole process), consistent
with "no ML/LLM dependency for basic dashboard functionality" and "every optional AI
component must have a fallback".
"""
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.context.live_context import LiveContextProcessor
from app.main import app


# ---- No internet / Ollama unavailable ----


def test_core_endpoints_work_with_no_external_network_at_all():
    """Simulates total network unavailability: every urlopen call raises. Only the
    optional narrative path touches the network (Ollama), so the rest of the API must be
    completely unaffected."""
    with patch("app.context.llm_explain.urllib.request.urlopen", side_effect=OSError("network unreachable")):
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            assert client.get("/machines").status_code == 200
            machine_id = client.get("/machines").json()[0]["machine_id"]
            resp = client.get(f"/recommendations/{machine_id}", params={"narrative": True})
            assert resp.status_code == 200
            assert resp.json()["explanation"]["source"] == "template"


# ---- WebSocket interruption ----


def test_simulation_continues_after_one_websocket_client_disconnects():
    """One client disconnecting abruptly must not stop the simulation or affect other
    subscribers (spec section 44: 'no cloud dependency', section 11: 'WebSocket
    interruption' must be tolerated)."""
    with TestClient(app) as client:
        client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.02})
        try:
            # first client connects then disconnects abruptly (context manager exit)
            with client.websocket_connect("/ws/telemetry") as ws1:
                ws1.receive_json()

            # simulation must still be running and a second client must still get data
            status = client.get("/simulation/status").json()
            assert status["running"] is True

            with client.websocket_connect("/ws/telemetry") as ws2:
                msg = ws2.receive_json()
                assert msg is not None
        finally:
            client.post("/simulation/stop")


def test_stopping_simulation_is_safe_even_with_active_subscribers():
    with TestClient(app) as client:
        client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.02})
        with client.websocket_connect("/ws/telemetry") as ws:
            ws.receive_json()
            resp = client.post("/simulation/stop")
            assert resp.status_code == 200
            assert resp.json()["running"] is False


# ---- Missing telemetry ----


def test_recommendation_for_machine_with_no_telemetry_returns_404_not_crash():
    with TestClient(app) as client:
        resp = client.get("/recommendations/NO_SUCH_MACHINE")
        assert resp.status_code == 404
        # app must still be up for the next request
        assert client.get("/").status_code == 200


def test_health_for_machine_with_no_telemetry_returns_404_not_crash():
    with TestClient(app) as client:
        resp = client.get("/health/NO_SUCH_MACHINE")
        assert resp.status_code == 404
        assert client.get("/machines").status_code == 200


# ---- Invalid / malformed telemetry ----


def test_live_context_processor_handles_missing_optional_fields():
    """A reading missing optional fields (proximity_events, ground_condition, weather)
    must not crash the live pipeline -- these should default sensibly."""
    processor = LiveContextProcessor()
    minimal_reading = {
        "timestamp": "2026-09-23T09:00:00",
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "engine_rpm": 1650,
        "engine_temp": 80.0,
        "hydraulic_pressure": 28.0,
        "hydraulic_temp": 62.0,
        "fuel_level": 64.0,
        "fuel_rate": 4.2,
        "engine_load": 55.0,
        "speed": 4.0,
        "cycle_time": 44.0,
        "idle_time": 8.0,
        "load_cycles": 10,
        "seatbelt_status": "Fastened",
        # no proximity_events / ground_condition / weather keys at all
    }
    result = processor.process_reading(minimal_reading)
    assert "risk_level" in result
    assert "next_best_action" in result


def test_ml_anomaly_scoring_skips_gracefully_on_incomplete_reading():
    processor = LiveContextProcessor()
    reading_missing_ml_features = {
        "timestamp": "2026-09-23T09:00:00",
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "engine_rpm": 1650,
        "engine_temp": 80.0,
        "hydraulic_pressure": 28.0,
        "hydraulic_temp": 62.0,
        "fuel_level": 64.0,
        # fuel_rate deliberately missing -- required by anomaly.FEATURES
        "engine_load": 55.0,
        "speed": 4.0,
        "cycle_time": 44.0,
        "idle_time": 8.0,
        "load_cycles": 10,
        "seatbelt_status": "Fastened",
    }
    result = processor.process_reading(reading_missing_ml_features)
    assert result is not None  # still produced a recommendation despite missing ML input


def test_context_engine_handles_empty_recent_telemetry_window():
    from app.context.context_engine import ContextFusionInput, build_context

    inp = ContextFusionInput(
        machine_id="EXC001",
        operator_id="OP1001",
        cycle_time=44.0,
        idle_time=8.0,
        speed=4.0,
        seatbelt_status="Fastened",
        proximity_events=0,
        ground_condition="Dry",
        shift_minutes=10,
        baseline_cycle_time=44.0,
        baseline_idle_time=8.0,
        recent_telemetry=pd.DataFrame(columns=["engine_temp", "hydraulic_pressure", "hydraulic_temp", "engine_load"]),
    )
    context = build_context(inp)
    assert context["risk_level"] in ("Low", "Moderate", "Elevated", "High")


# ---- ML failure (already covered per-endpoint in test_ml_wiring.py; this adds a
# whole-pipeline check that a totally broken model registry doesn't take down the API) ----


def test_full_recommendation_pipeline_survives_anomaly_model_exception():
    with TestClient(app) as client:
        machines = client.get("/machines").json()
        machine_id = machines[0]["machine_id"]
        with patch("app.routers.recommendations.get_anomaly_model", side_effect=Exception("disk read error")):
            resp = client.get(f"/recommendations/{machine_id}")
            assert resp.status_code == 200
            assert resp.json()["ml_anomaly"] is None
        # subsequent normal request still works
        assert client.get(f"/recommendations/{machine_id}").status_code == 200


# ---- Database failure ----


def test_db_query_failure_on_one_endpoint_does_not_take_down_the_app():
    with TestClient(app, raise_server_exceptions=False) as client:
        with patch("app.routers.machines.Session.query", side_effect=Exception("database is locked")):
            resp = client.get("/machines")
            assert resp.status_code == 500  # FastAPI's default error handling, not a hard crash

        # the app process itself is still alive and other endpoints still work
        resp2 = client.get("/")
        assert resp2.status_code == 200
        resp3 = client.get("/machines")
        assert resp3.status_code == 200


def test_incident_creation_duplicate_id_returns_conflict_not_crash():
    with TestClient(app) as client:
        payload = {
            "incident_id": "RELIABILITY_TEST_DUP",
            "timestamp": "2026-09-23T09:00:00",
            "machine_id": "EXC001",
            "operator_id": "OP1001",
            "site_zone": "Zone A",
            "event_type": "Proximity Alert",
            "severity": "Low",
            "trigger": "test",
            "action_taken": "test",
            "outcome": "test",
        }
        first = client.post("/incidents", json=payload)
        assert first.status_code in (201, 409)
        second = client.post("/incidents", json=payload)
        assert second.status_code == 409
        assert client.get("/incidents").status_code == 200
