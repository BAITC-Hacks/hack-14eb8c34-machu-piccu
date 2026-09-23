"""Final refits, availability-safe boundary checkpoints, and registry-based inference."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .ml_data import ROOT, REPORTS, TARGET, KEYS, dump_json, add_ml_transforms, sha256
from .ml_models import fit_learner, predict_learner, segments, subset, encode_transform
from .ml_selection import native_importance


def train_final(train, competition, groups, config, selected, run_dir, versions):
    model_dir = ROOT / "models" / run_dir.name
    model_dir.mkdir(parents=True, exist_ok=True)
    registry = {"schema_version": 1, "run_id": run_dir.name, "seed": config["seed"], "clip_bounds": config["clip_bounds"],
                "observation_delay_hours": config["observation_delay_hours"], "versions": versions,
                "input_training_sha256": sha256(ROOT / "data/final/training_dataset.parquet"),
                "input_competition_sha256": sha256(ROOT / "data/final/competition_features.parquet"),
                "routes": {}, "validation_note": "Four-month walk-forward model-selection results, not independent February test"}
    cache = {}
    importance_rows, shap_rows = [], []
    final_feature_map = {}
    for horizon, chosen in selected.items():
        features = groups[chosen["feature_group"]]
        route = {"model": chosen["model"], "feature_group": chosen["feature_group"], "architecture": chosen["architecture"],
                 "variant": chosen["variant"], "validation_mae": chosen[f"MAE_{horizon}"], "experiment_id": chosen["id"], "segments": []}
        records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((run_dir / chosen["id"]).glob("20??-??.json"))]
        for segment, match, fitting in segments(train, chosen["architecture"]):
            inference = subset(competition[competition.horizon_bucket == horizon], match)
            if inference.empty:
                continue
            iteration_history = [part["iterations"] for record in records for part in record["segments"] if part["segment"] == segment]
            if not iteration_history:
                raise ValueError("No stopping iterations for selected segment")
            rounds = max(1, int(np.median(iteration_history)))
            availability = fitting.target_time + pd.Timedelta(hours=config["observation_delay_hours"])
            last_available = availability.max()
            # All historical labels are used for the main final model. Early
            # competition issue times need earlier checkpoints to avoid leakage.
            early_issues = sorted(inference.loc[inference.forecast_issue_time <= last_available, "forecast_issue_time"].unique())
            checkpoints = []
            for cutoff in [None] + early_issues:
                checkpoint_name = "all_history" if cutoff is None else pd.Timestamp(cutoff).strftime("asof_%Y%m%dT%H%MZ")
                model_key = f"{chosen['id']}__{segment}__{checkpoint_name}"
                if model_key not in cache:
                    eligible = fitting if cutoff is None else fitting[availability < cutoff]
                    print(f"Final refit {model_key}: {len(eligible)} rows, {len(features)} features, {rounds} trees", flush=True)
                    bundle = fit_learner(eligible, features, chosen["model"], config, chosen["variant"], fixed_iterations=rounds)
                    path = model_dir / f"{model_key}.joblib"
                    joblib.dump(bundle, path, compress=3)
                    # Native model is also saved for inspection / interoperability.
                    native_path = model_dir / (model_key + {"CatBoost": ".cbm", "LightGBM": ".txt", "XGBoost": ".ubj"}[chosen["model"]])
                    if chosen["model"] == "LightGBM":
                        bundle["model"].booster_.save_model(str(native_path))
                    else:
                        bundle["model"].save_model(str(native_path))
                    meta = {k: v for k, v in bundle.items() if k != "model"}
                    meta.update(model_file=str(path.relative_to(ROOT)).replace("\\", "/"), model_sha256=sha256(path),
                                native_model_file=str(native_path.relative_to(ROOT)).replace("\\", "/"),
                                experiment_id=chosen["id"], feature_group=chosen["feature_group"], versions=versions,
                                seed=config["seed"], cutoff_kind=checkpoint_name)
                    dump_json(model_dir / f"{model_key}.json", meta)
                    cache[model_key] = meta
                    if cutoff is None:
                        for feature, importance in native_importance(bundle).items():
                            importance_rows.append({"model_key": model_key, "feature": feature, "importance": importance,
                                                    "training_rows": len(eligible), "method": "native_normalized"})
                        # Native tree SHAP on a small deterministic training sample;
                        # descriptive only, never used for outer-fold feature selection.
                        sample = eligible.sample(n=min(128, len(eligible)), random_state=config["seed"])
                        x, _ = encode_transform(sample, bundle["schema"])
                        if chosen["model"] == "CatBoost":
                            from catboost import Pool
                            shap = bundle["model"].get_feature_importance(Pool(x, cat_features=list(bundle["schema"]["categories"])), type="ShapValues")
                        elif chosen["model"] == "LightGBM":
                            shap = bundle["model"].booster_.predict(x, pred_contrib=True)
                        else:
                            import xgboost as xgb
                            shap = bundle["model"].get_booster().predict(xgb.DMatrix(x), pred_contribs=True)
                        for feature, value in zip(bundle["schema"]["encoded_features"], np.abs(np.asarray(shap)[:, :-1]).mean(axis=0)):
                            shap_rows.append({"model_key": model_key, "feature": feature.split("__cat_")[0], "mean_absolute_shap": float(value), "sample_rows": len(sample)})
                meta = cache[model_key]
                checkpoints.append({"issue_time": None if cutoff is None else str(cutoff),
                                    "model_file": meta["model_file"], "model_sha256": meta["model_sha256"],
                                    "train_max_target": meta["train_max_target"], "train_max_available": meta["train_max_available"],
                                    "training_rows": meta["train_rows"], "iterations": meta["iterations"]})
            route["segments"].append({"segment": segment, "match": match, "features": features, "checkpoints": checkpoints})
            final_feature_map[f"{horizon}__{segment}"] = features
        registry["routes"][horizon] = route
        registry[horizon] = {"model": route["model"], "feature_group": route["feature_group"],
                             "validation_mae": route["validation_mae"], "architecture": route["architecture"]}
    dump_json(ROOT / "models/model_registry.json", registry)
    dump_json(ROOT / "models/final_features.json", {"features": sorted(set(sum(final_feature_map.values(), []))), "by_route": final_feature_map})
    importance = pd.DataFrame(importance_rows)
    importance.to_csv(REPORTS / "feature_importance_by_model.csv", index=False)
    aggregate = importance.groupby("feature").importance.mean().sort_values(ascending=False).reset_index()
    aggregate.to_csv(REPORTS / "feature_importance.csv", index=False)
    pd.DataFrame(shap_rows).to_csv(REPORTS / "shap_importance.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    top = aggregate.head(25).iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, max(5, len(top) * .3)))
    ax.barh(top.feature, top.importance, color="#246a9d")
    ax.set_xlabel("Mean normalized native importance across final models")
    ax.set_title("Final power forecast model: feature importance")
    fig.tight_layout()
    fig.savefig(REPORTS / "feature_importance.png", dpi=150)
    plt.close(fig)
    from .ml_reporting import final_feature_report
    final_feature_report(groups, final_feature_map, aggregate, selected, run_dir)


def predict_final():
    registry = json.loads((ROOT / "models/model_registry.json").read_text(encoding="utf-8"))
    raw_path = ROOT / "data/final/competition_features.parquet"
    if sha256(raw_path) != registry["input_competition_sha256"]:
        raise ValueError("Competition input changed; inspect schema and retrain/re-register deliberately")
    frame = add_ml_transforms(pd.read_parquet(raw_path))
    predictions = frame[KEYS].copy()
    predictions["predicted_normalized_active_power"] = np.nan
    predictions["selected_model"] = ""
    predictions["selected_feature_group"] = ""
    predictions["model_checkpoint"] = ""
    assigned = np.zeros(len(frame), dtype=int)
    loaded, logs = {}, []
    for horizon, route in registry["routes"].items():
        for segment in route["segments"]:
            part = subset(frame[frame.horizon_bucket == horizon], segment["match"])
            main = next(c for c in segment["checkpoints"] if c["issue_time"] is None)
            for issue, query in part.groupby("forecast_issue_time"):
                checkpoint = next((c for c in segment["checkpoints"] if c["issue_time"] is not None and pd.Timestamp(c["issue_time"]) == issue), main)
                if pd.Timestamp(checkpoint["train_max_available"]) >= issue:
                    raise ValueError("Final model trained on a label unavailable at this forecast issue")
                model_file = checkpoint["model_file"]
                if model_file not in loaded:
                    path = ROOT / model_file
                    if sha256(path) != checkpoint["model_sha256"]:
                        raise ValueError("Model file integrity check failed")
                    loaded[model_file] = joblib.load(path)
                pred, unseen = predict_learner(loaded[model_file], query, registry["clip_bounds"])
                ids = query.index
                assigned[ids] += 1
                predictions.loc[ids, "predicted_normalized_active_power"] = pred
                predictions.loc[ids, "selected_model"] = route["experiment_id"]
                predictions.loc[ids, "selected_feature_group"] = route["feature_group"]
                predictions.loc[ids, "model_checkpoint"] = model_file
                logs.append({"horizon": horizon, "issue": str(issue), "rows": len(query), "checkpoint": model_file,
                             "train_max_available": checkpoint["train_max_available"], "unseen_categories": unseen})
    if not (assigned == 1).all() or not predictions.predicted_normalized_active_power.between(*registry["clip_bounds"]).all():
        raise ValueError("Missing, duplicate or invalid competition predictions")
    if predictions.duplicated(KEYS).any():
        raise ValueError("Duplicate output keys")
    directory = ROOT / "predictions"
    directory.mkdir(exist_ok=True)
    output = directory / "final_forecast.parquet"
    predictions.to_parquet(output, index=False)
    predictions.to_csv(directory / "final_forecast.csv", index=False)
    pd.testing.assert_frame_equal(predictions, pd.read_parquet(output))
    summary = {"status": "PASS", "rows": len(predictions), "finite_predictions": True,
               "one_prediction_per_input_key": True, "all_model_labels_available_before_issue": True,
               "min_prediction": float(predictions.predicted_normalized_active_power.min()),
               "max_prediction": float(predictions.predicted_normalized_active_power.max()),
               "coverage": predictions.groupby(["turbine_id", "horizon_bucket"]).size().to_dict(),
               "parquet_sha256": sha256(output), "csv_sha256": sha256(directory / "final_forecast.csv"), "batches": logs}
    summary["coverage"] = {"/".join(k): int(v) for k, v in summary["coverage"].items()}
    dump_json(REPORTS / "prediction_validation.json", summary)
    print(f"Predictions verified: {len(predictions)} rows; SHA256 {summary['parquet_sha256']}", flush=True)
    return predictions
