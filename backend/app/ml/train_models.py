"""Offline training entry point. Run after (re)generating datasets:

    python -m app.ml.train_models

Trains and saves Model A (anomaly) and Model B (ETA) joblib artifacts under
app/ml/artifacts/. Models C and D are stateless/rule-based and need no training step.
"""
from __future__ import annotations

import os

import pandas as pd

from app.config import DATA_DIR
from app.ml import anomaly, eta


def main() -> None:
    telemetry_path = os.path.join(DATA_DIR, "telemetry.csv")
    task_history_path = os.path.join(DATA_DIR, "task_history.csv")

    if not os.path.exists(telemetry_path) or not os.path.exists(task_history_path):
        from app.data_gen.generate_datasets import generate_all, save_all

        save_all(generate_all(), out_dir=DATA_DIR)

    telemetry = pd.read_csv(telemetry_path)
    task_history = pd.read_csv(task_history_path)

    anomaly_model = anomaly.train(telemetry)
    anomaly.save(anomaly_model)
    print(f"Saved anomaly model -> {anomaly.ARTIFACT_PATH}")

    eta_model = eta.train(task_history)
    eta.save(eta_model)
    print(f"Saved ETA model -> {eta.ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
