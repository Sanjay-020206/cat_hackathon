from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Operator
from app.schemas import OperatorOut

router = APIRouter(prefix="/operators", tags=["operators"])


@router.get("", response_model=list[OperatorOut])
def list_operators(db: Session = Depends(get_db)):
    return db.query(Operator).all()


@router.get("/{operator_id}", response_model=OperatorOut | None)
def get_operator(operator_id: str, db: Session = Depends(get_db)):
    return db.query(Operator).filter(Operator.operator_id == operator_id).first()
