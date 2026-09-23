"""Training Agent: operator behavior, skill level, training history and detected anomalies
-> a training recommendation (spec section 19 / 33).

Phase 4 provides the skill-gap detection used by the Context Engine's priority summary.
Phase 9 extends this with the full recommend -> intervene -> measure-improvement loop.
"""
from __future__ import annotations

import pandas as pd

SKILL_GAP_TRAINING_MAP = {
    "cycle_efficiency": "TRN001",
    "idle_reduction": "TRN002",
    "safe_zone_awareness": "TRN003",
    "wet_terrain_handling": "TRN004",
    "fuel_efficiency": "TRN005",
    "proximity_awareness": "TRN006",
}


def detect_skill_gap(
    cycle_time_deviation_pct: float,
    idle_rate_deviation_pct: float,
    proximity_events: int,
    ground_condition: str,
    seatbelt_violation: bool,
) -> str | None:
    """Returns a skill-gap key (matching SKILL_GAP_TRAINING_MAP), or None if no clear gap."""
    if proximity_events >= 2:
        return "proximity_awareness"
    if seatbelt_violation:
        return "safe_zone_awareness"
    if ground_condition in ("Wet", "Waterlogged") and cycle_time_deviation_pct > 0.1:
        return "wet_terrain_handling"
    if cycle_time_deviation_pct > 0.15:
        return "cycle_efficiency"
    if idle_rate_deviation_pct > 0.15:
        return "idle_reduction"
    return None


def recommend(
    training_catalog: pd.DataFrame,
    cycle_time_deviation_pct: float,
    idle_rate_deviation_pct: float,
    proximity_events: int,
    ground_condition: str,
    seatbelt_violation: bool,
) -> dict | None:
    gap = detect_skill_gap(
        cycle_time_deviation_pct, idle_rate_deviation_pct, proximity_events, ground_condition, seatbelt_violation
    )
    if gap is None:
        return None

    training_id = SKILL_GAP_TRAINING_MAP[gap]
    row = training_catalog.loc[training_catalog["training_id"] == training_id]
    if row.empty:
        return None

    row = row.iloc[0]
    return {
        "skill_gap": gap,
        "training_id": training_id,
        "title": row["title"],
        "duration_minutes": int(row["duration"]),
        "reason": _reason_for_gap(gap, cycle_time_deviation_pct, idle_rate_deviation_pct, proximity_events),
    }


def _reason_for_gap(gap: str, cycle_dev: float, idle_dev: float, proximity_events: int) -> str:
    if gap == "proximity_awareness":
        return f"{proximity_events} proximity events detected this shift."
    if gap == "safe_zone_awareness":
        return "Seatbelt violation detected."
    if gap == "wet_terrain_handling":
        return f"Cycle time is {round(cycle_dev * 100)}% above baseline under wet ground conditions."
    if gap == "cycle_efficiency":
        return f"Cycle time consistently exceeds baseline by {round(cycle_dev * 100)}%."
    if gap == "idle_reduction":
        return f"Idle time consistently exceeds baseline by {round(idle_dev * 100)}%."
    return "Recurring behavior pattern detected."
