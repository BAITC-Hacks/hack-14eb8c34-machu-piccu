"""Download only fixed-lead Previous Runs. Every HTTP response is cached."""
import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .input_data import ROOT, load_config
from .weather_cache import WeatherCache

ENDPOINT = "https://previous-runs-api.open-meteo.com/v1/forecast"


def download(config, offline=False):
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / "logs/pipeline.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    cache = WeatherCache(ROOT / "data/cache/weather", config["http"], offline)
    start, end = pd.Timestamp(config["download_start"]), pd.Timestamp(config["download_end"])
    provider_tables, manifest = [], []
    for model in config["weather_models"]:
        pieces = []
        for turbine, coordinates in config["coordinates"].items():
            for chunk_start in pd.date_range(start, end, freq=f"{config['download_chunk_days']}D"):
                chunk_end = min(end, chunk_start + pd.Timedelta(days=config["download_chunk_days"] - 1))
                params = {**coordinates, "models": config["model_ids"][model], "timezone": "GMT",
                          "wind_speed_unit": "ms", "temperature_unit": "celsius",
                          "start_date": str(chunk_start.date()), "end_date": str(chunk_end.date()),
                          "hourly": ",".join(f"{v}_previous_day{d}" for v in config["weather_variables"] for d in [1, 2])}
                response = cache.get(model, ENDPOINT, params)
                try:
                    body = json.loads(response["body"])
                except json.JSONDecodeError:
                    body = {}
                if not isinstance(body, dict):
                    body = {}
                success = response["status"] == 200 and not body.get("error")
                hours = body.get("hourly", {}) if success else {}
                returned_times = pd.DatetimeIndex(pd.to_datetime(hours.get("time", []), utc=True))
                if returned_times.has_duplicates:
                    raise ValueError(f"Duplicate forecast timestamps: {model} {turbine} {chunk_start}")
                expected = pd.date_range(chunk_start.tz_localize("UTC"), (chunk_end + pd.Timedelta(days=1)).tz_localize("UTC"), freq="h", inclusive="left")
                if len(returned_times.difference(expected)):
                    raise ValueError("API returned timestamps outside requested window")
                if len(returned_times) and not returned_times.is_monotonic_increasing:
                    raise ValueError("Nonmonotonic weather timestamps")
                sha = hashlib.sha256(response["body"].encode()).hexdigest()
                manifest.append({"model": model, "model_id": params["models"], "turbine_id": turbine,
                    "start_date": params["start_date"], "end_date": params["end_date"],
                    "http_status": response["status"], "expected_hours": len(expected), "returned_hours": len(returned_times),
                    "cache_key": response["cache_key"], "body_sha256": sha, "request_url": response["url"],
                    "retrieved_at": response["retrieved_at"], "error": body.get("reason", ""),
                    "grid_latitude": body.get("latitude"), "grid_longitude": body.get("longitude")})
                for day in [1, 2]:
                    frame = pd.DataFrame({"target_time": expected})
                    frame["turbine_id"] = turbine
                    frame["archive_day"] = day
                    for variable in config["weather_variables"]:
                        key = f"{variable}_previous_day{day}"
                        values = hours.get(key, [None] * len(returned_times))
                        if len(values) != len(returned_times):
                            raise ValueError(f"Invalid array length for {model}/{key}")
                        unit = (body.get("hourly_units") or {}).get(key)
                        expected_unit = "m/s" if variable.startswith("wind_speed") or variable == "wind_gusts_10m" else ("°C" if variable == "temperature_2m" else None)
                        if expected_unit and unit is not None and unit != expected_unit:
                            raise ValueError(f"Unexpected unit {unit} for {key}")
                        series = pd.Series(pd.to_numeric(values, errors="raise"), index=returned_times, dtype=float)
                        frame[f"{model}_{variable}"] = series.reindex(expected).to_numpy()
                    frame[f"{model}_api_error"] = not success
                    frame[f"{model}_missing_target_hour"] = ~expected.isin(returned_times)
                    frame[f"{model}_cache_key"] = response["cache_key"]
                    frame[f"{model}_grid_latitude"] = body.get("latitude", np.nan)
                    frame[f"{model}_grid_longitude"] = body.get("longitude", np.nan)
                    pieces.append(frame)
                pd.DataFrame(manifest).to_csv(ROOT / "reports/weather_request_manifest.csv", index=False)
                print(f"{model} {turbine} {params['start_date']}..{params['end_date']}: HTTP {response['status']} {len(returned_times)}/{len(expected)}h", flush=True)
        table = pd.concat(pieces, ignore_index=True)
        keys = ["turbine_id", "target_time", "archive_day"]
        if table.duplicated(keys).any():
            raise ValueError("Duplicate provider primary key")
        table.to_parquet(ROOT / f"data/processed/{model}_archive.parquet", index=False)
        provider_tables.append(table)
    merged = provider_tables[0]
    for table in provider_tables[1:]:
        merged = merged.merge(table, on=keys, how="outer", validate="one_to_one")
    merged.to_parquet(ROOT / "data/processed/weather_archive.parquet", index=False)
    state = {"completed_at": datetime.now(timezone.utc).isoformat(), "rows": len(merged),
             "request_count": len(manifest), "failed_requests": sum(x["http_status"] != 200 for x in manifest),
             "method": "open_meteo_previous_runs"}
    (ROOT / "reports/download_status.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    download(load_config(), parser.parse_args().offline)
