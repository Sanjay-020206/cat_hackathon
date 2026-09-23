"""Operating Situation representation + Situation Recognition (spec sections 5-6).

`OperatingSituation` is the normalized snapshot of "what is the machine doing right now"
that the rest of the Expertise Engine reasons over. This machine/dataset does not carry
real sensors for several of the fields the spec asks for (material resistance,
penetration rate, cylinder force, vibration, bucket/boom/stick angle, GPS position) --
those are clearly-labeled *synthetic derivations* from the telemetry fields that ARE real
in this project (hydraulic pressure, engine load, cycle time, fuel rate, speed), never
presented as measured sensor data. Real fields are reused as-is wherever they exist.

Situation Recognition then classifies that snapshot into one of a small set of
operating states, using configurable thresholds (no magic numbers scattered through the
codebase -- see `SITUATION_THRESHOLDS`).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

MACHINE_TYPE_TO_ATTACHMENT = {
    "Excavator": "bucket",
    "Wheel Loader": "bucket",
    "Dozer": "blade",
}

SKILL_TO_EXPERIENCE_LEVEL = {
    "Novice": "novice",
    "Intermediate": "intermediate",
    "Skilled": "expert",
    "Expert": "expert",
}

# Baselines used only to derive the synthetic fields below from real telemetry.
_BASELINE_CYCLE_TIME = 44.0
_BASELINE_HYDRAULIC_PRESSURE = 28.0
_BASELINE_ENGINE_LOAD = 55.0


@dataclass
class OperatingSituation:
    machine_id: str
    machine_model: str
    attachment_type: str
    task_type: str

    # Real telemetry fields.
    hydraulic_pressure: float
    engine_load: float
    rpm: int
    cycle_time: float
    fuel_rate: float
    machine_speed: float

    # Synthetic derivations (SIM/DERIVED) -- documented, never claimed as real sensors.
    material_resistance: float  # 0-1, derived from hydraulic pressure + engine load + cycle deviation
    penetration_rate: float  # 0-1, inversely related to resistance
    hydraulic_pressure_change: float  # delta vs previous reading, 0 if unknown
    cylinder_force: float  # synthetic scaling of hydraulic pressure
    engine_load_change: float
    bucket_angle: float
    boom_angle: float
    stick_angle: float
    vibration_level: float  # 0-1, synthetic proxy (no accelerometer telemetry exists)

    energy_per_cycle: float  # from app.expertise.energy (shared with Site/Ground layer)

    position_x: int
    position_y: int
    depth: float

    task_progress: float
    operator_experience_level: str

    timestamp: str

    is_synthetic: dict[str, bool] = field(
        default_factory=lambda: {
            "material_resistance": True,
            "penetration_rate": True,
            "cylinder_force": True,
            "bucket_angle": True,
            "boom_angle": True,
            "stick_angle": True,
            "vibration_level": True,
            "position": True,
            "energy_per_cycle": True,
        }
    )


def _deterministic_unit(*parts: str) -> float:
    """Deterministic pseudo-random value in [0, 1] from a hash of the given parts -- used
    only for cosmetic synthetic fields (bucket/boom/stick angle) that situation recognition
    does not depend on, so the same reading always produces the same demo visuals."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def derive_operating_situation(
    reading: dict,
    machine_model: str,
    machine_type: str,
    task_type: str = "Earth Excavation",
    operator_skill: str = "Intermediate",
    previous_reading: dict | None = None,
    position: tuple[int, int, float] | None = None,
    task_progress: float = 0.5,
) -> OperatingSituation:
    from app.expertise.energy import estimate_energy_per_cycle

    hydraulic_pressure = float(reading["hydraulic_pressure"])
    engine_load = float(reading["engine_load"])
    cycle_time = float(reading["cycle_time"])

    cycle_dev = max(0.0, (cycle_time - _BASELINE_CYCLE_TIME) / _BASELINE_CYCLE_TIME)
    pressure_dev = max(0.0, (hydraulic_pressure - _BASELINE_HYDRAULIC_PRESSURE) / _BASELINE_HYDRAULIC_PRESSURE)
    load_dev = max(0.0, (engine_load - _BASELINE_ENGINE_LOAD) / _BASELINE_ENGINE_LOAD)

    material_resistance = max(0.0, min(1.0, 0.45 * pressure_dev + 0.35 * load_dev + 0.20 * cycle_dev))
    penetration_rate = max(0.05, min(1.0, 1.0 - material_resistance * 0.8))
    vibration_level = max(0.0, min(1.0, 0.6 * material_resistance + 0.4 * load_dev))
    cylinder_force = round(hydraulic_pressure * 3.1, 1)

    hydraulic_pressure_change = 0.0
    engine_load_change = 0.0
    if previous_reading is not None:
        hydraulic_pressure_change = round(hydraulic_pressure - float(previous_reading["hydraulic_pressure"]), 2)
        engine_load_change = round(engine_load - float(previous_reading["engine_load"]), 2)

    ts = reading.get("timestamp", "")
    machine_id = reading["machine_id"]
    bucket_angle = round(_deterministic_unit(machine_id, ts, "bucket") * 60 - 30, 1)
    boom_angle = round(_deterministic_unit(machine_id, ts, "boom") * 50 + 10, 1)
    stick_angle = round(_deterministic_unit(machine_id, ts, "stick") * 70 - 20, 1)

    energy_per_cycle = estimate_energy_per_cycle(hydraulic_pressure, cycle_time, material_resistance, engine_load)

    pos_x, pos_y, depth = position if position is not None else (0, 0, 0.0)

    return OperatingSituation(
        machine_id=machine_id,
        machine_model=machine_model,
        attachment_type=MACHINE_TYPE_TO_ATTACHMENT.get(machine_type, "bucket"),
        task_type=task_type,
        hydraulic_pressure=hydraulic_pressure,
        engine_load=engine_load,
        rpm=int(reading.get("engine_rpm", 0)),
        cycle_time=cycle_time,
        fuel_rate=float(reading.get("fuel_rate", 0.0)),
        machine_speed=float(reading.get("speed", 0.0)),
        material_resistance=round(material_resistance, 3),
        penetration_rate=round(penetration_rate, 3),
        hydraulic_pressure_change=hydraulic_pressure_change,
        cylinder_force=cylinder_force,
        engine_load_change=engine_load_change,
        bucket_angle=bucket_angle,
        boom_angle=boom_angle,
        stick_angle=stick_angle,
        vibration_level=round(vibration_level, 3),
        energy_per_cycle=energy_per_cycle,
        position_x=pos_x,
        position_y=pos_y,
        depth=depth,
        task_progress=task_progress,
        operator_experience_level=SKILL_TO_EXPERIENCE_LEVEL.get(operator_skill, "intermediate"),
        timestamp=ts,
    )


