"""Daily issue schedule with fixed-lead archive provenance kept distinct from run time."""
from datetime import timedelta, timezone
import numpy as np
import pandas as pd


def build_schedule(config, decision):
    horizon = config["forecast_horizon_hours"]
    if not 1 <= horizon <= 48 or not 0 <= config["forecast_run_hour"] <= 23:
        raise ValueError("Supported horizons 1..48 and run hours 0..23")
    tz = timezone(timedelta(hours=decision["selected_offset_hours"]))
    start = pd.Timestamp(config["training_target_start"]).tz_localize(tz)
    end = pd.Timestamp(config["competition_end"]).tz_localize(tz)
    issues = pd.date_range(start.normalize() - pd.Timedelta(days=2), end.normalize(), freq="D") + pd.Timedelta(hours=config["forecast_run_hour"])
    frame = pd.DataFrame({"forecast_issue_time": issues.repeat(horizon), "lead_hours": np.tile(np.arange(1, horizon + 1), len(issues))})
    frame["target_time"] = frame.forecast_issue_time + pd.to_timedelta(frame.lead_hours, unit="h")
    frame = frame[(frame.target_time >= start) & (frame.target_time <= end)].copy()
    frame["archive_day"] = np.where(frame.lead_hours <= 24, 1, 2)
    frame["forecast_day"] = frame.archive_day
    frame["horizon_bucket"] = np.where(frame.archive_day == 1, "D1", "D2")
    frame["target_local_time"] = frame.target_time.dt.tz_localize(None)
    for col in ["forecast_issue_time", "target_time"]:
        frame[col] = frame[col].dt.tz_convert("UTC")
    frame["archive_nominal_lead_hours"] = 24 * frame.archive_day
    frame["archive_reference_time"] = frame.target_time - pd.to_timedelta(frame.archive_nominal_lead_hours, unit="h")
    frame["dataset_split"] = np.where(frame.target_local_time <= pd.Timestamp(config["train_end"]), "train", "competition_test")
    return frame.reset_index(drop=True)
