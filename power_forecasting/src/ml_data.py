"""Read-only ML views of existing archives; explicit features and purged month folds."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .input_data import ROOT, load_config
from .weather_evaluation import rolling_stats
from .weather_ensemble import add_ensembles
from .feature_engineering import engineer_features

REPORTS = ROOT / "reports"
ML_CACHE = ROOT / "data" / "ml"
TARGET = "normalized_active_power"
KEYS = ["turbine_id", "forecast_issue_time", "target_time", "lead_hours", "horizon_bucket"]


def dump_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str, allow_nan=False), encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def md_table(frame, digits=5):
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return f"{v:.{digits}f}" if np.isfinite(v) else "NaN"
        return str(v).replace("|", "/")
    return "\n".join(["| " + " | ".join(map(str, frame.columns)) + " |",
                      "| " + " | ".join(["---"] * len(frame.columns)) + " |"] +
                     ["| " + " | ".join(fmt(x) for x in row) + " |" for row in frame.itertuples(index=False, name=None)])


def read_inputs():
    train = pd.read_parquet(ROOT / "data/final/training_dataset.parquet").reset_index(drop=True)
    comp = pd.read_parquet(ROOT / "data/final/competition_features.parquet").reset_index(drop=True)
    manifest = json.loads((ROOT / "data/final/feature_columns.json").read_text(encoding="utf-8"))
    if manifest["target"] != TARGET or TARGET not in train:
        raise ValueError("Actual dataset target differs from requested normalized_active_power")
    for frame in [train, comp]:
        if frame.duplicated(KEYS).any():
            raise ValueError("Duplicate forecast keys")
        if not (frame.target_time > frame.forecast_issue_time).all():
            raise ValueError("Invalid issue/target chronology")
        expected = (frame.target_time - frame.forecast_issue_time).dt.total_seconds() / 3600
        if not np.array_equal(expected, frame.lead_hours):
            raise ValueError("Lead does not match timestamps")
    if not train[TARGET].between(0, 1).all():
        raise ValueError("Observed target does not support [0,1] prediction bounds")
    if train.target_time.max() >= comp.target_time.min():
        raise ValueError("Training target overlaps competition")
    consistency = train.groupby(["turbine_id", "target_time"])[TARGET].nunique()
    if (consistency != 1).any():
        raise ValueError("D1/D2 disagree on the same observation")
    return train, comp, manifest


def add_ml_transforms(frame):
    out = frame.copy()
    for height in ["10m", "100m"]:
        col = f"wind_direction_{height}_mean"
        out[col + "_sin"] = np.sin(np.deg2rad(out[col]))
        out[col + "_cos"] = np.cos(np.deg2rad(out[col]))
    return out


def build_feature_groups(train, manifest):
    allowed = []
    excluded = []
    declared = set(manifest["features"])
    for col in train:
        reason = None
        if col == TARGET:
            reason = "Supervised target; never X"
        elif re.search(r"(^eval_|actual|observation|scada_|history_latest)", col):
            reason = "Observed/evaluation/provenance field; not a predictor"
        elif pd.api.types.is_datetime64_any_dtype(train[col]):
            reason = "Raw timestamp; only explicit calendar transforms allowed"
        elif col == "dataset_split":
            reason = "Split identifier"
        elif col not in declared:
            reason = "Not in audited upstream feature allowlist; metadata/ID/provenance"
        if reason:
            excluded.append({"feature": col, "reason": reason})
        else:
            allowed.append(col)
    if set(allowed) != declared:
        raise ValueError(f"Suspicious declared features: {declared - set(allowed)}")
    base = [c for c in allowed if c in ["turbine_id", "lead_hours", "horizon_bucket", "archive_nominal_lead_hours",
            "target_hour", "target_day_of_week", "target_month", "target_day_of_year", "hour_sin", "hour_cos", "day_of_year_sin", "day_of_year_cos"]]
    performance = [c for c in allowed if re.search(r"_(wind|temperature)_(mae|rmse|bias|n)_\d+d$", c)]
    weights = [c for c in allowed if c.endswith("_weight") or c.endswith("_weights_cold_start")]
    disagreement = [c for c in allowed if c.endswith(("_models_std", "_models_range", "_circular_dispersion")) and not c.startswith("ensemble_")]
    providers = {}
    for provider in ["ecmwf", "gfs", "icon"]:
        providers[provider] = [c for c in allowed if c.startswith(provider + "_") and c not in performance + weights]
    simple = [c for c in allowed if c.endswith("_mean")]
    weighted = [c for c in allowed if c.startswith("ensemble_") and not c.endswith("_circular_dispersion")]
    raw = sum(providers.values(), [])
    groups = {p.upper(): base + cols for p, cols in providers.items()}
    groups.update(Simple=base + simple, Weighted=base + weighted + weights,
                  All=base + raw, All_Disagreement=base + raw + disagreement, Full=allowed)
    # Removes explicit historical statistics; weighted forecasts remain. This is
    # the incremental value of supplying history to ML, not removal of all history.
    groups["Full206"] = allowed
    compact_base = ["turbine_id", "lead_hours", "hour_sin", "hour_cos", "day_of_year_sin", "day_of_year_cos"]
    compact_raw = []
    for p in providers:
        cols = [f"{p}_wind_speed_100m", f"{p}_wind_direction_100m_sin", f"{p}_wind_direction_100m_cos"]
        compact_raw += cols
        groups[p.upper()] = compact_base + cols + [f"{p}_temperature_2m", f"{p}_quality_ok"]
    groups["Simple"] = compact_base + ["wind_speed_100m_mean", "wind_direction_100m_mean_sin", "wind_direction_100m_mean_cos", "temperature_2m_mean"]
    groups["Weighted"] = compact_base + ["ensemble_wind_speed_100m", "ensemble_wind_direction_100m_sin", "ensemble_wind_direction_100m_cos", "ensemble_temperature_2m"] + [p + "_weight" for p in providers]
    groups["All"] = compact_base + compact_raw + ["temperature_2m_mean"]
    groups["All_Disagreement"] = groups["All"] + ["wind_speed_models_std"]
    groups["CORE"] = groups["All_Disagreement"] + ["ensemble_wind_speed_100m"] + [p + "_wind_mae_30d" for p in providers]
    groups["Full"] = groups["CORE"] + [p + "_quality_ok" for p in providers]
    groups["Full_No_Performance"] = [c for c in groups["Full"] if c not in performance]
    if any(len(cols) != len(set(cols)) for cols in groups.values()):
        raise ValueError("Repeated feature within group")
    for p in providers:
        assert not any(c.startswith(q + "_") for c in groups[p.upper()] for q in providers if q != p)
    assert not set(raw) & set(groups["Simple"] + groups["Weighted"])
    dump_json(ROOT / "models/feature_groups.json", groups)
    exclusions = pd.DataFrame(excluded)
    exclusions.to_csv(REPORTS / "ml_excluded_features.csv", index=False)
    text = "# Feature safety\n\nExplicit allowlist: no eval/actual/target/timestamp/split fields in X.\n\n"
    text += "Turbine and horizon are categorical, never arbitrary numerical IDs. Category vocabularies are fitted on training only. Invalid provider measurements are masked by existing valid flags; missing values are not backfilled.\n\n"
    text += "Historical weather error features are checked against their latest-available provenance. Validation-month SCADA is excluded from their calculation; previous-month observations still require availability < issue.\n\n"
    text += "Full206 is a benchmark only. CORE has 21 predictors; Full means compact Full Agent features (24), not all 206. Simple direction sin/cos are deterministic row-local transforms of archived circular means.\n\n"
    text += "## SAFE CANDIDATES (NOT ALL USED)\n\n" + md_table(pd.DataFrame({"feature": allowed, "dtype": [str(train[c].dtype) for c in allowed]}))
    text += "\n\n## EXCLUDED FEATURES / REASON FOR EXCLUSION\n\n" + md_table(exclusions)
    text += "\n\n## Experiment groups\n\n" + md_table(pd.DataFrame([{"group": k, "count": len(v), "features": ", ".join(v)} for k, v in groups.items()]))
    (REPORTS / "feature_safety_report.md").write_text(text, encoding="utf-8")
    return groups


def audit(train, comp, groups):
    schema = pd.DataFrame({"column": train.columns, "dtype": [str(t) for t in train.dtypes],
                           "missing_n": train.isna().sum().values, "missing_pct": train.isna().mean().values * 100})
    schema.to_csv(REPORTS / "ml_data_schema.csv", index=False)
    monthly = train.groupby(train.target_local_time.dt.to_period("M")).agg(rows=(TARGET, "size"), first=("target_local_time", "min"), last=("target_local_time", "max"))
    power = train.drop_duplicates(["turbine_id", "target_time"])
    hourly = pd.read_parquet(ROOT / "data/processed/scada_hourly.parquet")
    observed = hourly[TARGET].dropna()
    if not observed.between(0, 1).all():
        raise ValueError("Unfiltered prepared SCADA contradicts bounded target")
    text = "# ML data audit\n\n"
    text += f"Train: {train.shape}; competition: {comp.shape}. Target: {TARGET}. Upstream safe candidates: {len(groups['Full206'])}; compact CORE: {len(groups['CORE'])}.\n\n"
    text += f"Duplicate full rows: {train.duplicated().sum()}; duplicate forecast keys: {train.duplicated(KEYS).sum()}. Unique turbine/target observations: {len(power)}. The same target legitimately appears in D1 and D2; folds split by target time for all turbines.\n\n"
    text += "Target is named normalized active power in source and bounded in BOTH filtered training and unfiltered prepared hourly SCADA. Clipping [0,1] is supported by observed range, not proof of the operator's normalization convention. Nameplate capacity is unavailable.\n\n"
    text += f"Unfiltered hourly range: {observed.min():.8f}–{observed.max():.8f}.\n\n"
    text += "## Target distribution (forecast rows)\n\n" + md_table(train[TARGET].describe(percentiles=[.01,.1,.5,.9,.99]).rename_axis("statistic").reset_index(name="value"))
    text += "\n\n## Turbine / horizon counts\n\n" + md_table(train.groupby(["turbine_id", "horizon_bucket"]).size().reset_index(name="rows"))
    text += "\n\n## Per lead hour\n\n" + md_table(train.groupby("lead_hours").size().reset_index(name="rows"))
    text += "\n\n## Calendar coverage\n\n" + md_table(monthly.reset_index())
    text += "\n\n## All columns, dtypes and missingness\n\n" + md_table(schema)
    text += "\n\nEvaluation-only/provenance columns are identified in feature_safety_report.md. Offline February file is never loaded by ML training or selection.\n"
    (REPORTS / "ml_data_audit.md").write_text(text, encoding="utf-8")


def make_folds(train, config):
    months = train.target_local_time.dt.to_period("M")
    candidates = []
    for month in sorted(months.unique()):
        sub = train.loc[months == month]
        start, end = month.start_time, (month + 1).start_time
        expected = len(pd.date_range(start, end, freq="h", inclusive="left"))
        complete = sub.target_local_time.min() == start and sub.target_local_time.max() == end - pd.Timedelta(hours=1)
        coverage = sub.groupby(["turbine_id", "horizon_bucket"]).target_time.nunique().min() / expected
        if complete and coverage >= config["minimum_month_coverage"] and (train.target_local_time < start).sum() > 5000:
            candidates.append(month)
    candidates = candidates[-config["validation_months"]:]
    if len(candidates) < 3:
        raise ValueError("Fewer than three sufficiently covered complete calendar months")
    folds, rows = [], []
    delay = pd.Timedelta(hours=config["observation_delay_hours"])
    for month in candidates:
        valid = train.index[months == month].to_numpy()
        first_issue = train.loc[valid, "forecast_issue_time"].min()
        fit = train.index[(months < month) & (train.target_time + delay < first_issue)].to_numpy()
        if train.loc[fit, "target_time"].max() >= train.loc[valid, "target_time"].min():
            raise ValueError("Overlapping fold targets")
        if set(train.loc[fit, "target_time"]) & set(train.loc[valid, "target_time"]):
            raise ValueError("Same target leaks across fold")
        # Translate local month boundary using the actual UTC/local delta.
        offset = train.loc[valid[0], "target_local_time"] - train.loc[valid[0], "target_time"].tz_localize(None)
        month_start_utc = (month.start_time - offset).tz_localize("UTC")
        folds.append({"name": str(month), "train": fit, "valid": valid, "first_issue": first_issue, "history_target_cutoff": month_start_utc})
        rows.append({"fold": str(month), "train_rows": len(fit), "validation_rows": len(valid),
                     "train_max_target": train.loc[fit, "target_time"].max(), "train_max_available": (train.loc[fit, "target_time"] + delay).max(),
                     "validation_min_target": train.loc[valid, "target_time"].min(), "validation_max_target": train.loc[valid, "target_time"].max(),
                     "first_forecast_issue": first_issue, "history_target_cutoff": month_start_utc,
                     "purged_boundary_rows": int(((months < month) & (train.target_time + delay >= first_issue)).sum())})
    pd.DataFrame(rows).to_csv(REPORTS / "validation_folds.csv", index=False)
    return folds


def verify_history(frame):
    for col in frame:
        if "_history_latest_" in col:
            valid = frame[col].notna()
            if not (frame.loc[valid, col] < frame.loc[valid, "forecast_issue_time"]).all():
                raise ValueError(f"Future weather performance provenance: {col}")


def frozen_history_view(query, source, target_cutoff, weather_config):
    """Reuse archived weather only; no API, no mutation of the original parquet."""
    out = query.copy().reset_index(drop=True)
    for model in weather_config["weather_models"]:
        for kind, variable, obs in [("wind", "wind_speed_100m", "eval_actual_wind_speed"), ("temperature", "temperature_2m", "eval_actual_temperature")]:
            for days in weather_config["rolling_windows"]:
                for (turbine, horizon), ids in out.groupby(["turbine_id", "horizon_bucket"]).groups.items():
                    history = source[(source.turbine_id == turbine) & (source.horizon_bucket == horizon) & (source.target_time < target_cutoff)]
                    ok = history[f"{model}_{variable}_valid"] & history.scada_hour_complete.fillna(False) & (history.dataset_split == "train")
                    errors = (history[f"{model}_{variable}"] - history[obs]).where(ok).to_numpy()
                    stats = rolling_stats(history.observation_available_time, errors, out.loc[ids, "forecast_issue_time"], days, weather_config["rolling_min_samples"])
                    for metric in ["mae", "rmse", "bias", "n"]:
                        out.loc[ids, f"{model}_{kind}_{metric}_{days}d"] = stats[metric]
                    out.loc[ids, f"{model}_{kind}_history_latest_{days}d"] = stats["latest_available_time"].to_numpy()
    # add_ensembles appends columns: remove exactly the computed outputs first.
    original = list(out.columns)
    probe = add_ensembles(out.head(1), weather_config)
    generated = list(probe.columns[len(original):])
    out = add_ensembles(out.drop(columns=generated, errors="ignore"), weather_config)
    out, _ = engineer_features(out, weather_config)
    verify_history(out)
    return out


def prepare():
    REPORTS.mkdir(exist_ok=True)
    ML_CACHE.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "ml_config.json").read_text(encoding="utf-8"))
    train, comp, manifest = read_inputs()
    verify_history(train)
    verify_history(comp)
    groups = build_feature_groups(train, manifest)
    audit(train, comp, groups)
    folds = make_folds(train, config)
    source = pd.read_parquet(ROOT / "data/final/training_weather_dataset.parquet")
    for fold in folds:
        view = frozen_history_view(train.loc[fold["valid"]], source, fold["history_target_cutoff"], load_config())
        view.index = fold["valid"]
        fold["validation_frame"] = add_ml_transforms(view)
        print(f"Prepared {fold['name']}: train={len(fold['train'])}, validation={len(view)}, latest train label available < {fold['first_issue']}", flush=True)
    return add_ml_transforms(train), add_ml_transforms(comp), groups, folds, config
