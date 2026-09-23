T1/T2 hourly 48-hour forecast published for 2026-02-23 (files: outputs/cycles/forecast_20260223_rolling.csv, outputs/cycles/analysis_20260223_rolling.json).

Input summary and watchouts
- Weather: mean ensemble spread moderate (mean_ensemble_spread_ms = 1.55 m/s). Models agree overall but there is enough spread to reduce confidence — use P10–P90 where operational decisions are risk-averse.
- Recent model performance: no verified forecast history in the last 14 days for either turbine, so no bias correction could be applied. Treat the output as uncalibrated.
- Input updates: today's NWP runs materially revised the day-ahead (overlapping) hours for both turbines versus the 2026-02-22 run. Mean absolute change ~0.031 (3.14% of rated); mean signed change −0.0087 (small downwards), max hourly change 0.085. Action: day-ahead updated with current 24‑h lead runs.

Key numbers (from model output)
- t1 energy_48h_eflh = 22.46
- t1 energy_day_ahead_24h_eflh = 13.33
- t2 energy_48h_eflh = 22.46
- t2 energy_day_ahead_24h_eflh = 13.33

Forecast character (both turbines)
- Mean capacity factor ~0.468 (mean wind speed ~7.64 m/s).
- Peak output around local 2026-02-24 00:00 (max_output = 0.911).
- Trough around local 2026-02-25 00:00 (min_output = 0.05).
- A few hours (3) near-rated output; no cut-in issues expected.
- Confidence: low — ensemble spread, no recent verification/calibration, and day-ahead revisions were non-negligible.

Operator briefing (for dispatchers; under 250 words)
- Expected energy per turbine: 48‑hour = 22.46 eflh; day‑ahead 24‑hour = 13.33 eflh.
- Day shape: moderate winds through the next 24 hours with a peak near local 2026-02-24 00:00 (up to ~0.91 of rated). Winds then decline toward the second day with a low near local 2026-02-25 00:00 (~0.05 of rated).
- Ramps/staffing: no model-flagged sudden ramp events, but the day-ahead update shows some hourly changes (max single-hour change 0.085 of rated). Be prepared for a modest downwards adjustment into some hours overnight — hold moderate upward reserve through the peak-to-trough transition around 2026-02-24 00:00 to 2026-02-25 00:00.
- Confidence & reason: low confidence — ensemble spread is moderate and there is no recent verified bias correction available. Also today's NWP updates changed the day‑ahead forecast by ~3% on average with peaks up to 8.5%, so treat hourly point values as uncertain and rely on the broader P10–P90 band for reserve planning.

Files published: outputs/cycles/forecast_20260223_rolling.csv and outputs/cycles/analysis_20260223_rolling.json.
