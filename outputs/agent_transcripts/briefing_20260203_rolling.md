T1 — recent weather and model summary:
- Model means at 100 m: ECMWF 9.98 m/s, GFS 10.17 m/s, ICON 11.66 m/s. 
- 48 h mean wind 10.61 m/s (max 17.06, min 3.57). Ensemble spread mean 2.05 m/s, max 4.77 m/s — ensemble spread moderate; expect uncertainty where runs diverge near peak winds.

T2 — recent weather and model summary:
- Same NWP fields as T1 (site pair). Mean wind 10.61 m/s; per-model means as above. Ensemble spread same.

Recent forecast performance (last 14 days):
- T1: MAE 0.1596, RMSE 0.2098, small positive bias 0.01 (over-forecasting). P10–P90 coverage 0.812.
- T2: MAE 0.1638, RMSE 0.2188, small positive bias 0.009 (over-forecasting). P10–P90 coverage 0.777.
Calibration note: model bias small but consistent; bands scaled (T1 x1.04, T2 x1.14) to reflect uncertainty.

Input updates since prior run:
- T1: check_input_updates returned no error earlier but overall run indicates rolling policy; newest runs moved day-ahead marginally (calibration applied). Net effect: slight downward shift via bias correction (over-forecast) and band modestly widened for T2.
- T2: same — day-ahead adjusted down slightly after bias correction; uncertainty band increased more for T2 (band scale 1.14).

Forecast file published:
- CSV and JSON written to disk: forecast_20260203_rolling.csv and analysis_20260203_rolling.json (96 rows).

Forecast highlights (48 h, both turbines):
- Mean capacity factor: T1 0.637, T2 0.639.
- Day-ahead energy (first 24 h) equivalent full-load hours: T1 9.59, T2 9.62.
- 48-h energy equivalent full-load hours: T1 30.59, T2 30.66.
- Peak output around local 2026-02-05 14:00 (T1 max 0.928, T2 max 0.93).
- Trough around local 2026-02-04 16:00 (T1 min 0.122, T2 min 0.124).
- Hours near rated: 16 hours each; no hours below cut-in.
- Confidence: low (ensemble spread and recent model disagreement).

Operator briefing (for dispatcher, <250 words):
Expected energy: day‑ahead energy ~9.6 full-load hours (per turbine). Over the full 48‑hour window expect ~30.6 full-load hours per turbine.

Shape of the day: winds moderate to strong overall with a broad high‑wind period centered on local afternoon of 2026‑02‑05 (~14:00) producing the forecast peak (~0.93 of rated). A lower period occurs around local 16:00 on 2026‑02‑04 (~0.12 of rated). Most other hours sit in the 0.4–0.9 range with ~16 hours near rated output.

Ramps and reserve needs: no sharp ramp events flagged by the model run. Because ensemble spread peaks where winds are strongest, be prepared for upward or downward deviations around the afternoon peak; consider holding moderate upward/downward reserve for the 12:00–18:00 local window on 2026‑02‑05.

Confidence and reasons: overall confidence low — ensemble spread is moderate (mean 2.05 m/s, max 4.77 m/s) and recent model runs show a small systematic over‑forecast (bias ~0.01), which we corrected. Uncertainty bands have been widened (especially T2). Use the published P10–P90 bands in the CSV for dispatch limits.
