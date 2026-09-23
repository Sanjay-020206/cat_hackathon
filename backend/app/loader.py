"""Loads generated CSVs into SQLite on startup if the relevant tables are empty."""
from __future__ import annotations

import os

import pandas as pd
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.data_gen.generate_datasets import generate_all, save_all
from app.models import (
    Environment,
    Machine,
    Operator,
    SafetyEvent,
    Task,
    TaskHistory,
    Telemetry,
    Training,
)

TABLE_MODEL_MAP = {
    "machines": Machine,
    "operators": Operator,
    "telemetry": Telemetry,
    "tasks": Task,
    "safety_events": SafetyEvent,
    "environment": Environment,
    "task_history": TaskHistory,
    "training": Training,
}


def _ensure_csvs_exist() -> None:
    missing = [name for name in TABLE_MODEL_MAP if not os.path.exists(os.path.join(DATA_DIR, f"{name}.csv"))]
    if missing:
        datasets = generate_all()
        save_all(datasets, out_dir=DATA_DIR)


def load_csvs_into_db(db: Session, force: bool = False) -> dict[str, int]:
    _ensure_csvs_exist()
    counts: dict[str, int] = {}

    for name, model in TABLE_MODEL_MAP.items():
        existing = db.query(model).count()
        if existing > 0 and not force:
            counts[name] = existing
            continue

        if force and existing > 0:
            db.query(model).delete()

        csv_path = os.path.join(DATA_DIR, f"{name}.csv")
        df = pd.read_csv(csv_path)
        records = df.to_dict(orient="records")
        db.bulk_insert_mappings(model, records)
        db.commit()
        counts[name] = len(records)

    return counts
