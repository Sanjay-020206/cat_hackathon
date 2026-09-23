"""CAT Expertise Engine API (spec section 36).

Bringing the right experience to the operator at the right moment: situation recognition,
ground/area intelligence, expert-moment detection, experience retrieval and the
energy-aware Next Best Action layer, built on top of (not replacing) the existing
Context Engine / NBA Engine.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.expertise.service import get_expertise_engine
from app.models import Machine, Operator, Task, Telemetry

router = APIRouter(prefix="/expertise", tags=["expertise"])


def _latest_reading_dict(t: Telemetry) -> dict:
    return {
        "timestamp": t.timestamp,
        "machine_id": t.machine_id,
        "operator_id": t.operator_id,
        "engine_rpm": t.engine_rpm,
        "hydraulic_pressure": t.hydraulic_pressure,
        "engine_load": t.engine_load,
        "cycle_time": t.cycle_time,
        "fuel_rate": t.fuel_rate,
        "speed": t.speed,
    }


@router.get("/evaluate/{machine_id}")
def evaluate_current_situation(machine_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.id.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail=f"No telemetry found for machine {machine_id}")

    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    operator = db.query(Operator).filter(Operator.operator_id == latest.operator_id).first()
    task = (
        db.query(Task)
        .filter(Task.machine_id == machine_id, Task.operator_id == latest.operator_id)
        .first()
    )

    engine = get_expertise_engine()
    result = engine.evaluate(
        _latest_reading_dict(latest),
        machine_model=machine.model if machine else "Unknown",
        machine_type=machine.machine_type if machine else "Excavator",
        task_type=task.task_type if task else "Earth Excavation",
        operator_skill=operator.skill_level if operator else "Intermediate",
    )
    return result


@router.get("/episodes")
def list_episodes(situation: str | None = None, trusted_only: bool = True):
    engine = get_expertise_engine()
    pool = engine.matcher.trusted_episodes if trusted_only else engine.episodes
    episodes = [e for e in pool if situation is None or e.situation == situation]
    return {
        "count": len(episodes),
        "episodes": [
            {
                "episode_id": e.episode_id,
                "machine_model": e.machine_model,
                "attachment": e.attachment,
                "task": e.task,
                "situation": e.situation,
                "context": e.context,
                "operator_profile": e.operator_profile,
                "action_sequence": e.action_sequence,
                "outcome": e.outcome,
                "cell_id": e.cell_id,
                "quality_score": e.quality_score,
                "is_synthetic": e.is_synthetic,
            }
            for e in episodes
        ],
        "data_source": "synthetic_demo",
    }


class OutcomeRequest(BaseModel):
    machine_id: str
    cycle_time_after: float
    successful: bool = True


@router.post("/outcome")
def record_outcome(req: OutcomeRequest):
    engine = get_expertise_engine()
    try:
        return engine.record_outcome(req.machine_id, req.cycle_time_after, req.successful)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/memory")
def machine_memory():
    return get_expertise_engine().machine_memory()


@router.get("/statistics")
def statistics():
    return get_expertise_engine().statistics()
