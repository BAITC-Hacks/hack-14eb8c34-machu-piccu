"""Train the pooled forecast model and report hold-out skill.

Run:  python -m src.train
      python -m src.train --no-cache      (rebuild the replayed dataset)

The two turbines stand a few hundred metres apart and see effectively the same
weather, so they are trained as one pooled model with a turbine indicator. That
doubles the rows available for learning the wind-to-power relationship while
still letting the model separate the two machines' behaviour.
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from src import calibration, config, dataset, features, metrics, model

TRAIN_ISSUE_START = config.LEAD_ARCHIVE_START
TRAIN_ISSUE_END = "2026-01-30"     # last issue date whose targets are still in SCADA
VALID_ISSUE_START = "2025-10-01"   # final ~4 months held out
POOLED_KEY = "pooled"

FEATURE_COLUMNS = features.FEATURE_COLUMNS + ["turbine_id"]


def dataset_path(turbine_key: str):
    return config.ARTIFACT_DIR / f"ds_{turbine_key}.parquet"


def load_or_build(turbine_key: str, use_cache: bool = True) -> pd.DataFrame:
    """Replayed feature table for one turbine, cached to parquet."""
    path = dataset_path(turbine_key)
    if use_cache and path.exists():
        frame = pd.read_parquet(path)
    else:
        frame = dataset.build_dataset(turbine_key, TRAIN_ISSUE_START, config.TEST_END)
        frame.to_parquet(path, index=False)

    frame["is_anomaly_hour"] = frame["is_anomaly_hour"].fillna(False)
    frame["turbine_id"] = list(config.TURBINES).index(turbine_key)
    frame["turbine"] = turbine_key
    return frame


def load_pooled(use_cache: bool = True) -> pd.DataFrame:
    return pd.concat([load_or_build(k, use_cache) for k in config.TURBINES], ignore_index=True)


def train(use_cache: bool = True, verbose: bool = True) -> model.TrainedModel:
    pooled = load_pooled(use_cache)
    labelled = pooled[pooled["issue_time"] <= pd.Timestamp(TRAIN_ISSUE_END)]

    train_part = labelled[labelled["issue_time"] < VALID_ISSUE_START].copy()
    valid_part = labelled[labelled["issue_time"] >= VALID_ISSUE_START].copy()

    # The power curve is a learned artefact: fitted on the training split only.
    curve = dataset.fit_effective_power_curve(train_part)
    train_part = dataset.attach_power_curve_prior(train_part, curve)
    valid_part = dataset.attach_power_curve_prior(valid_part, curve)

    fitted = model.fit(
        train_part, FEATURE_COLUMNS, power_curve=curve, turbine=POOLED_KEY, valid=valid_part
    )

    scored = pd.concat(
        [valid_part.reset_index(drop=True), model.predict(fitted, valid_part).reset_index(drop=True)],
        axis=1,
    )
    report = _report(scored, fitted, verbose)
    fitted.save(config.ARTIFACT_DIR)
    (config.ARTIFACT_DIR / "validation_summary.json").write_text(json.dumps(report, indent=2, default=float))
    if verbose:
        print(f"\nSaved model + validation summary to {config.ARTIFACT_DIR}")
    return fitted


def _report(scored: pd.DataFrame, fitted: model.TrainedModel, verbose: bool) -> dict:
    """Score raw output, then output after the online calibration layer."""
    calibrated = _replay_calibration(scored)
    baselines = metrics.build_baselines(scored)
    table = metrics.evaluate(calibrated, prediction_col="forecast_cal", baselines=baselines)

    raw = metrics.point_metrics(scored["power"], scored["forecast"])
    cal = metrics.point_metrics(calibrated["power"], calibrated["forecast_cal"])
    band_raw = metrics.interval_coverage(scored["power"], scored["p10"], scored["p90"])
    band_cal = metrics.interval_coverage(calibrated["power"], calibrated["p10_cal"], calibrated["p90_cal"])

    by_lead = {
        int(lead): metrics.point_metrics(g["power"], g["forecast_cal"])
        for lead, g in calibrated.groupby("lead_day")
    }

    if verbose:
        print(f"\n===== POOLED MODEL =====")
        print(f"train rows {fitted.trained_rows:,} | features {len(fitted.feature_columns)} | best_iteration {fitted.best_iteration}")
        print(f"\nHold-out: issue dates >= {VALID_ISSUE_START} (lead 24-71 h)\n")
        print(table.to_string(float_format=lambda v: f"{v:8.4f}"))
        print(f"\nraw model        MAE {raw['mae']:.4f}  bias {raw['bias']:+.4f}  coverage {band_raw['coverage']:.3f}")
        print(f"after calibration MAE {cal['mae']:.4f}  bias {cal['bias']:+.4f}  coverage {band_cal['coverage']:.3f}")
        print("\nBy forecast horizon:")
        for lead, m in sorted(by_lead.items()):
            label = "24-47 h" if lead == 1 else "48-71 h"
            print(f"  day+{lead} ({label}): MAE {m['mae']:.4f}  RMSE {m['rmse']:.4f}  R2 {m['r2']:.3f}  n={m['n']}")
        print("\nTop features by gain:")
        print(model.feature_importance(fitted, 15).to_string(index=False))

    return {
        "validation_start": VALID_ISSUE_START,
        "raw": raw, "calibrated": cal,
        "coverage_raw": band_raw, "coverage_calibrated": band_cal,
        "by_lead_day": {str(k): v for k, v in by_lead.items()},
        "comparison_table": table.to_dict(),
        "best_iteration": fitted.best_iteration,
        "trained_rows": fitted.trained_rows,
    }


def _replay_calibration(scored: pd.DataFrame) -> pd.DataFrame:
    """Walk the hold-out forward, calibrating only on already-verified hours."""
    calibrator = calibration.ForecastCalibrator()
    out = scored.sort_values(["turbine_id", "issue_time", "time"]).copy()
    for column in ("forecast", "p10", "p50", "p90"):
        out[f"{column}_cal"] = out[column]

    for _, group in out.groupby("turbine_id"):
        log = group[["time", "forecast", "p10", "p50", "p90", "power"]]
        for issue, block in group.groupby("issue_time"):
            state = calibrator.fit(log, as_of=issue)
            adjusted = calibration.ForecastCalibrator.apply(
                block[["forecast", "p10", "p50", "p90"]], state
            )
            for column in ("forecast", "p10", "p50", "p90"):
                out.loc[block.index, f"{column}_cal"] = adjusted[column]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the WindAgent forecast model")
    parser.add_argument("--no-cache", action="store_true", help="rebuild the replayed dataset")
    args = parser.parse_args()
    train(use_cache=not args.no_cache)


if __name__ == "__main__":
    main()
