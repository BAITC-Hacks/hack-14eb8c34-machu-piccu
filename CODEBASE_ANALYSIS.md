# Codebase analysis: wind power forecasting pipeline

This document describes the repository as inspected on 23 September 2026. It reports what the code does and what the saved artifacts show; it does not treat the existing backtest as proof of issue-time-correct performance.

## Purpose and entry points

The project forecasts **hourly normalized active power** (0–1) for two nearby wind turbines in Kazakhstan. The task calls for a daily 24–48 hour forecast for February 2026 using weather forecasts available when each forecast was issued. The code actually constructs **48 hourly targets at nominal leads 24–71 hours** from each 00:00 UTC issue date: the whole of day D+1 and day D+2. Consecutive daily runs overlap on the second day, and the submission uses the newer, day-ahead prediction for each target hour.

| Entry point | Role |
| --- | --- |
| `python -m src.train` | Build/load supervised tables, fit the pooled LightGBM model and quantiles, write model and validation report. |
| `python -m src.agent --date YYYY-MM-DD [--mode archive\|live] [--reason]` | Run and publish one forecast cycle. Default agent policy is deterministic; `--reason` optionally uses Anthropic tools if credentials exist. |
| `python -m src.backtest --start ... --end ... --label ...` | Replay daily issue dates, attach any measured power, score, and write monthly files. Defaults to 31 Jan–27 Feb 2026. |

The root `README.md` now contains a quickstart, architecture narrative and reported results, and `requirements.txt` pins dependencies. Module docstrings give additional command examples. No test suite is visible. Most source/data/artifact files are untracked in Git at the time of inspection; the only tracked file is `README.md`. The README calls the weather blocks single-run, issue-correct forecasts, which conflicts with the API semantics explained below.

## Data and stored artifacts

| Item | What is present |
| --- | --- |
| `dataset/*turbine 1.csv`, `*turbine 2.csv` | 142,360 and 149,499 ten-minute SCADA rows respectively, from 11 Mar 2023 through 31 Jan 2026 local logger time. Columns are timestamp, measured wind speed, normalized active power, temperature, plus ID. Both files stop at 31 Jan despite the broader date range in their filenames. |
| Open-Meteo archive | Eight hourly weather variables at both coordinates: wind speed at 10/100 m, direction at 10/100 m, gust at 10 m, temperature, surface pressure, humidity. Requested separately for ECMWF IFS 0.25°, GFS seamless, and ICON seamless, with `_previous_day1` or `_previous_day2` suffixes. |
| `cache/om_*.parquet` | Request-keyed weather cache; key is a hash of URL and parameters. It avoids repeated HTTP calls. |
| `artifacts/ds_t1.parquet`, `ds_t2.parquet` | Existing flat, replayed feature tables: 34,992 rows and 85 columns each, covering 729 issue dates from 1 Mar 2024 to 27 Feb 2026. These include the forecast-hour rows used for training and later unlabeled issue dates. |
| `artifacts/pooled_model.joblib`, `.json` | Active LightGBM artifact and metadata: 63 input features, 51,620 fitted rows, best point-model iteration 194. `t1_model.*` is present but the current train/inference path loads `pooled_model`. |
| `outputs/` | Single-cycle forecasts/analysis, verified replay, February replay, daily briefings and local-clock submission. |

`src/config.py` defines paths, turbine coordinates, the assumed clock offset, weather model list, and forecast window. Importing it also creates cache, artifact, output, and report directories.

## End-to-end flow

```text
Ten-minute SCADA CSVs ── flag anomalies ── hourly UTC measurements ──┐
                                                                  │ past state + labels
Archived/live Open-Meteo forecasts ── parquet cache ── ensemble ── 48-hour block
                                                                  │
                           physical + calendar + neighbor features + power-curve prior
                                                                  │
                           pooled LightGBM point + P10/P50/P90 models
                                                                  │
                           rolling bias / interval calibration
                                                                  │
                           analysis + agent policy ── CSV / JSON / submission
                                                                  │
                           later measured power ── verification log ── next calibration
```

### 1. SCADA preparation (`src/scada.py`, `src/dataset.py`)

