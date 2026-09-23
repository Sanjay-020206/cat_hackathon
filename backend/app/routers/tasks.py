from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Task
from app.schemas import TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    operator_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if operator_id:
        q = q.filter(Task.operator_id == operator_id)
    if machine_id:
        q = q.filter(Task.machine_id == machine_id)
    return q.all()


@router.get("/{task_id}", response_model=TaskOut | None)
def get_task(task_id: str, db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.task_id == task_id).first()