# Situation Recognition -----------------------------------------------------------------

SITUATION_THRESHOLDS = {
    "high_resistance": 0.62,
    # penetration_rate is derived as `1 - resistance * 0.8` (see derive_operating_situation),
    # so this must be calibrated against that formula rather than picked independently --
    # at resistance == high_resistance, penetration is already ~0.50, not near zero.
    "low_penetration": 0.55,
    "excessive_hydraulic_load": 0.70,
    "inefficient_cycle_dev_pct": 0.20,
    "unstable_vibration": 0.65,
    "high_energy": 1.0,
}


def classify_situation(situation: OperatingSituation) -> str:
    """Rule-based situation recognition (spec section 6). Combinations of signals, not a
    single threshold, so the classification matches the spec's worked example: rising
    hydraulic pressure + falling penetration + rising engine load + rising cycle time =>
    HIGH_RESISTANCE_DIGGING."""
    t = SITUATION_THRESHOLDS
    cycle_dev_pct = max(0.0, (situation.cycle_time - _BASELINE_CYCLE_TIME) / _BASELINE_CYCLE_TIME)

    if situation.vibration_level >= t["unstable_vibration"] and situation.material_resistance >= t["high_resistance"]:
        return "UNSTABLE_OPERATION"

    if (
        situation.material_resistance >= t["high_resistance"]
        and situation.penetration_rate <= t["low_penetration"]
        and situation.engine_load_change >= 0
    ):
        return "HIGH_RESISTANCE_DIGGING"

    if situation.penetration_rate <= t["low_penetration"] and situation.material_resistance < t["high_resistance"]:
        return "LOW_PENETRATION"

    if situation.hydraulic_pressure_change > 0 and situation.material_resistance >= t["excessive_hydraulic_load"]:
        return "EXCESSIVE_HYDRAULIC_LOAD"

    if situation.energy_per_cycle >= t["high_energy"]:
        return "HIGH_ENERGY_CYCLE"

    if cycle_dev_pct >= t["inefficient_cycle_dev_pct"] and situation.material_resistance < t["high_resistance"]:
        return "INEFFICIENT_CYCLE"

    if situation.material_resistance >= t["high_resistance"] * 0.85 and situation.penetration_rate <= t["low_penetration"] * 1.3:
        return "UNUSUAL_MATERIAL_RESPONSE"

    return "NORMAL_DIGGING"


MEANINGFUL_SITUATIONS = {
    "HIGH_RESISTANCE_DIGGING",
    "LOW_PENETRATION",
    "EXCESSIVE_HYDRAULIC_LOAD",
    "INEFFICIENT_CYCLE",
    "UNSTABLE_OPERATION",
    "REPOSITION_REQUIRED",
    "RECOVERY_REQUIRED",
    "UNUSUAL_MATERIAL_RESPONSE",
    "HIGH_ENERGY_CYCLE",
}
