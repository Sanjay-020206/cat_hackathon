"""Jobsite Ground Memory API (spec section 36-37): the site/area intelligence map."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.expertise.service import get_expertise_engine
from app.site.energy_forecast import forecast_area_energy
from app.site.ground import get_ground_estimate
from app.site.grid import SiteCell

router = APIRouter(prefix="/site", tags=["site"])


def _cell_summary(cell: SiteCell) -> dict:
    return {
        "cell_id": cell.cell_id,
        "x": cell.x,
        "y": cell.y,
        "estimated_material": cell.estimated_material,
        "material_confidence": cell.material_confidence,
        "excavation_difficulty": cell.excavation_difficulty,
        "observation_count": cell.observation_count,
        "successful_episode_count": cell.successful_episode_count,
    }


@router.get("/map")
def get_site_map():
    engine = get_expertise_engine()
    cells = list(engine.site_cells.values())
    return {
        "width": max(c.x for c in cells) + 1,
        "height": max(c.y for c in cells) + 1,
        "cells": [_cell_summary(c) for c in cells],
        "data_source": "synthetic_demo",
    }


def _get_cell_or_404(cell_id: str) -> SiteCell:
    engine = get_expertise_engine()
    cell = engine.site_cells.get(cell_id.upper())
    if cell is None:
        raise HTTPException(status_code=404, detail=f"No site cell '{cell_id}'")
    return cell


@router.get("/cells/{cell_id}")
def get_cell(cell_id: str):
    cell = _get_cell_or_404(cell_id)
    return {
        **_cell_summary(cell),
        "resistance_score": cell.resistance_score,
        "average_hydraulic_load": cell.average_hydraulic_load,
        "average_engine_load": cell.average_engine_load,
        "average_energy_per_cycle": cell.average_energy_per_cycle,
        "average_cycle_time": cell.average_cycle_time,
        "last_updated": cell.last_updated,
        "recent_history": cell.history[-10:],
    }


@router.get("/ground-estimate/{cell_id}")
def ground_estimate(cell_id: str):
    return get_ground_estimate(_get_cell_or_404(cell_id))


@router.get("/energy-forecast/{cell_id}")
def energy_forecast(cell_id: str):
    return forecast_area_energy(_get_cell_or_404(cell_id))
