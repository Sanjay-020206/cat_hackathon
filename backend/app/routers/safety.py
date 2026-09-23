from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import SafetyEvent
from app.schemas import SafetyEventOut

router = APIRouter(prefix="/safety", tags=["safety"])


@router.get("", response_model=list[SafetyEventOut])
def list_safety_events(
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(SafetyEvent)
    if machine_id:
        q = q.filter(SafetyEvent.machine_id == machine_id)
    if operator_id:
        q = q.filter(SafetyEvent.operator_id == operator_id)
    return q.order_by(SafetyEvent.timestamp.desc()).limit(limit).all()
