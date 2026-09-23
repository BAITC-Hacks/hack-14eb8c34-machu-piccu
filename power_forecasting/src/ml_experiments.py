"""Resumable walk-forward tournament with an identical outer row set per experiment."""
import json
import time

import numpy as np
import pandas as pd

from .ml_data import ROOT, REPORTS, KEYS, TARGET, dump_json
from .ml_models import fit_learner, predict_learner, metric_values, segments, subset
from .ml_selection import native_importance


def spec(model, group, architecture="global", variant="default"):
    return {"id": f"{model}__{group}__{architecture}__{variant}", "model": model,
            "feature_group": group, "architecture": architecture, "variant": variant}


def historical_baseline(train, valid, kind):
    observations = train.drop_duplicates(["turbine_id", "target_time"])
    stat = "mean" if kind == "HistoricalMean" else "median"
    table = observations.groupby(["turbine_id", "target_hour"])[TARGET].agg(stat)
    fallback = observations.groupby("turbine_id")[TARGET].agg(stat)
    return np.array([table.get((t, h), fallback[t]) for t, h in zip(valid.turbine_id, valid.target_hour)])


def persistence_baseline(valid, history_target_cutoff):
    history = pd.read_parquet(ROOT / "data/processed/scada_hourly.parquet")
    history = history[(history.target_time < history_target_cutoff) & history[TARGET].notna()]
    result = pd.Series(np.nan, index=valid.index)
    for turbine, part in valid.groupby("turbine_id"):
        obs = history[history.turbine_id == turbine].sort_values("observation_available_time")
        times = pd.DatetimeIndex(obs.observation_available_time).as_unit("ns").asi8
        issues = pd.DatetimeIndex(part.forecast_issue_time).as_unit("ns").asi8
        positions = np.searchsorted(times, issues, side="left") - 1
        if (positions < 0).any():
            raise ValueError("No available past observation for persistence")
        result.loc[part.index] = obs[TARGET].to_numpy()[positions]
    return result.to_numpy()


def evaluate(specification, train, groups, folds, config, run_dir):
    exp_dir = run_dir / specification["id"]
    exp_dir.mkdir(parents=True, exist_ok=True)
    features = groups.get(specification["feature_group"], [])
    records, infos = [], []
    for fold in folds:
        output = exp_dir / (fold["name"] + ".parquet")
        metadata = exp_dir / (fold["name"] + ".json")
        if output.exists() and metadata.exists():
            predictions = pd.read_parquet(output)
            info = json.loads(metadata.read_text(encoding="utf-8"))
            if not np.array_equal(predictions.row_id, fold["valid"]):
                raise ValueError("Cached fold keys differ from current validation")
        else:
            started = time.perf_counter()
            fit = train.loc[fold["train"]]
            valid = fold["validation_frame"]
            bundles = []
            if specification["model"] in ["HistoricalMean", "HistoricalMedian"]:
                pred = historical_baseline(fit, valid, specification["model"])
            elif specification["model"] == "Persistence":
                pred = persistence_baseline(valid, fold["history_target_cutoff"])
            else:
                result = pd.Series(np.nan, index=valid.index)
                for segment, match, part in segments(fit, specification["architecture"]):
                    query = subset(valid, match)
                    bundle = fit_learner(part, features, specification["model"], config, specification["variant"])
                    values, unseen = predict_learner(bundle, query, config["clip_bounds"])
                    result.loc[query.index] = values
                    bundles.append({k: v for k, v in bundle.items() if k != "model"} | {"segment": segment, "match": match,
                                   "native_importance": native_importance(bundle), "unseen_categories": unseen})
                pred = result.to_numpy()
            predictions = valid[KEYS + [TARGET]].copy()
            predictions.insert(0, "row_id", valid.index)
            predictions["prediction"] = np.clip(pred, *config["clip_bounds"])
            predictions["fold"] = fold["name"]
            if predictions.prediction.isna().any():
                raise ValueError("Incomplete OOF coverage")
            info = {"specification": specification, "fold": fold["name"], "training_seconds": time.perf_counter() - started,
                    "features": features, "segments": bundles, "metrics": metric_values(predictions[TARGET], predictions.prediction)}
            predictions.to_parquet(output, index=False)
            dump_json(metadata, info)
            print(f"{specification['id']} | {fold['name']} | MAE={info['metrics']['MAE']:.5f} | {info['training_seconds']:.1f}s", flush=True)
        records.append(predictions)
        infos.append(info)
    combined = pd.concat(records, ignore_index=True)
    result = {**specification, **metric_values(combined[TARGET], combined.prediction)}
    result.update(feature_count=len(features), training_time=sum(i["training_seconds"] for i in infos),
                  mean_fold_MAE=float(np.mean([i["metrics"]["MAE"] for i in infos])),
                  std_fold_MAE=float(np.std([i["metrics"]["MAE"] for i in infos])),
                  D1_D2_strategy="separate" if "horizon" in specification["architecture"] else "combined",
                  turbine_strategy="separate" if "turbine" in specification["architecture"] else "global")
    for horizon in ["D1", "D2"]:
        part = combined[combined.horizon_bucket == horizon]
        result[f"MAE_{horizon}"] = metric_values(part[TARGET], part.prediction)["MAE"]
    for turbine in train.turbine_id.unique():
        part = combined[combined.turbine_id == turbine]
        result[f"MAE_{turbine}"] = metric_values(part[TARGET], part.prediction)["MAE"]
    dump_json(exp_dir / "summary.json", result)
    combined.to_parquet(exp_dir / "oof_predictions.parquet", index=False)
    return result


def choose_simple(candidates, config, metric="MAE"):
    table = pd.DataFrame(candidates).copy()
    compact = table[table.feature_count <= config["maximum_preferred_features"]]
    if len(compact):
        compact_best = compact[metric].min()
        table = table[(table.feature_count <= config["maximum_preferred_features"]) |
                      (table[metric] <= compact_best * (1 - config["large_model_required_relative_gain"]))]
    band = table[metric].min() * (1 + config["simplicity_tolerance_relative"])
    near = table[table[metric] <= band].copy()
    near["complexity"] = near.architecture.map({"global": 1, "horizon": 2, "turbine": 2, "horizon_turbine": 4})
    return near.sort_values(["complexity", "feature_count", "std_fold_MAE", metric]).iloc[0].drop(labels="complexity").to_dict()


def load_oof(run_dir, experiment_id):
    return pd.read_parquet(run_dir / experiment_id / "oof_predictions.parquet")
