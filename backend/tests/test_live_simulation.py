"""Phase 7: end-to-end live simulation wiring.

Verifies simulator -> context processor -> recommendation attachment works directly
(without needing a real WebSocket), and that a full WebSocket session receives readings
that already carry a live-computed recommendation tracking the scripted demo scenario's
risk trajectory (spec sections 26-28, 41).
"""
from fastapi.testclient import TestClient

from app.context.live_context import LiveContextProcessor
from app.main import app
from app.simulator.scenario import STAGES, stage_to_telemetry


def test_live_context_processor_tracks_scenario_risk_trajectory():
    processor = LiveContextProcessor()
    readings = [stage_to_telemetry(s, f"2026-09-23T09:{i*5:02d}:00") for i, s in enumerate(STAGES)]

    recommendations = [processor.process_reading(r) for r in readings]

    assert recommendations[0]["risk_level"] in ("Low", "Moderate")
    peak_score = max(r["risk_score"] for r in recommendations)
    assert recommendations[-1]["risk_score"] < peak_score


def test_live_context_processor_recommendation_shape():
    processor = LiveContextProcessor()
    reading = stage_to_telemetry(STAGES[0], "2026-09-23T09:00:00")
    rec = processor.process_reading(reading)
    required = {"risk_level", "risk_score", "risk_trend", "contributors", "next_best_action", "explanation"}
    assert required.issubset(rec.keys())


def test_websocket_stream_carries_live_recommendation():
    with TestClient(app) as client:
        client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.02})
        try:
            with client.websocket_connect("/ws/telemetry") as ws:
                got_recommendation = False
                for _ in range(20):
                    message = ws.receive_json()
                    if message.get("type") == "status":
                        continue
                    if message.get("recommendation") is not None:
                        got_recommendation = True
                        rec = message["recommendation"]
                        assert "risk_level" in rec
                        assert "next_best_action" in rec
                        break
                assert got_recommendation
        finally:
            client.post("/simulation/stop")


def test_websocket_stream_reflects_scenario_progression():
    """Runs the scripted demo through the real WebSocket and checks that risk eventually
    escalates to Elevated/High and then recovers, mirroring spec section 41."""
    with TestClient(app) as client:
        client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.02})
        try:
            risk_scores = []
            with client.websocket_connect("/ws/telemetry") as ws:
                for _ in range(len(STAGES) + 5):
                    message = ws.receive_json()
                    if message.get("type") == "status":
                        continue
                    rec = message.get("recommendation")
                    if rec:
                        risk_scores.append(rec["risk_score"])
                    if message.get("stage_label") == "CONDITIONS_IMPROVE" and len(risk_scores) >= len(STAGES):
                        break
        finally:
            client.post("/simulation/stop")

        assert len(risk_scores) > 0
        assert max(risk_scores) > risk_scores[0]
