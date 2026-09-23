"""Hourly SCADA aggregation with explicit sample and observation availability rules."""
from datetime import timedelta, timezone
import pandas as pd
from .input_data import ROOT, TIMESTAMP, NUMERIC


def read_hourly_local(config):
    pieces = []
    for turbine, filename in config["input_files"].items():
        frame = pd.read_csv(ROOT / filename)
        frame = frame.rename(columns={TIMESTAMP: "target_local_time", NUMERIC["wind_speed"]: "eval_actual_wind_speed",
            NUMERIC["temperature"]: "eval_actual_temperature", NUMERIC["normalized_active_power"]: "normalized_active_power"})
        frame["target_local_time"] = pd.to_datetime(frame["target_local_time"], format="mixed")
        if frame.target_local_time.duplicated().any():
            raise ValueError("SCADA duplicate timestamps must be resolved explicitly")
        columns = ["eval_actual_wind_speed", "eval_actual_temperature", "normalized_active_power"]
        data = frame.set_index("target_local_time")[columns].sort_index()
        means = data.resample("h", label="left", closed="left").mean()
        counts = data.resample("h").count()
        means["scada_samples"] = counts.min(axis=1).astype("int16")
        means["scada_hour_complete"] = means.scada_samples >= config["minimum_hourly_samples"]
        means.loc[~means.scada_hour_complete, columns] = float("nan")
        means["turbine_id"] = turbine
        pieces.append(means.reset_index())
    return pd.concat(pieces, ignore_index=True)


def localize_scada(local, decision, config):
    frame = local.copy()
    tz = timezone(timedelta(hours=decision["selected_offset_hours"]))
    frame["target_time"] = frame.target_local_time.dt.tz_localize(tz).dt.tz_convert("UTC")
    # Left-labelled hour completes after 60 min; an additional conservative delay follows.
    frame["observation_available_time"] = frame.target_time + pd.Timedelta(minutes=60 + config["observation_publication_delay_minutes"])
    return frame
