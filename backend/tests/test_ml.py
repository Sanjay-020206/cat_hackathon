import pandas as pd
import pytest

from app.data_gen.generate_datasets import generate_all
from app.ml import anomaly, eta, machine_health, risk


@pytest.fixture(scope="module")
def datasets():
    return generate_all()


# ---- Model A: anomaly detection ----


def test_anomaly_model_trains_and_predicts(datasets):
    telemetry = datasets["telemetry"]
    model = anomaly.train(telemetry)
    scored = anomaly.predict(model, telemetry)
    assert "anomaly_flag" in scored.columns
    assert "anomaly_score" in scored.columns
    # roughly matches the contamination rate we trained with
    rate = scored["anomaly_flag"].mean()
    assert 0.03 <= rate <= 0.30


def test_anomaly_model_flags_injected_extreme_row(datasets):
    telemetry = datasets["telemetry"]
    model = anomaly.train(telemetry)

    extreme_row = pd.DataFrame(
        [
            {
                "cycle_time": 200.0,
                "idle_time": 90.0,
                "fuel_rate": 25.0,
                "engine_load": 100.0,
                "hydraulic_pressure": 60.0,
                "engine_temp": 130.0,
            }
        ]
    )
    result = anomaly.score_single(model, extreme_row.iloc[0].to_dict())
    assert result["anomaly_flag"] is True


def test_anomaly_model_save_and_load_roundtrip(datasets, tmp_path):
    telemetry = datasets["telemetry"]
    model = anomaly.train(telemetry)
    path = tmp_path / "anomaly.joblib"
    anomaly.save(model, str(path))
    loaded = anomaly.load(str(path))
    scored = anomaly.predict(loaded, telemetry.head(5))
    assert len(scored) == 5


# ---- Model B: task ETA ----


def test_eta_model_trains_and_predicts(datasets):
    task_history = datasets["task_history"]
    model = eta.train(task_history)
    preds = model.predict(task_history[eta.ALL_FEATURES].head(10))
    assert len(preds) == 10
    assert all(p > 0 for p in preds)


def test_eta_model_confidence_in_range(datasets):
    task_history = datasets["task_history"]
    model = eta.train(task_history)
    preds, confidence = model.predict_with_confidence(task_history.head(10))
    assert len(preds) == len(confidence) == 10
    assert all(0.0 <= c <= 1.0 for c in confidence)


def test_eta_model_rain_predicts_longer_than_clear(datasets):
    """Directional correctness: rainy conditions should predict longer duration than
    otherwise-identical clear-weather conditions (spec relationship 1)."""
    task_history = datasets["task_history"]
    model = eta.train(task_history)

    base_row = {
        "task_type": "Earth Excavation",
        "operator_skill": "Intermediate",
        "terrain": "Uneven",
        "machine_age": 5.0,
        "load": 0.6,
        "historical_cycle_time": 50.0,
        "estimated_time": 80.0,
    }
    clear_row = pd.DataFrame([{**base_row, "weather": "Clear"}])
    rain_row = pd.DataFrame([{**base_row, "weather": "Heavy Rain"}])

    pred_clear = model.predict(clear_row)[0]
    pred_rain = model.predict(rain_row)[0]
    assert pred_rain >= pred_clear


def test_eta_model_explanation_returns_contributors(datasets):
    task_history = datasets["task_history"]
    model = eta.train(task_history)
    row = task_history.iloc[0]
    contributions = model.explain(row)
    assert isinstance(contributions, list)
    for c in contributions:
        assert {"factor", "raw_value", "impact_minutes"}.issubset(c.keys())


def test_eta_model_save_and_load_roundtrip(datasets, tmp_path):
    task_history = datasets["task_history"]
    model = eta.train(task_history)
    path = tmp_path / "eta.joblib"
    eta.save(model, str(path))
    loaded = eta.load(str(path))
    preds = loaded.predict(task_history[eta.ALL_FEATURES].head(3))
    assert len(preds) == 3


# ---- Model C: machine health ----


