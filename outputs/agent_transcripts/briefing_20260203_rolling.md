T1 and T2 48-hour forecast published for issue 2026-02-03 (files saved; 96 hourly rows).

Weather summary (48 h)
- Mean wind ~10.6 m/s at 100 m, range ~3.6–17.1 m/s.
- Models disagree moderately: ICON higher (~11.7 m/s) vs ECMWF (~10.0) and GFS (~10.2). Ensemble spread mean 2.05 m/s, max 4.77 m/s — expect uncertainty in short-term peaks.

Recent forecast performance
- T1: 14-day verification shows small systematic over-forecast (bias +0.0168 of rated power); MAE 0.160.
- T2: similar over-forecast (bias +0.0177); MAE 0.165.
- P10–P90 coverage under nominal (T1 0.773, T2 0.736) — bands are slightly widened in calibration.

Input update note
- For both turbines today's NWP runs materially changed the day‑ahead (overlap 24h). Mean absolute change ~0.112 of rated; mean signed change +0.084 (i.e., updated winds/higher outputs vs yesterday). Max single-hour change ~0.28. Action: day‑ahead revised with current runs.

Forecast highlights (from model outputs)
- Energy: T1 energy_48h_eflh = 30.17; energy_day_ahead_24h_eflh = 9.37.
- Energy: T2 energy_48h_eflh = 30.13; energy_day_ahead_24h_eflh = 9.35.
- Mean capacity factor ~0.628 for both; peak hour local at 2026-02-05 14:00; trough at 2026-02-04 16:00.
- Max hourly outputs ~0.92 of rated, minima ~0.11. Hours near rated ~14.
- Confidence: low (ensemble spread and recent over-forecast bias). Bands have been scaled (t1 x1.057, t2 x1.112) to reflect uncertainty.

Operational implications / dispatch briefing (under 250 words)
- Expected energy per turbine: T1 48-h = 30.17 eflh (day‑ahead 24-h = 9.37 eflh); T2 48-h = 30.13 eflh (day‑ahead 24-h = 9.35 eflh).
- Shape: moderate-to-strong winds through the two days with a lull producing the lowest output around 16:00 local on 2026-02-04, and the highest output around 14:00 local on 2026-02-05. Expect most high-output hours clustered into about 14 hours near rated across the window.
- Ramps/staffing: No model-flagged rapid ramp events, but the input update produced fairly large hour-to-hour revision compared with yesterday (mean change ~0.11, max ~0.28). Be ready for possible upward adjustments into the day‑ahead window where ICON-driven higher winds could materialize. Reserve: hold moderate upward reserve for late Day‑1 to Day‑2 peak (around local 14:00 on 5 Feb), and some downward flexibility around the trough on 4 Feb 16:00.
- Confidence summary: Low confidence due to inter-model spread (ICON notably higher) and a persistent slight over-forecast bias in the last 14 days. Use P10–P90 bands for reserve sizing rather than the point forecast.

Files written: outputs/cycles/forecast_20260203_rolling.csv and outputs/cycles/analysis_20260203_rolling.json.
