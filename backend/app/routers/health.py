"""GET /health — machine health snapshot.

Phase 2: simple rule-based heuristic on the latest telemetry row (no ML yet).
Phase 3 replaces the internals with Model C (rolling stats + trend) while keeping this
same endpoint/response shape, per the spec's incremental-build approach.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Telemetry

router = APIRouter(prefix="/health", tags=["health"])


def _naive_health_state(t: Telemetry) -> tuple[str, float]:
    score = 100.0
    if t.hydraulic_temp > 80:
        score -= 20
    if t.engine_temp > 95:
        score -= 20
    if t.hydraulic_pressure > 34 or t.hydraulic_pressure < 15:
        score -= 10
    if t.engine_load > 90:
        score -= 10
    score = max(0.0, min(100.0, score))
    if score >= 85:
        state = "Normal"
    elif score >= 65:
        state = "Watch"
    elif score >= 40:
        state = "Elevated"
    else:
        state = "Critical"
    return state, score


@router.get("/{machine_id}")
def get_machine_health(machine_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.id.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail=f"No telemetry found for machine {machine_id}")

    state, score = _naive_health_state(latest)
    return {
        "machine_id": machine_id,
        "state": state,
        "score": score,
        "as_of": latest.timestamp,
    }
