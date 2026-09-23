# ML reproducibility check

Run: `644e19e22a6c2779`, 2026-09-23. Seed: 20260923; CPU threads: 4.

Executed 53 configurations on the same four chronological folds (212 outer-fold evaluations). Experiment results, predictions, parameters and train-only stopping metadata are preserved under experiments/644e19e22a6c2779.

Checks completed:

- `python train.py`: initial tournament, final refits, registry and competition predictions completed.
- `python predict.py`: independent reload of saved models reproduced the forecast.
- `python train.py` repeated: compatible tournament results were resumed from cache; all four final LightGBM checkpoints were trained again. The forecast was reproduced exactly. This is not a claim that every tournament model was independently retrained twice.
- `python -m src.run_tests`: 42 tests passed, zero failures/errors/skips. Includes a separate same-seed repeat fit, chronological/availability purge, feature encoding, future-observation mutation, identical OOF keys, final model registry and forecast checks.
- Every original input Parquet checked by the ML run retained its SHA-256. No weather requests or raw dataset edits were made.

Final prediction Parquet SHA-256, identical across all three inference executions:

`1f7c13271ad82584fadad542bda4f6150c17812c811a8ccfc54698b2dd7bbe05`

Final main model uses all 64,503 permitted historical rows and 15 features, with 143 trees. Three earlier as-of checkpoints protect forecasts issued before the last historical labels became available. Model bundles include elapsed training times, so their binary hashes need not match across refits even when predictions match exactly.

Versions: requirements-ml.txt and models/environment.json. Input/code fingerprints: experiments/644e19e22a6c2779/run_manifest.json. Actual prediction coverage and checkpoint availability checks: reports/prediction_validation.json.

Metrics are model-selection walk-forward results, not independent February test scores. The upstream inferred timezone and fixed historical lead-time archive limitations remain documented in final_ml_report.md.
