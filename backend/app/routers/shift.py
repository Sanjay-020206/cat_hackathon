"""Shift Memory (spec section 22): a start-of-shift greeting built from historical
database queries -- no LLM memory system needed, just a lookup against the operator's
most recent prior telemetry and safety events."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.training_agent import detect_skill_gap
from app.db import get_db
from app.models import Machine, Operator, SafetyEvent, Task, Telemetry

router = APIRouter(prefix="/shift", tags=["shift"])

_FOCUS_LABELS = {
    "cycle_efficiency": "Improve cycle time consistency during excavation.",
    "idle_reduction": "Reduce idle time during loading.",
    "safe_zone_awareness": "Complete Safe Zone Awareness training before starting.",
    "wet_terrain_handling": "Take extra care on wet terrain.",
    "proximity_awareness": "Maintain safe distance from other equipment and personnel.",
}


@router.get("/greeting/{operator_id}")
def get_shift_greeting(operator_id: str, db: Session = Depends(get_db)):
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if operator is None:
        raise HTTPException(status_code=404, detail=f"Operator {operator_id} not found")

    recent_rows = (
        db.query(Telemetry)
        .filter(Telemetry.operator_id == operator_id)
        .order_by(Telemetry.id.desc())
        .limit(20)
        .all()
    )
    task = db.query(Task).filter(Task.operator_id == operator_id).order_by(Task.deadline.asc()).first()
    machine = db.query(Machine).filter(Machine.machine_id == task.machine_id).first() if task else None
    safety_event_count = db.query(SafetyEvent).filter(SafetyEvent.operator_id == operator_id).count()

    if recent_rows:
        avg_idle_pct = round(
            100 * sum(r.idle_time for r in recent_rows) / max(1.0, sum(r.cycle_time + r.idle_time for r in recent_rows)),
            1,
        )
        latest = recent_rows[0]
        cycle_dev = max(0.0, (latest.cycle_time - operator.historical_cycle_time) / operator.historical_cycle_time)
        idle_dev = max(0.0, (latest.idle_time - operator.historical_idle_rate) / max(1.0, operator.historical_idle_rate))
        gap = detect_skill_gap(
            cycle_time_deviation_pct=cycle_dev,
            idle_rate_deviation_pct=idle_dev,
            proximity_events=2 if getattr(latest, "abnormal_scenario", False) else 0,
            ground_condition="Dry",
            seatbelt_violation=latest.seatbelt_status != "Fastened",
        )
    else:
        avg_idle_pct = None
        gap = None

    focus = _FOCUS_LABELS.get(gap, "Maintain consistent cycle efficiency and stay within safety guidelines.")

    return {
        "operator_id": operator_id,
        "machine_id": machine.machine_id if machine else None,
        "machine_model": machine.model if machine else None,
        "previous_shift": {
            "idle_pct": avg_idle_pct,
            "safety_events": safety_event_count,
        },
        "todays_focus": focus,
    }
