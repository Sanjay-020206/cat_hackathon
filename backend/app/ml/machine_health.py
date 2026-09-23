"""Model C -- Machine Health.

Rolling mean/std + baseline-deviation + trend-slope over recent telemetry for a machine,
classified into Normal / Watch / Elevated / Critical. No opaque black-box classification --
combines simple statistical signals so the state is always explainable (spec section 11/32).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

HEALTH_FIELDS = ["engine_temp", "hydraulic_pressure", "hydraulic_temp", "engine_load"]

# Rule-of-thumb "safe operating" reference bands used to compute deviation, informed by the
# synthetic dataset's normal-operation ranges.
BASELINES = {
    "engine_temp": {"mean": 82.0, "std": 6.0},
    "hydraulic_pressure": {"mean": 27.0, "std": 4.0},
    "hydraulic_temp": {"mean": 65.0, "std": 8.0},
    "engine_load": {"mean": 60.0, "std": 15.0},
}


def _trend_slope(values: pd.Series) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values.to_numpy(), 1)
    return float(slope)


def assess_machine_health(recent_telemetry: pd.DataFrame) -> dict:
    """`recent_telemetry` should be time-ordered rows (oldest first) for a single machine."""
    if recent_telemetry.empty:
        return {"state": "Normal", "score": 100.0, "deviations": {}, "trends": {}}

    deviations: dict[str, float] = {}
    trends: dict[str, float] = {}
    penalty = 0.0

    for field in HEALTH_FIELDS:
        series = recent_telemetry[field]
        mean = float(series.mean())
        baseline = BASELINES[field]
        deviation = (mean - baseline["mean"]) / baseline["std"]
        deviations[field] = round(deviation, 2)

        slope = _trend_slope(series)
        trends[field] = round(slope, 3)

        # penalize deviation beyond ~1 std, and rising trends compound the concern
        if abs(deviation) > 1.0:
            penalty += min(30.0, (abs(deviation) - 1.0) * 15)
        if slope > 0 and field in ("hydraulic_temp", "engine_temp"):
            penalty += min(15.0, slope * 5)

    score = max(0.0, min(100.0, 100.0 - penalty))
    if score >= 85:
        state = "Normal"
    elif score >= 65:
        state = "Watch"
    elif score >= 40:
        state = "Elevated"
    else:
        state = "Critical"

    return {"state": state, "score": round(score, 1), "deviations": deviations, "trends": trends}
