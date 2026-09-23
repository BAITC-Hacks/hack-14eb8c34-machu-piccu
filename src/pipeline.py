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
from pathlib import Path

import numpy as np
import pandas as pd

from src import calibration, config, dataset, features, model, weather

PUBLISH_COLUMNS = [
    "turbine", "policy", "issue_date", "issue_time_utc", "issue_time_local",
    "time_utc", "time_local", "horizon_day", "lead_hours", "nwp_lead_hours",
    "forecast", "p10", "p50", "p90", "wind_speed_100m", "ws100_ens_std", "temperature_2m",
]

RAMP_THRESHOLD = 0.25       # change in normalised power within one hour
HIGH_SPREAD = 0.30          # P10-P90 width above which confidence is "low"
LOW_SPREAD = 0.15
REVISION_THRESHOLD = 0.02   # mean |change| of normalised power that counts as "inputs moved"


@dataclass
class ForecastRun:
    """Everything one cycle produced, ready to publish or reason about."""

    issue_time: pd.Timestamp            # cycle date D (a local calendar day)
    mode: str
    policy: str = config.DEFAULT_POLICY
    forecasts: dict[str, pd.DataFrame] = field(default_factory=dict)
    analysis: dict = field(default_factory=dict)
    calibration_states: dict = field(default_factory=dict)
    revisions: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def combined(self) -> pd.DataFrame:
        if not self.forecasts:
            return pd.DataFrame()
        return pd.concat(self.forecasts.values(), ignore_index=True)

    def summary(self) -> dict:
        return {
            "issue_date": self.issue_time.strftime("%Y-%m-%d"),
            "issue_time_utc": features.issue_moment_utc(self.issue_time, self.policy).isoformat(),
            "policy": self.policy,
            "mode": self.mode,
            "turbines": {k: v for k, v in self.analysis.items()},
            "calibration": {k: v.as_dict() for k, v in self.calibration_states.items()},
            "revisions": self.revisions,
            "notes": self.notes,
        }


