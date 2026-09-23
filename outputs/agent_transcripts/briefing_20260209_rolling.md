Forecast published for issue 2026-02-09 (files: outputs/cycles/forecast_20260209_rolling.csv and outputs/cycles/analysis_20260209_rolling.json).

What the models are saying
- Next 48 h mean wind at hub ~8.43 m/s, min 3.01, max 15.57 m/s.
- Per-model mean wind: ECMWF 8.03, GFS 8.88, ICON 8.39 m/s.
- Ensemble spread is notable: mean spread 2.69 m/s, max spread 7.53 m/s — models disagree at times, so uncertainty is elevated.

Input changes since yesterday
- check_input_updates: day-ahead forecast was revised with today's NWP runs for both turbines. Overlapping 24h hours show mean absolute change 0.0912 (fraction of rated power), mean signed change +0.0131 (t1) / +0.013 (t2) — net slight increase on average, with max absolute change up to 0.2181. Action: day-ahead numbers updated to reflect today's runs.

Recent forecast performance
- t1 (last 14 days): MAE 0.165, RMSE 0.2138, bias +0.0297 (over-forecasting), P10–P90 coverage 0.862.
- t2 (last 14 days): MAE 0.1671, RMSE 0.2204, bias +0.0132 (over-forecasting), P10–P90 coverage 0.79.
- Calibration applied: small positive bias correction and widened uncertainty bands (band scales ~1.13–1.19).

Forecast highlights (from model run)
- Turbine t1: energy_48h_eflh = 21.83 ; energy_day_ahead_24h_eflh = 6.88. Mean capacity factor 0.455. Peak hour local 2026-02-11 21:00; trough 2026-02-10 17:00. One near-rated hour. Confidence flagged low.
- Turbine t2: energy_48h_eflh = 22.53 ; energy_day_ahead_24h_eflh = 7.23. Mean capacity factor 0.469. Peak hour local 2026-02-11 21:00; trough 2026-02-10 17:00. Three near-rated hours. Confidence flagged low.
- Both turbines: mean ensemble spread 2.69 m/s in forecast; a significant ramp event at 2026-02-11 06:00 local with delta -0.289 (fraction of rated power).

Operator briefing (for reserve decisions — ~150 words)
Expected energy per turbine over next 48 h: t1 = 21.83 eflh (day-ahead 24h = 6.88 eflh); t2 = 22.53 eflh (day-ahead 24h = 7.23 eflh). Shape: lower output through 2026-02-10 late afternoon (trough at 17:00 local), recovery to a peak around 2026-02-11 21:00. Key ramp: sharp drop around 2026-02-11 06:00 (~-0.289 p.u.) — staff for this potential downward ramp and ensure enough upward reserve if needed. Confidence: low — ensemble spread is elevated and recent model bias shows a small tendency to over-forecast; day-ahead was revised modestly upward with today's runs but uncertainty bands have been widened. Recommendation: hold moderate upward reserve through the night into 2026-02-11 and be ready for a short, substantial down-ramp around 06:00 local on 2026-02-11.
