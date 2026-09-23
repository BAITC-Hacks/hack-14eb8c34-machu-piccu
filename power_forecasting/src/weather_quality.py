"""Deterministic, documented masks; raw values are retained, never imputed."""
import numpy as np
import pandas as pd

BOUNDS = {"wind_speed_10m": (0, 75), "wind_speed_100m": (0, 100),
          "wind_direction_10m": (0, 360), "wind_direction_100m": (0, 360),
          "temperature_2m": (-90, 65), "surface_pressure": (300, 1100),
          "relative_humidity_2m": (0, 100), "wind_gusts_10m": (0, 150)}
CORE = ["wind_speed_100m", "wind_direction_100m", "temperature_2m"]


def quality_checks(frame, config):
    out = frame.copy()
    counts, usable, scores = [], [], []
    for model in config["weather_models"]:
        validity = []
        invalids = []
        for variable in config["weather_variables"]:
            col = f"{model}_{variable}"
            lower, upper = BOUNDS[variable]
            flag = out[col].notna() & np.isfinite(out[col]) & out[col].between(lower, upper)
            out[f"{col}_valid"] = flag
            validity.append(flag)
            invalids.append(out[col].notna() & ~flag)
        flags = pd.concat(validity, axis=1)
        available = out[[f"{model}_{v}" for v in config["weather_variables"]]].notna().any(axis=1)
        out[f"{model}_available"] = available
        out[f"{model}_missing_values_count"] = out[[f"{model}_{v}" for v in config["weather_variables"]]].isna().sum(axis=1).astype("int8")
        out[f"{model}_impossible_values_count"] = pd.concat(invalids, axis=1).sum(axis=1).astype("int8")
        out[f"{model}_partial_coverage"] = available & ~flags.all(axis=1)
        out[f"{model}_quality_ok"] = out[[f"{model}_{v}_valid" for v in CORE]].all(axis=1) & ~out[f"{model}_api_error"] & ~out[f"{model}_missing_target_hour"]
        out[f"{model}_duplicate_forecast"] = False  # duplicate keys fail before this stage
        out[f"{model}_timestamps_consistent"] = out.archive_reference_time <= out.forecast_issue_time
        # Unknown is not the same as fresh. Previous Runs exposes no precise run timestamp.
        out[f"{model}_run_time"] = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns, UTC]")
        out[f"{model}_estimated_availability_time"] = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns, UTC]")
        out[f"{model}_stale_run"] = pd.Series(pd.NA, index=out.index, dtype="boolean")
        counts.append(available.astype(int))
        usable.append(out[f"{model}_quality_ok"].astype(int))
        scores.append(flags.sum(axis=1))
    out["weather_models_available_count"] = sum(counts).astype("int8")
    out["weather_models_usable_count"] = sum(usable).astype("int8")
    out["weather_data_quality_score"] = sum(scores) / (len(config["weather_variables"]) * len(config["weather_models"]))
    out["weather_critical_missing"] = out.weather_models_usable_count == 0
    return out.copy()
