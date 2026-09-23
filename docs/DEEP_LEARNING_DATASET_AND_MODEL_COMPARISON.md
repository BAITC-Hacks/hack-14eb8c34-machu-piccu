# Sequence dataset and deep learning model comparison plan

## Answer

**Yes.** The two SCADA histories and archived weather are enough to design a supervised, issue-indexed sequence dataset for RNNs, LSTMs, GRUs, temporal CNNs and other multi-horizon models. The existing `artifacts/ds_t*.parquet` files are useful as a feature inventory and prototype input, but **should not be the final benchmark dataset** until the forecast issue-time problem in [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) is resolved. No new dataset or model has been built yet, and no deep learning score is claimed here.

The data scale is moderate: the current cached tables have 729 issue dates per turbine, of which 579 dates per turbine precede the 1 Oct 2025 hold-out. Forty-eight rows from the same issue are **one highly correlated forecast example**, not 48 independent samples. With only two turbines, simple neural models may generalize better than large attention models; this is a hypothesis to test, not a measured result. The available SCADA history starts in March 2023, while the current forecast-offset archive and replay tables start in March 2024.

## Define the prediction task before comparing models

Fix an explicit issue timestamp `I` in UTC, ideally a time when the chosen NWP runs were actually available. For each turbine and issue, predict a vector of 48 normalized hourly power values for the same target timestamps used by the project: **I+24 through I+71 hours** if the issue remains 00:00 UTC. This is the code's current horizon, although the brief describes a 24–48 hour horizon; the final competition interpretation should be confirmed separately. Choose either an issue-aligned 24–47-hour day-ahead score or the full 48-output score as the primary ranking metric, and publish both.

