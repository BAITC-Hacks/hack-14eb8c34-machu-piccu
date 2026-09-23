"""Forecast scoring, including the baselines a wind forecast must beat."""
from __future__ import annotations

import numpy as np
import pandas as pd


def point_metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
    """Standard accuracy metrics on normalised power (so MAE == nMAE)."""
    valid = actual.notna() & predicted.notna()
    a, p = actual[valid].to_numpy(), predicted[valid].to_numpy()
    if len(a) == 0:
        return {"n": 0, "mae": np.nan, "rmse": np.nan, "bias": np.nan, "r2": np.nan}
    error = p - a
    ss_res = float((error**2).sum())
    ss_tot = float(((a - a.mean()) ** 2).sum())
    return {
        "n": int(len(a)),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt((error**2).mean())),
        "bias": float(error.mean()),
        "r2": float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan,
    }


def pinball_loss(actual: pd.Series, predicted: pd.Series, alpha: float) -> float:
    """Quantile (pinball) loss -- the proper score for a quantile forecast."""
    valid = actual.notna() & predicted.notna()
    a, p = actual[valid].to_numpy(), predicted[valid].to_numpy()
    if len(a) == 0:
        return float("nan")
    diff = a - p
    return float(np.maximum(alpha * diff, (alpha - 1) * diff).mean())


def interval_coverage(actual: pd.Series, lower: pd.Series, upper: pd.Series) -> dict[str, float]:
    """How often the truth lands inside the band, and how wide the band is.

    A P10-P90 band should cover about 80% of outcomes; much more means the
    band is uselessly wide, much less means it is overconfident.
    """
    valid = actual.notna() & lower.notna() & upper.notna()
    a, lo, hi = actual[valid], lower[valid], upper[valid]
    if len(a) == 0:
        return {"coverage": np.nan, "mean_width": np.nan}
    return {
        "coverage": float(((a >= lo) & (a <= hi)).mean()),
        "mean_width": float((hi - lo).mean()),
    }


def skill_score(model_error: float, baseline_error: float) -> float:
    """Fractional error reduction against a baseline; 0 means no better."""
    if not np.isfinite(baseline_error) or baseline_error == 0:
        return float("nan")
    return float(1 - model_error / baseline_error)


def build_baselines(frame: pd.DataFrame, climatology: pd.Series | None = None) -> pd.DataFrame:
    """Reference forecasts that any useful model must outperform.

    `persistence` repeats the last full day observed before issue time -- the
    standard naive benchmark. `power_curve` is the site's fitted curve applied
    to forecast wind, i.e. a competent forecast with no machine learning at
    all; beating it is what justifies the model.
    """
    out = pd.DataFrame(index=frame.index)
    out["persistence"] = frame["last_power_24h"]
    out["power_curve"] = frame["pc_prior"]
    if climatology is not None:
        key = frame["local_hour"].round().astype(int) % 24
        out["climatology"] = key.map(climatology).astype(float)
    else:
        out["climatology"] = frame["power"].mean()
    return out


def evaluate(
    frame: pd.DataFrame,
    prediction_col: str = "forecast",
    actual_col: str = "power",
    baselines: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Score the model and every baseline on the same rows, side by side."""
    rows = []
    model_row = point_metrics(frame[actual_col], frame[prediction_col])
    model_row["model"] = "WindAgent"
    rows.append(model_row)

    if baselines is not None:
        for name in baselines.columns:
            row = point_metrics(frame[actual_col], baselines[name])
            row["model"] = name
            rows.append(row)

    table = pd.DataFrame(rows).set_index("model")
    if baselines is not None and "persistence" in baselines:
        ref = table.loc["persistence", "mae"]
        table["skill_vs_persistence"] = [skill_score(m, ref) for m in table["mae"]]
    return table
