"""Explicit feature allowlist excludes all outcomes and observation-derived metadata."""
import numpy as np
import pandas as pd


def engineer_features(frame, config):
    out = frame.copy()
    calendar = out.target_local_time.dt
    out["target_hour"] = calendar.hour
    out["target_day_of_week"] = calendar.dayofweek
    out["target_month"] = calendar.month
    out["target_day_of_year"] = calendar.dayofyear
    out["hour_sin"] = np.sin(2 * np.pi * calendar.hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * calendar.hour / 24)
    days_in_year = np.where(calendar.is_leap_year, 366, 365)
    out["day_of_year_sin"] = np.sin(2 * np.pi * (calendar.dayofyear - 1) / days_in_year)
    out["day_of_year_cos"] = np.cos(2 * np.pi * (calendar.dayofyear - 1) / days_in_year)
    for prefix in list(config["weather_models"]) + ["ensemble"]:
        for height in ["10m", "100m"]:
            col = f"{prefix}_wind_direction_{height}"
            values = out[col]
            if prefix != "ensemble":
                values = values.where(out[f"{col}_valid"])
            out[f"{col}_sin"] = np.sin(np.deg2rad(values))
            out[f"{col}_cos"] = np.cos(np.deg2rad(values))
    features = ["turbine_id", "lead_hours", "horizon_bucket", "archive_nominal_lead_hours",
        "target_hour", "target_day_of_week", "target_month", "target_day_of_year", "hour_sin", "hour_cos", "day_of_year_sin", "day_of_year_cos",
        "weather_models_available_count", "weather_models_usable_count", "weather_data_quality_score", "weather_critical_missing", "best_weather_model_recent",
        "wind_weights_cold_start", "temperature_weights_cold_start"]
    quality_suffixes = ["available", "quality_ok", "missing_values_count", "impossible_values_count", "partial_coverage", "api_error", "missing_target_hour"]
    for model in config["weather_models"]:
        for variable in config["weather_variables"]:
            features.extend([f"{model}_{variable}", f"{model}_{variable}_valid"])
        features.extend(f"{model}_{suffix}" for suffix in quality_suffixes)
        features.extend([f"{model}_weight", f"{model}_temperature_weight"])
        for kind in ["wind", "temperature"]:
            for metric in ["mae", "rmse", "bias", "n"]:
                features.extend(f"{model}_{kind}_{metric}_{days}d" for days in config["rolling_windows"])
    for variable in config["weather_variables"]:
        features.extend([f"{variable}_mean", f"ensemble_{variable}"])
    features += [col for col in out if col.endswith(("_models_std", "_models_range", "_circular_dispersion"))]
    for prefix in list(config["weather_models"]) + ["ensemble"]:
        for height in ["10m", "100m"]:
            features.extend([f"{prefix}_wind_direction_{height}_sin", f"{prefix}_wind_direction_{height}_cos"])
    if len(features) != len(set(features)):
        raise ValueError("Duplicate feature allowlist entries")
    return out.copy(), features
