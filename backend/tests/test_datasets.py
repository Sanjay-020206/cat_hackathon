import numpy as np
import pandas as pd

from app.data_gen.generate_datasets import generate_all
from app.simulator.scenario import STAGES, stage_to_telemetry
from app.simulator.telemetry_simulator import TelemetrySimulator

EXPECTED_COLUMNS = {
    "machines": {"machine_id", "model", "machine_type", "age_years", "engine_hours", "maintenance_status"},
    "operators": {
        "operator_id",
        "skill_level",
        "experience_months",
        "certifications",
        "historical_cycle_time",
        "historical_idle_rate",
        "historical_safety_events",
    },
    "telemetry": {
        "timestamp",
        "machine_id",
        "operator_id",
        "engine_rpm",
        "engine_temp",
        "hydraulic_pressure",
        "hydraulic_temp",
        "fuel_level",
        "fuel_rate",
        "engine_load",
        "speed",
        "cycle_time",
        "idle_time",
        "load_cycles",
        "seatbelt_status",
    },
    "tasks": {
        "task_id",
        "machine_id",
        "operator_id",
        "task_type",
        "material",
        "target_quantity",
        "deadline",
        "zone",
        "original_estimated_time",
    },
    "safety_events": {
        "event_id",
        "timestamp",
        "machine_id",
        "operator_id",
        "event_type",
        "severity",
        "distance",
        "duration",
        "zone",
    },
    "environment": {
        "timestamp",
        "site_id",
        "weather",
        "temperature",
        "humidity",
        "visibility",
        "rainfall",
        "terrain",
        "ground_condition",
        "dust_level",
    },
    "task_history": {
        "task_id",
        "task_type",
        "weather",
        "operator_skill",
        "machine_age",
        "terrain",
        "load",
        "historical_cycle_time",
        "estimated_time",
        "actual_time",
    },
    "training": {"training_id", "skill", "title", "duration", "difficulty", "resource"},
}


def test_all_datasets_generated_with_expected_columns():
    datasets = generate_all()
    assert set(datasets.keys()) == set(EXPECTED_COLUMNS.keys())
    for name, df in datasets.items():
        assert set(EXPECTED_COLUMNS[name]).issubset(set(df.columns)), f"{name} missing expected columns"
        assert len(df) > 0, f"{name} is empty"


def test_no_nan_in_core_datasets():
    datasets = generate_all()
    for name in ["machines", "operators", "telemetry", "tasks", "safety_events", "environment"]:
        df = datasets[name]
        assert not df.isnull().values.any(), f"{name} contains NaN values"


def test_deterministic_seeded_generation():
    a = generate_all(seed=42)
    b = generate_all(seed=42)
    pd.testing.assert_frame_equal(a["telemetry"], b["telemetry"])


def test_rain_increases_cycle_time_relationship():
    """Relationship 1: rain -> terrain difficulty up -> cycle time up."""
    datasets = generate_all()
    hist = datasets["task_history"]
    rain_mean = hist.loc[hist["weather"].isin(["Rain", "Heavy Rain"]), "actual_time"].mean()
    clear_mean = hist.loc[hist["weather"] == "Clear", "actual_time"].mean()
    assert rain_mean > clear_mean


def test_skill_reduces_cycle_time_relationship():
    """Relationship 5: skill up -> cycle time down."""
    datasets = generate_all()
    ops = datasets["operators"]
    novice_cycle = ops.loc[ops["skill_level"] == "Novice", "historical_cycle_time"].mean()
    expert_cycle = ops.loc[ops["skill_level"] == "Expert", "historical_cycle_time"].mean()
    assert np.isnan(novice_cycle) or np.isnan(expert_cycle) or expert_cycle <= novice_cycle


def test_machine_age_increases_maintenance_risk_proxy():
    """Relationship 4: machine age up -> maintenance risk slightly up (proxied by status ordering)."""
    datasets = generate_all()
    machines = datasets["machines"]
    status_rank = {"Normal": 0, "Watch": 1, "Critical": 2}
    machines = machines.copy()
    machines["risk_rank"] = machines["maintenance_status"].map(status_rank)
    corr = machines["age_years"].corr(machines["risk_rank"])
    assert corr > 0


def test_abnormal_rate_within_expected_band():
    """Spec section 25: ~80-90% normal / 10-20% abnormal scenarios."""
    datasets = generate_all()
    telemetry = datasets["telemetry"]
    assert "abnormal_scenario" in telemetry.columns
    rate = telemetry["abnormal_scenario"].mean()
    assert 0.08 <= rate <= 0.25


def test_scenario_has_ten_stages_matching_spec():
    assert len(STAGES) == 10
    labels = [s.label for s in STAGES]
    assert "PROXIMITY_EVENTS" in labels
    assert "RISK_ESCALATION" in labels
    assert "AI_RECOMMENDATION" in labels
    assert "CONDITIONS_IMPROVE" in labels


def test_scenario_risk_indicators_rise_then_recover():
    readings = [stage_to_telemetry(s, "2026-09-23T09:00:00") for s in STAGES]
    cycle_times = [r["cycle_time"] for r in readings]
    idle_times = [r["idle_time"] for r in readings]

    peak_idx = idle_times.index(max(idle_times))
    assert peak_idx not in (0, len(idle_times) - 1)
    assert idle_times[-1] < max(idle_times)
    assert cycle_times[-1] < max(cycle_times)


def test_scripted_simulator_matches_scenario_length_then_holds():
    sim = TelemetrySimulator(mode="scripted", seed=1)
    readings = [sim.next_reading() for _ in range(len(STAGES) + 3)]
    assert readings[0]["stage_label"] == "NORMAL"
    assert readings[len(STAGES) - 1]["stage_label"] == "CONDITIONS_IMPROVE"
    # holds at final stage once exhausted
    assert readings[-1]["stage_label"] == "CONDITIONS_IMPROVE"


def test_random_simulator_produces_valid_contract_fields():
    sim = TelemetrySimulator(mode="random", seed=3)
    reading = sim.next_reading()
    required = {
        "timestamp",
        "machine_id",
        "operator_id",
        "engine_rpm",
        "engine_temp",
        "hydraulic_pressure",
        "hydraulic_temp",
        "fuel_level",
        "fuel_rate",
        "engine_load",
        "speed",
        "cycle_time",
        "idle_time",
        "load_cycles",
        "seatbelt_status",
    }
    assert required.issubset(reading.keys())