`load_raw` reads one CSV, renames the four useful fields, parses/sorts timestamps, and discards the ID. `flag_anomalies` flags a possible curtailment/outage when SCADA wind is at least 6 m/s and power at most 0.02; it flags a stuck wind sensor when six consecutive ten-minute speeds have zero rolling standard deviation. These are heuristics, not independently verified operating states.

`to_hourly` computes hourly means and flag fractions. If an hour has fewer than four power samples, power, wind and temperature become missing. It marks an anomaly hour if more than half its samples are flagged. `scada_utc` subtracts a **fixed six hours** from the logger timestamp; this is an assumption documented in `config.py`, not derived by code in this repository. Past power is summarized over the three and 24 hours **strictly before** the issue time, plus a 24-hour healthy-observation share. Future SCADA wind and temperature are never inference inputs.

### 2. Weather acquisition (`src/weather.py`, `src/dataset.py`)

Archive mode calls `historical-forecast-api.open-meteo.com/v1/forecast`; live mode calls the current forecast API. Requests specify UTC (`timezone=GMT`) and one weather model. `fetch_archive_chunked` breaks long ranges into chunks and reads/writes parquet cache files. `_tidy` converts wind speeds/gusts from km/h to m/s and represents unavailable fields as missing values. `build_ensemble_frame` retains per-model weather columns, computes arithmetic means for scalar variables, circular means for directions, and standard deviation/min/max/range of 100 m wind speed across the three models.

For each nominal issue date D, `build_block` takes day D+1 from `_previous_day1` and day D+2 from `_previous_day2`, then assigns `issue_time=D 00:00 UTC` and `lead_hours=24..71`. The 48 rows are subsequently treated as one issued forecast block. **That issue-time interpretation is not supported by the API semantics; see the audit below.**

### 3. Features and labels (`src/features.py`, `src/dataset.py`)

The block receives air density and density-adjusted wind speed, wind shear, wind speed powers, wind-power density, gust ratios, sine/cosine direction encoding, directional veer, neighboring forecast-wind values, rolling wind statistics, local-hour and annual-cycle features, lead indicators, ensemble spread, individual NWP members, and the issue-time SCADA persistence state. Neighbor and rolling operations stay inside each 48-hour block. They may look forward **within forecast weather**, which is permissible only when the whole forecast block was actually available at issue time.

`build_dataset` joins the later hourly SCADA power as the target and measured SCADA wind as a label-side field. The measured wind is not among model input columns. A monotone empirical curve is fitted on **training rows** from density-adjusted *forecast* wind to observed power. Its hourly predictions, three-hour smoothing, per-NWP member predictions and spread become further features. Training masks exclude missing power, anomaly hours, and missing 100 m forecast wind; anomalous hours remain in reported evaluation where their targets exist.

### 4. Training (`src/train.py`, `src/model.py`)

The existing feature table is pooled across the two turbines with `turbine_id` (0/1). Nominal training issues run from 1 Mar 2024 through 30 Sep 2025; nominal hold-out issues run from 1 Oct 2025 through 30 Jan 2026. The curve is fitted only on the training split. `model.fit` trains one LightGBM L2 point regressor with early stopping on the hold-out and three independent LightGBM quantile regressors at P10/P50/P90, using the selected point-model iteration count. Prediction clips outputs to [0,1] and sorts the three quantiles to prevent crossings. It reports raw and rolling-calibrated validation results, then saves the same model selected on that validation period; it does **not** refit on all history before February.

The saved validation report says 51,620 fitted rows and 11,412 scored rows, with calibrated MAE **0.1658** and RMSE **0.2246** in normalized-power units. It lists persistence MAE 0.3360 and power-curve MAE 0.1860. These are **recorded results from the current data construction**, subject to the issue-time audit below. The reported baseline rows are not perfectly identical: persistence has fewer nonmissing predictions, and its climatology baseline is calculated using the validation period's own target mean, so the latter is not a strictly deployable comparator.

### 5. Inference, calibration, agent and export (`src/pipeline.py`, `src/agent.py`, `src/backtest.py`)

