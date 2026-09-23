from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Telemetry
from app.schemas import TelemetryOut

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("", response_model=list[TelemetryOut])
def list_telemetry(
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(Telemetry)
    if machine_id:
        q = q.filter(Telemetry.machine_id == machine_id)
    if operator_id:
        q = q.filter(Telemetry.operator_id == operator_id)
    return q.order_by(Telemetry.id.desc()).limit(limit).all()
