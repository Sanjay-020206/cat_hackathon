"""Safety Agent: seatbelt, proximity, safety-event, environment and behavior signals ->
a structured safety assessment (spec section 10.2 / 33)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyAgentInput:
    seatbelt_status: str
    proximity_events: int
    recent_safety_event_count: int
    speed: float
    shift_minutes: int
    weather: str
    ground_condition: str


def assess(inputs: SafetyAgentInput) -> dict:
    reasons: list[str] = []
    score = 100.0

    if inputs.seatbelt_status != "Fastened":
        score -= 25
        reasons.append("Seatbelt not fastened.")

    if inputs.proximity_events > 0:
        score -= min(30, inputs.proximity_events * 12)
        reasons.append(f"{inputs.proximity_events} proximity event(s) detected.")

    if inputs.recent_safety_event_count > 1:
        score -= min(20, (inputs.recent_safety_event_count - 1) * 8)
        reasons.append(f"{inputs.recent_safety_event_count} safety events this shift.")

    if inputs.speed > 6.0:
        score -= 10
        reasons.append("Operating speed above normal range.")

    if inputs.ground_condition in ("Wet", "Waterlogged"):
        score -= 8
        reasons.append(f"Ground condition is {inputs.ground_condition.lower()}.")

    if inputs.shift_minutes > 360:
        score -= 5
        reasons.append("Extended shift duration may increase fatigue.")

    score = max(0.0, min(100.0, score))
    if score >= 85:
        state = "Normal"
    elif score >= 65:
        state = "Elevated"
    else:
        state = "Critical"

    return {"safety_score": round(score, 1), "safety_state": state, "reasons": reasons}
