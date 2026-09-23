"""Optional archive probes; publication proof differs from accepted fixed-lead methodology."""
import argparse
import csv
import json
import logging
import math
from datetime import datetime
from .input_data import ROOT, load_config
from .weather_cache import WeatherCache

ENDPOINTS = {
    "single_runs": "https://single-runs-api.open-meteo.com/v1/forecast",
    "previous_runs": "https://previous-runs-api.open-meteo.com/v1/forecast",
}


def summarize_response(entry, date, mode):
    try:
        body = json.loads(entry["body"])
    except json.JSONDecodeError:
        body = {}
    if not isinstance(body, dict):
        body = {}
    hourly = body.get("hourly") or {}
    times = hourly.get("time", [])
    usable = {}
    first, last = [], []
    nominal_offsets = set()
    actual_run_leads = set()
    for variable, values in hourly.items():
        if variable == "time":
            continue
        valid = [i for i, value in enumerate(values) if isinstance(value, (int, float)) and math.isfinite(value)]
        usable[variable] = len(valid)
        stamps = [times[i] for i in valid if i < len(times)]
        if stamps:
            first.append(min(stamps))
            last.append(max(stamps))
            if "_previous_day" in variable:
                nominal_offsets.add(24 * int(variable.rsplit("_previous_day", 1)[1]))
            elif mode == "single_runs":
                origin = datetime.fromisoformat(date + "T00:00")
                actual_run_leads.update(int((datetime.fromisoformat(t) - origin).total_seconds() / 3600) for t in stamps)
    return {
        "http_status": entry["status"], "error": body.get("reason", "") if body else entry["body"][:200],
        "returned_hours": len(times), "available_variable_counts": json.dumps(usable, sort_keys=True),
        "earliest_nonnull_in_probe": min(first) if first else "",
        "latest_nonnull_in_probe": max(last) if last else "",
        "nominal_offset_hours": ";".join(map(str, sorted(nominal_offsets))),
        "run_lead_hours": ";".join(map(str, sorted(actual_run_leads))),
        "has_nonnull_values": bool(first),
        "returned_latitude": body.get("latitude", ""), "returned_longitude": body.get("longitude", ""),
        "response_metadata_fields": ";".join(k for k in body if k not in ["hourly", "hourly_units"]),
        "source_run_proven": False, "publication_time_proven": False,
        "exact_point_in_time_proven": False, "fixed_lead_method_accepted": mode == "previous_runs",
        "coverage_scope": "sampled_dates_only_not_global_archive_bounds",
        "cache_key": entry["cache_key"], "request_url": entry["url"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--ecmwf-hres", action="store_true", help="Separately probe ecmwf_ifs; never substitute for operational IFS025")
    args = parser.parse_args()
    config = load_config()
    report_name = "weather_preflight_report.csv"
    endpoints = ENDPOINTS
    if args.ecmwf_hres:
        config["weather_models"] = ["ecmwf"]
        config["model_ids"]["ecmwf"] = "ecmwf_ifs"
        endpoints = {"single_runs": ENDPOINTS["single_runs"]}
        report_name = "ecmwf_hres_probe.csv"
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / "logs/preflight.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    cache = WeatherCache(ROOT / "data/cache/weather", config["http"], offline=args.offline)
    rows = []
    for provider in config["weather_models"]:
        for turbine_id, coordinates in config["coordinates"].items():
            for mode, endpoint in endpoints.items():
                for date in config["probe_dates"]:
                    variables = config["weather_variables"]
                    params = {**coordinates, "models": config["model_ids"][provider],
                              "wind_speed_unit": "ms", "temperature_unit": "celsius", "timezone": "GMT"}
                    if mode == "previous_runs":
                        params.update(start_date=date, end_date=date)
                        variables = [f"{v}_previous_day{d}" for v in variables for d in config["probe_previous_days"]]
                    else:
                        params.update(run=date + "T00:00", forecast_hours=49)
                    params["hourly"] = ",".join(variables)
                    entry = cache.get(provider, endpoint, params)
                    row = {"model": provider, "model_id": params["models"], "turbine_id": turbine_id,
                           "archive": mode, "probe_date": date, **summarize_response(entry, date, mode)}
                    rows.append(row)
                    # Save incrementally for resume after interruption.
                    with (ROOT / "reports" / report_name).open("w", encoding="utf-8", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                        writer.writeheader()
                        writer.writerows(rows)
                    print(f"{provider} {turbine_id} {mode} {date}: HTTP {entry['status']}, nonnull={row['has_nonnull_values']}", flush=True)
    print("PREFLIGHT COMPLETE: fixed-lead methodology accepted; exact publication time unknown. Build validates issue schedule separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
