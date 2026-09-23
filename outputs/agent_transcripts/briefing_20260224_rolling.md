Forecast published for issue 2026-02-24 and written to outputs/cycles/forecast_20260224_rolling.csv (hourly 48 h per turbine) and outputs/cycles/analysis_20260224_rolling.json.

Key points from model runs and NWP inspection
- Model outputs (run_forecast_cycle): both turbines identical outputs.
  - energy_48h_eflh = 18.9 (per turbine)
  - energy_day_ahead_24h_eflh = 3.12 (per turbine)
  - mean_capacity_factor = 0.394
  - peak hour local: 2026-02-26 04:00
  - trough hour local: 2026-02-25 00:00
  - max output 0.822, min 0.048
  - mean ensemble spread (wind) 1.79 m/s
  - confidence: low
  - calibration: no verified history yet — publishing uncorrected model output

- Weather models: mean 100 m wind ~6.62 m/s over 48 h; per-model means show some spread (ECMWF 6.78, GFS 6.98, ICON 6.10). Max ensemble spread up to 4.44 m/s; this indicates notable disagreement at some hours.

- Input updates: check_input_updates shows the day-ahead (first 24 h) changed materially from yesterday's run:
  - overlapping 24 h mean absolute change = 0.2502 (fraction of rated power), mean signed change = -0.2502 (the change is on average a downward revision), max abs change = 0.6653.
  - Action: day-ahead forecast revised with today's NWP runs. Both turbines affected the same way.

- Recent performance: no verified forecast history in the last 14 days for either turbine, so no bias correction possible and no scoring to validate the model.

Interpretation and guidance for control room (operator briefing; under 250 words)
- Expected energy per turbine: energy_48h_eflh = 18.9; energy_day_ahead_24h_eflh = 3.12.
- Shape of the day: moderate mean winds (~6.6 m/s) with a low overnight trough around 2026-02-25 00:00 and a peak around 2026-02-26 04:00. Hourly outputs range roughly 0.05–0.82 of rated power.
- Ramps/staffing: no automated ramp events flagged by the model, but the day-ahead update was a material downward revision (mean change ~-0.25 p.u., max ~-0.67 p.u.). Expect possible significant hour-to-hour departures compared with yesterday's plan; consider holding extra upward reserve for the first 24 hours in case actual winds come in closer to yesterday’s higher runs, and downward reserve for later hours if the downward revision verifies.
- Confidence: low. Reasons: sizable NWP model spread (max ensemble spread 4.44 m/s), identical uncalibrated model output with no recent verification data, and the day-ahead forecast was materially revised since yesterday. Use the P10–P90 spread (noted in ensemble spread) if you need a conservative reserve margin.

Files published: outputs/cycles/forecast_20260224_rolling.csv and outputs/cycles/analysis_20260224_rolling.json.
