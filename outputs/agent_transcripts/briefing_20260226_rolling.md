Turbine forecasts published for 2026-02-26.

Summary of model weather input (both turbines)
- Mean 100 m wind speed next 48 h: 9.57 m/s (models disagree: ECMWF 8.23, GFS 10.95, ICON 9.53).
- Ensemble spread moderate: mean 1.72 m/s, max 3.44 m/s. Expect model disagreement at times — rely on P10–P90 for uncertainty.

Recent forecast performance
- No verified forecast hours in the last 14 days for either turbine. No bias correction applied; publishing uncorrected model output.

Input updates since previous run
- New NWP runs materially changed the day-ahead forecast for both turbines. Overlapping day-ahead hours: 24.
- Mean absolute change in power: 0.1032 (fraction of rated). Mean signed change: -0.1022 — overall downward revision vs yesterday. Max individual-hour change: 0.3066.
- Action: day-ahead forecast revised with today's NWP runs.

Forecast highlights (from model run)
- energy_48h_eflh (t1): 29.99
- energy_day_ahead_24h_eflh (t1): 13.41
- energy_48h_eflh (t2): 29.99
- energy_day_ahead_24h_eflh (t2): 13.41
- Mean capacity factor (both): 0.625. Peak hour local for both turbines: 2026-02-28 13:00. Trough hour local for both: 2026-02-27 11:00.
- Mean wind speed ~9.57 m/s; max ~11.76 m/s, min ~6.07 m/s.
- No predicted hours near rated output; no hours below cut-in.
- Mean ensemble spread indicates low-to-moderate confidence; calibration: none (no verified history).

Operator briefing (for dispatchers)
- Expected energy per turbine: energy_48h_eflh = 29.99; day‑ahead 24h energy per turbine = 13.41.
- Day shape: moderate winds overall with a mid-day peak on 2026-02-28 around 13:00 and a low late morning on 2026-02-27 around 11:00. Expect sustained generation rather than short spikes; mean capacity factor ~0.625.
- Ramps and staffing: no large, model-predicted ramp events flagged by the model run. However, the day‑ahead forecast was revised downward on average (mean signed change -0.1022) with some hours changing by as much as ~0.307 of rated power — watch the transition into the lower-power period on the morning of 2026-02-27 (~trough hour). Consider holding moderate upward reserve during that morning window in case the stronger-model members verify.
- Confidence and reason: overall confidence low (mean ensemble spread 1.72 m/s, max 3.44 m/s; models diverge notably between ECMWF and GFS). No recent verification data available, so no bias correction applied. Use the P10–P90 bands from the published files for reserve sizing; expect greater uncertainty around hours where model spread peaks.

Files written: outputs/cycles/forecast_20260226_rolling.csv and outputs/cycles/analysis_20260226_rolling.json.
