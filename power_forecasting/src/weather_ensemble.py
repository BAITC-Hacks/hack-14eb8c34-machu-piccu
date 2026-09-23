"""Replaceable inverse-MAE weighting and circular direction ensembles."""
import numpy as np
import pandas as pd


def performance_weights(valid, mae, epsilon):
    """Equal weights while any currently usable provider lacks sufficient history."""
    valid = np.asarray(valid, bool)
    mae = np.asarray(mae, float)
    complete_history = ((~valid) | np.isfinite(mae)).all(axis=1)
    score = np.where(valid, 1.0, 0.0)
    inverse = np.divide(1, mae + epsilon, out=np.zeros_like(mae), where=np.isfinite(mae))
    score = np.where(complete_history[:, None], np.where(valid, inverse, 0), score)
    sums = score.sum(axis=1, keepdims=True)
    weights = np.divide(score, sums, out=np.zeros_like(score), where=sums > 0)
    return weights, ~complete_history


def circular_average(values, weights):
    values = np.asarray(values, float)
    valid = np.isfinite(values)
    w = np.where(valid, weights, 0)
    sums = w.sum(axis=1)
    angles = np.deg2rad(np.where(valid, values, 0))
    s = (w * np.sin(angles)).sum(axis=1)
    c = (w * np.cos(angles)).sum(axis=1)
    resultant = np.divide(np.hypot(s, c), sums, out=np.full(len(sums), np.nan), where=sums > 0)
    direction = np.mod(np.rad2deg(np.arctan2(s, c)), 360)
    direction[(sums <= 0) | (resultant < 1e-8)] = np.nan
    return direction, 1 - np.clip(resultant, 0, 1)


def add_ensembles(frame, config):
    out = frame.copy()
    models = config["weather_models"]
    windows = config["ensemble_weight_window_days"]
    added, weights_by_kind = {}, {}
    for kind, variable in [("wind", "wind_speed_100m"), ("temperature", "temperature_2m")]:
        valid = out[[f"{m}_{variable}_valid" for m in models]].to_numpy(bool)
        mae = out[[f"{m}_{kind}_mae_{windows}d" for m in models]].to_numpy(float)
        weights, fallback = performance_weights(valid, mae, config["ensemble_epsilon"])
        weights_by_kind[kind] = weights
        added[f"{kind}_weights_cold_start"] = fallback
        for i, model in enumerate(models):
            added[f"{model}_weight" if kind == "wind" else f"{model}_temperature_weight"] = weights[:, i]
        if kind == "wind":
            scores = np.where(valid & np.isfinite(mae), mae, np.inf)
            choice = np.asarray(models, dtype=object)[np.argmin(scores, axis=1)]
            choice[np.isinf(scores).all(axis=1)] = "unknown"
            added["best_weather_model_recent"] = choice
    for variable in config["weather_variables"]:
        values = out[[f"{m}_{variable}" for m in models]].to_numpy(float)
        valid = out[[f"{m}_{variable}_valid" for m in models]].to_numpy(bool)
        clean = np.where(valid, values, np.nan)
        equal = valid.astype(float)
        base = weights_by_kind["temperature" if variable == "temperature_2m" else "wind"]
        weighted = np.where(valid, base, 0.0)
        # Some auxiliary variable may exist only on a model without wind. Use equal weights there.
        weighted = np.where((weighted.sum(axis=1) == 0)[:, None], equal, weighted)
        if variable.startswith("wind_direction"):
            simple, dispersion = circular_average(clean, equal)
            ensemble, weighted_dispersion = circular_average(clean, weighted)
            added[f"{variable}_circular_dispersion"] = dispersion
            added[f"ensemble_{variable}_circular_dispersion"] = weighted_dispersion
        else:
            count = valid.sum(axis=1)
            simple = np.divide(np.nansum(clean, axis=1), count, out=np.full(len(out), np.nan), where=count > 0)
            sums = weighted.sum(axis=1)
            ensemble = np.divide(np.nansum(clean * weighted, axis=1), sums, out=np.full(len(out), np.nan), where=sums > 0)
            if variable in ["wind_speed_100m", "temperature_2m"]:
                stem = "wind_speed" if variable == "wind_speed_100m" else "temperature"
                variance = np.divide(np.nansum((clean - simple[:, None]) ** 2, axis=1), count, out=np.full(len(out), np.nan), where=count > 0)
                added[f"{stem}_models_std"] = np.sqrt(variance)
                maximum = np.where(valid, values, -np.inf).max(axis=1)
                minimum = np.where(valid, values, np.inf).min(axis=1)
                added[f"{stem}_models_range"] = np.where(count > 0, maximum - minimum, np.nan)
        added[f"{variable}_mean"] = simple
        added[f"ensemble_{variable}"] = ensemble
    return pd.concat([out, pd.DataFrame(added, index=out.index)], axis=1)
