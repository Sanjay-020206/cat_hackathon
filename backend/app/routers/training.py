from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Training
from app.schemas import TrainingOut

router = APIRouter(prefix="/training", tags=["training"])


@router.get("", response_model=list[TrainingOut])
def list_training(db: Session = Depends(get_db)):
    return db.query(Training).all()
