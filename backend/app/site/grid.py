"""Jobsite Ground Memory -- spatial grid (spec sections 13-16, 34).

Represents the jobsite as an 8x8 grid of `SiteCell`s. Generated deterministically with
spatially-correlated regions (soft -> mixed -> high-resistance bands radiating from a
couple of "hotspots"), not independent random noise per cell, so the map looks like a
believable jobsite rather than static.

This is a *conceptual* ground/area intelligence layer. It never claims to detect exact
soil composition -- only an `estimated_material_class` with an explicit confidence, built
up from simulated machine-response observations (spec section 18).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

GRID_WIDTH = 8
GRID_HEIGHT = 8
SEED = 42

MATERIAL_CLASSES = [
    "SOFT_SOIL",
    "NORMAL_SOIL",
    "COMPACTED_SOIL",
    "GRAVEL",
    "MIXED_MATERIAL",
    "HARD_LAYER",
    "ROCK_LIKE",
]

# Two synthetic "hotspots" (hard ground) the resistance field radiates outward from, plus
# one soft-ground trough, so the grid reads as spatially coherent regions rather than
# random cells (spec section 34).
_HOTSPOTS = [(6, 2, 0.9), (2, 6, 0.65)]
_SOFT_SPOT = (1, 1, 0.9)

# Observation counts start low almost everywhere (jobsite is mostly unexplored at demo
# start) except along the scripted demo's path, which gets a modest head start so the
# UI has something to show on first load without requiring a full simulation run.
_PRESEEDED_CELLS = {(3, 3): 22, (4, 3): 31, (5, 3): 43, (5, 2): 12}


@dataclass
class SiteCell:
    cell_id: str
    x: int
    y: int

    estimated_material: str
    material_confidence: float

    resistance_score: float
    excavation_difficulty: str

    average_hydraulic_load: float
    average_engine_load: float
    average_energy_per_cycle: float
    average_cycle_time: float

    observation_count: int
    successful_episode_count: int

    last_updated: str | None = None
    history: list[dict] = field(default_factory=list)


def cell_id_for(x: int, y: int) -> str:
    col = chr(ord("A") + x)
    return f"{col}{y + 1}"


def _base_resistance(x: int, y: int) -> float:
    resistance = 0.15
    for hx, hy, strength in _HOTSPOTS:
        dist = math.hypot(x - hx, y - hy)
        resistance += strength * math.exp(-(dist**2) / 6.0)

    sx, sy, strength = _SOFT_SPOT
    dist = math.hypot(x - sx, y - sy)
    resistance -= strength * math.exp(-(dist**2) / 5.0)

    return max(0.05, min(0.95, resistance))


def material_for_resistance(resistance: float) -> str:
    if resistance < 0.20:
        return "SOFT_SOIL"
    if resistance < 0.35:
        return "NORMAL_SOIL"
    if resistance < 0.50:
        return "COMPACTED_SOIL"
    if resistance < 0.62:
        return "GRAVEL"
    if resistance < 0.75:
        return "MIXED_MATERIAL"
    if resistance < 0.85:
        return "HARD_LAYER"
    return "ROCK_LIKE"


def difficulty_for_resistance(resistance: float) -> str:
    if resistance < 0.35:
        return "LOW"
    if resistance < 0.62:
        return "MEDIUM"
    return "HIGH"


def confidence_from_observations(observation_count: int) -> float:
    """Confidence rises with more observations but never claims certainty (spec section 16).
    Diminishing returns via a saturating curve; capped at 0.97."""
    if observation_count <= 0:
        return 0.0
    return round(min(0.97, 1.0 - math.exp(-observation_count / 18.0)), 2)


def generate_site_grid(seed: int = SEED) -> dict[str, SiteCell]:
    cells: dict[str, SiteCell] = {}
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            resistance = _base_resistance(x, y)
            observation_count = _PRESEEDED_CELLS.get((x, y), 0)
            confidence = confidence_from_observations(observation_count) if observation_count else 0.0
            material = material_for_resistance(resistance) if observation_count else "UNKNOWN"

            cell = SiteCell(
                cell_id=cell_id_for(x, y),
                x=x,
                y=y,
                estimated_material=material,
                material_confidence=confidence,
                resistance_score=round(resistance, 3),
                excavation_difficulty=difficulty_for_resistance(resistance),
                average_hydraulic_load=round(24 + resistance * 12, 1),
                average_engine_load=round(45 + resistance * 35, 1),
                average_energy_per_cycle=0.0,
                average_cycle_time=round(40 + resistance * 25, 1),
                observation_count=observation_count,
                successful_episode_count=0,
            )
            cells[cell.cell_id] = cell
    return cells
