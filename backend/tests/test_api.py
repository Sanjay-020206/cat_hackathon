import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_machines(client):
    resp = client.get("/machines")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "machine_id" in data[0]


def test_get_machine_by_id(client):
    machines = client.get("/machines").json()
    machine_id = machines[0]["machine_id"]
    resp = client.get(f"/machines/{machine_id}")
    assert resp.status_code == 200
    assert resp.json()["machine_id"] == machine_id


def test_list_operators(client):
    resp = client.get("/operators")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_list_tasks(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_list_tasks_filtered_by_operator(client):
    tasks = client.get("/tasks").json()
    operator_id = tasks[0]["operator_id"]
    resp = client.get("/tasks", params={"operator_id": operator_id})
    assert resp.status_code == 200
    assert all(t["operator_id"] == operator_id for t in resp.json())


def test_list_telemetry(client):
    resp = client.get("/telemetry", params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 10
    assert "cycle_time" in data[0]


def test_list_safety_events(client):
    resp = client.get("/safety")
    assert resp.status_code == 200


def test_get_health(client):
    machines = client.get("/machines").json()
    machine_id = machines[0]["machine_id"]
    resp = client.get(f"/health/{machine_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] in ("Normal", "Watch", "Elevated", "Critical")


def test_get_health_unknown_machine_404(client):
    resp = client.get("/health/DOES_NOT_EXIST")
    assert resp.status_code == 404


def test_get_prediction(client):
    tasks = client.get("/tasks").json()
    task_id = tasks[0]["task_id"]
    resp = client.get(f"/predictions/{task_id}")
    assert resp.status_code == 200
    assert "predicted_duration" in resp.json()


def test_list_training(client):
    resp = client.get("/training")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_create_and_list_incident(client):
    payload = {
        "incident_id": "TEST_INC_001",
        "timestamp": "2026-09-23T09:00:00",
        "machine_id": "EXC001",
        "operator_id": "OP1001",
        "site_zone": "Zone A",
        "event_type": "Proximity Alert",
        "severity": "Medium",
        "trigger": "test",
        "action_taken": "reassessed zone",
        "outcome": "resolved",
    }
    resp = client.post("/incidents", json=payload)
    assert resp.status_code in (201, 409)  # 409 if re-run against a persisted DB

    resp = client.get("/incidents")
    assert resp.status_code == 200
    ids = [i["incident_id"] for i in resp.json()]
    assert "TEST_INC_001" in ids


def test_get_recommendation_placeholder(client):
    resp = client.get("/recommendations/EXC001")
    assert resp.status_code == 200
    assert "risk_level" in resp.json()


def test_simulation_start_status_stop(client):
    resp = client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.05})
    assert resp.status_code == 200
    assert resp.json()["running"] is True

    resp = client.get("/simulation/status")
    assert resp.status_code == 200

    resp = client.post("/simulation/stop")
    assert resp.status_code == 200
    assert resp.json()["running"] is False


def test_websocket_telemetry_stream(client):
    client.post("/simulation/start", json={"mode": "scripted", "interval_seconds": 0.05})
    try:
        with client.websocket_connect("/ws/telemetry") as ws:
            message = ws.receive_json()
            assert "timestamp" in message or message.get("type") == "status"
    finally:
        client.post("/simulation/stop")
