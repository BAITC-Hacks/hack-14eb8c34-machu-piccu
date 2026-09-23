Forecast issued 2026-02-11 18:00 UTC for Shelek corridor (two turbines). Forecast files written to outputs/cycles/forecast_20260211_rolling.csv and outputs/cycles/analysis_20260211_rolling.json.

Summary (both turbines)
- Overall conditions: light-to-moderate winds for the next 48 h. Model mean wind speed at hub (~100 m) ~4.33 m/s, with per-model means 4.19 (ECMWF), 4.44 (GFS), 4.36 (ICON). Ensemble spread is substantial (mean spread 1.86 m/s, max spread ~4.34 m/s) — expect notable uncertainty in wind timing and magnitude.
- Day-ahead update: Today's NWP runs materially revised the day-ahead hours compared with yesterday (overlapping 24 h). Mean absolute change ~0.14 of rated power; mean signed change ~-0.066 — the day-ahead forecast was reduced on average. Max single-hour change up to ~0.34 of rated power.
- Calibration & recent performance: T1 shows a small persistent high bias (14-day bias ≈ +0.0168 to +0.022; verification window shows bias +0.022 and MAE 0.168). T2 bias is near zero in recent calibration but verification shows a small positive bias (+0.0047). Bands were scaled (t1 band ×1.017, t2 band ×1.102) to reflect uncertainty. P10–P90 coverage for T1 better than T2 (T1 ~0.84, T2 ~0.73).
- Confidence: low for both turbines because of ensemble spread and recent over-forecast tendency (especially T1). Use P10–P90 spread for reserve planning rather than the point forecast.

Turbine-specific highlights (from model run)
- T1:
  - energy_48h_eflh = 7.54
  - energy_day_ahead_24h_eflh = 5.37
  - mean capacity factor 0.157; peak hour local 2026-02-12 01:00; trough 2026-02-13 07:00
  - mean ensemble spread 1.86 m/s; mean wind ~4.33 m/s
  - confidence: low
  - calibration notes: recent 14d record shows the model running over-forecast by ~0.017 of rated power; band scaled ×1.02
- T2:
  - energy_48h_eflh = 8.33
  - energy_day_ahead_24h_eflh = 5.77
  - mean capacity factor 0.174; peak hour local 2026-02-12 01:00; trough 2026-02-13 07:00
  - mean ensemble spread 1.86 m/s; mean wind ~4.33 m/s
  - confidence: low
  - calibration notes: recent 14d record shows the model running over-forecast by ~0.000 of rated power; band scaled ×1.10

What changed with today's inputs
- For both turbines the day-ahead (next-24h) forecast was revised downward on average compared with yesterday's longer-lead run (mean_signed_change ≈ -0.066). Some hours moved substantially (up to ~0.34 of rated power). Action: day-ahead forecast replaced with today's NWP runs.

Operator briefing (for dispatchers; under 250 words)
- Expected energy per turbine:
  - T1: energy_48h_eflh = 7.54; energy_day_ahead_24h_eflh = 5.37
  - T2: energy_48h_eflh = 8.33; energy_day_ahead_24h_eflh = 5.77
- Shape of the day: low-to-moderate output overall, with the highest hour around local 01:00 on 2026-02-12 and the lowest around 07:00 on 2026-02-13. No sustained near-rated hours; minima remain above cut-in.
- Ramps and staffing: no model-identified rapid ramp events flagged in the analysis, but day-ahead inputs trimmed the forecast and individual hours changed up to ~0.34 of rated power. Expect potential hour-to-hour variability overnight around the peak/trough — keep a small amount of flexible reserve ready for a few-hour drop after the overnight peak.
- Confidence and reserve recommendation: confidence is low due to sizeable ensemble spread and a small persistent over-forecast bias (especially T1). Use the P10–P90 band for reserve sizing; I recommend holding moderate contingency reserve for the night-to-morning trough (cover roughly the downward edge of the P10 band relative to the point forecast).

Files published: outputs/cycles/forecast_20260211_rolling.csv and outputs/cycles/analysis_20260211_rolling.json.
