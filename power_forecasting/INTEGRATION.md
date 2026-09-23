# Compact power forecasting experiment

This directory is an isolated addition to the existing WindAgent repository. It does not replace the repository-root source, README, models or submission.

## What is included

- Standalone weather-dataset and ML code, configurations, dependency versions and tests.
- Compact feature selection, chronological model tournament, evaluation reports and model-routing metadata.
- Final February forecast in predictions/final_forecast.csv and .parquet (2,688 rows, both D1 and D2).
- Winning configuration: global LightGBM, 15 features, MAE 0.150544 on four model-selection months; error ratio 0.500381 against this experiment's historical-median baseline.

Raw SCADA files, weather response cache, prepared datasets, per-experiment OOF predictions, local dependencies and trained model binaries are not included in this addition. The repository's pre-existing dataset is left unchanged. Model registry and reports describe the completed local run; the registry is not a substitute for the excluded model binaries.

## Important differences from the repository-root solution

This experiment uses an inferred fixed UTC+5 SCADA offset, whereas the existing root solution documents UTC+6. Its forecast schedule uses lead_hours 1–48 with D1=1–24 and D2=25–48, while the root solution documents different lead ranges and a different evaluation protocol. This experiment's 2,688-row forecast is NOT a drop-in replacement for the root solution's 1,344-row submission.

Consequently, MAE values across the two solutions are NOT directly comparable. Reconcile timezone, timestamps, horizons, observation availability, filtering and scoring rows before combining models or choosing a submission. No timezone or root-pipeline changes were made by this addition.

Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value. The fixed-lead-time interpretation is documented in README.md and reports/final_ml_report.md. The inferred timezone was established upstream and is not an independently validated part of the four-month ML evaluation.

## Running this isolated project

Run commands from this directory, NOT the repository root (both projects have a src package):

```sh
cd power_forecasting
python -m pip install -r requirements-ml.txt
python train.py
python predict.py
python -m src.run_tests
```

Before training, supply the existing prepared artifacts locally, preserving their relative paths:

- data/final/training_dataset.parquet
- data/final/competition_features.parquet
- data/final/training_weather_dataset.parquet
- data/processed/scada_hourly.parquet

feature_columns.json and run_config.json are included as small schema/provenance metadata. For the complete original weather/SCADA test suite, also provide the two raw source CSV files under the filenames in config.yaml at this directory's root. The upstream repository already tracks CSVs in dataset/; use only confirmed matching originals. Do not mix different timezone-derived Parquet datasets.

train.py does not download weather: it audits the prepared files, runs/resumes the tournament, refits final models and produces predictions. predict.py requires models produced by train.py (or the exact matching original local model files). Standalone weather preparation commands are documented separately in README.md and require the raw inputs/cache or explicit network access.

After a fresh clone, artifact-dependent tests require the prepared inputs and a completed local ML run. Historical test results in reports/tests_report.json record the original run, not a claim that an artifact-free clone can immediately run every integration test.

The first February issues predate the last January observations. The trainer saves earlier as-of checkpoints alongside the all-history model; inference checks that each model's last training label was available before its forecast issue.

## Review starting points

- reports/final_ml_report.md — outcomes, validation and limitations.
- reports/model_leaderboard.csv — all 53 configurations.
- reports/feature_count_experiment.csv — compact vs full feature sets.
- reports/ablation_study.md — controlled provider and architecture comparisons.
- reports/ml_reproducibility.md — exact reproduction checks and exclusions.
- models/final_features.json — the actual 15 predictors.

February targets are unavailable. Reported scores are chronological model-selection validation, not independent February test results.
