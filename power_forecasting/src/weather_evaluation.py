"""Rolling errors sampled by observation availability, strictly before each issue."""
import numpy as np
import pandas as pd


def rolling_stats(available_times, errors, query_times, days, min_samples):
    valid = np.isfinite(errors) & pd.notna(available_times)
    times = pd.DatetimeIndex(available_times[valid]).as_unit("ns").asi8
    values = np.asarray(errors)[valid]
    order = np.argsort(times, kind="stable")
    times, values = times[order], values[order]
    queries = pd.DatetimeIndex(query_times).as_unit("ns").asi8
    # left excludes observations becoming available exactly at the issue time.
    right = np.searchsorted(times, queries, side="left")
    left = np.searchsorted(times, queries - pd.Timedelta(days=days).value, side="left")
    count = right - left
    result = {"n": count}
    for name, array in [("mae", np.abs(values)), ("bias", values), ("rmse", values ** 2)]:
        sums = np.r_[0.0, np.cumsum(array)]
        means = np.divide(sums[right] - sums[left], count, out=np.full(len(count), np.nan), where=count >= min_samples)
        result[name] = np.sqrt(np.maximum(means, 0)) if name == "rmse" else means
    latest = np.full(len(queries), np.iinfo(np.int64).min, dtype="int64")
    use = count >= min_samples
    latest[use] = times[right[use] - 1]
    result["latest_available_time"] = pd.to_datetime(latest, utc=True)
    return result


def add_provider_performance(frame, config):
    out = frame.copy()
    added = {}
    for model in config["weather_models"]:
        for kind, variable, observation in [("wind", "wind_speed_100m", "eval_actual_wind_speed"), ("temperature", "temperature_2m", "eval_actual_temperature")]:
            for window in config["rolling_windows"]:
                prefix = f"{model}_{kind}"
                for metric in ["mae", "rmse", "bias", "n"]:
                    added[f"{prefix}_{metric}_{window}d"] = np.full(len(out), np.nan)
                latest_col = f"{prefix}_history_latest_{window}d"
                added[latest_col] = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns, UTC]")
                for _, indices in out.groupby(["turbine_id", "horizon_bucket"], sort=False).groups.items():
                    group = out.loc[indices]
                    # No competition outcomes are eligible, even if offline targets are supplied later.
                    error_ok = group[f"{model}_{variable}_valid"] & group.scada_hour_complete.fillna(False) & (group.dataset_split == "train")
                    errors = (group[f"{model}_{variable}"] - group[observation]).where(error_ok).to_numpy()
                    stats = rolling_stats(group.observation_available_time, errors, group.forecast_issue_time, window, config["rolling_min_samples"])
                    for metric in ["mae", "rmse", "bias", "n"]:
                        added[f"{prefix}_{metric}_{window}d"][indices] = stats[metric]
                    added[latest_col].loc[indices] = stats["latest_available_time"]
    return pd.concat([out, pd.DataFrame(added, index=out.index)], axis=1)
