"""Ground/Area Intelligence: estimate lookup + the observation update loop that grows
site memory over time (spec sections 15-18).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.expertise.energy import estimate_energy_per_cycle
from app.site.grid import SiteCell, difficulty_for_resistance, material_for_resistance, confidence_from_observations

MIN_OBSERVATIONS_FOR_MATERIAL_CALL = 5


@dataclass
class GroundObservation:
    cell_id: str
    hydraulic_pressure: float
    engine_load: float
    cycle_time: float
    material_resistance: float
    successful: bool = False


def get_ground_estimate(cell: SiteCell) -> dict:
    if cell.observation_count < MIN_OBSERVATIONS_FOR_MATERIAL_CALL:
        return {
            "cell_id": cell.cell_id,
            "estimated_material": "UNKNOWN",
            "material_confidence": cell.material_confidence,
            "resistance_score": cell.resistance_score if cell.observation_count > 0 else None,
            "excavation_difficulty": cell.excavation_difficulty if cell.observation_count > 0 else "UNKNOWN",
            "observation_count": cell.observation_count,
            "confidence_note": "Low confidence -- insufficient observations in this area.",
        }

    return {
        "cell_id": cell.cell_id,
        "estimated_material": cell.estimated_material,
        "material_confidence": cell.material_confidence,
        "resistance_score": cell.resistance_score,
        "excavation_difficulty": cell.excavation_difficulty,
        "observation_count": cell.observation_count,
        "confidence_note": None,
    }


def update_cell_from_observation(cell: SiteCell, obs: GroundObservation, alpha: float = 0.2) -> SiteCell:
    """Incrementally updates a cell's running stats from one new observation (spec section
    17's "Ground Map Update Loop"). Uses an exponential moving average so recent machine
    response gradually reshapes the estimate without one noisy reading swinging it wildly."""
    n = cell.observation_count

    energy = estimate_energy_per_cycle(obs.hydraulic_pressure, obs.cycle_time, obs.material_resistance, obs.engine_load)

    if n == 0:
        cell.average_hydraulic_load = obs.hydraulic_pressure
        cell.average_engine_load = obs.engine_load
        cell.average_cycle_time = obs.cycle_time
        cell.average_energy_per_cycle = energy
        cell.resistance_score = obs.material_resistance
    else:
        cell.average_hydraulic_load = round((1 - alpha) * cell.average_hydraulic_load + alpha * obs.hydraulic_pressure, 2)
        cell.average_engine_load = round((1 - alpha) * cell.average_engine_load + alpha * obs.engine_load, 2)
        cell.average_cycle_time = round((1 - alpha) * cell.average_cycle_time + alpha * obs.cycle_time, 2)
        cell.average_energy_per_cycle = round((1 - alpha) * cell.average_energy_per_cycle + alpha * energy, 3)
        cell.resistance_score = round((1 - alpha) * cell.resistance_score + alpha * obs.material_resistance, 3)

    cell.observation_count += 1
    cell.material_confidence = confidence_from_observations(cell.observation_count)
    cell.excavation_difficulty = difficulty_for_resistance(cell.resistance_score)

    if cell.observation_count >= MIN_OBSERVATIONS_FOR_MATERIAL_CALL:
        cell.estimated_material = material_for_resistance(cell.resistance_score)
    else:
        cell.estimated_material = "UNKNOWN"

    if obs.successful:
        cell.successful_episode_count += 1

    cell.last_updated = datetime.now(timezone.utc).isoformat()
    cell.history.append(
        {
            "timestamp": cell.last_updated,
            "resistance": obs.material_resistance,
            "successful": obs.successful,
        }
    )
    cell.history = cell.history[-50:]  # bounded, this is an in-memory demo store

    return cell
