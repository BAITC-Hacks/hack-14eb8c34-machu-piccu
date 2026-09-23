"""Online calibration: the forecaster learning from its own track record.

A model trained once on history slowly goes stale -- the NWP changes, the
season turns, the machine ages. Both corrections here are refitted from the
forecasts the system has already made and seen verified, using only data that
existed at issue time, so they keep working without retraining.

`BiasState` records what was applied and why, so every published forecast can
explain the adjustment it carries.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

QUANTILE_COLUMNS = ("p10", "p50", "p90")


@dataclass
class CalibrationState:
    """The correction in force at one issue time, and the evidence behind it."""

    bias: float = 0.0
    band_scale: float = 1.0
    bias_samples: int = 0
    band_samples: int = 0
    bias_window_days: int = 14
    band_window_days: int = 21

    def as_dict(self) -> dict:
        return asdict(self)

    def describe(self) -> str:
        if self.bias_samples == 0:
            return "no verified history yet - publishing uncorrected model output"
        direction = "over" if self.bias > 0 else "under"
        return (
            f"recent {self.bias_window_days}d record shows the model running "
            f"{direction}-forecast by {abs(self.bias):.3f} of rated power "
            f"({self.bias_samples} verified hours); band scaled x{self.band_scale:.2f}"
        )


class ForecastCalibrator:
    """Rolling bias correction plus conformal widening of the P10-P90 band."""

    def __init__(
        self,
        bias_window_days: int = 14,
        band_window_days: int = 21,
        target_coverage: float = 0.80,
        bias_cap: float = 0.12,
        min_bias_obs: int = 48,
        min_band_obs: int = 200,
    ) -> None:
        self.bias_window_days = bias_window_days
        self.band_window_days = band_window_days
        self.target_coverage = target_coverage
        self.bias_cap = bias_cap
        self.min_bias_obs = min_bias_obs
        self.min_band_obs = min_band_obs

    def fit(self, verification: pd.DataFrame, as_of: pd.Timestamp) -> CalibrationState:
        """Derive corrections from forecasts already verified before `as_of`.

        Only rows whose *target* time has passed are usable: a forecast for
        tomorrow teaches nothing until tomorrow happens.
        """
        state = CalibrationState(
            bias_window_days=self.bias_window_days, band_window_days=self.band_window_days
        )
        if verification is None or verification.empty:
            return state

        history = verification.dropna(subset=["power", "forecast"])
        history = history[history["time"] < as_of]
        if history.empty:
            return state

        bias_rows = history[history["time"] >= as_of - pd.Timedelta(days=self.bias_window_days)]
        if len(bias_rows) >= self.min_bias_obs:
            raw = float((bias_rows["forecast"] - bias_rows["power"]).mean())
            # Capped so one freak week cannot swing the forecast wildly.
            state.bias = float(np.clip(raw, -self.bias_cap, self.bias_cap))
            state.bias_samples = int(len(bias_rows))

        band_rows = history[history["time"] >= as_of - pd.Timedelta(days=self.band_window_days)]
        band_rows = band_rows.dropna(subset=list(QUANTILE_COLUMNS))
        if len(band_rows) >= self.min_band_obs:
            state.band_scale = self._conformal_scale(band_rows, state.bias)
            state.band_samples = int(len(band_rows))
        return state

    def _conformal_scale(self, rows: pd.DataFrame, bias: float) -> float:
        """Split-conformal scale factor that restores nominal coverage.

        The nonconformity score is each observation's distance from the median
        measured in units of the model's own half-band, so the widening respects
        where the model already knew it was uncertain instead of inflating the
        interval uniformly.
        """
        eps = 1e-6
        p10, p50, p90 = (rows[c] - bias for c in QUANTILE_COLUMNS)
        actual = rows["power"]
        lower = (p50 - actual) / (p50 - p10 + eps)
        upper = (actual - p50) / (p90 - p50 + eps)
        score = np.maximum(lower, upper).clip(lower=0)
        return float(np.clip(np.quantile(score, self.target_coverage), 0.5, 3.0))

    @staticmethod
    def apply(predictions: pd.DataFrame, state: CalibrationState) -> pd.DataFrame:
        """Shift the forecast by the learned bias, then rescale the band."""
        out = predictions.copy()
        for column in ("forecast", *QUANTILE_COLUMNS):
            if column in out:
                out[column] = (out[column] - state.bias).clip(0, 1)

        if {"p10", "p50", "p90"} <= set(out.columns) and state.band_scale != 1.0:
            median = out["p50"]
            out["p10"] = (median - state.band_scale * (median - out["p10"])).clip(0, 1)
            out["p90"] = (median + state.band_scale * (out["p90"] - median)).clip(0, 1)
        return out
