"""Offline jury checks. No weather calls; no scoring of final models on training data."""
import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def fingerprint(path, mode="binary"):
    data = path.read_bytes()
    if mode == "text_lf":
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def verify_bundle():
    manifest = json.loads((ROOT / "jury_bundle_manifest.json").read_text(encoding="utf-8"))
    errors = []
    for entry in manifest["files"]:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise ValueError("Manifest path outside the jury project")
        if not path.is_file():
            errors.append("missing: " + entry["path"])
        elif fingerprint(path, entry["hash_mode"]) != entry["sha256"]:
            errors.append("modified: " + entry["path"])
    if errors:
        raise ValueError("Jury bundle integrity failed:\n" + "\n".join(errors[:25]))
    print(f"Bundle integrity: PASS ({len(manifest['files'])} files)", flush=True)
    return manifest


def check_environment():
    names = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "scipy", "joblib"]
    expected = json.loads((ROOT / "models/environment.json").read_text(encoding="utf-8"))
    versions, missing, mismatched = {}, [], []
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
            continue
        if versions[name] != expected[name]:
            mismatched.append(f"{name}: installed {versions[name]}, expected {expected[name]}")
    if missing or mismatched:
        raise RuntimeError("Use a clean Python 3.12 environment and run:\npython -m pip install -r requirements-jury.txt\n"
                           + "\n".join(["Missing: " + ", ".join(missing)] if missing else []) + "\n" + "\n".join(mismatched))
    if sys.version_info[:2] != (3, 12):
        print("Warning: published run used Python 3.12; this Python version has not been verified.", flush=True)
    print("Required library versions: PASS", flush=True)
    return versions


def evaluate_saved_oof():
    import numpy as np
    import pandas as pd
    from src.ml_data import TARGET, KEYS
    from src.ml_models import metric_values

    registry = json.loads((ROOT / "models/model_registry.json").read_text(encoding="utf-8"))
    run = ROOT / "experiments" / registry["run_id"]
    train = pd.read_parquet(ROOT / "data/final/training_dataset.parquet")
    selected = pd.read_parquet(ROOT / "predictions/validation_predictions.parquet").sort_values("row_id").reset_index(drop=True)
    if selected.row_id.duplicated().any():
        raise ValueError("Duplicated OOF observation")
    truth = train.loc[selected.row_id]
    pd.testing.assert_frame_equal(selected[KEYS].reset_index(drop=True), truth[KEYS].reset_index(drop=True))
    np.testing.assert_array_equal(selected[TARGET], truth[TARGET])
    # Validate the same held-out rows for every archived experiment, recomputing
    # metrics from predictions rather than trusting the published score tables.
    leaderboard = pd.read_csv(ROOT / "reports/model_leaderboard.csv")
    table = []
    for row in leaderboard.itertuples():
        oof = pd.read_parquet(run / row.id / "oof_predictions.parquet").sort_values("row_id").reset_index(drop=True)
        np.testing.assert_array_equal(oof.row_id, selected.row_id)
        np.testing.assert_array_equal(oof[TARGET], selected[TARGET])
        metrics = metric_values(oof[TARGET], oof.prediction)
        np.testing.assert_allclose(metrics["MAE"], row.MAE, rtol=0, atol=1e-12)
        np.testing.assert_allclose(metrics["RMSE"], row.RMSE, rtol=0, atol=1e-12)
        for horizon, route in registry["routes"].items():
            if route["experiment_id"] == row.id:
                mask = selected.horizon_bucket == horizon
                np.testing.assert_allclose(selected.loc[mask, "prediction"], oof.loc[mask, "prediction"], rtol=0, atol=1e-12)
        table.append({"experiment": row.id, **metrics})
    summary = metric_values(selected[TARGET], selected.prediction)
    reference = json.loads((ROOT / "reports/ml_summary.json").read_text(encoding="utf-8"))
    np.testing.assert_allclose(summary["MAE"], reference["overall"]["MAE"], rtol=0, atol=1e-12)
    baselines = leaderboard[leaderboard.model.isin(["HistoricalMean", "HistoricalMedian", "Persistence"])]
    ratio = summary["MAE"] / baselines.MAE.min()
    horizon_metrics = {h: metric_values(part[TARGET], part.prediction) for h, part in selected.groupby("horizon_bucket")}
    print(f"Recomputed saved OOF scores: PASS ({len(table)} configurations, {len(selected)} held-out rows)", flush=True)
    print(f"Power MAE={summary['MAE']:.6f}; RMSE={summary['RMSE']:.6f}; MAE/best baseline={ratio:.6f}", flush=True)
    return {"overall": summary, "by_horizon": horizon_metrics, "ratio_vs_baseline": float(ratio), "configurations": len(table),
            "note": "Recomputed metrics from archived out-of-fold predictions, not a fresh retraining or independent February test"}


