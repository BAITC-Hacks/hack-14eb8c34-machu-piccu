"""LightGBM power-forecast models: a point forecast plus predictive quantiles.

Two things a dispatcher needs are modelled separately. The point forecast is a
plain L2 regression, tuned for volume accuracy. The P10/P50/P90 band comes from
three quantile regressors, because the cost of being wrong in wind is wildly
asymmetric and a bare point forecast hides that.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from src import config

# Tuned on the Oct-2025..Jan-2026 hold-out. The headline choice is a
# deliberately small tree (31 leaves, 150 rows per leaf) with strong L1/L2:
# the ensemble weather input carries only so much information, and a larger
# model memorised the training seasons instead of generalising to the next one.
BASE_PARAMS: dict = {
    "objective": "regression",
    "metric": "l2",
    "learning_rate": 0.02,
    "num_leaves": 31,
    "min_data_in_leaf": 150,
    "feature_fraction": 0.7,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l1": 0.5,
    "lambda_l2": 5.0,
    "verbosity": -1,
    "num_threads": 0,
    "seed": 42,
}

NUM_ROUNDS = 1200
EARLY_STOPPING = 80


@dataclass
class TrainedModel:
    """A fitted forecaster: the point model, the quantile band, and metadata."""

    point: lgb.Booster
    quantiles: dict[float, lgb.Booster]
    feature_columns: list[str]
    power_curve: pd.DataFrame
    turbine: str
    trained_rows: int
    best_iteration: int

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, directory / f"{self.turbine}_model.joblib")
        meta = {
            "turbine": self.turbine,
            "trained_rows": self.trained_rows,
            "best_iteration": self.best_iteration,
            "n_features": len(self.feature_columns),
            "quantiles": sorted(self.quantiles),
        }
        (directory / f"{self.turbine}_model.json").write_text(json.dumps(meta, indent=2))

    @staticmethod
    def load(directory: Path, turbine: str) -> "TrainedModel":
        return joblib.load(Path(directory) / f"{turbine}_model.joblib")


def training_mask(frame: pd.DataFrame) -> pd.Series:
    """Rows a power model should learn from.

    Hours with no measurement cannot teach anything, and hours flagged as
    curtailment or outage would teach the model that strong wind sometimes
    yields nothing -- an operational fact, but not one the weather can predict.
    They are excluded from fitting and kept for evaluation.
    """
    return (
        frame["power"].notna()
        & ~frame["is_anomaly_hour"].astype(bool)
        & frame["wind_speed_100m"].notna()
    )


def fit(
    train: pd.DataFrame,
    feature_columns: list[str],
    power_curve: pd.DataFrame,
    turbine: str,
    valid: pd.DataFrame | None = None,
    quantiles: tuple[float, ...] = config.QUANTILES,
    params: dict | None = None,
) -> TrainedModel:
    """Fit the point model and the quantile band on prepared feature rows."""
    params = {**BASE_PARAMS, **(params or {})}

    train_rows = train[training_mask(train)]
    x_train = train_rows[feature_columns]
    y_train = train_rows["power"]
    train_set = lgb.Dataset(x_train, y_train, free_raw_data=False)

    callbacks = [lgb.log_evaluation(0)]
    valid_sets = [train_set]
    if valid is not None and not valid.empty:
        valid_rows = valid[training_mask(valid)]
        valid_set = lgb.Dataset(
            valid_rows[feature_columns], valid_rows["power"], reference=train_set
        )
        valid_sets.append(valid_set)
        callbacks.append(lgb.early_stopping(EARLY_STOPPING, verbose=False))

    point = lgb.train(
        params, train_set, num_boost_round=NUM_ROUNDS, valid_sets=valid_sets, callbacks=callbacks
    )
    best_iteration = point.best_iteration or NUM_ROUNDS

    quantile_models: dict[float, lgb.Booster] = {}
    for alpha in quantiles:
        q_params = {**params, "objective": "quantile", "alpha": alpha, "metric": "quantile"}
        quantile_models[alpha] = lgb.train(
            q_params, train_set, num_boost_round=best_iteration, callbacks=[lgb.log_evaluation(0)]
        )

    return TrainedModel(
        point=point,
        quantiles=quantile_models,
        feature_columns=list(feature_columns),
        power_curve=power_curve,
        turbine=turbine,
        trained_rows=len(train_rows),
        best_iteration=best_iteration,
    )


def predict(model: TrainedModel, frame: pd.DataFrame) -> pd.DataFrame:
    """Predict power and the uncertainty band for prepared feature rows."""
    x = frame[model.feature_columns]
    out = pd.DataFrame(index=frame.index)
    out["forecast"] = np.clip(model.point.predict(x, num_iteration=model.best_iteration), 0, 1)

    for alpha, booster in sorted(model.quantiles.items()):
        out[f"p{int(alpha * 100)}"] = np.clip(booster.predict(x), 0, 1)

    # Quantile regressors are fitted independently and can cross; sorting each
    # row restores a coherent, non-decreasing predictive band.
    q_cols = [c for c in out.columns if c.startswith("p")]
    out[q_cols] = np.sort(out[q_cols].to_numpy(), axis=1)
    return out


def feature_importance(model: TrainedModel, top: int = 25) -> pd.DataFrame:
    gain = model.point.feature_importance("gain")
    return (
        pd.DataFrame({"feature": model.feature_columns, "gain": gain})
        .sort_values("gain", ascending=False)
        .head(top)
        .reset_index(drop=True)
    )
