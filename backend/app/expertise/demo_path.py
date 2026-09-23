"""Deterministic jobsite path for the scripted demo machine (spec section 20's
"Pre-Excavation Intelligence" needs a location to hang off of, and this project has no
real GPS telemetry). The path walks the demo machine from an unmapped approach, through a
moderately-observed corridor, into the grid's synthetic high-resistance hotspot (cell G3)
right as the scripted scenario reaches its risk-escalation stages -- so "approaching a
known difficult area" and "Expert Moment" line up with the existing 10-stage demo
scenario (spec section 41) instead of competing with it.

For random-mode simulation (no scripted stage index), position cycles through the same
path by tick count so the feature still has *something* to show outside the demo script.
"""
from __future__ import annotations

from app.site.grid import cell_id_for

# One (x, y) per STAGES index -- see app/simulator/scenario.py for the stage labels this
# lines up with (index 6 = RISK_ESCALATION, entering the hotspot cell G3).
DEMO_PATH: list[tuple[int, int]] = [
    (2, 2),  # NORMAL
    (3, 2),  # NORMAL
    (3, 3),  # LOAD_INCREASE -- entering the pre-seeded moderately-known corridor
    (4, 3),  # CYCLE_DEVIATION
    (5, 3),  # PROXIMITY_EVENTS
    (5, 2),  # IDLE_INCREASE
    (6, 2),  # RISK_ESCALATION -- hotspot cell (G3), initially unmapped
    (6, 2),  # AI_RECOMMENDATION -- Expert Moment should fire here
    (6, 2),  # OPERATOR_INTERVENTION -- outcome gets recorded here
    (6, 1),  # CONDITIONS_IMPROVE -- moving on
]

_DEPTH_BASE = 1.0
_DEPTH_STEP = 0.15


def position_for_tick(stage_index: int | None, tick: int) -> tuple[int, int, float]:
    if stage_index is not None and 0 <= stage_index < len(DEMO_PATH):
        idx = stage_index
    else:
        idx = tick % len(DEMO_PATH)

    x, y = DEMO_PATH[idx]
    depth = round(_DEPTH_BASE + idx * _DEPTH_STEP, 2)
    return x, y, depth


def cell_id_for_tick(stage_index: int | None, tick: int) -> str:
    x, y, _ = position_for_tick(stage_index, tick)
    return cell_id_for(x, y)
