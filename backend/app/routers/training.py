"""Adaptive Training loop (spec section 19): Behavior anomaly -> skill gap -> training
recommendation -> operator completes it -> measure improvement.

Completion records are kept in-memory (per process) -- adequate for a 24-hour hackathon
demo; a production build would persist these alongside `incidents`.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.training_agent import recommend, simulate_intervention
from app.db import get_db
from app.models import Operator, Telemetry, Training

router = APIRouter(prefix="/training", tags=["training"])

_completions: dict[str, list[dict]] = {}


class CompleteTrainingRequest(BaseModel):
    operator_id: str
    training_id: str
    skill_gap: str
    before_cycle_time: float


@router.get("")
def list_training(db: Session = Depends(get_db)):
    return db.query(Training).all()


@router.get("/recommendation/{operator_id}")
def get_training_recommendation(operator_id: str, db: Session = Depends(get_db)):
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if operator is None:
        raise HTTPException(status_code=404, detail=f"Operator {operator_id} not found")

    latest = (
        db.query(Telemetry)
        .filter(Telemetry.operator_id == operator_id)
        .order_by(Telemetry.id.desc())
        .first()
    )
    if latest is None:
        return {"operator_id": operator_id, "recommendation": None}

    cycle_dev = max(0.0, (latest.cycle_time - operator.historical_cycle_time) / operator.historical_cycle_time)
    idle_dev = max(0.0, (latest.idle_time - operator.historical_idle_rate) / max(1.0, operator.historical_idle_rate))
    proximity_events = 2 if getattr(latest, "abnormal_scenario", False) else 0

    catalog_rows = db.query(Training).all()
    catalog_df = pd.DataFrame(
        [
            {
                "training_id": t.training_id,
                "skill": t.skill,
                "title": t.title,
                "duration": t.duration,
                "difficulty": t.difficulty,
                "resource": t.resource,
            }
            for t in catalog_rows
        ]
    )

    rec = recommend(
        catalog_df,
        cycle_time_deviation_pct=cycle_dev,
        idle_rate_deviation_pct=idle_dev,
        proximity_events=proximity_events,
        ground_condition="Dry",
        seatbelt_violation=latest.seatbelt_status != "Fastened",
    )

    if rec is not None:
        rec["current_cycle_time"] = latest.cycle_time

    return {"operator_id": operator_id, "recommendation": rec}


@router.post("/complete")
def complete_training(req: CompleteTrainingRequest):
    result = simulate_intervention(req.before_cycle_time, req.skill_gap)
    record = {
        "operator_id": req.operator_id,
        "training_id": req.training_id,
        "skill_gap": req.skill_gap,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    _completions.setdefault(req.operator_id, []).append(record)
    return record


@router.get("/history/{operator_id}")
def get_training_history(operator_id: str):
    return _completions.get(operator_id, [])