class ForecastPipeline:
    """Runs forecast cycles for both turbines against a trained model."""

    def __init__(
        self,
        mode: str = "archive",
        policy: str = config.DEFAULT_POLICY,
        model_dir: Path | None = None,
        horizon_days: int = config.HORIZON_DAYS,
        calibrator: calibration.ForecastCalibrator | None = None,
    ) -> None:
        if mode not in {"archive", "live"}:
            raise ValueError("mode must be 'archive' (replay) or 'live' (operational)")
        if policy not in config.ASOF_POLICIES:
            raise ValueError(f"policy must be one of {list(config.ASOF_POLICIES)}")
        self.mode = mode
        self.policy = policy
        self.offset = config.ASOF_POLICIES[policy]
        self.horizon_days = horizon_days
        self.model = model.TrainedModel.load(model_dir or config.ARTIFACT_DIR, "pooled")
        self.calibrator = calibrator or calibration.ForecastCalibrator()
        self._scada: dict[str, pd.DataFrame] = {}
        self._archive: dict[str, dict[int, pd.DataFrame]] = {}
        self._weather_cache: dict[tuple, dict] = {}
        self.verification_log = pd.DataFrame(
            columns=["turbine", "issue_time", "time", "horizon_day",
                     "forecast", "p10", "p50", "p90", "power"]
        )

    @property
    def leads(self) -> tuple[int, ...]:
        """NWP lead days this policy reads: (1, 2) for rolling, (2, 3) for strict."""
        return tuple(range(1 + self.offset, self.horizon_days + self.offset + 1))

    def issue_moment(self, issue_time: pd.Timestamp) -> pd.Timestamp:
        return features.issue_moment_utc(issue_time, self.policy)

    # -- step 1: external weather -----------------------------------------
    def fetch_weather(
        self, turbine_key: str, issue_time: pd.Timestamp, refresh: bool = False
    ) -> dict[int, pd.DataFrame]:
        """Get the multi-model ensemble forecast for cycle date `issue_time`.

        In archive mode this reads what each model predicted N days ahead, so a
        replay of February 2026 uses only what was knowable then. In live mode
        it calls the operational endpoint for the run happening now; `refresh`
        bypasses the in-memory copy so a later call really re-reads the source.
        """
        key = (turbine_key, issue_time.normalize(), self.mode)
        if not refresh and key in self._weather_cache:
            return self._weather_cache[key]

        turbine = config.TURBINES[turbine_key]
        if self.mode == "archive":
            by_lead = self._archived_weather(turbine_key, issue_time)
        else:
            per_model = {
                name: weather.fetch_live(
                    turbine.latitude, turbine.longitude,
                    forecast_days=self.horizon_days + 2, nwp_model=name,
                )
                for name in config.NWP_MODELS
            }
            ensemble = dataset.build_ensemble_frame(per_model)
            # A live run predicts every horizon at once, so each lead slot reads
            # the same frame; `build_block` slices it by target date.
            by_lead = {lead: ensemble for lead in self.leads}

        self._weather_cache[key] = by_lead
        return by_lead

    def _archived_weather(self, turbine_key: str, issue_time: pd.Timestamp) -> dict[int, pd.DataFrame]:
        """The lead archive for one turbine, loaded once and sliced per cycle.

        The whole archive window is fetched in the same six-month chunks the
        training replay uses, so the requests are already in `cache/` and a
        replay makes no network calls at all. A cycle outside that window
        (e.g. a replay of a later month) falls back to fetching its own days.
        """
        window_start = pd.Timestamp(config.LEAD_ARCHIVE_START)
        window_end = pd.Timestamp(config.ARCHIVE_END)
        last_target = issue_time + pd.Timedelta(days=self.horizon_days)
        if window_start <= issue_time and last_target <= window_end:
            if turbine_key not in self._archive:
                self._archive[turbine_key] = dataset.load_weather_by_lead(
                    turbine_key, window_start.strftime("%Y-%m-%d"), window_end.strftime("%Y-%m-%d"),
                    lead_days=self.leads,
                )
            return self._archive[turbine_key]
        # Local day D+1 starts at 18:00 UTC of D, so the UTC window runs D .. D+horizon.
        return dataset.load_weather_by_lead(
            turbine_key, issue_time.strftime("%Y-%m-%d"), last_target.strftime("%Y-%m-%d"),
            lead_days=self.leads,
        )

    # -- step 2: data preparation -----------------------------------------
    def scada(self, turbine_key: str) -> pd.DataFrame:
        if turbine_key not in self._scada:
            self._scada[turbine_key] = dataset.scada_utc(turbine_key)
        return self._scada[turbine_key]

    def prepare(
        self, turbine_key: str, issue_time: pd.Timestamp, weather_by_lead: dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """Build the model-ready feature block for this cycle."""
        block = features.build_block(
            weather_by_lead, issue_time, horizon_days=self.horizon_days, policy=self.policy
        )
        if block.empty:
            return block

        state = dataset.persistence_state(self.scada(turbine_key), self.issue_moment(issue_time))
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
        state = self.calibrator.fit(history, as_of=self.issue_moment(issue_time))
        return self.calibrator.apply(raw, state), state

    # -- step 5: analysis --------------------------------------------------
    def analyse(self, published: pd.DataFrame, turbine_key: str) -> dict:
        """Turn 48 numbers into the handful of facts a dispatcher acts on."""
        fc = published["forecast"]
        band = published["p90"] - published["p10"]
        ramp = fc.diff()

        # Energy is the sum of hourly normalised power: "equivalent full-load
        # hours", directly proportional to MWh once scaled by rated capacity.
        day_ahead = published[published["horizon_day"] == 1]

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
            "nwp_lead_hours": sorted(int(v) for v in published["nwp_lead_hours"].unique()),
        }

    # -- step 6: publication ----------------------------------------------
    @staticmethod
    def _publishable(
        frame: pd.DataFrame, predictions: pd.DataFrame, issue_time: pd.Timestamp, policy: str
    ) -> pd.DataFrame:
        tz = pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)
        out = frame[[
            "time", "horizon_day", "lead_hours", "nwp_lead_hours",
            "wind_speed_100m", "ws100_ens_std", "temperature_2m", "turbine",
        ]].copy()
        out = pd.concat([out.reset_index(drop=True), predictions.reset_index(drop=True)], axis=1)
        out["policy"] = policy
        out["issue_date"] = issue_time.normalize()
        out["issue_time_utc"] = features.issue_moment_utc(issue_time, policy)
        out["issue_time_local"] = out["issue_time_utc"] + tz
        out = out.rename(columns={"time": "time_utc"})
        out["time_local"] = out["time_utc"] + tz
        return out[PUBLISH_COLUMNS]

    # -- the full cycle ----------------------------------------------------
    def run_cycle(
        self, issue_time: pd.Timestamp | str, turbines: list[str] | None = None, refresh: bool = False
    ) -> ForecastRun:
        """Execute one complete forecast cycle for the requested turbines."""
        issue_time = pd.Timestamp(issue_time).normalize()
        run = ForecastRun(issue_time=issue_time, mode=self.mode, policy=self.policy)

        for turbine_key in turbines or list(config.TURBINES):
            weather_by_lead = self.fetch_weather(turbine_key, issue_time, refresh=refresh)
            frame = self.prepare(turbine_key, issue_time, weather_by_lead)
            if frame.empty:
                run.notes.append(f"{turbine_key}: no weather available for {issue_time.date()}")
                continue

            predictions, state = self.predict(frame, turbine_key, issue_time)
            published = self._publishable(frame, predictions, issue_time, self.policy)

            run.forecasts[turbine_key] = published
            run.calibration_states[turbine_key] = state
            run.analysis[turbine_key] = self.analyse(published, turbine_key)
            run.analysis[turbine_key]["calibration"] = state.describe()
        return run

    # -- step 7: learning from what actually happened ----------------------
    def record(self, run: ForecastRun) -> None:
        """Append a run to the verification log and attach any known actuals.

        This is what closes the loop: once these hours are measured, the next
        cycle's calibration sees its own past errors -- and the next cycle can
        measure how much fresher inputs moved the answer.
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
                    "horizon_day": published["horizon_day"].to_numpy(),
                    "forecast": published["forecast"].to_numpy(),
                    "p10": published["p10"].to_numpy(),
                    "p50": published["p50"].to_numpy(),
                    "p90": published["p90"].to_numpy(),
                    "power": merged["power"].to_numpy(),
                })
            )
        if rows:
            self.verification_log = pd.concat([self.verification_log, *rows], ignore_index=True)

    def previous_forecast(self, turbine_key: str, issue_time: pd.Timestamp) -> pd.Series | None:
        """What this system said one cycle earlier for the hours now day-ahead.

        Yesterday's D+2 block covers today's D+1 block. It is read from the
        verification log; a standalone cycle with no log reconstructs
        yesterday's run from the archive (no publishing, no recording).
        """
        prev_issue = issue_time - pd.Timedelta(days=1)
        log = self.verification_log
        rows = log[(log["turbine"] == turbine_key) & (log["issue_time"] == prev_issue)]
        if rows.empty:
            prev = self.run_cycle(prev_issue, turbines=[turbine_key])
            if turbine_key not in prev.forecasts:
                return None
            rows = prev.forecasts[turbine_key].rename(columns={"time_utc": "time"})
        return rows.set_index("time")["forecast"].astype(float)

    def revision_vs_previous(self, turbine_key: str, issue_time: pd.Timestamp, run: ForecastRun) -> dict:
        """How much did fresher NWP input move the day-ahead forecast?

        In a replay the inputs can only update once a day, when the next set
        of model runs enters the archive. This measures that update on the
        hours both cycles forecast, which is exactly the "recompute when inputs
        change" step of the brief, made observable.
        """
        current = run.forecasts.get(turbine_key)
        if current is None:
            return {"changed": False, "reason": "no forecast for this turbine"}
        today = current[current["horizon_day"] == 1].set_index("time_utc")["forecast"].astype(float)
        previous = self.previous_forecast(turbine_key, issue_time)
        if previous is None:
            return {"changed": False, "reason": "no earlier forecast covers these hours"}
        overlap = today.index.intersection(previous.index)
        if len(overlap) == 0:
            return {"changed": False, "reason": "no overlapping hours with the previous cycle"}

        delta = today.loc[overlap] - previous.loc[overlap]
        return {
            "changed": bool(delta.abs().mean() > REVISION_THRESHOLD),
            "units": "fraction of rated power",
            "previous_issue_date": (issue_time - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "overlapping_hours": int(len(overlap)),
            "mean_abs_change": round(float(delta.abs().mean()), 4),
            "mean_signed_change": round(float(delta.mean()), 4),
            "max_abs_change": round(float(delta.abs().max()), 4),
            "previous_nwp_lead_hours": int(24 * (2 + self.offset)),
            "current_nwp_lead_hours": int(24 * (1 + self.offset)),
        }

    def detect_input_change(
        self, turbine_key: str, issue_time: pd.Timestamp, previous: ForecastRun
    ) -> dict:
        """The recompute trigger.

        Live mode refetches the operational forecast and reports how much the
        answer moved. Archive mode cannot conjure a newer run than the archive
        holds, so the honest comparison is against the previous cycle: the
        arrival of today's NWP runs *is* the input update.
        """
        if self.mode == "archive":
            return self.revision_vs_previous(turbine_key, issue_time, previous)

        fresh = self.run_cycle(issue_time, turbines=[turbine_key], refresh=True)
        if turbine_key not in fresh.forecasts or turbine_key not in previous.forecasts:
            return {"changed": False, "reason": "no comparable forecast"}

        new = fresh.forecasts[turbine_key].set_index("time_utc")["forecast"]
        old = previous.forecasts[turbine_key].set_index("time_utc")["forecast"]
        overlap = new.index.intersection(old.index)
        if len(overlap) == 0:
            return {"changed": False, "reason": "no overlapping hours"}

        delta = (new.loc[overlap] - old.loc[overlap]).abs()
        return {
            "changed": bool(delta.mean() > REVISION_THRESHOLD),
            "units": "fraction of rated power",
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

    csv_path = directory / f"forecast_{stamp}_{run.policy}.csv"
    json_path = directory / f"analysis_{stamp}_{run.policy}.json"
    run.combined().to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(run.summary(), indent=2, default=str))
    return {"csv": csv_path, "json": json_path}