def test_machine_health_normal_for_baseline_values():
    normal_telemetry = pd.DataFrame(
        [
            {"engine_temp": 82, "hydraulic_pressure": 27, "hydraulic_temp": 65, "engine_load": 60}
            for _ in range(10)
        ]
    )
    result = machine_health.assess_machine_health(normal_telemetry)
    assert result["state"] == "Normal"
    assert result["score"] >= 85


def test_machine_health_elevated_for_high_hydraulic_temp_trend():
    rising_temps = [65 + i * 3 for i in range(10)]  # strong rising trend
    telemetry = pd.DataFrame(
        [
            {"engine_temp": 82, "hydraulic_pressure": 27, "hydraulic_temp": t, "engine_load": 60}
            for t in rising_temps
        ]
    )
    result = machine_health.assess_machine_health(telemetry)
    assert result["state"] in ("Watch", "Elevated", "Critical")
    assert result["trends"]["hydraulic_temp"] > 0


def test_machine_health_empty_input_defaults_normal():
    result = machine_health.assess_machine_health(pd.DataFrame(columns=["engine_temp"]))
    assert result["state"] == "Normal"


# ---- Model D: hybrid risk engine ----


def test_risk_engine_low_for_normal_conditions():
    inputs = risk.RiskInputs(
        machine_health_score=95,
        safety_score=96,
        productivity_score=88,
        task_health_score=90,
        cycle_time_deviation_pct=0.02,
        idle_rate_deviation_pct=0.0,
        proximity_events=0,
        seatbelt_violation=False,
        hydraulic_temp_trend=0.0,
        shift_minutes=120,
    )
    result = risk.compute_risk(inputs)
    assert result["risk_level"] == "Low"
    assert result["risk_score"] < 0.2


def test_risk_engine_elevated_for_combined_deterioration_scenario():
    """Mirrors spec section 41 stage 6-7: cycle deviation + proximity events + wet ground +
    machine (hydraulic) trend -> risk should rise into at least the Elevated band."""
    inputs = risk.RiskInputs(
        machine_health_score=80,
        safety_score=71,
        productivity_score=63,
        task_health_score=68,
        cycle_time_deviation_pct=0.23,
        idle_rate_deviation_pct=0.18,
        proximity_events=2,
        seatbelt_violation=False,
        hydraulic_temp_trend=1.2,
        shift_minutes=280,
        ground_condition="Wet",
    )
    result = risk.compute_risk(inputs)
    assert result["risk_level"] in ("Elevated", "High")
    factors = [c["factor"] for c in result["contributors"]]
    assert "cycle_time_deviation" in factors
    assert "proximity_events" in factors


def test_risk_engine_seatbelt_violation_adds_contributor():
    inputs = risk.RiskInputs(
        machine_health_score=90,
        safety_score=85,
        productivity_score=85,
        task_health_score=85,
        cycle_time_deviation_pct=0.0,
        idle_rate_deviation_pct=0.0,
        proximity_events=0,
        seatbelt_violation=True,
        hydraulic_temp_trend=0.0,
        shift_minutes=100,
    )
    result = risk.compute_risk(inputs)
    factors = [c["factor"] for c in result["contributors"]]
    assert "seatbelt_violation" in factors


def test_risk_trend_increasing_decreasing_stable():
    assert risk.compute_trend([0.1, 0.15, 0.22, 0.3]) == "Increasing"
    assert risk.compute_trend([0.4, 0.3, 0.2, 0.1]) == "Decreasing"
    assert risk.compute_trend([0.2, 0.2, 0.21, 0.19]) == "Stable"
    assert risk.compute_trend([]) == "Stable"


def test_risk_trend_matches_scenario_escalation_then_recovery():
    """Spec section 9 example: 12 -> 15 -> 18 -> 27 -> 41 then recovering after intervention."""
    escalating = [0.12, 0.15, 0.18, 0.27, 0.41]
    assert risk.compute_trend(escalating) == "Increasing"

    recovering = escalating + [0.30, 0.19]
    assert risk.compute_trend(recovering) == "Decreasing"
