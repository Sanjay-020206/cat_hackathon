"""Area-based energy forecast (spec sections 19, 22).

Turns a site cell's accumulated ground memory into a forward-looking estimate of what the
*next* excavation cycle in that area will cost -- energy, time, difficulty -- so the
operator can be warned before entering a difficult area, not after (spec section 20:
"Pre-Excavation Intelligence"). This deliberately does NOT decide Power/Eco mode or any
machine setting; Caterpillar already has dynamic power management for that (spec section
19) -- this only informs the human-readable Next Best Action layer.
"""
from __future__ import annotations

from app.expertise.energy import energy_demand_label
from app.site.grid import SiteCell
from app.site.ground import MIN_OBSERVATIONS_FOR_MATERIAL_CALL


def forecast_area_energy(cell: SiteCell) -> dict:
    if cell.observation_count < MIN_OBSERVATIONS_FOR_MATERIAL_CALL:
        return {
            "cell_id": cell.cell_id,
            "expected_resistance": "UNKNOWN",
            "expected_energy_per_cycle": None,
            "expected_cycle_time": None,
            "expected_difficulty": "UNKNOWN",
            "confidence": cell.material_confidence,
            "note": "Insufficient observations in this area for a reliable forecast.",
        }

    return {
        "cell_id": cell.cell_id,
        "expected_resistance": cell.excavation_difficulty,
        "expected_energy_per_cycle": cell.average_energy_per_cycle,
        "expected_energy_label": energy_demand_label(cell.average_energy_per_cycle),
        "expected_cycle_time": cell.average_cycle_time,
        "expected_difficulty": cell.excavation_difficulty,
        "confidence": cell.material_confidence,
        "note": None,
    }
