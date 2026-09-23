Turbine forecasts published.

Inspection of inputs and recent performance
- Weather models (both turbines): next 48 h mean wind ~6.48 m/s (100 m), maximum ~10.5 m/s, minimum ~2.86 m/s. Per-model means: ECMWF 6.67, GFS 6.66, ICON 6.12 m/s. Ensemble spread moderate (mean spread 1.61 m/s, max spread 3.76 m/s) — models broadly consistent but some disagreement at peak hours.
- Input updates: For both turbines the day‑ahead (first 24 h) forecast was materially revised compared with yesterday’s run. Mean absolute change ~0.089 of rated power, mean signed change +0.073–+0.075 (today’s NWP runs increased the day‑ahead expected output), max hour change ~0.243–0.244.
- Recent performance (last 14 days): Both turbines running a small positive bias (over-forecast) — t1 bias 0.0296, t2 bias 0.0318. MAE ~0.17–0.17; P10–P90 coverage below nominal (t1 0.765, t2 0.729). Given this, I applied the calibration adjustments in the cycle (small downward bias correction and band scaling).

Forecast summary (issued 2026-02-02 18:00 UTC; published)
- Files: outputs/cycles/forecast_20260202_rolling.csv and outputs/cycles/analysis_20260202_rolling.json
- Both turbines: mean wind 6.48 m/s; ensemble spread moderate → overall forecast confidence low (see calibration).

Key numbers from model run (do not invent other values)
- Turbine t1: energy_48h_eflh = 13.94; energy_day_ahead_24h_eflh = 6.57; mean_capacity_factor = 0.29; max_output = 0.642; min_output = 0.042; confidence = low.
- Turbine t2: energy_48h_eflh = 13.89; energy_day_ahead_24h_eflh = 6.55; mean_capacity_factor = 0.289; max_output = 0.641; min_output = 0.041; confidence = low.

What changed in today's inputs
- Day‑ahead revised up relative to yesterday (mean_signed_change ~+0.073–+0.075), so expect somewhat higher output in the first 24 hours than yesterday’s plan. Changes were material (mean_abs_change ~0.089, max per-hour change ~0.244).

Operationally relevant shape and ramps
- Low diurnal baseline with a single broad peak late in the 48 h at local 2026-02-04 23:00 (both turbines peak hour reported); trough around local 2026-02-03 12:00.
- No model-detected discrete ramp events flagged by the system, but ensemble spread increases near the peak window (higher uncertainty around peak). Because the day‑ahead inputs were revised upward materially, expect potential hour-to-hour swings up to ~0.24 of rated power compared with yesterday’s schedule in the worst hour.
- No hours near rated power, no cut‑in issues flagged.

Operator briefing (under 250 words)
- Expected energy per turbine: t1 energy_48h_eflh = 13.94 (48 h), day‑ahead energy_day_ahead_24h_eflh = 6.57; t2 energy_48h_eflh = 13.89, day‑ahead energy_day_ahead_24h_eflh = 6.55.
- Shape: modest winds through the first day with a trough around local 2026-02-03 12:00, building to a broad peak late in the 48‑hour window (peak local 2026-02-04 23:00). Expect mean capacity factor ~0.29.
- Ramps/risks: no discrete ramps flagged, but today's NWP runs raised the day‑ahead output materially (mean per-hour signed increase ~0.073; worst-hour change up to ~0.24 of rated). Ensemble spread increases at the peak, so uncertainty is concentrated there.
- Confidence and reserves: overall confidence rated low due to moderate ensemble spread and the model’s recent small over-forecast bias (calibration applied). Hold modest upward reserve to cover the chance of the realized output exceeding the point forecast during the peak window, and keep some downward reserve around the trough midday tomorrow in case the over-forecast bias persists.

Forecast files have been written to disk for the control room.
