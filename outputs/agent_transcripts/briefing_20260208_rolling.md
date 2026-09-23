T1:
- Weather summary (48 h): mean wind at 100 m 10.7 m/s, max 18.4 m/s, min 4.7 m/s. Model means: ECMWF 10.12, GFS 11.43, ICON 10.52 m/s. Ensemble spread moderate: mean spread 2.51 m/s, max spread 6.37 m/s — some model disagreement at times.
- Recent performance (14 d): MAE 0.1626, RMSE 0.2115, bias +0.0253 (over-forecasting). P10–P90 coverage 0.861.
- Input updates: today's NWP runs changed the day-ahead hours vs yesterday. Overlapping 24 h mean absolute change 0.0297 (fraction of rated); mean signed change -0.0287 (net down), max abs change 0.1844. Day-ahead revised with current NWP.
- Forecast run: 48-h energy 24.09 eflh; day-ahead 24-h energy 17.52 eflh. Mean capacity factor 0.502. Max output 0.897, min 0.161. Peak hour local 2026-02-09 00:00:00; trough 2026-02-10 00:00:00. Hours near rated: 0. Confidence: low. Calibration: recent 14d over-forecast ~0.0337 of rated; uncertainty band scaled x1.23.

T2:
- Weather summary (48 h): same as T1 (site close): mean wind 10.7 m/s, max 18.4 m/s, min 4.7 m/s. Per-model means as above. Ensemble spread mean 2.51 m/s, max 6.37 m/s.
- Recent performance (14 d): MAE 0.1645, RMSE 0.2171, bias +0.0121 (over-forecasting). P10–P90 coverage 0.799.
- Input updates: today's NWP runs changed the day-ahead hours vs yesterday. Overlapping 24 h mean abs change 0.0277; mean signed change -0.0263 (net down); max abs change 0.1819. Day-ahead revised with current NWP.
- Forecast run: 48-h energy 24.79 eflh; day-ahead 24-h energy 17.88 eflh. Mean capacity factor 0.517. Max output 0.912, min 0.176. Peak hour local 2026-02-09 00:00:00; trough 2026-02-10 00:00:00. Hours near rated: 5. Confidence: low. Calibration: recent 14d over-forecast ~0.0190 of rated; uncertainty band scaled x1.26.

Publishing:
- Forecast files written: outputs/cycles/forecast_20260208_rolling.csv and outputs/cycles/analysis_20260208_rolling.json (96 rows).

Operator briefing (under 250 words)
- Expected energy per turbine: T1 energy_48h_eflh = 24.09, day-ahead energy_day_ahead_24h_eflh = 17.52. T2 energy_48h_eflh = 24.79, day-ahead energy_day_ahead_24h_eflh = 17.88.
- Shape of the day: winds pick up into late evening (peak at local 00:00 on 2026-02-09) producing highest outputs around that hour. A decline follows toward the second day's trough (local 00:00 on 2026-02-10).
- Ramps/risks: no large sustained step ramps flagged by the model, but ensemble spread peaks at times (max spread 6.37 m/s) indicating periods of model disagreement — expect possible shorter-term swings. Today's NWP update lowered the day-ahead forecast on average (mean signed change ~ -0.03 fraction of rated), with some hours revised down by as much as ~0.18 of rated power; watch the evening hours where changes were largest.
- Confidence and reserve guidance: overall confidence low due to moderate ensemble spread and the model's recent tendency to over-forecast. Bias correction applied, and uncertainty bands widened. Hold extra upward reserve relative to a typical clear forecast (recommend modest upward reserve margin through the evening peak and into the overnight decline to cover the possibility of under-output).