def reproduce_forecast():
    import numpy as np
    import pandas as pd
    from src.ml_data import KEYS
    from src.ml_final import predict_final

    reference = pd.read_parquet(ROOT / "predictions/final_forecast.parquet")
    regenerated = predict_final()
    pd.testing.assert_frame_equal(reference[KEYS], regenerated[KEYS])
    col = "predicted_normalized_active_power"
    difference = float(np.abs(reference[col] - regenerated[col]).max())
    np.testing.assert_allclose(reference[col], regenerated[col], rtol=0, atol=1e-10)
    print(f"Saved-model inference: PASS ({len(regenerated)} rows; maximum prediction difference {difference:.3g})", flush=True)
    return {"rows": len(regenerated), "max_abs_difference": difference, "tolerance": 1e-10}


def retrain_winner():
    import numpy as np
    import pandas as pd
    from src.input_data import load_config
    from src.ml_data import TARGET, add_ml_transforms, frozen_history_view
    from src.ml_models import fit_learner, predict_learner, metric_values, segments, subset

    config = json.loads((ROOT / "ml_config.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "models/model_registry.json").read_text(encoding="utf-8"))
    train = add_ml_transforms(pd.read_parquet(ROOT / "data/final/training_dataset.parquet"))
    source = pd.read_parquet(ROOT / "data/final/training_weather_dataset.parquet")
    expected = pd.read_parquet(ROOT / "predictions/validation_predictions.parquet").set_index("row_id")
    published_folds = pd.read_csv(ROOT / "reports/validation_folds.csv")
    months = train.target_local_time.dt.to_period("M")
    output = []
    config_cache = {}
    for record in published_folds.itertuples():
        month = pd.Period(record.fold, freq="M")
        valid = train.loc[months == month]
        first_issue = valid.forecast_issue_time.min()
        fit = train[(months < month) & (train.target_time + pd.Timedelta(hours=config["observation_delay_hours"]) < first_issue)]
        if first_issue != pd.Timestamp(record.first_forecast_issue) or len(fit) != record.train_rows or len(valid) != record.validation_rows:
            raise ValueError("Recomputed validation fold differs from published fold")
        if fit.target_time.max() >= valid.target_time.min():
            raise ValueError("Training/validation target overlap")
        query = frozen_history_view(valid, source, pd.Timestamp(record.history_target_cutoff), load_config())
        query.index = valid.index
        query = add_ml_transforms(query)
        pred = pd.Series(np.nan, index=query.index)
        for horizon, route in registry["routes"].items():
            for segment, match, part in segments(fit, route["architecture"]):
                target = subset(query[query.horizon_bucket == horizon], match)
                if target.empty:
                    continue
                route_segment = next(s for s in route["segments"] if s["segment"] == segment)
                key = (record.fold, route["experiment_id"], segment)
                if key not in config_cache:
                    config_cache[key] = fit_learner(part, route_segment["features"], route["model"], config, route["variant"])
                values, _ = predict_learner(config_cache[key], target, config["clip_bounds"])
                pred.loc[target.index] = values
        if pred.isna().any():
            raise ValueError("Incomplete replay")
        actual = expected.loc[pred.index, "prediction"]
        difference = float(np.abs(pred - actual).max())
        # Native floating-point implementations can vary across OS/CPU. The
        # same tested environment reproduced identical results; fail loudly if
        # the numerical prediction drift is larger than the declared tolerance.
        np.testing.assert_allclose(pred, actual, rtol=0, atol=1e-8)
        metrics = metric_values(query[TARGET], pred)
        print(f"Fresh winner fit {record.fold}: MAE={metrics['MAE']:.6f}, max OOF prediction difference={difference:.3g}", flush=True)
        output.append({"fold": record.fold, "max_abs_difference": difference, **metrics})
    return {"folds": output, "status": "PASS", "note": "Fresh training from historical labels; outer validation not used for early stopping"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Verify artifact checksums without third-party dependencies")
    parser.add_argument("--retrain-winner", action="store_true", help="Additionally fit the selected model on each of the four historical folds")
    args = parser.parse_args()
    manifest = verify_bundle()
    if args.check_only:
        return
    versions = check_environment()
    # This import enables the optional local .deps directory for the original
    # development workspace; a clean jury clone uses only its virtualenv.
    import src
    import warnings
    warnings.filterwarnings("ignore", message="The argument 'eval_set' is deprecated")
    result = {"bundle_run_id": manifest["run_id"], "versions": versions,
              "saved_oof": evaluate_saved_oof(), "forecast": reproduce_forecast()}
    if args.retrain_winner:
        result["fresh_retraining"] = retrain_winner()
    out = ROOT / "jury_results"
    out.mkdir(exist_ok=True)
    (out / "verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("JURY VERIFICATION PASSED. Details: jury_results/verification.json", flush=True)


if __name__ == "__main__":
    main()
