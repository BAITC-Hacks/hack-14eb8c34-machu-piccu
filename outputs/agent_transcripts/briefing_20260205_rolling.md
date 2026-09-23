Forecast published for issue 2026-02-05 (files: outputs/cycles/forecast_20260205_rolling.csv, outputs/cycles/analysis_20260205_rolling.json).

Weather overview (both turbines)
- Model means: per-model mean wind speeds around 8.4–8.8 m/s (ecmwf_ifs025 8.39, gfs_seamless 8.78, icon_seamless 8.52). 
- Mean wind 100 m ≈ 8.57 m/s, max ≈ 16.99 m/s, min ≈ 2.24 m/s.
- Ensemble spread moderate (mean spread 1.8 m/s, max spread 4.76 m/s) — use the P10–P90 band where needed; uncertainty is material.

Input updates (day‑ahead change)
- t1: day‑ahead revised with today's NWP runs. Overlapping 24h: mean_abs_change 0.0481 (fraction of rated), mean_signed_change -0.0155 (small net downward), max_abs_change 0.1467. Action: day‑ahead forecast revised with today's NWP runs.
- t2: day‑ahead revised with today's NWP runs. Overlapping 24h: mean_abs_change 0.0481, mean_signed_change -0.0152 (small net downward), max_abs_change 0.1464. Action: day‑ahead forecast revised with today's NWP runs.

Recent forecast performance
- t1 (last 14 days): MAE 0.1637, RMSE 0.2103, bias +0.0169 (model slightly over‑forecasting), P10–P90 coverage 0.803.
- t2 (last 14 days): MAE 0.1701, RMSE 0.2211, bias +0.0164 (slight over‑forecast), P10–P90 coverage 0.756.
Calibration applied: band scaled up (t1 x1.11, t2 x1.17) and small bias correction applied.

Forecast summary (from model output)
- t1: mean capacity factor 0.455; max output 0.919; min 0.063; hours near rated 8; peak hour local 2026-02-06 20:00:00; trough 2026-02-07 08:00:00; confidence: low.
- t2: mean capacity factor 0.454; max output 0.918; min 0.062; hours near rated 8; peak hour local 2026-02-06 20:00:00; trough 2026-02-07 08:00:00; confidence: low.
- No automated large ramp events flagged in the analysis.

Operator briefing (under 250 words)
- Expected energy per turbine: t1 energy_48h_eflh = 21.82, energy_day_ahead_24h_eflh = 14.01. t2 energy_48h_eflh = 21.8, energy_day_ahead_24h_eflh = 14.0.
- Shape: winds moderate with a broad peak into the evening of 2026-02-06 (peak hour 20:00 local) and a low in the early morning of 2026-02-07 (08:00 local). Each turbine has ~8 hours near rated output across the 48h.
- Ramps/staffing: no model‑flagged rapid ramps, but day‑ahead was revised today (mean_abs_change ~0.048) with some hours changing up to ~0.147 of rated power — watch the transition into the evening peak (around 20:00 on 2026-02-06) where uncertainty is higher.
- Confidence & reason: low confidence. Ensemble spread is moderate (mean 1.8 m/s, max 4.76 m/s) and recent verification shows a small persistent over‑forecast bias (~+0.016). Bands have been widened by calibration (t1 x1.11, t2 x1.17). Hold modest upward reserve around the evening peak and overnight trough to cover model spread and the small downward revision seen in today's NWP update.
