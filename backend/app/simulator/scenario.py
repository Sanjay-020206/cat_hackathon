"""
Scripted 10-stage demo scenario (spec section 41), reproducible deterministically.

Each stage is a dict of telemetry/environment/safety deltas applied on top of a normal
baseline for a fixed machine/operator pair, so the same scenario always plays out the
same way for a demo, while still going through the exact same internal data contract
(spec section 49) used for live/random simulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEMO_MACHINE_ID = "EXC001"
DEMO_OPERATOR_ID = "OP1001"

BASELINE_CYCLE_TIME = 44.0
BASELINE_IDLE_TIME = 8.0
BASELINE_FUEL_RATE = 4.2
BASELINE_HYDRAULIC_TEMP = 62.0
BASELINE_ENGINE_TEMP = 80.0
BASELINE_ENGINE_LOAD = 55.0
BASELINE_SPEED = 4.0


@dataclass
class ScenarioStage:
    label: str
    time_offset_min: int
    cycle_time_delta: float = 0.0
    idle_time_delta: float = 0.0
    fuel_rate_delta: float = 0.0
    hydraulic_temp_delta: float = 0.0
    engine_load_delta: float = 0.0
    speed_delta: float = 0.0
    proximity_events: int = 0
    seatbelt_status: str = "Fastened"
    weather: str = "Clear"
    ground_condition: str = "Dry"
    note: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


STAGES: list[ScenarioStage] = [
    ScenarioStage(
        label="NORMAL",
        time_offset_min=0,
        note="Stable operation: machine health 94%, safety 96%, productivity 88%, risk low.",
    ),
    ScenarioStage(
        label="NORMAL",
        time_offset_min=5,
        note="Continued stable operation.",
    ),
    ScenarioStage(
        label="LOAD_INCREASE",
        time_offset_min=10,
        engine_load_delta=18,
        fuel_rate_delta=1.2,
        hydraulic_temp_delta=3,
        note="Rain begins; heavier load handling starts to show in hydraulics/fuel.",
        weather="Rain",
        ground_condition="Wet",
    ),
    ScenarioStage(
        label="CYCLE_DEVIATION",
        time_offset_min=15,
        cycle_time_delta=10,
        idle_time_delta=3,
        weather="Rain",
        ground_condition="Wet",
        note="Terrain difficulty rising: cycle time and idle time both increase.",
    ),
    ScenarioStage(
        label="PROXIMITY_EVENTS",
        time_offset_min=20,
        cycle_time_delta=12,
        idle_time_delta=5,
        proximity_events=2,
        weather="Rain",
        ground_condition="Wet",
        note="Two proximity events recorded under wet-ground conditions.",
    ),
    ScenarioStage(
        label="IDLE_INCREASE",
        time_offset_min=25,
        cycle_time_delta=11,
        idle_time_delta=13,
        proximity_events=2,
        weather="Rain",
        ground_condition="Wet",
        note="Idle rate climbs further; operator behavior deviating from baseline.",
    ),
    ScenarioStage(
        label="RISK_ESCALATION",
        time_offset_min=30,
        cycle_time_delta=10,
        idle_time_delta=13,
        hydraulic_temp_delta=9,
        proximity_events=2,
        weather="Rain",
        ground_condition="Wet",
        note="Hydraulic temperature trending up; combined deterioration scenario active.",
    ),
    ScenarioStage(
        label="AI_RECOMMENDATION",
        time_offset_min=35,
        cycle_time_delta=10,
        idle_time_delta=13,
        hydraulic_temp_delta=9,
        proximity_events=2,
        weather="Rain",
        ground_condition="Wet",
        note="Context engine flags increasing risk; Next Best Action generated: reposition before continuing.",
    ),
    ScenarioStage(
        label="OPERATOR_INTERVENTION",
        time_offset_min=40,
        cycle_time_delta=4,
        idle_time_delta=6,
        hydraulic_temp_delta=4,
        proximity_events=0,
        weather="Rain",
        ground_condition="Wet",
        note="Operator repositions and reassesses the operating zone as recommended.",
    ),
    ScenarioStage(
        label="CONDITIONS_IMPROVE",
        time_offset_min=45,
        cycle_time_delta=-2,
        idle_time_delta=-1,
        hydraulic_temp_delta=1,
        proximity_events=0,
        weather="Cloudy",
        ground_condition="Damp",
        note="Metrics recover: cycle time, idle and risk all trend back down.",
    ),
]


def stage_to_telemetry(stage: ScenarioStage, timestamp: str) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "machine_id": DEMO_MACHINE_ID,
        "operator_id": DEMO_OPERATOR_ID,
        "engine_rpm": 1650,
        "engine_temp": round(BASELINE_ENGINE_TEMP + stage.engine_load_delta * 0.15, 1),
        "hydraulic_pressure": 28.0,
        "hydraulic_temp": round(BASELINE_HYDRAULIC_TEMP + stage.hydraulic_temp_delta, 1),
        "fuel_level": 64.0,
        "fuel_rate": round(BASELINE_FUEL_RATE + stage.fuel_rate_delta, 2),
        "engine_load": round(min(100.0, BASELINE_ENGINE_LOAD + stage.engine_load_delta), 1),
        "speed": round(max(0.5, BASELINE_SPEED + stage.speed_delta), 1),
        "cycle_time": round(BASELINE_CYCLE_TIME + stage.cycle_time_delta, 1),
        "idle_time": round(max(0.0, BASELINE_IDLE_TIME + stage.idle_time_delta), 1),
        "load_cycles": 10,
        "seatbelt_status": stage.seatbelt_status,
        "proximity_alert": stage.proximity_events > 0,
        "proximity_events": stage.proximity_events,
        "stage_label": stage.label,
        "note": stage.note,
        "weather": stage.weather,
        "ground_condition": stage.ground_condition,
    }
