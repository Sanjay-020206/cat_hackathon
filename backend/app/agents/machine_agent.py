"""Machine Agent: wraps Model C (machine_health) with additional context (fuel, maintenance
status) into a structured machine assessment (spec section 11 / 33)."""
from __future__ import annotations

import pandas as pd

from app.ml.machine_health import assess_machine_health


def assess(recent_telemetry: pd.DataFrame, maintenance_status: str = "Normal") -> dict:
    health = assess_machine_health(recent_telemetry)
    reasons: list[str] = []

    for field, dev in health["deviations"].items():
        if abs(dev) > 1.0:
            direction = "above" if dev > 0 else "below"
            reasons.append(f"{field.replace('_', ' ')} is {direction} baseline range.")

    for field, slope in health["trends"].items():
        if slope > 0.3:
            reasons.append(f"{field.replace('_', ' ')} is trending upward.")

    if maintenance_status != "Normal":
        reasons.append(f"Maintenance status flagged as {maintenance_status}.")

    return {
        "machine_health_score": health["score"],
        "machine_health_state": health["state"],
        "deviations": health["deviations"],
        "trends": health["trends"],
        "reasons": reasons,
    }
