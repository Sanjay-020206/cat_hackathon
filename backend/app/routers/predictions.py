"""GET /predictions/{task_id} -- task ETA prediction.

Uses the trained Model B (RandomForestRegressor) to predict task duration from the
task/operator/machine/environment context, with confidence and an approximate per-factor
explainability breakdown (spec section 14): how long, how confident, why different from
the original estimate.
"""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.ml.registry import get_eta_model
from app.models import Environment, Machine, Operator, Task, Telemetry

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{task_id}")
def get_task_prediction(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    operator = db.query(Operator).filter(Operator.operator_id == task.operator_id).first()
    machine = db.query(Machine).filter(Machine.machine_id == task.machine_id).first()
    latest_env = db.query(Environment).order_by(Environment.id.desc()).first()
    latest_telemetry = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == task.machine_id)
        .order_by(Telemetry.id.desc())
        .first()
    )

    row = {
        "task_type": task.task_type,
        "weather": latest_env.weather if latest_env else "Clear",
        "operator_skill": operator.skill_level if operator else "Intermediate",
        "terrain": latest_env.terrain if latest_env else "Flat",
        "machine_age": machine.age_years if machine else 5.0,
        "load": (latest_telemetry.engine_load / 100.0) if latest_telemetry else 0.5,
        "historical_cycle_time": operator.historical_cycle_time if operator else 44.0,
        "estimated_time": task.original_estimated_time,
    }

    df = pd.DataFrame([row])

    try:
        model = get_eta_model()
        preds, confidence = model.predict_with_confidence(df)
        predicted_duration = float(preds[0])
        conf = float(confidence[0])
        contributions = model.explain(pd.Series(row))
    except Exception as exc:  # ML failure must degrade, not crash the API
        return {
            "task_id": task_id,
            "original_estimated_time": task.original_estimated_time,
            "predicted_duration": task.original_estimated_time,
            "confidence": None,
            "explanation": [],
            "note": f"ETA model unavailable, falling back to original estimate ({type(exc).__name__})",
        }

    deadline_risk = predicted_duration > task.original_estimated_time * 1.15

    return {
        "task_id": task_id,
        "original_estimated_time": task.original_estimated_time,
        "predicted_duration": round(predicted_duration, 1),
        "confidence": round(conf, 2),
        "explanation": contributions,
        "deadline_at_risk": deadline_risk,
    }