The central constraint is: **every input must have been available by `I`; only labels may come from after `I`.** Open-Meteo's `_previous_dayN` fields are fixed offsets from each *valid time*, not a full weather run issued at one time. In the current cache, late target hours may draw on forecasts created after 00:00 UTC on the nominal issue date. That is enough to make an otherwise careful RNN/LSTM comparison misleading. See [Open-Meteo's offset definition](https://open-meteo.com/en/docs/previous-runs-api) and [run-archive availability](https://open-meteo.com/en/docs/single-runs-api).

## Proposed dataset record

One record is `(turbine_id, issue_time_utc)`. Store an explicit input-availability timestamp and source/run identifier for every weather field; do not infer it from the target date.

| Tensor/table | Suggested shape per record | Contents and rules |
| --- | --- | --- |
| `past_observed` | `L × F_p`, start with `L=72` hours; test 24 and 168 | Hourly power, SCADA wind/temperature, anomaly/availability masks and observed/missing indicators, strictly before `I`. Keep real outages distinguishable from missing measurements. |
| `future_known` | `48 × F_f` | Forecast wind/temperature/pressure/humidity/direction/gust, forecast-member spread, lead and calendar features, all from runs available by `I`. Keep member values and missing-member masks; do not insert realized future weather. |
| `static` | `F_s` | Turbine ID, and coordinates/capacity if meaningful and known. With only two turbines, avoid high-dimensional embeddings. |
| `target` | `48` | Measured hourly normalized power at the exact target timestamps. Preserve missing-target and anomaly masks. |
| `metadata` | one row | Issue time, target timestamps, source model IDs, run initialization and publication/ingest times, local-clock convention, dataset version, split ID. |

Output quantiles can be `48 × 3` for P10/P50/P90 in addition to a point vector. Use the same clipping, power-curve baseline, and optional post-model calibration for every architecture; report raw and calibrated results separately. If converting to MWh, obtain each turbine's rated capacity first; the repository provides normalized power only.

### How to build it, in order

1. **Audit weather availability.** Check exact run initialization and public availability for every provider and target hour. Use an issue-stamped archive or stored historical forecasts. Open-Meteo's Single Runs API has ECMWF history in this period but not equivalent historical coverage for the other listed models, so a three-model reconstruction may need a different archive. If only ECMWF can be established as causal, benchmark all architectures on the same ECMWF-only dataset, with three-model results deferred until the archive is solved. [Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api)
2. **Construct one complete issue example at a time.** Resample SCADA exactly as in `src/scada.py`, align its assumed UTC+6 local clock with weather UTC, and attach historical observations only for timestamps `< I`. Forecast channels come from the same known-by-issue source for all 48 target hours. Keep explicit masks for missing hours and unavailable NWP members.
3. **Separate operational regimes.** Decide whether the target is delivered power (including curtailment/outages) or wind-available power. The current LightGBM fits after excluding anomaly hours but evaluates on all observed hours. Preserve both a full-delivered-power score and a clean-hours score; use the same training mask across models.
4. **Fit transforms only on training data.** This includes scaling, imputing statistics, empirical power curves and any learned weather-bias correction. Missing future wind must not be filled using realized weather or later-run forecasts.
5. **Freeze data and audit it.** Save a manifest with issue count, sample count, missingness, target coverage, exact train/validation/test windows and forecast provenance. Spot-check several boundary issue dates by hand against original weather run metadata.

## Models to compare

This is a representative comparison across relevant model families, rather than every named time-series architecture. All models should receive the same information at issue time. For sequence models, prefer a **direct 48-output decoder** (or a decoder conditioned on the 48 known future weather rows) so predictions do not recursively feed unknown future SCADA back into themselves.

| Model | How it would use this dataset | Why include it | Main limitation here | Priority |
| --- | --- | --- | --- | --- |
| Persistence and fitted power curve | Repeat recent power; map forecast wind through training-only curve | Required no-learning references | Limited response to weather error/availability | Essential |
| Current pooled LightGBM | One row per target hour with engineered weather/state features | Strong existing non-neural reference; quantify any gain over current system | Feature design and current replay need issue-time repair | Essential |
| Linear / DLinear | Flatten past sequence; add an exogenous-weather branch if needed | Cheap, hard-to-beat low-capacity sequence baseline [DLinear paper](https://arxiv.org/abs/2205.13504) | Original DLinear does not naturally fuse the full future NWP ensemble | High |
| Simple RNN | Encode past hourly state, decode future with NWP inputs | Direct test of the requested recurrent family | Harder to retain long history; mostly a diagnostic baseline | Medium |
| GRU encoder–decoder | Encode past; condition 48 outputs on future NWP | Gated recurrence with fewer parameters than typical LSTM [GRU paper](https://aclanthology.org/D14-1179/) | Still sequential to train; may not beat tabular model on small data | High |
| LSTM encoder–decoder | Same input/output contract as GRU | Established longer-memory recurrent comparison [LSTM paper](https://direct.mit.edu/neco/article/9/8/1735/6109/Long-Short-Term-Memory) | More parameters and tuning than GRU | High |
| TCN / dilated 1-D CNN | Convolve over past and forecast-weather sequences, then output 48 hours | Local ramps and multiscale weather patterns; parallel training [TCN paper](https://arxiv.org/abs/1803.01271) | Must design receptive field to cover the history window | High |
| TiDE / weather-aware MLP | Encode past and future covariates into direct horizon outputs | Natural exogenous-covariate challenger with modest compute [TiDE paper](https://research.google/pubs/long-horizon-forecasting-with-tide-time-series-dense-encoder/) | Can overfit with many correlated weather channels | High |
| N-BEATSx | Backcast/forecast blocks plus exogenous weather | Interpretable-style decomposition with covariates [N-BEATSx paper](https://arxiv.org/abs/2104.05522) | More architecture work than a plain MLP | Medium |
| TFT | Past observed, known future weather and static turbine input; direct quantiles | Explicit multi-horizon covariate handling [TFT paper](https://arxiv.org/abs/1912.09363) | Large tuning cost and overfit risk for two turbines | Later |
| PatchTST or another patch Transformer | Patch temporal history, with an explicit future-weather fusion path | Tests longer context/attention [PatchTST paper](https://openreview.net/pdf?id=Jbdc0vTOcol) | Original channel-independent setup is not automatically suitable for forecast covariates | Later |

DeepAR-style autoregressive probabilistic models and unmodified N-BEATS are optional follow-ups. They need extra design to use the future NWP sequence fairly; otherwise their comparison with weather-aware models would answer a different question. Transformer scale is not itself evidence of accuracy: the [DLinear study](https://arxiv.org/abs/2205.13504) shows why simple baselines belong in the same benchmark.

## Fair evaluation protocol

| Decision | Proposed rule |
| --- | --- |
| Split | Chronological by issue **and target timestamp**. Use multiple rolling-origin folds before February; purge/embargo any issue whose 48-hour targets overlap the next fold. Keep Feb 2026 as a final untouched test only if its measured labels become available. The provided CSVs stop 31 Jan 2026, so February accuracy cannot currently be measured. |
| Primary metrics | Day-ahead MAE and RMSE in normalized-power units, scored on exactly the same turbine/target-hour rows. Also report full-window and per-turbine metrics, bias and ramp errors. |
| Probabilistic metrics | P10/P50/P90 pinball loss, P10–P90 coverage and mean width; nominal coverage is 80%. Compare calibration using only earlier verified data. |
| Training budget | Same data, direct-horizon target and selected feature channels; a defined tuning budget and several random seeds for neural models. Report parameters, training/inference time and variance across seeds. |
| Baseline integrity | Refit LightGBM on the same corrected issue-indexed dataset and folds. Build persistence/curve/climatology from training or issue-available history only, and score all methods on identical valid rows. |
| Decision criterion | Promote a deep model only if its reduction in held-out MAE or pinball loss is repeatable across folds/turbines and worth its runtime and maintenance cost. Keep the LightGBM and physical baselines in the final report. |

An initial experiment set of **LightGBM, DLinear, GRU, LSTM, TCN and TiDE** covers tabular, linear, recurrent, convolutional and MLP approaches. Add TFT/PatchTST only after the data-provenance audit and first benchmark show room for a more complex model. A hybrid can also be tested: sequence model predicts a residual around the empirical power curve or blends with LightGBM, using blend weights fitted only on past validation folds.

## Current blockers and deliverables for the next phase

The main blocker is a **causal historical weather archive** covering the issue dates. The second is the absence of February 2026 power labels. Neither is solved by changing the model architecture. The next implementation phase should produce (1) a versioned, issue-indexed sequence dataset with weather provenance and masks, (2) a leakage audit and chronological fold manifest, and (3) a comparison table with measured scores and runtime for each model. This document is the design for those deliverables, not a claim that any deep learning model outperforms the current one.
