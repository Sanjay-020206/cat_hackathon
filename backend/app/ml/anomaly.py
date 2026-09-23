"""Model A -- Anomaly Detection (Isolation Forest).

Detects operator/machine-behavior anomalies from telemetry features. Trained on the
generated telemetry (predominantly-normal observations act as the effective baseline,
consistent with the spec's guidance to train on historical/operator-normal data).
"""
from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import ML_ARTIFACTS_DIR

FEATURES = [
    "cycle_time",
    "idle_time",
    "fuel_rate",
    "engine_load",
    "hydraulic_pressure",
    "engine_temp",
]
ARTIFACT_PATH = os.path.join(ML_ARTIFACTS_DIR, "anomaly_model.joblib")


def train(telemetry: pd.DataFrame, contamination: float = 0.12, random_state: int = 42) -> IsolationForest:
    X = telemetry[FEATURES].to_numpy()
    model = IsolationForest(contamination=contamination, random_state=random_state, n_estimators=200)
    model.fit(X)
    return model


def save(model: IsolationForest, path: str = ARTIFACT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)


def load(path: str = ARTIFACT_PATH) -> IsolationForest:
    return joblib.load(path)


def predict(model: IsolationForest, rows: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of `rows` with `anomaly_flag` (bool) and `anomaly_score` (higher = more
    anomalous) columns added. `rows` must contain the FEATURES columns."""
    X = rows[FEATURES].to_numpy()
    raw_pred = model.predict(X)  # -1 = anomaly, 1 = normal
    scores = -model.score_samples(X)  # invert so higher score = more anomalous

    out = rows.copy()
    out["anomaly_flag"] = raw_pred == -1
    out["anomaly_score"] = scores
    return out


def score_single(model: IsolationForest, features: dict) -> dict:
    row = pd.DataFrame([{k: features[k] for k in FEATURES}])
    scored = predict(model, row).iloc[0]
    return {"anomaly_flag": bool(scored["anomaly_flag"]), "anomaly_score": float(scored["anomaly_score"])}
