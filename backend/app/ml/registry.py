"""Lazy-loaded singletons for the trained ML artifacts, so routers can use the real
models without every request paying model-load cost, and without the app crashing if
`train_models.py` hasn't been run yet -- it trains on first use in that case (mirrors
`app/loader.py`'s "generate CSVs if missing" pattern)."""
from __future__ import annotations

import os

import pandas as pd

from app.config import DATA_DIR
from app.ml import anomaly, eta

_anomaly_model = None
_eta_model = None


def get_anomaly_model():
    global _anomaly_model
    if _anomaly_model is not None:
        return _anomaly_model

    if os.path.exists(anomaly.ARTIFACT_PATH):
        _anomaly_model = anomaly.load()
    else:
        telemetry_path = os.path.join(DATA_DIR, "telemetry.csv")
        telemetry = pd.read_csv(telemetry_path)
        _anomaly_model = anomaly.train(telemetry)
        anomaly.save(_anomaly_model)

    return _anomaly_model


def get_eta_model():
    global _eta_model
    if _eta_model is not None:
        return _eta_model

    if os.path.exists(eta.ARTIFACT_PATH):
        _eta_model = eta.load()
    else:
        task_history_path = os.path.join(DATA_DIR, "task_history.csv")
        task_history = pd.read_csv(task_history_path)
        _eta_model = eta.train(task_history)
        eta.save(_eta_model)

    return _eta_model


def reset() -> None:
    """Test/reliability-injection hook: forces the next get_*() call to reload from disk."""
    global _anomaly_model, _eta_model
    _anomaly_model = None
    _eta_model = None
