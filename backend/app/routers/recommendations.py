"""GET /recommendations/{machine_id} -- Next Best Action.

Builds fused context from the most recent telemetry for the machine, computes risk +
contributors via the Context Engine, derives the Next Best Action, and generates a
template-based explanation (spec sections 16-18). No LLM dependency here (that's the
optional Phase 8 layer sitting in front of this template).
"""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.context.context_engine import ContextFusionInput, build_context
from app.context.explain import build_explanation
from app.context.nba_engine import next_best_action
from app.db import get_db
from app.models import Machine, Operator, SafetyEvent, Telemetry

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

RECENT_WINDOW = 10


@router.get("/{machine_id}")
def get_recommendation(machine_id: str, db: Session = Depends(get_db)):
    recent_rows = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.id.desc())
        .limit(RECENT_WINDOW)
        .all()
    )
    if not recent_rows:
        raise HTTPException(status_code=404, detail=f"No telemetry found for machine {machine_id}")

    recent_rows = list(reversed(recent_rows))  # oldest first
    latest = recent_rows[-1]

    operator = db.query(Operator).filter(Operator.operator_id == latest.operator_id).first()
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    safety_event_count = (
        db.query(SafetyEvent)
        .filter(SafetyEvent.machine_id == machine_id, SafetyEvent.operator_id == latest.operator_id)
        .count()
    )

    recent_df = pd.DataFrame(
        [
            {
                "engine_temp": r.engine_temp,
                "hydraulic_pressure": r.hydraulic_pressure,
                "hydraulic_temp": r.hydraulic_temp,
                "engine_load": r.engine_load,
            }
            for r in recent_rows
        ]
    )

    proximity_events = 2 if getattr(latest, "abnormal_scenario", False) else 0

    inp = ContextFusionInput(
        machine_id=machine_id,
        operator_id=latest.operator_id,
        cycle_time=latest.cycle_time,
        idle_time=latest.idle_time,
        speed=0.0,
        seatbelt_status=latest.seatbelt_status,
        proximity_events=proximity_events,
        ground_condition="Dry",
        shift_minutes=len(recent_rows) * 8,
        baseline_cycle_time=operator.historical_cycle_time if operator else 44.0,
        baseline_idle_time=operator.historical_idle_rate if operator else 8.0,
        recent_telemetry=recent_df,
        recent_safety_event_count=safety_event_count,
        maintenance_status=machine.maintenance_status if machine else "Normal",
    )

    context = build_context(inp)
    nba = next_best_action(context)
    explanation = build_explanation(context, nba)

    return {
        "machine_id": machine_id,
        "operator_id": latest.operator_id,
        "risk_level": context["risk_level"],
        "risk_score": context["risk_score"],
        "risk_trend": context["risk_trend"],
        "contributors": context["contributors"],
        "next_best_action": nba,
        "explanation": explanation,
    }
