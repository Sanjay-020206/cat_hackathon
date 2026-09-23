"""Phase 9: adaptive training recommendation + intervention + measured improvement loop
(spec section 19: Behavior anomaly -> skill gap -> training -> intervention -> measure)."""
import pandas as pd
from fastapi.testclient import TestClient

from app.agents.training_agent import recommend, simulate_intervention
from app.main import app

CATALOG = pd.DataFrame(
    [
        {"training_id": "TRN001", "skill": "cycle_efficiency", "title": "Efficient Excavation Positioning", "duration": 4, "difficulty": "Beginner", "resource": "x"},
        {"training_id": "TRN006", "skill": "proximity_awareness", "title": "Proximity Hazard Awareness & Response", "duration": 7, "difficulty": "Advanced", "resource": "x"},
    ]
)


def test_recurring_cycle_time_anomaly_recommends_cycle_efficiency_training():
    """A recurring cycle-time anomaly (spec section 19 example) should recommend the
    cycle-efficiency module, matching the spec's own example title."""
    rec = recommend(
        CATALOG,
        cycle_time_deviation_pct=0.20,
        idle_rate_deviation_pct=0.05,
        proximity_events=0,
        ground_condition="Dry",
        seatbelt_violation=False,
    )
    assert rec is not None
    assert rec["training_id"] == "TRN001"
    assert rec["title"] == "Efficient Excavation Positioning"


def test_proximity_events_take_priority_over_cycle_time():
    rec = recommend(
        CATALOG,
        cycle_time_deviation_pct=0.20,
        idle_rate_deviation_pct=0.05,
        proximity_events=2,
        ground_condition="Dry",
        seatbelt_violation=False,
    )
    assert rec is not None
    assert rec["training_id"] == "TRN006"


def test_no_recommendation_when_no_anomaly():
    rec = recommend(
        CATALOG,
        cycle_time_deviation_pct=0.02,
        idle_rate_deviation_pct=0.02,
        proximity_events=0,
        ground_condition="Dry",
        seatbelt_violation=False,
    )
    assert rec is None


def test_simulate_intervention_matches_spec_example_direction():
    """Spec section 19 example: 51.4 sec/cycle -> 45.8 sec/cycle, ~10.9% improvement."""
    result = simulate_intervention(51.4, "cycle_efficiency")
    assert result["before"] == 51.4
    assert result["after"] < result["before"]
    assert 9.0 <= result["improvement_pct"] <= 12.0


def test_simulate_intervention_is_deterministic():
    a = simulate_intervention(50.0, "idle_reduction")
    b = simulate_intervention(50.0, "idle_reduction")
    assert a == b


def test_training_recommendation_endpoint_and_completion_loop():
    with TestClient(app) as client:
        operators = client.get("/operators").json()
        operator_id = operators[0]["operator_id"]

        resp = client.get(f"/training/recommendation/{operator_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["operator_id"] == operator_id
        # recommendation may be None if this operator has no current anomaly -- that's valid

        complete_resp = client.post(
            "/training/complete",
            json={
                "operator_id": operator_id,
                "training_id": "TRN001",
                "skill_gap": "cycle_efficiency",
                "before_cycle_time": 51.4,
            },
        )
        assert complete_resp.status_code == 200
        record = complete_resp.json()
        assert record["before"] == 51.4
        assert record["after"] < record["before"]

        history_resp = client.get(f"/training/history/{operator_id}")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert len(history) == 1
        assert history[0]["training_id"] == "TRN001"


def test_training_recommendation_unknown_operator_404():
    with TestClient(app) as client:
        resp = client.get("/training/recommendation/NOT_A_REAL_OPERATOR")
        assert resp.status_code == 404
