"""Independent model benchmark -- challenge the production model without touching it.

The forecasting pipeline ships one model (LightGBM, in `src/model.py`). This
module exists to question that choice honestly: it trains challenger models on
exactly the same rows, features and power-curve prior, scores them over
rolling-origin folds, and reports whether any difference is real or noise.

Nothing here is imported by the production path. Running it cannot change a
published forecast -- it only produces evidence.

Run:
    python -m src.benchmark                      # 3 rolling-origin folds
    python -m src.benchmark --folds 1            # the production hold-out only
    python -m src.benchmark --models lightgbm catboost --quantiles
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from src import calibration, config, dataset, metrics, model, train

# Validation windows, oldest first. Each fold trains on everything before its
# start, so no fold ever sees its own future.
DEFAULT_FOLDS: tuple[tuple[str, str], ...] = (
    ("2025-02-01", "2025-06-01"),
    ("2025-06-01", "2025-10-01"),
    ("2025-10-01", "2026-01-31"),
)
QUANTILES = (0.1, 0.5, 0.9)
BOOTSTRAP_RESAMPLES = 4000


@dataclass
class Prediction:
    """One candidate's output on one fold."""

    point: np.ndarray
    quantiles: dict[float, np.ndarray] | None = None
    iterations: int = 0


# --------------------------------------------------------------------------
# Candidates
# --------------------------------------------------------------------------
def fit_lightgbm(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """The production model, refitted here so the comparison is like-for-like."""
    fitted = model.fit(
        tr, features, curve, "benchmark", valid=va,
        quantiles=QUANTILES if with_quantiles else (),
    )
    point = np.clip(fitted.point.predict(va[features], num_iteration=fitted.best_iteration), 0, 1)
    quantiles = (
        {a: np.clip(b.predict(va[features]), 0, 1) for a, b in fitted.quantiles.items()}
        if with_quantiles else None
    )
    return Prediction(point=point, quantiles=quantiles, iterations=fitted.best_iteration)


def fit_lightgbm_l1(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """LightGBM with an L1 objective.

    The fair control for any model trained on Huber or MAE loss. Comparing an
    L2-trained booster against an MAE-trained network on MAE flatters the
    network for reasons that have nothing to do with architecture.
    """
    fitted = model.fit(tr, features, curve, "benchmark", valid=va, quantiles=(),
                       params={"objective": "regression_l1", "metric": "l1"})
    return Prediction(
        point=np.clip(fitted.point.predict(va[features], num_iteration=fitted.best_iteration), 0, 1),
        iterations=fitted.best_iteration,
    )


def fit_catboost(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """CatBoost challenger.

    Imported lazily so the repository still runs end to end for anyone who has
    not installed the optional benchmark dependency.
    """
    try:
        from catboost import CatBoostRegressor
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise SystemExit(
            "catboost is not installed. Run: pip install catboost\n"
            "It is an optional benchmark-only dependency; the forecast pipeline "
            "does not need it."
        ) from exc

    mask_tr, mask_va = model.training_mask(tr), model.training_mask(va)
    x_train, y_train = tr.loc[mask_tr, features], tr.loc[mask_tr, "power"]
    eval_set = (va.loc[mask_va, features], va.loc[mask_va, "power"])

    base = dict(depth=6, learning_rate=0.03, l2_leaf_reg=5, random_seed=42,
                verbose=0, allow_writing_files=False)
    point_model = CatBoostRegressor(
        iterations=4000, loss_function="RMSE", early_stopping_rounds=120, **base
    )
    point_model.fit(x_train, y_train, eval_set=eval_set)
    best = point_model.get_best_iteration() or 4000
    point = np.clip(point_model.predict(va[features]), 0, 1)

    quantiles = None
    if with_quantiles:
        quantiles = {}
        for alpha in QUANTILES:
            q = CatBoostRegressor(iterations=best, loss_function=f"Quantile:alpha={alpha}", **base)
            q.fit(x_train, y_train)
            quantiles[alpha] = np.clip(q.predict(va[features]), 0, 1)

    return Prediction(point=point, quantiles=quantiles, iterations=int(best))


# --------------------------------------------------------------------------
# Linear candidates
#
# These answer a different question from the boosting comparison: how much of
# the skill is the non-linearity, and how much is already carried by the
# features? A linear model here is not fitting raw wind speed -- it gets
# `pc_prior`, the fitted power curve, which has already absorbed the S-shaped
# wind-to-power relationship. So this measures what the trees add *on top of*
# the physics, not the value of machine learning as such.
#
# Trees ignore feature scale and handle missing values natively; linear models
# do neither, so every linear candidate is wrapped in median imputation and
# standardisation. Regularisation strength is chosen by TimeSeriesSplit on the
# training rows only -- a shuffled CV would leak future hours into the choice.
# --------------------------------------------------------------------------
LINEAR_ALPHAS = np.logspace(-4, 2, 25)


def _linear_frame(tr, va, features):
    """Chronologically ordered training matrix, plus the validation matrix."""
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    mask = model.training_mask(tr)
    ordered = tr.loc[mask].sort_values("time")
    steps = [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    return ordered[features], ordered["power"], va[features], steps


def _fit_linear(estimator, tr, va, features) -> Prediction:
    from sklearn.pipeline import Pipeline

    x_train, y_train, x_valid, steps = _linear_frame(tr, va, features)
    pipeline = Pipeline([*steps, ("model", estimator)])
    pipeline.fit(x_train, y_train)
    # Power is physically bounded; an unbounded linear fit will predict outside
    # [0, 1] near calm and above rated, and clipping is the honest correction.
    return Prediction(point=np.clip(pipeline.predict(x_valid), 0, 1), quantiles=None)


def fit_linear(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """Ordinary least squares -- no regularisation."""
    from sklearn.linear_model import LinearRegression

    return _fit_linear(LinearRegression(), tr, va, features)


def fit_ridge(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """L2. Shrinks correlated coefficients together rather than choosing between them.

    That suits this feature set, which is deliberately collinear: ws100, its
    square and cube, three ensemble members and their consensus all move together.
    """
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import TimeSeriesSplit

    return _fit_linear(RidgeCV(alphas=LINEAR_ALPHAS, cv=TimeSeriesSplit(4)), tr, va, features)


def fit_lasso(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """L1. Drives coefficients to exactly zero, so it also selects features."""
    from sklearn.linear_model import LassoCV
    from sklearn.model_selection import TimeSeriesSplit

    estimator = LassoCV(alphas=LINEAR_ALPHAS, cv=TimeSeriesSplit(4),
                        max_iter=20000, random_state=42, n_jobs=-1)
    return _fit_linear(estimator, tr, va, features)


def fit_elasticnet(tr, va, features, curve, with_quantiles: bool) -> Prediction:
    """L1 + L2 combined, with the mix chosen by cross-validation."""
    from sklearn.linear_model import ElasticNetCV
    from sklearn.model_selection import TimeSeriesSplit

    estimator = ElasticNetCV(l1_ratio=[0.1, 0.5, 0.7, 0.9, 0.95, 1.0], alphas=LINEAR_ALPHAS,
                             cv=TimeSeriesSplit(4), max_iter=20000, random_state=42, n_jobs=-1)
    return _fit_linear(estimator, tr, va, features)


CANDIDATES: dict[str, Callable[..., Prediction]] = {
    "lightgbm": fit_lightgbm,
    "lightgbm_l1": fit_lightgbm_l1,
    "catboost": fit_catboost,
    "linear": fit_linear,
    "ridge": fit_ridge,
    "lasso": fit_lasso,
    "elasticnet": fit_elasticnet,
}


# --------------------------------------------------------------------------
# Protocol
# --------------------------------------------------------------------------
def prepare_fold(labelled: pd.DataFrame, valid_start: str, valid_end: str):
    """Split chronologically and fit the power-curve prior on training rows only."""
    tr = labelled[labelled["issue_time"] < valid_start].copy()
    va = labelled[(labelled["issue_time"] >= valid_start) & (labelled["issue_time"] < valid_end)].copy()
    curve = dataset.fit_effective_power_curve(tr)
    return dataset.attach_power_curve_prior(tr, curve), dataset.attach_power_curve_prior(va, curve), curve


def apply_online_calibration(va: pd.DataFrame, column: str) -> pd.Series:
    """Replay the shipped bias correction so models are compared as deployed.

    A model is only as good as its calibrated output: a challenger that wins on
    raw predictions but whose edge is pure bias would be flattered by a raw-only
    comparison, because the production pipeline removes bias anyway.
    """
    out = va.sort_values(["turbine_id", "issue_time", "time"]).copy()
    out["calibrated"] = out[column]
    calibrator = calibration.ForecastCalibrator()
    for _, group in out.groupby("turbine_id"):
        log = group[["time", column, "power"]].rename(columns={column: "forecast"})
        for issue, block in group.groupby("issue_time"):
            state = calibrator.fit(log, as_of=issue)
            out.loc[block.index, "calibrated"] = (block[column] - state.bias).clip(0, 1)
    return out["calibrated"].reindex(va.index)


def paired_bootstrap(errors_a: np.ndarray, errors_b: np.ndarray, seed: int = 0) -> dict:
    """Is B's lower error real, or could the same hours have gone either way?

    Paired on the hour, because both models saw identical weather -- an unpaired
    test would drown the difference in day-to-day variance the models share.
    """
    rng = np.random.default_rng(seed)
    diff = errors_a - errors_b
    draws = np.array([rng.choice(diff, diff.size, replace=True).mean()
                      for _ in range(BOOTSTRAP_RESAMPLES)])
    low, high = np.percentile(draws, [2.5, 97.5])
    # Two-sided: the interval excluding zero is what makes a difference real,
    # in whichever direction it falls. Testing only `low > 0` would report a
    # decisively *worse* challenger as "not significant", which is backwards.
    return {
        "mean_mae_difference": float(diff.mean()),
        "ci_low": float(low), "ci_high": float(high),
        "prob_b_better": float((draws > 0).mean()),
        "significant": bool(low > 0 or high < 0),
        "direction": "challenger better" if diff.mean() > 0 else "baseline better",
    }


def run(models: list[str], folds, with_quantiles: bool, verbose: bool = True) -> dict:
    """Score every candidate over every fold and test the differences."""
    pooled = train.load_pooled()
    labelled = pooled[pooled["issue_time"] <= pd.Timestamp(train.TRAIN_ISSUE_END)]
    features = train.FEATURE_COLUMNS

    fold_rows: list[dict] = []
    calibrated_errors: dict[str, list[np.ndarray]] = {m: [] for m in models}

    for valid_start, valid_end in folds:
        tr, va, curve = prepare_fold(labelled, valid_start, valid_end)
        label = f"{valid_start[:7]}..{valid_end[:7]}"
        if verbose:
            print(f"\nfold {label}  train={int(model.training_mask(tr).sum()):,}  valid={len(va):,}")

        for name in models:
            prediction = CANDIDATES[name](tr, va, features, curve, with_quantiles)
            va[name] = prediction.point
            va[f"{name}_cal"] = apply_online_calibration(va, name)

            scored = va.dropna(subset=["power"])
            raw = metrics.point_metrics(scored["power"], scored[name])
            cal = metrics.point_metrics(scored["power"], scored[f"{name}_cal"])
            row = {
                "fold": label, "model": name, "n": raw["n"], "iterations": prediction.iterations,
                "mae_raw": raw["mae"], "mae_calibrated": cal["mae"],
                "rmse_calibrated": cal["rmse"], "r2_calibrated": cal["r2"],
                "bias_calibrated": cal["bias"],
            }

            if with_quantiles and prediction.quantiles:
                band = np.sort(np.column_stack([prediction.quantiles[a] for a in QUANTILES]), axis=1)
                for i, alpha in enumerate(QUANTILES):
                    va[f"{name}_p{int(alpha*100)}"] = band[:, i]
                scored = va.dropna(subset=["power"])
                coverage = metrics.interval_coverage(
                    scored["power"], scored[f"{name}_p10"], scored[f"{name}_p90"]
                )
                row["coverage"] = coverage["coverage"]
                row["band_width"] = coverage["mean_width"]
                row["pinball_p50"] = metrics.pinball_loss(scored["power"], scored[f"{name}_p50"], 0.5)

            fold_rows.append(row)
            calibrated_errors[name].append(
                (scored[f"{name}_cal"] - scored["power"]).abs().to_numpy()
            )
            if verbose:
                extra = f"  coverage {row['coverage']:.3f}" if "coverage" in row else ""
                print(f"  {name:10s} MAE raw {row['mae_raw']:.4f} -> calibrated "
                      f"{row['mae_calibrated']:.4f}   R2 {row['r2_calibrated']:.3f}{extra}")

    table = pd.DataFrame(fold_rows)
    report = {"folds": fold_rows, "summary": {}, "significance": {}}

    summary = table.groupby("model")[["mae_raw", "mae_calibrated", "rmse_calibrated", "r2_calibrated"]].mean()
    report["summary"] = summary.to_dict()

    baseline = models[0]
    for challenger in models[1:]:
        a = np.concatenate(calibrated_errors[baseline])
        b = np.concatenate(calibrated_errors[challenger])
        test = paired_bootstrap(a, b)
        wins = int(
            (table[table.model == challenger].set_index("fold")["mae_calibrated"]
             < table[table.model == baseline].set_index("fold")["mae_calibrated"]).sum()
        )
        test["folds_won"] = wins
        test["folds_total"] = len(folds)
        report["significance"][f"{challenger}_vs_{baseline}"] = test

    if verbose:
        _print_summary(table, summary, report, baseline, models)

    path = config.REPORT_DIR / "model_comparison.json"
    path.write_text(json.dumps(report, indent=2, default=float))
    if verbose:
        print(f"\nWrote {path}")
    return report


def _print_summary(table, summary, report, baseline, models) -> None:
    print("\n" + "=" * 72)
    print("MEAN ACROSS FOLDS (calibrated = as the pipeline would actually ship it)")
    print(summary.to_string(float_format=lambda v: f"{v:8.4f}"))

    for key, test in report["significance"].items():
        challenger = key.split("_vs_")[0]
        base_mae = summary.loc[baseline, "mae_calibrated"]
        chal_mae = summary.loc[challenger, "mae_calibrated"]
        print(f"\n{challenger} vs {baseline}:")
        print(f"  MAE {base_mae:.4f} -> {chal_mae:.4f} ({100*(1-chal_mae/base_mae):+.2f}%), "
              f"won {test['folds_won']}/{test['folds_total']} folds")
        verdict = f"SIGNIFICANT, {test['direction']}" if test["significant"] else "not significant"
        print(f"  paired bootstrap {test['mean_mae_difference']:+.5f} "
              f"95% CI [{test['ci_low']:+.5f}, {test['ci_high']:+.5f}] -> {verdict}")
    print("=" * 72)


def dump_reference_predictions(
    out_path, valid_start: str = "2025-10-01", valid_end: str = "2026-01-31",
    candidate: str = "lightgbm", day_ahead_only: bool = True,
) -> None:
    """Write the baseline's validation predictions to parquet.

    Exists so that consumers which cannot host LightGBM in-process can still
    compare against it. On macOS, PyTorch ships its own OpenMP runtime and
    LightGBM links another; loading both into one interpreter segfaults the
    moment LightGBM opens a parallel region. Running this in a torch-free
    process and exchanging a parquet file sidesteps that entirely.
    """
    pooled = train.load_pooled()
    labelled = pooled[pooled["issue_time"] <= pd.Timestamp(train.TRAIN_ISSUE_END)]
    tr, va, curve = prepare_fold(labelled, valid_start, valid_end)
    va = va.copy()
    names = [candidate] if isinstance(candidate, str) else list(candidate)
    for name in names:
        va[name] = CANDIDATES[name](tr, va, train.FEATURE_COLUMNS, curve, False).point
    if day_ahead_only:
        va = va[va["lead_hours"] < 48]
    va[["turbine", "time", "power", *names]].to_parquet(out_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark challenger models against production")
    parser.add_argument("--models", nargs="+", default=["lightgbm", "catboost"],
                        choices=sorted(CANDIDATES), help="first entry is the baseline")
    parser.add_argument("--folds", type=int, default=len(DEFAULT_FOLDS),
                        help="how many rolling-origin folds, counting back from the most recent")
    parser.add_argument("--quantiles", action="store_true", help="also compare P10-P90 bands")
    args = parser.parse_args()
    run(args.models, DEFAULT_FOLDS[-args.folds:], args.quantiles)


if __name__ == "__main__":
    main()
