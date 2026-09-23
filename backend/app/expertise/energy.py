"""Energy estimation (spec section 21).

Physics-inspired synthetic model -- this project has no real energy-consumption
telemetry, so every value produced here is an *estimate*, never presented as measured
energy. Shared by both the Expertise layer (per-cycle energy on the current operating
situation) and the Site/Ground layer (area energy forecasts), so the two intelligence
layers stay consistent with each other (spec section 24: they must not be unrelated
features).

Conceptual relationship (spec section 21):
    Energy Demand ∝ hydraulic load × cycle duration × resistance
"""
from __future__ import annotations

# Calibration constants keep the output in a human-readable "energy units" range
# (roughly 0.3-1.4 for the synthetic dataset's normal-to-heavy-load spread) rather than
# raw physical units we cannot actually measure.
_HYDRAULIC_REFERENCE = 30.0  # bar, mid-range of the synthetic dataset's normal pressure
_CYCLE_REFERENCE_SECONDS = 45.0


def estimate_energy_per_cycle(hydraulic_pressure: float, cycle_time: float, resistance: float, engine_load: float) -> float:
    """Returns an *estimated* energy-per-cycle index (unitless, roughly 0.2-2.0).

    Not a measured value -- there is no energy telemetry on this machine/dataset. Callers
    must label this "Estimated Energy" in any user-facing text (spec section 21).
    """
    hydraulic_factor = max(0.1, hydraulic_pressure / _HYDRAULIC_REFERENCE)
    cycle_factor = max(0.1, cycle_time / _CYCLE_REFERENCE_SECONDS)
    resistance_factor = max(0.2, resistance)
    load_factor = max(0.3, engine_load / 100.0)

    energy = hydraulic_factor * cycle_factor * resistance_factor * (0.5 + 0.5 * load_factor)
    return round(energy, 3)


def energy_demand_label(estimated_energy: float) -> str:
    if estimated_energy < 0.55:
        return "LOW"
    if estimated_energy < 0.9:
        return "MODERATE"
    if estimated_energy < 1.3:
        return "HIGH"
    return "VERY_HIGH"
