"""Orchestrate compact-feature experiments without touching the weather pipeline."""
import argparse
import importlib.metadata
import json
import platform
import hashlib
import warnings

import numpy as np
import pandas as pd

from .ml_data import ROOT, REPORTS, prepare, dump_json, sha256
from .ml_experiments import spec, evaluate, choose_simple
from .ml_selection import select_candidates


def environment_versions():
    names = ["numpy", "pandas", "pyarrow", "catboost", "lightgbm", "xgboost", "scikit-learn", "scipy", "matplotlib", "joblib"]
    # import paths take priority over potentially duplicated dist-info directories.
    import numpy, pandas, pyarrow, catboost, lightgbm, xgboost, sklearn, scipy, matplotlib, joblib
    modules = [numpy, pandas, pyarrow, catboost, lightgbm, xgboost, sklearn, scipy, matplotlib, joblib]
    return dict(zip(names, [m.__version__ for m in modules])) | {"python": platform.python_version()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    warnings.filterwarnings("ignore", message="The argument 'eval_set' is deprecated")
    train, comp, groups, folds, config = prepare()
    versions = environment_versions()
    inputs = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in [
        ROOT / "data/final/training_dataset.parquet", ROOT / "data/final/competition_features.parquet",
        ROOT / "data/final/training_weather_dataset.parquet", ROOT / "data/processed/scada_hourly.parquet",
        ROOT / "ml_config.json", ROOT / "src/ml_data.py", ROOT / "src/ml_models.py",
        ROOT / "src/ml_selection.py", ROOT / "src/ml_experiments.py"]}
    run_id = hashlib.sha256(json.dumps({"inputs": inputs, "versions": versions}, sort_keys=True).encode()).hexdigest()[:16]
    run_dir = ROOT / "experiments" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    dump_json(run_dir / "run_manifest.json", {"run_id": run_id, "inputs": inputs, "versions": versions, "config": config})
    dump_json(ROOT / "models/environment.json", versions)
    (ROOT / "requirements-ml.txt").write_text("\n".join(f"{name}=={version}" for name, version in versions.items() if name != "python") + "\n", encoding="utf-8")
    dump_json(REPORTS / "ml_active_run.json", {"run_id": run_id, "run_directory": str(run_dir)})
    if args.audit_only:
        print("AUDIT COMPLETE", flush=True)
        return
    np.random.seed(config["seed"])
    results = []

    def run(s):
        if any(r["id"] == s["id"] for r in results):
            return next(r for r in results if r["id"] == s["id"])
        result = evaluate(s, train, groups, folds, config, run_dir)
        results.append(result)
        pd.DataFrame(results).sort_values("MAE").to_csv(REPORTS / "model_leaderboard_progress.csv", index=False)
        return result

    for baseline in ["HistoricalMean", "HistoricalMedian", "Persistence"]:
        run(spec(baseline, "Baseline"))
    # CORE is evaluated first, before the broader controlled tournament.
    for model in config["models"]:
        run(spec(model, "CORE"))
    groups = select_candidates(train.loc[folds[0]["train"]], groups, config, run_dir)
    for model in config["models"]:
        for group in config["feature_groups"]:
            run(spec(model, group))
    # Reference benchmark and identical feature-count curves for two learners.
    for model in ["CatBoost", "LightGBM"]:
        run(spec(model, "Full206"))
        run(spec(model, "Full_No_Performance"))
        for count in config["feature_count_grid"]:
            run(spec(model, f"Top{count}"))
    # SELECTED is exactly Top30, not an additional statistically independent trial.
    table = pd.DataFrame(results)
    candidates = table[(table.model.isin(config["models"])) & (table.feature_count <= config["maximum_preferred_features"])]
    top = candidates.sort_values(["MAE", "std_fold_MAE"]).head(config["top_configurations_to_tune"])
    for _, row in top.iterrows():
        for variant in ["regularized", "richer"]:
            run(spec(row.model, row.feature_group, "global", variant))
    global_candidates = [r for r in results if r["model"] in config["models"] and r["architecture"] == "global"]
    global_best = choose_simple(global_candidates, config)
    # Same underlying learner/group/hyperparameters isolate architecture effects.
    for architecture in ["horizon", "turbine", "horizon_turbine"]:
        run(spec(global_best["model"], global_best["feature_group"], architecture, global_best["variant"]))
    eligible = [r for r in results if r["model"] in config["models"]]
    selected = {h: choose_simple(eligible, config, f"MAE_{h}") for h in ["D1", "D2"]}
    # Prefer a single global configuration unless horizon routing makes a material difference.
    oof_counts = pd.concat([f["validation_frame"] for f in folds]).horizon_bucket.value_counts()
    policy_mae = sum(selected[h][f"MAE_{h}"] * int(oof_counts[h]) for h in selected) / oof_counts.sum()
    global_gain = 1 - policy_mae / global_best["MAE"]
    if global_gain < config["simplicity_tolerance_relative"]:
        selected = {h: global_best for h in ["D1", "D2"]}
    dump_json(run_dir / "selection.json", {"selected": selected, "architecture_reference": global_best,
                                          "tuning_shortlist": top.id.tolist(), "feature_groups": groups})
    dump_json(run_dir / "all_results.json", results)
    # Late import permits standalone audit and keeps reports out of experiment fingerprints.
    from .ml_reporting import write_reports
    from .ml_final import train_final, predict_final
    write_reports(train, comp, folds, groups, config, results, selected, global_best, run_dir)
    train_final(train, comp, groups, config, selected, run_dir, versions)
    predict_final()
    # Verify immutable Parquet inputs after every expensive stage has completed.
    for relative, expected in inputs.items():
        if relative.endswith(".parquet") and sha256(ROOT / relative) != expected:
            raise ValueError(f"Input was modified: {relative}")
    dump_json(REPORTS / "ml_training_status.json", {"status": "COMPLETE", "run_id": run_id,
              "experiments": len(results), "selected": {h: s["id"] for h, s in selected.items()},
              "competition_rows": len(comp), "immutable_input_hashes_verified": True})
    print("ML TRAINING AND COMPETITION INFERENCE COMPLETE", flush=True)


if __name__ == "__main__":
    main()
