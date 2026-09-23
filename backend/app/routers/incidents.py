from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Incident
from app.schemas import IncidentIn, IncidentOut

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).order_by(Incident.timestamp.desc()).all()


@router.post("", response_model=IncidentOut, status_code=201)
def create_incident(incident: IncidentIn, db: Session = Depends(get_db)):
    if db.query(Incident).filter(Incident.incident_id == incident.incident_id).first():
        raise HTTPException(status_code=409, detail="Incident with this ID already exists")
    row = Incident(**incident.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