`ForecastPipeline` loads `pooled_model.joblib`. For each turbine it fetches weather, assembles the block, computes issue-time state/features and power-curve priors, predicts point and quantiles, then calibrates from its per-turbine verification log. `ForecastCalibrator` uses already verified hours before the issue: up to 14 days for capped mean-bias correction (minimum 48 samples) and 21 days for interval scale (minimum 200 samples). The point and band are clipped to [0,1]. A new single-cycle agent starts with an **empty** in-memory verification log; a sequential backtest fills it via `record` after each daily run. The log is not persisted between separate process invocations.

`analyse` computes equivalent full-load hours (sum of normalized hourly forecasts), capacity factor, peaks/troughs, one-hour ramps of at least 0.25 rated power, ensemble spread, band width, and a confidence label based on mean P10–P90 width. It does not compute MWh without turbine nameplate capacities. `WindAgent.run_cycle` triggers a second run on low confidence or ramps, and replaces a turbine forecast if mean absolute change exceeds 0.02. However, `detect_input_change` reuses `ForecastPipeline._weather_cache` for the same turbine/date, so this path normally compares the same weather and does **not actually refetch updates**. The optional `--reason` mode exposes inspect/run/performance/update/publish functions to Anthropic; numerical forecasts still come from the deterministic pipeline.

`backtest.py` loops issue dates, records forecasts, joins measured power where available, and writes all-lead and day-ahead CSVs, JSON reports and briefings. Its CLI defaults start on 31 Jan, while the README's 30 Jan start is necessary to cover local 1 Feb 00:00–05:00 with day-ahead forecasts. The saved local-clock submission has **1,344 rows = 672 hours × 2 turbines** for 1–28 Feb 2026; the associated report records 29 issue dates. That February report has only **36 verified rows**, all from known 31 Jan UTC hours reached by the 30 Jan issue; it cannot establish February forecast accuracy. The separately saved Oct–Jan verified replay reports day-ahead MAE **0.1615** on 5,730 rows, again subject to the audit below.

## Findings that affect interpretation

1. **The archive does not reproduce one 00:00 UTC issue per 48-hour block.** Open-Meteo defines `_previous_day1` as the value predicted **24 hours before each valid hour**, and `_previous_day2` as **48 hours before each valid hour**. For a target at D+1 23:00, the `_previous_day1` value corresponds to D 23:00, 23 hours after the code's stated D 00:00 issue. Likewise, D+2 23:00 with `_previous_day2` corresponds to D 23:00. The weather series can therefore contain information unavailable at the nominal issue time. Neighbor features can also combine those later forecasts within the block. The reported validation/backtest errors should be treated as **potentially optimistic**, and model comparisons should first use issue-stamped forecast runs or a conservative availability rule. [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api)
2. **Single-run archives have limited coverage for this period.** Open-Meteo describes its Single Runs API as preserving exact run identity, but currently lists ECMWF IFS from March 2024 and most other models only from April 2026. An issue-correct multi-model 2024–Feb 2026 dataset will need another archive/source, retained original forecast files, or a defensible reduced-feature design. A run's initialization time also precedes public availability, so availability time must be checked. [Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api)
3. **The validation boundary overlaps target times.** Splitting by issue date lets the last September training issues contain target hours in early October that also appear in October validation issues. A fair split must also keep target timestamps disjoint, or impose a gap between issue windows.
4. **Two reporting defects are visible.** In `backtest._score`, `lead_hours // 24` yields 1 or 2, but both groups are named `24-47h`, so the saved `by_lead_day` entry is overwritten by the 48–71-hour group. The separate `day_ahead_24_47h` field and `src/train.py` lead-day breakdown are unaffected. `recent_performance` filters `verification_log["time"]` correctly, but its initial log is empty for an isolated agent run.
5. **Reproducibility is incomplete.** `requirements.txt` pins dependencies and the README gives commands, but the repository has no visible test suite, data-source version record or issue-time weather availability ledger. Cached parquets, model artifacts and source files are present locally but untracked, so a fresh clone currently does not contain the pipeline. Any next model experiment should version its exact training dataset and forecast-source metadata before comparing scores.

These findings describe the current implementation; no code or model artifacts were changed for this analysis.
