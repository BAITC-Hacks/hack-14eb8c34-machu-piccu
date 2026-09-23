Turbine t1 — NWP summary (48 h)
- Mean wind at 100 m: 9.53 m/s, max 12.44 m/s, min 1.8 m/s.
- Per-model means: ECMWF 9.01 m/s, GFS 11.01 m/s, ICON 8.56 m/s — models differ by ~2.5 m/s, ensemble spread mean 1.51 m/s (max 2.96 m/s). That disagreement is the main uncertainty driver.

Turbine t2 — NWP summary (48 h)
- Same as t1 (site pair): mean 9.53 m/s, max 12.44 m/s, min 1.8 m/s.
- Per-model means identical; ensemble spread same as t1.

Recent forecast performance (last 14 days)
- t1: MAE 0.1632, RMSE 0.2212, small positive bias 0.0099 (slight over-forecast), P10–P90 coverage 0.889.
- t2: MAE 0.1806, RMSE 0.2373, small negative bias -0.0188 (slight under-forecast), P10–P90 coverage 0.75.
- Neither turbine has a large systematic error, but t2's interval coverage is low — treat P10–P90 as less reliable for t2.

Input updates since yesterday (day-ahead hours)
- t1: Day-ahead revised by today's NWP: mean absolute change 0.0858 (fraction of rated power), mean signed change +0.084 (upwards), max change 0.1749. Action: day-ahead forecast revised with today's runs.
- t2: Day-ahead revised: mean absolute change 0.0723, mean signed change +0.0685 (upwards), max 0.1546. Action: day-ahead forecast revised with today's runs.

Forecast cycle outputs (published)
- Files written: outputs/cycles/forecast_20260214_rolling.csv and outputs/cycles/analysis_20260214_rolling.json (96 rows).

Key modeled numbers you should use (do not invent other numbers)
- For both turbines: energy_48h_eflh = 31.54; energy_day_ahead_24h_eflh = 13.71.
- Mean capacity factor (48 h) = 0.657; peak hourly output 0.911 (local peak at 2026-02-15 15:00), trough 0.046 (local trough at 2026-02-15 02:00).
- Confidence flagged as "low" in both analyses; mean ensemble spread 1.51 m/s.

Operator briefing (under 250 words)
Expected energy per turbine: energy_48h_eflh = 31.54 eflh for the 48-h window, with energy_day_ahead_24h_eflh = 13.71 eflh for the upcoming 24 h.

Shape of the day: winds pick up into the afternoon of 2026-02-15 with a modeled peak output around 15:00 local (peak output 0.911 p.u.), and a low in the early hours around 02:00 local the same night (trough 0.046 p.u.). The mean capacity factor over 48 h is 0.657, so expect generally strong production with a midday peak.

Ramps / staffing: No discrete large ramp events flagged by the model, but the day-ahead update increased the forecast (mean upward change ~0.07–0.08 p.u.). The largest hour-to-hour revisions reached ~0.15–0.17 p.u.; consider holding moderate upward reserve into the afternoon peak in case the higher GFS-driven wind verifies.

Confidence and caveats: Overall confidence is low. There is notable inter-model spread (ECMWF vs GFS differ by ~2 m/s) and ensemble spread ~1.5 m/s; recent performance shows small opposing biases (t1 slight over-forecast, t2 slight under-forecast) and limited verification samples. The day-ahead forecast was materially revised upward with today's NWP runs. Use the P10–P90 band where possible to manage uncertainty; for t2 treat the interval cautiously given lower historical P10–P90 coverage.

Forecast published to outputs/cycles/forecast_20260214_rolling.csv and analysis_20260214_rolling.json.
