Turbine energy (48 h and day-ahead)
- T1: energy_48h_eflh = 35.25 ; energy_day_ahead_24h_eflh = 20.87
- T2: energy_48h_eflh = 35.22 ; energy_day_ahead_24h_eflh = 20.86

What changed with the newest runs
- check_input_updates: today's NWP runs did not materially change the day‑ahead forecast for either turbine (changed: false). Mean absolute change vs yesterday was ~0.015 fraction of rated power; today's runs essentially confirm yesterday's plan.

Summary of the forecast and shape of the day
- Both machines show the same overall pattern: a strong productive night into early morning with the peak hour around 2026-02-05 03:00 local, then a drawn‑out decline to the trough at 2026-02-06 07:00 local.
- Mean capacity factor across the 48 h is 0.734 and each turbine has ~24 hours near rated output. Mean wind speed at hub ~12.32 m/s.
- No discrete high-rate ramp events were flagged by the model; changes are gradual rather than stepwise.

Uncertainty and recent performance
- Ensemble spread is non‑trivial (mean spread 1.77 m/s, max spread up to 6.0 m/s). The system confidence is flagged as low.
- Calibration and recent verification show a small, persistent over‑forecast bias (T1 bias ≈ 0.015; T2 bias ≈ 0.0157) derived from the last 14 days; MAE ~0.17–0.18. Ensemble bands have been widened (band scale ~1.08 for T1, ~1.12 for T2).

Operational guidance for reserves (brief)
- Expect high overnight/early‑morning production with gradual taper into the following morning; hold moderate upward reserve through the trough period around 2026-02-06 07:00 local in case winds fall below the lower band.
- Because the forecast has a small systematic over‑forecast and ensemble spread is elevated, plan conservatively: maintain additional upward reserve margin overnight and into the morning trough rather than extra downward reserve.
- No rapid ramps identified that would require immediate dispatch actions; monitor NWP updates if model spread increases.

If you want, I can attach the hourly CSV and the JSON summary we published.
