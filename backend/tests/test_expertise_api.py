"""API-level smoke tests for the CAT Expertise Engine + Site Map endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.expertise.service import reset_expertise_engine
from app.main import app


@pytest.fixture(scope="module")
def client():
    reset_expertise_engine()
    with TestClient(app) as c:
        yield c
    reset_expertise_engine()


def test_evaluate_current_situation(client):
    resp = client.get("/expertise/evaluate/EXC001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["machine_id"] == "EXC001"
    assert "situation" in body
    assert "ground_estimate" in body
    assert "energy_forecast" in body
    assert body["data_source"] == "synthetic_demo"


def test_evaluate_unknown_machine_404(client):
    resp = client.get("/expertise/evaluate/DOES_NOT_EXIST")
    assert resp.status_code == 404


def test_list_episodes(client):
    resp = client.get("/expertise/episodes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == len(body["episodes"])
    assert body["data_source"] == "synthetic_demo"


def test_record_outcome_after_evaluate(client):
    client.get("/expertise/evaluate/EXC001")
    resp = client.post("/expertise/outcome", json={"machine_id": "EXC001", "cycle_time_after": 40.0, "successful": True})
    assert resp.status_code == 200
    body = resp.json()
    assert "cell_id" in body
    assert "material_confidence_after" in body


def test_record_outcome_without_evaluation_404(client):
    resp = client.post("/expertise/outcome", json={"machine_id": "NEVER_EVALUATED", "cycle_time_after": 40.0})
    assert resp.status_code == 404


def test_memory_and_statistics(client):
    assert client.get("/expertise/memory").status_code == 200
    assert client.get("/expertise/statistics").status_code == 200


def test_site_map(client):
    resp = client.get("/site/map")
    assert resp.status_code == 200
    body = resp.json()
    assert body["width"] > 0
    assert body["height"] > 0
    assert len(body["cells"]) == body["width"] * body["height"]


def test_site_cell_detail(client):
    resp = client.get("/site/cells/G3")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cell_id"] == "G3"
    assert "resistance_score" in body


def test_site_cell_unknown_404(client):
    resp = client.get("/site/cells/Z9")
    assert resp.status_code == 404


def test_site_ground_estimate_and_energy_forecast(client):
    assert client.get("/site/ground-estimate/G3").status_code == 200
    assert client.get("/site/energy-forecast/G3").status_code == 200
