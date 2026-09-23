"""The forecast cycle: the deterministic engine the agent drives.

One cycle is the loop the brief asks for -- fetch external weather, prepare
data, run the model, produce an hourly forecast, analyse the result, and
recompute when the inputs change. Each step is a plain method here so it can be
run directly, replayed over history, or exposed to an LLM as a callable tool.

Nothing in this module talks to an LLM. That separation is deliberate: the
numbers a control room acts on are produced by code that always behaves the
same way, and the language model reasons *about* those numbers rather than
inventing them.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src import calibration, config, dataset, features, model, weather

PUBLISH_COLUMNS = [
    "turbine", "issue_time_utc", "time_utc", "time_local", "lead_hours",
    "forecast", "p10", "p50", "p90", "wind_speed_100m", "ws100_ens_std", "temperature_2m",
]

RAMP_THRESHOLD = 0.25       # change in normalised power within one hour
HIGH_SPREAD = 0.30          # P10-P90 width above which confidence is "low"
LOW_SPREAD = 0.15


@dataclass
class ForecastRun:
    """Everything one cycle produced, ready to publish or reason about."""

    issue_time: pd.Timestamp
    mode: str
    forecasts: dict[str, pd.DataFrame] = field(default_factory=dict)
    analysis: dict = field(default_factory=dict)
    calibration_states: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def combined(self) -> pd.DataFrame:
        if not self.forecasts:
            return pd.DataFrame()
        return pd.concat(self.forecasts.values(), ignore_index=True)

    def summary(self) -> dict:
        return {
            "issue_time_utc": self.issue_time.isoformat(),
            "mode": self.mode,
            "turbines": {k: v for k, v in self.analysis.items()},
            "calibration": {k: v.as_dict() for k, v in self.calibration_states.items()},
            "notes": self.notes,
        }


class ForecastPipeline:
    """Runs forecast cycles for both turbines against a trained model."""

    def __init__(
        self,
        mode: str = "archive",
        model_dir: Path | None = None,
        horizon_days: int = 2,
        calibrator: calibration.ForecastCalibrator | None = None,
    ) -> None:
        if mode not in {"archive", "live"}:
            raise ValueError("mode must be 'archive' (replay) or 'live' (operational)")
        self.mode = mode
        self.horizon_days = horizon_days
        self.model = model.TrainedModel.load(model_dir or config.ARTIFACT_DIR, "pooled")
        self.calibrator = calibrator or calibration.ForecastCalibrator()
        self._scada: dict[str, pd.DataFrame] = {}
        self._weather_cache: dict[tuple, dict] = {}
        self.verification_log = pd.DataFrame(
            columns=["turbine", "issue_time", "time", "forecast", "p10", "p50", "p90", "power"]
        )

    # -- step 1: external weather -----------------------------------------
    def fetch_weather(self, turbine_key: str, issue_time: pd.Timestamp) -> dict[int, pd.DataFrame]:
        """Get the multi-model ensemble forecast issued at `issue_time`.

        In archive mode this reads what each model predicted N days ahead, so a
        replay of February 2026 uses only what was knowable then. In live mode
        it calls the operational endpoint for the run happening now.
        """
        key = (turbine_key, issue_time.normalize(), self.mode)
        if key in self._weather_cache:
            return self._weather_cache[key]

        turbine = config.TURBINES[turbine_key]
        if self.mode == "archive":
            start = (issue_time + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            end = (issue_time + pd.Timedelta(days=self.horizon_days)).strftime("%Y-%m-%d")
            by_lead = dataset.load_weather_by_lead(
                turbine_key, start, end, lead_days=tuple(range(1, self.horizon_days + 1))
            )
        else:
            per_model = {
                name: weather.fetch_live(
                    turbine.latitude, turbine.longitude,
                    forecast_days=self.horizon_days + 1, nwp_model=name,
                )
                for name in config.NWP_MODELS
            }
            ensemble = dataset.build_ensemble_frame(per_model)
            # A live run predicts every horizon at once, so each lead slot reads
            # the same frame; `build_block` slices it by target date.
            by_lead = {lead: ensemble for lead in range(1, self.horizon_days + 1)}

        self._weather_cache[key] = by_lead
        return by_lead

    # -- step 2: data preparation -----------------------------------------
    def scada(self, turbine_key: str) -> pd.DataFrame:
        if turbine_key not in self._scada:
            self._scada[turbine_key] = dataset.scada_utc(turbine_key)
        return self._scada[turbine_key]

    def prepare(
        self, turbine_key: str, issue_time: pd.Timestamp, weather_by_lead: dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """Build the model-ready feature block for this issue time."""
        block = features.build_block(weather_by_lead, issue_time, horizon_days=self.horizon_days)
        if block.empty:
            return block

        state = dataset.persistence_state(self.scada(turbine_key), issue_time)
        frame = features.build_features(block, power_curve=None, persistence=state)
        frame = dataset.attach_power_curve_prior(frame, self.model.power_curve)
        frame["turbine"] = turbine_key
        frame["turbine_id"] = list(config.TURBINES).index(turbine_key)
        return frame

    # -- step 3/4: model and online calibration ---------------------------
    def predict(self, frame: pd.DataFrame, turbine_key: str, issue_time: pd.Timestamp):
        """Run the model, then apply corrections learned from verified history."""
        raw = model.predict(self.model, frame)
        history = self.verification_log[self.verification_log["turbine"] == turbine_key]
        state = self.calibrator.fit(history, as_of=issue_time)
        return self.calibrator.apply(raw, state), state

    # -- step 5: analysis --------------------------------------------------
    def analyse(self, published: pd.DataFrame, turbine_key: str) -> dict:
        """Turn 48 numbers into the handful of facts a dispatcher acts on."""
        fc = published["forecast"]
        band = published["p90"] - published["p10"]
        ramp = fc.diff()

        # Energy is the sum of hourly normalised power: "equivalent full-load
        # hours", directly proportional to MWh once scaled by rated capacity.
        day_ahead = published[published["lead_hours"] < 48]

        big_ramps = published.loc[ramp.abs() >= RAMP_THRESHOLD]
        mean_band = float(band.mean())
        confidence = "low" if mean_band > HIGH_SPREAD else "high" if mean_band < LOW_SPREAD else "medium"

        peak = published.loc[fc.idxmax()]
        trough = published.loc[fc.idxmin()]

        return {
            "turbine": turbine_key,
            "hours": int(len(published)),
            "energy_equivalent_full_load_hours": round(float(fc.sum()), 2),
            "day_ahead_energy_eflh": round(float(day_ahead["forecast"].sum()), 2),
            "mean_capacity_factor": round(float(fc.mean()), 3),
            "max_output": round(float(fc.max()), 3),
            "min_output": round(float(fc.min()), 3),
            "peak_hour_local": str(peak["time_local"]),
            "trough_hour_local": str(trough["time_local"]),
            "hours_near_rated": int((fc >= 0.9).sum()),
            "hours_below_cutin": int((fc <= 0.02).sum()),
            "mean_band_width": round(mean_band, 3),
            "confidence": confidence,
            "ramp_events": [
                {"time_local": str(r["time_local"]), "delta": round(float(ramp.loc[i]), 3)}
                for i, r in big_ramps.iterrows()
            ],
            "mean_ensemble_spread_ms": round(float(published["ws100_ens_std"].mean()), 2),
            "mean_wind_speed_ms": round(float(published["wind_speed_100m"].mean()), 2),
        }

    # -- step 6: publication ----------------------------------------------
    @staticmethod
    def _publishable(frame: pd.DataFrame, predictions: pd.DataFrame, issue_time) -> pd.DataFrame:
        out = frame[["time", "lead_hours", "wind_speed_100m", "ws100_ens_std", "temperature_2m", "turbine"]].copy()
        out = pd.concat([out.reset_index(drop=True), predictions.reset_index(drop=True)], axis=1)
        out["issue_time_utc"] = issue_time
        out = out.rename(columns={"time": "time_utc"})
        out["time_local"] = out["time_utc"] + pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)
        return out[PUBLISH_COLUMNS]

    # -- the full cycle ----------------------------------------------------
    def run_cycle(self, issue_time: pd.Timestamp | str, turbines: list[str] | None = None) -> ForecastRun:
        """Execute one complete forecast cycle for the requested turbines."""
        issue_time = pd.Timestamp(issue_time).normalize()
        run = ForecastRun(issue_time=issue_time, mode=self.mode)

        for turbine_key in turbines or list(config.TURBINES):
            weather_by_lead = self.fetch_weather(turbine_key, issue_time)
            frame = self.prepare(turbine_key, issue_time, weather_by_lead)
            if frame.empty:
                run.notes.append(f"{turbine_key}: no weather available for {issue_time.date()}")
                continue

            predictions, state = self.predict(frame, turbine_key, issue_time)
            published = self._publishable(frame, predictions, issue_time)

            run.forecasts[turbine_key] = published
            run.calibration_states[turbine_key] = state
            run.analysis[turbine_key] = self.analyse(published, turbine_key)
            run.analysis[turbine_key]["calibration"] = state.describe()
        return run

    # -- step 7: learning from what actually happened ----------------------
    def record(self, run: ForecastRun) -> None:
        """Append a run to the verification log and attach any known actuals.

        This is what closes the loop: once these hours are measured, the next
        cycle's calibration sees its own past errors.
        """
        rows = []
        for turbine_key, published in run.forecasts.items():
            actual = self.scada(turbine_key)[["time", "power"]]
            merged = published.merge(actual, left_on="time_utc", right_on="time", how="left")
            rows.append(
                pd.DataFrame({
                    "turbine": turbine_key,
                    "issue_time": run.issue_time,
                    "time": published["time_utc"].to_numpy(),
                    "forecast": published["forecast"].to_numpy(),
                    "p10": published["p10"].to_numpy(),
                    "p50": published["p50"].to_numpy(),
                    "p90": published["p90"].to_numpy(),
                    "power": merged["power"].to_numpy(),
                })
            )
        if rows:
            self.verification_log = pd.concat([self.verification_log, *rows], ignore_index=True)

    def detect_input_change(
        self, turbine_key: str, issue_time: pd.Timestamp, previous: ForecastRun
    ) -> dict:
        """Compare a fresh forecast against the last one for the same hours.

        The brief asks the system to recompute when inputs update. This is the
        trigger: refetch, re-run, and report how much the answer moved, so a
        recompute is published only when it actually says something new.
        """
        fresh = self.run_cycle(issue_time, turbines=[turbine_key])
        if turbine_key not in fresh.forecasts or turbine_key not in previous.forecasts:
            return {"changed": False, "reason": "no comparable forecast"}

        new = fresh.forecasts[turbine_key].set_index("time_utc")["forecast"]
        old = previous.forecasts[turbine_key].set_index("time_utc")["forecast"]
        overlap = new.index.intersection(old.index)
        if len(overlap) == 0:
            return {"changed": False, "reason": "no overlapping hours"}

        delta = (new.loc[overlap] - old.loc[overlap]).abs()
        return {
            "changed": bool(delta.mean() > 0.02),
            "mean_abs_change": round(float(delta.mean()), 4),
            "max_abs_change": round(float(delta.max()), 4),
            "overlapping_hours": int(len(overlap)),
            "run": fresh,
        }


def write_outputs(run: ForecastRun, directory: Path | None = None) -> dict[str, Path]:
    """Persist a run as an hourly CSV plus a JSON analysis summary."""
    directory = Path(directory or config.OUTPUT_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = run.issue_time.strftime("%Y%m%d")

    csv_path = directory / f"forecast_{stamp}.csv"
    json_path = directory / f"analysis_{stamp}.json"
    run.combined().to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(run.summary(), indent=2, default=str))
    return {"csv": csv_path, "json": json_path}
