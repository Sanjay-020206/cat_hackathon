import pandas as pd
import pytest

from app.context.context_engine import ContextEngine, ContextFusionInput
from app.simulator.scenario import DEMO_MACHINE_ID, DEMO_OPERATOR_ID, STAGES, stage_to_telemetry


def _recent_window(readings: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "engine_temp": r["engine_temp"],
                "hydraulic_pressure": r["hydraulic_pressure"],
                "hydraulic_temp": r["hydraulic_temp"],
                "engine_load": r["engine_load"],
            }
            for r in readings
        ]
    )


def _fusion_input_for_stage(stage_idx: int, readings: list[dict], safety_event_count: int) -> ContextFusionInput:
    reading = readings[stage_idx]
    window = readings[: stage_idx + 1]
    return ContextFusionInput(
        machine_id=DEMO_MACHINE_ID,
        operator_id=DEMO_OPERATOR_ID,
        cycle_time=reading["cycle_time"],
        idle_time=reading["idle_time"],
        speed=reading["speed"],
        seatbelt_status=reading["seatbelt_status"],
        proximity_events=reading["proximity_events"],
        ground_condition=reading["ground_condition"],
        shift_minutes=stage_idx * 5,
        baseline_cycle_time=44.0,
        baseline_idle_time=8.0,
        recent_telemetry=_recent_window(window),
        recent_safety_event_count=safety_event_count,
        weather=reading["weather"],
    )


@pytest.fixture
def scenario_readings():
    return [stage_to_telemetry(s, f"2026-09-23T09:{i*5:02d}:00") for i, s in enumerate(STAGES)]


def test_context_engine_produces_expected_shape(scenario_readings):
    engine = ContextEngine()
    inp = _fusion_input_for_stage(0, scenario_readings, safety_event_count=0)
    context = engine.process(inp)

    required_keys = {
        "machine_id",
        "operator_id",
        "risk_level",
        "risk_score",
        "risk_trend",
        "machine_health",
        "safety_score",
        "productivity_score",
        "task_health",
        "contributors",
        "priority_domain",
    }
    assert required_keys.issubset(context.keys())


def test_context_engine_risk_low_at_normal_stage(scenario_readings):
    engine = ContextEngine()
    inp = _fusion_input_for_stage(0, scenario_readings, safety_event_count=0)
    context = engine.process(inp)
    assert context["risk_level"] in ("Low", "Moderate")


def test_context_engine_risk_trend_increases_through_deterioration(scenario_readings):
    """Replays scenario stages 0 (NORMAL) through 6 (RISK_ESCALATION) and expects the
    engine to detect an increasing risk trend, matching spec section 41 stages 1-6."""
    engine = ContextEngine()
    safety_counts = [0, 0, 0, 0, 2, 2, 2]  # proximity events recorded from stage 4 onward

    context = None
    for idx in range(7):
        inp = _fusion_input_for_stage(idx, scenario_readings, safety_event_count=safety_counts[idx])
        context = engine.process(inp)

    assert context is not None
    assert context["risk_trend"] == "Increasing"
    assert context["risk_level"] in ("Elevated", "High", "Moderate")


def test_context_engine_contributors_include_expected_factors_at_risk_escalation(scenario_readings):
    """Spec section 41 stage 7 / section 50 example: cycle_time_deviation, proximity_events
    and hydraulic_temperature should appear among the contributors at the escalation stage."""
    engine = ContextEngine()
    safety_counts = [0, 0, 0, 0, 2, 2, 2]

    context = None
    for idx in range(7):
        inp = _fusion_input_for_stage(idx, scenario_readings, safety_event_count=safety_counts[idx])
        context = engine.process(inp)

    assert context is not None
    factors = {c["factor"] for c in context["contributors"]}
    assert "cycle_time_deviation" in factors
    assert "proximity_events" in factors
    assert "hydraulic_temperature" in factors


def test_context_engine_risk_recovers_after_intervention(scenario_readings):
    """Spec section 41 stages 8-9: after operator intervention, conditions improve and risk
    should trend back down."""
    engine = ContextEngine()
    safety_counts = [0, 0, 0, 0, 2, 2, 2, 2, 0, 0]

    contexts = []
    for idx in range(len(STAGES)):
        inp = _fusion_input_for_stage(idx, scenario_readings, safety_event_count=safety_counts[idx])
        contexts.append(engine.process(inp))

    peak_score = max(c["risk_score"] for c in contexts)
    final_score = contexts[-1]["risk_score"]
    assert final_score < peak_score
    assert contexts[-1]["risk_trend"] == "Decreasing"


def test_context_engine_priority_domain_is_one_of_expected(scenario_readings):
    engine = ContextEngine()
    inp = _fusion_input_for_stage(6, scenario_readings, safety_event_count=2)
    context = engine.process(inp)
    assert context["priority_domain"] in ("safety", "machine", "productivity")


def test_context_engine_reset_clears_history(scenario_readings):
    engine = ContextEngine()
    inp = _fusion_input_for_stage(0, scenario_readings, safety_event_count=0)
    engine.process(inp)
    assert len(engine.get_risk_history(inp.machine_id)) == 1
    engine.reset(inp.machine_id)
    assert len(engine.get_risk_history(inp.machine_id)) == 0
