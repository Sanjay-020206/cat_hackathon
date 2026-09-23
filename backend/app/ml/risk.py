"""Model D -- Operational Risk (hybrid: ML anomaly signals + rule-based domain constraints
+ trend analysis + operator baseline). Deliberately not a single opaque model -- safety
recommendations must trace back to explainable rule + statistical contributions
(spec sections 9, 32).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskInputs:
    machine_health_score: float  # 0-100
    safety_score: float  # 0-100
    productivity_score: float  # 0-100
    task_health_score: float  # 0-100
    cycle_time_deviation_pct: float  # operator's current vs. baseline cycle time, e.g. 0.23 = +23%
    idle_rate_deviation_pct: float
    proximity_events: int
    seatbelt_violation: bool
    hydraulic_temp_trend: float  # slope, > 0 rising
    shift_minutes: int
    ground_condition: str = "Dry"


RULE_WEIGHTS = {
    "cycle_time_deviation": 0.25,
    "idle_deviation": 0.15,
    "proximity_events": 0.25,
    "seatbelt_violation": 0.15,
    "hydraulic_temp_trend": 0.15,
    "long_shift": 0.05,
}


def compute_risk(inputs: RiskInputs) -> dict:
    contributors = []
    risk_score = 0.0

    # Base risk from the three composite health scores (inverse -- lower health = higher risk)
    composite_health = (inputs.machine_health_score + inputs.safety_score + inputs.productivity_score) / 3.0
    base_risk = max(0.0, (100.0 - composite_health) / 100.0) * 0.35
    risk_score += base_risk

    if inputs.cycle_time_deviation_pct > 0.1:
        contrib = min(0.3, inputs.cycle_time_deviation_pct) * RULE_WEIGHTS["cycle_time_deviation"]
        risk_score += contrib
        contributors.append({"factor": "cycle_time_deviation", "value": round(inputs.cycle_time_deviation_pct, 2), "importance": 0.30})

    if inputs.idle_rate_deviation_pct > 0.1:
        contrib = min(0.3, inputs.idle_rate_deviation_pct) * RULE_WEIGHTS["idle_deviation"]
        risk_score += contrib
        contributors.append({"factor": "idle_rate_deviation", "value": round(inputs.idle_rate_deviation_pct, 2), "importance": 0.15})

    if inputs.proximity_events > 0:
        contrib = min(1.0, inputs.proximity_events / 3.0) * RULE_WEIGHTS["proximity_events"]
        risk_score += contrib
        contributors.append({"factor": "proximity_events", "value": inputs.proximity_events, "importance": 0.25})

    if inputs.seatbelt_violation:
        risk_score += RULE_WEIGHTS["seatbelt_violation"]
        contributors.append({"factor": "seatbelt_violation", "value": True, "importance": 0.15})

    if inputs.hydraulic_temp_trend > 0:
        contrib = min(1.0, inputs.hydraulic_temp_trend / 2.0) * RULE_WEIGHTS["hydraulic_temp_trend"]
        risk_score += contrib
        contributors.append({"factor": "hydraulic_temperature", "value": "increasing", "importance": 0.20})

    if inputs.shift_minutes > 360:  # > 6h
        over = (inputs.shift_minutes - 360) / 240.0
        contrib = min(1.0, over) * RULE_WEIGHTS["long_shift"]
        risk_score += contrib
        contributors.append({"factor": "long_shift_duration", "value": inputs.shift_minutes, "importance": 0.10})

    if inputs.ground_condition in ("Wet", "Waterlogged"):
        risk_score += 0.05
        contributors.append({"factor": "wet_ground_condition", "value": inputs.ground_condition, "importance": 0.10})

    risk_score = max(0.0, min(1.0, risk_score))
    contributors.sort(key=lambda c: -c["importance"])

    if risk_score < 0.2:
        level = "Low"
    elif risk_score < 0.4:
        level = "Moderate"
    elif risk_score < 0.65:
        level = "Elevated"
    else:
        level = "High"

    return {
        "risk_score": round(risk_score, 3),
        "risk_level": level,
        "contributors": contributors,
    }


def compute_trend(risk_score_history: list[float], window: int = 3) -> str:
    """Classifies the trend of a risk-score time series as Increasing / Decreasing / Stable."""
    if len(risk_score_history) < 2:
        return "Stable"

    recent = risk_score_history[-window:]
    if len(recent) < 2:
        return "Stable"

    deltas = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    avg_delta = sum(deltas) / len(deltas)

    if avg_delta > 0.02:
        return "Increasing"
    if avg_delta < -0.02:
        return "Decreasing"
    return "Stable"
