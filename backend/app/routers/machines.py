from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Machine
from app.schemas import MachineOut

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("", response_model=list[MachineOut])
def list_machines(db: Session = Depends(get_db)):
    return db.query(Machine).all()


@router.get("/{machine_id}", response_model=MachineOut | None)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    return db.query(Machine).filter(Machine.machine_id == machine_id).first()
