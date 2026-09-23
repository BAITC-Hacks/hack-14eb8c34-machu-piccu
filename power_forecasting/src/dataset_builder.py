"""Build all final datasets from cached fixed-lead weather; never train power models."""
import argparse
import hashlib
import json
import numpy as np
import pandas as pd
from .input_data import ROOT, load_config
from .download_weather import download
from .scada import read_hourly_local, localize_scada
from .timezone_inference import infer_timezone
from .timeline import build_schedule
from .weather_quality import quality_checks
from .weather_evaluation import add_provider_performance
from .weather_ensemble import add_ensembles
from .feature_engineering import engineer_features
from .validation import validate_point_in_time_integrity, validate_feature_columns
from .reporting import write_reports


def build(config, weather):
    for folder in ["data/processed", "data/final", "reports"]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    local = read_hourly_local(config)
    decision = infer_timezone(local, weather, config)
    scada = localize_scada(local, decision, config)
    scada.to_parquet(ROOT / "data/processed/scada_hourly.parquet", index=False)
    schedule = build_schedule(config, decision)
    schedule.to_parquet(ROOT / "data/processed/forecast_schedule.parquet", index=False)
    schedule = schedule.merge(pd.DataFrame({"turbine_id": list(config["coordinates"])}), how="cross")
    frame = schedule.merge(weather, on=["turbine_id", "target_time", "archive_day"], how="left", validate="one_to_one")
    for model in config["weather_models"]:
        # Missing join is explicit missing coverage, never populated by a later forecast.
        frame[f"{model}_api_error"] = frame[f"{model}_api_error"].fillna(True).astype(bool)
        frame[f"{model}_missing_target_hour"] = frame[f"{model}_missing_target_hour"].fillna(True).astype(bool)
    frame["methodology_status"] = "lead_time_archive"
    frame["weather_archive_method"] = "open_meteo_previous_runs"
    frame["weather_archive_confidence"] = "fixed_lead_time_archive"
    frame["timezone_status"] = decision["timezone_status"]
    frame["scada_utc_offset_hours"] = decision["selected_offset_hours"]
    config_id = hashlib.sha256(json.dumps({"config": config, "timezone_decision": decision}, sort_keys=True).encode()).hexdigest()[:16]
    frame["weather_configuration"] = config_id
    (ROOT / "data/final/run_config.json").write_text(json.dumps({"weather_configuration": config_id, "config": config, "timezone_decision": decision}, ensure_ascii=False, indent=2), encoding="utf-8")
    frame.to_parquet(ROOT / "data/processed/weather_raw.parquet", index=False)
    frame = quality_checks(frame, config)
    frame = frame.merge(scada.drop(columns="target_local_time"), on=["turbine_id", "target_time"], how="left", validate="many_to_one")
    frame["scada_hour_complete"] = frame.scada_hour_complete.astype("boolean")
    frame["scada_samples"] = frame.scada_samples.astype("Int16")
    frame = frame.reset_index(drop=True)
    print("Calculating strictly past rolling provider metrics...", flush=True)
    frame = add_provider_performance(frame, config)
    frame = add_ensembles(frame, config)
    frame, features = engineer_features(frame, config)
    frame["training_eligible"] = (frame.dataset_split == "train") & frame.normalized_active_power.between(0, 1) & (frame.weather_models_usable_count > 0)
    frame["training_exclusion_reason"] = np.select([
        frame.dataset_split != "train", frame.normalized_active_power.isna(), ~frame.normalized_active_power.between(0, 1), frame.weather_models_usable_count == 0],
        ["competition", "missing_or_incomplete_target", "invalid_power_target", "no_usable_weather_provider"], default="")
    validation = validate_point_in_time_integrity(frame, config, features)
    # All observation-dependent columns are excluded from deployable exports, not just the two eval values.
    forbidden = [c for c in frame if c.startswith("eval_") or c in ["normalized_active_power", "observation_available_time", "scada_samples", "scada_hour_complete", "training_eligible", "training_exclusion_reason"]]
    export_cols = [c for c in frame if c not in forbidden]
    train = frame.loc[frame.training_eligible, export_cols + ["normalized_active_power"]].copy()
    competition = frame.loc[frame.dataset_split == "competition_test", export_cols].copy()
    offline = frame.loc[frame.dataset_split == "competition_test"].copy()
    if not len(train) or not len(competition):
        raise ValueError("Empty train or competition export")
    if competition.weather_critical_missing.any():
        raise ValueError("Competition contains hours with zero usable weather providers; inspect coverage and retry cached failures")
    validate_feature_columns(features)
    excluded = frame.loc[(frame.dataset_split == "train") & ~frame.training_eligible,
        ["turbine_id", "forecast_issue_time", "target_time", "lead_hours", "training_exclusion_reason", "scada_samples", "weather_models_usable_count"]]
    excluded.to_csv(ROOT / "reports/training_exclusions.csv", index=False)
    # Master is an audit artifact, not an implicit X matrix. Competition actuals live only in offline export.
    master = frame.copy()
    competition_mask = master.dataset_split == "competition_test"
    for column in ["normalized_active_power", "eval_actual_wind_speed", "eval_actual_temperature"]:
        master.loc[competition_mask, column] = np.nan
    paths = {"training_dataset": train, "competition_features": competition, "offline_test_with_targets": offline, "training_weather_dataset": master}
    for name, data in paths.items():
        path = ROOT / f"data/final/{name}.parquet"
        data.to_parquet(path, index=False, compression="zstd")
        restored = pd.read_parquet(path)
        pd.testing.assert_frame_equal(data.reset_index(drop=True), restored.reset_index(drop=True))
        print(f"Export verified: {name}: {len(data):,} rows, {len(data.columns)} columns", flush=True)
    master.to_csv(ROOT / "data/final/training_weather_dataset.csv", index=False)
    categorical = [c for c in features if pd.api.types.is_string_dtype(frame[c])]
    (ROOT / "data/final/feature_columns.json").write_text(json.dumps({"features": features, "categorical_features": categorical,
        "target": "normalized_active_power", "note": "Select X by this allowlist; identifiers/provenance/evaluation columns outside it are not predictors."}, indent=2), encoding="utf-8")
    summary = write_reports(frame, weather, train, competition, offline, features, config, decision, validation)
    print(json.dumps({key: summary[key] for key in ["status", "training_rows", "competition_rows", "feature_columns", "provider_usable_pct_training", "provider_usable_pct_competition"]}, indent=2), flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch or reuse all raw HTTP responses")
    parser.add_argument("--offline", action="store_true", help="Use only cached HTTP responses with --download")
    args = parser.parse_args()
    config = load_config()
    weather = download(config, args.offline) if args.download else pd.read_parquet(ROOT / "data/processed/weather_archive.parquet")
    build(config, weather)
