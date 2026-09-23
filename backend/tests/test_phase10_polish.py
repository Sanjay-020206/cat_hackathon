"""Phase 10: Shift Memory greeting, incident logging round-trip, and the spec section 53
Definition-of-Done checklist replayed end-to-end against the running API."""
from fastapi.testclient import TestClient

from app.main import app


def test_shift_greeting_returns_expected_shape():
    with TestClient(app) as client:
        operators = client.get("/operators").json()
        operator_id = operators[0]["operator_id"]

        resp = client.get(f"/shift/greeting/{operator_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["operator_id"] == operator_id
        assert "previous_shift" in body
        assert "idle_pct" in body["previous_shift"]
        assert "safety_events" in body["previous_shift"]
        assert "todays_focus" in body
        assert isinstance(body["todays_focus"], str) and len(body["todays_focus"]) > 0


def test_shift_greeting_unknown_operator_404():
    with TestClient(app) as client:
        resp = client.get("/shift/greeting/NOT_REAL")
        assert resp.status_code == 404


def test_incident_logging_full_round_trip():
    with TestClient(app) as client:
        payload = {
            "incident_id": "PHASE10_INC_001",
            "timestamp": "2026-09-23T10:00:00",
            "machine_id": "EXC001",
            "operator_id": "OP1001",
            "site_zone": "Zone B",
            "event_type": "Proximity Alert",
            "severity": "Medium",
            "trigger": "operator approached restricted zone",
            "action_taken": "repositioned machine",
            "outcome": "resolved without harm",
        }
        create_resp = client.post("/incidents", json=payload)
        assert create_resp.status_code in (201, 409)

        list_resp = client.get("/incidents")
        assert list_resp.status_code == 200
        ids = [i["incident_id"] for i in list_resp.json()]
        assert "PHASE10_INC_001" in ids


def test_definition_of_done_end_to_end_flow():
    """Replays spec section 53's checklist against the live API: start app, dashboard data
    loads, telemetry streams, ML/context/risk/NBA all produce output, intervention/training
    loop works, entire flow requires no internet and survives Ollama being unavailable."""
    with TestClient(app) as client:
        # 1-3: app starts, dashboard loads operator/machine, today's tasks visible
        assert client.get("/").status_code == 200
        machines = client.get("/machines").json()
        assert len(machines) > 0
        machine_id = machines[0]["machine_id"]
        operators = client.get("/operators").json()
        assert len(operators) > 0
        tasks = client.get("/tasks").json()
        assert len(tasks) > 0

        # 4: machine telemetry streaming (scripted simulation)
        client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.02})
        try:
            with client.websocket_connect("/ws/telemetry") as ws:
                reading = None
                for _ in range(10):
                    msg = ws.receive_json()
                    if msg.get("type") != "status":
                        reading = msg
                        break
                assert reading is not None

                # 5-9: machine/operator/task/environment state calculated, ML analyzes
                # stream, anomaly/ETA/risk trajectory all present via the live recommendation
                assert reading.get("recommendation") is not None
                rec = reading["recommendation"]
                assert "risk_level" in rec
                assert "risk_trend" in rec

                # 10-12: context engine identifies dominant issue, NBA generated with evidence
                assert "next_best_action" in rec
                assert "evidence" in rec["explanation"]
        finally:
            client.post("/simulation/stop")

        # 13: optional local LLM explanation must not break anything even if unavailable
        rec_resp = client.get(f"/recommendations/{machine_id}", params={"narrative": True})
        assert rec_resp.status_code == 200
        assert rec_resp.json()["explanation"]["source"] in ("llm", "template")

        # 14-15: operator intervention simulated via training loop, metrics improve
        complete_resp = client.post(
            "/training/complete",
            json={
                "operator_id": operators[0]["operator_id"],
                "training_id": "TRN001",
                "skill_gap": "cycle_efficiency",
                "before_cycle_time": 55.0,
            },
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["after"] < complete_resp.json()["before"]

        # 16-17: system records outcome, training recommendation can be generated
        history_resp = client.get(f"/training/history/{operators[0]['operator_id']}")
        assert history_resp.status_code == 200
        assert len(history_resp.json()) >= 1

        # 18: shift summary reflects outcome (shift greeting endpoint works)
        greeting_resp = client.get(f"/shift/greeting/{operators[0]['operator_id']}")
        assert greeting_resp.status_code == 200

        # 19-20: entire demo works without internet (no external calls made above) and LLM
        # failure does not break the app -- already exercised via test_llm_explain.py
