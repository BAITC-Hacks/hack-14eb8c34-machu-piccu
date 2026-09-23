Turbine forecasts published for issue 2026-02-18 (files: forecast_20260218_rolling.csv, analysis_20260218_rolling.json).

Key points from the model and inputs
- Both turbines (t1, t2) have identical model output for this run.
- 48-hour summary (model output only, uncalibrated):
  - Mean capacity factor: 0.349
  - Day-ahead energy (first 24 h) equivalent full-load hours: 9.33
  - 48-h energy equivalent full-load hours: 16.76
  - Peak hourly output: 0.725 (local 2026-02-19 01:00)
  - Trough hourly output: 0.08 (local 2026-02-20 15:00)
  - No hours near rated power; no hours below cut-in.
- Weather inputs (100 m):
  - Mean wind speed: 6.94 m/s (per-model means: ECMWF 7.02, GFS 7.33, ICON 6.45)
  - Mean ensemble spread: 2.19 m/s; max spread 5.82 m/s — ensemble disagreement is non-trivial.
- Model calibration and verification:
  - No verified forecast history available yet; calibration settings are default and outputs are uncorrected.
  - Recent performance: zero verified hours in the past 14 days — treat bias/skill as unknown.
- Input updates since yesterday:
  - Today's NWP runs revised the day-ahead hours materially (mean absolute change 0.077 fraction of rated power; mean signed change -0.047, max abs change 0.256). The day-ahead forecast was adjusted downward on average after ingesting the newer runs.

Uncertainty and operational advice
- Confidence: low. Ensemble spread and lack of verified forecaster history both reduce confidence.
- Use the P10–P90 band (wide; mean band width ~0.59 fraction) rather than a single point value for reserve decisions, especially through the overnight peak and the late-day trough.
- Because the most recent NWP runs moved the day-ahead forecast downward on average (mean signed change -0.048), expect slightly lower generation than yesterday’s published day-ahead, but with individual hours potentially up to ~0.25 fraction different.

Operator briefing (for dispatchers; <250 words)
Expected energy: Day‑ahead (next 24 h) ~9.33 full-load hours per turbine; 48‑h total ~16.76 FLH per turbine. Shape: Generation rises into a nighttime peak around local 01:00 on 2026-02-19 (peak hourly CF ~0.725), then trends down with the lowest output mid‑afternoon on 2026-02-20 (~0.08). There are no predicted hours at rated power and no cut-in gaps.

Ramps and staffing: No model-flagged sharp ramp events, but ensemble spread is sizable — some hours could be ~0.25 fraction different versus yesterday’s run. Hold moderate upward and downward reserve across the night-to-day transitions, especially around the peak (01:00) and the late‑afternoon trough on Day 2.

Confidence and reason: Low confidence due to substantial ensemble disagreement and no verified forecast history to calibrate against. Recent NWP updates have nudged the day‑ahead downwards on average; use the provided P10–P90 uncertainty band for scheduling reserves.

Files saved: forecast_20260218_rolling.csv and analysis_20260218_rolling.json.
