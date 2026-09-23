"""Load and clean the turbine SCADA history, and resample it to hourly."""
from __future__ import annotations

import glob

import numpy as np
import pandas as pd

from src import config

RAW_COLUMNS = {
    "ID": "id",
    "Статистическое время": "ts",
    "Средняя скорость ветра(m/s)": "ws_scada",
    "Нормализованная активная мощность": "power",
    "Средняя температура окружающей среды(°C)": "temp_scada",
}


def load_raw(turbine_key: str) -> pd.DataFrame:
    """Read one turbine's 10-minute SCADA CSV into a tidy frame."""
    turbine = config.TURBINES[turbine_key]
    matches = sorted(config.DATASET_DIR.glob(turbine.csv_glob))
    if not matches:
        raise FileNotFoundError(
            f"No SCADA CSV matching {turbine.csv_glob!r} in {config.DATASET_DIR}"
        )
    df = pd.read_csv(matches[0])
    df = df.rename(columns=RAW_COLUMNS)
    df["ts"] = pd.to_datetime(df["ts"])
    df = df[["ts", "ws_scada", "power", "temp_scada"]].sort_values("ts")
    return df.reset_index(drop=True)


def flag_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Mark 10-minute records that should not teach the model a power curve.

    Two failure modes matter here. An *outage or curtailment* shows up as
    near-zero power while the anemometer still reads well above cut-in, and a
    *stuck sensor* shows up as a wind speed that does not move at all for an
    hour or more. Both are real operational states, but neither reflects the
    wind-to-power physics we want the model to learn.
    """
    out = df.copy()

    # Cut-in for this class of machine sits near 3 m/s; by 6 m/s a healthy
    # turbine is unambiguously producing.
    out["is_curtailed"] = (out["ws_scada"] >= 6.0) & (out["power"] <= 0.02)

    stuck = out["ws_scada"].rolling(6, min_periods=6).std() == 0
    out["is_stuck_sensor"] = stuck.fillna(False)

    out["is_anomaly"] = out["is_curtailed"] | out["is_stuck_sensor"]
    return out


def to_hourly(df: pd.DataFrame, min_samples: int = 4) -> pd.DataFrame:
    """Aggregate 10-minute records to hourly means.

    An hour is only trusted when at least `min_samples` of its six slots are
    present, so that a single surviving record after a long outage does not
    masquerade as a full hour of production.
    """
    work = df.set_index("ts")
    grouped = work.resample("1h")

    hourly = pd.DataFrame(
        {
            "power": grouped["power"].mean(),
            "ws_scada": grouped["ws_scada"].mean(),
            "temp_scada": grouped["temp_scada"].mean(),
            "n_samples": grouped["power"].count(),
            "anomaly_frac": grouped["is_anomaly"].mean(),
            "curtailed_frac": grouped["is_curtailed"].mean(),
            "stuck_frac": grouped["is_stuck_sensor"].mean(),
        }
    )
    hourly.loc[hourly["n_samples"] < min_samples, ["power", "ws_scada", "temp_scada"]] = np.nan
    hourly["is_anomaly_hour"] = hourly["anomaly_frac"].fillna(0) > 0.5
    # Kept apart on purpose. A stuck sensor is bad data and must never train the
    # model. Curtailment is a real operational state that genuinely reduces
    # delivered energy, so whether to train on it is a modelling choice, not a
    # data-cleaning one -- see the training-mask experiment in the README.
    hourly["is_curtailed_hour"] = hourly["curtailed_frac"].fillna(0) > 0.5
    hourly["is_stuck_hour"] = hourly["stuck_frac"].fillna(0) > 0.5
    return hourly.reset_index().rename(columns={"ts": "time"})


def load_hourly(turbine_key: str) -> pd.DataFrame:
    """Full SCADA pipeline for one turbine: raw -> flagged -> hourly."""
    return to_hourly(flag_anomalies(load_raw(turbine_key)))


def fit_power_curve(ws: pd.Series, power: pd.Series, n_bins: int = 60) -> pd.DataFrame:
    """Fit a monotone empirical power curve by binning wind speed.

    Returned as a lookup table; `apply_power_curve` interpolates it. Fitting is
    always done on training rows only, so the curve carries no test-set signal.
    """
    valid = ws.notna() & power.notna()
    ws, power = ws[valid], power[valid]
    edges = np.linspace(0, 25, n_bins + 1)
    centres = (edges[:-1] + edges[1:]) / 2
    binned = pd.cut(ws, edges, labels=False, include_lowest=True)
    means = power.groupby(binned).mean()

    curve = pd.Series(index=range(n_bins), dtype=float)
    curve.update(means)
    curve = curve.interpolate(limit_direction="both").fillna(0.0)
    # A power curve is physically non-decreasing until cut-out; enforce it so
    # sparse high-wind bins cannot introduce spurious dips.
    curve = pd.Series(np.maximum.accumulate(curve.to_numpy()), index=curve.index)
    return pd.DataFrame({"ws": centres, "power": curve.to_numpy()})


def apply_power_curve(curve: pd.DataFrame, ws: pd.Series) -> pd.Series:
    """Interpolate a fitted power curve at arbitrary wind speeds."""
    return pd.Series(
        np.interp(ws.to_numpy(dtype=float), curve["ws"], curve["power"]),
        index=ws.index,
    ).clip(0, 1)
