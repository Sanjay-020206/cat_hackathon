"""GET /predictions/{task_id} — task ETA prediction.

Phase 2: placeholder that echoes the original estimate. Phase 3 replaces this with
Model B (RandomForest/GradientBoosting ETA regressor) and explainability breakdown.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Task

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{task_id}")
def get_task_prediction(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return {
        "task_id": task_id,
        "original_estimated_time": task.original_estimated_time,
        "predicted_duration": task.original_estimated_time,
        "confidence": None,
        "explanation": [],
        "note": "placeholder prediction — Model B not yet trained (Phase 3)",
    }
