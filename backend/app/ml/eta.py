"""Model B -- Task ETA prediction.

RandomForestRegressor predicting `actual_time` (task duration) from task/operator/machine/
environment features, with an approximate explainability breakdown (spec section 14):
"how long, how confident, why different from the original estimate".

Explainability approach: for a single prediction, decompose the delta between the
predicted duration and the dataset-wide mean duration into per-feature contributions,
weighted by the model's global feature importances and how far each feature's encoded
value sits from its training-set mean/mode. This is an approximation (not SHAP), which is
adequate for hackathon-grade "directionally correct, human-readable" explanations.
"""
from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OrdinalEncoder

from app.config import ML_ARTIFACTS_DIR

CATEGORICAL_FEATURES = ["task_type", "weather", "operator_skill", "terrain"]
NUMERIC_FEATURES = ["machine_age", "load", "historical_cycle_time", "estimated_time"]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "actual_time"

ARTIFACT_PATH = os.path.join(ML_ARTIFACTS_DIR, "eta_model.joblib")


class ETAModel:
    def __init__(self, model: RandomForestRegressor, encoder: OrdinalEncoder, feature_means: dict[str, float]):
        self.model = model
        self.encoder = encoder
        self.feature_means = feature_means

    def _encode(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out[CATEGORICAL_FEATURES] = self.encoder.transform(out[CATEGORICAL_FEATURES])
        return out[ALL_FEATURES]

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = self._encode(df)
        return self.model.predict(X)

    def predict_with_confidence(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Confidence approximated from agreement across the forest's trees: tighter
        spread of individual tree predictions -> higher confidence."""
        X = self._encode(df).to_numpy()
        tree_preds = np.stack([tree.predict(X) for tree in self.model.estimators_], axis=0)
        mean_pred = tree_preds.mean(axis=0)
        std_pred = tree_preds.std(axis=0)
        # map std (minutes) to a 0-1 confidence score; tuned so ~0 std -> ~0.95, larger std -> lower
        confidence = np.clip(1.0 - (std_pred / (mean_pred + 1e-6)), 0.35, 0.97)
        return mean_pred, confidence

    def explain(self, row: pd.Series) -> list[dict]:
        """Approximate per-feature contribution (in minutes) for one prediction."""
        importances = dict(zip(ALL_FEATURES, self.model.feature_importances_))
        encoded_row = self._encode(pd.DataFrame([row]))
        contributions = []

        pred = float(self.model.predict(encoded_row)[0])
        baseline = self.feature_means["_target_mean"]
        total_delta = pred - baseline
        importance_sum = sum(importances.values()) or 1.0

        for feat in ALL_FEATURES:
            value = encoded_row.iloc[0][feat]
            mean = self.feature_means.get(feat, value)
            spread = self.feature_means.get(f"_{feat}_std", 1.0) or 1.0
            normalized_dev = (value - mean) / spread
            weight = importances[feat] / importance_sum
            minutes = float(np.clip(normalized_dev, -3, 3) * weight * total_delta)
            if abs(minutes) >= 0.3:
                contributions.append(
                    {
                        "factor": feat,
                        "raw_value": row[feat],
                        "impact_minutes": round(minutes, 1),
                    }
                )

        contributions.sort(key=lambda c: -abs(c["impact_minutes"]))
        return contributions


def train(task_history: pd.DataFrame, random_state: int = 42) -> ETAModel:
    df = task_history.copy()
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    df[CATEGORICAL_FEATURES] = encoder.fit_transform(df[CATEGORICAL_FEATURES])

    X = df[ALL_FEATURES]
    y = df[TARGET]

    model = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=random_state)
    model.fit(X, y)

    feature_means: dict[str, float] = {"_target_mean": float(y.mean())}
    for feat in ALL_FEATURES:
        feature_means[feat] = float(df[feat].mean())
        feature_means[f"_{feat}_std"] = float(df[feat].std()) or 1.0

    return ETAModel(model, encoder, feature_means)


def save(eta_model: ETAModel, path: str = ARTIFACT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(eta_model, path)


def load(path: str = ARTIFACT_PATH) -> ETAModel:
    return joblib.load(path)
