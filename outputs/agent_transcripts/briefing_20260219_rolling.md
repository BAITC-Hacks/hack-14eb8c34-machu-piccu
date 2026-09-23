Forecast published for issue date 2026-02-19 (rolling). Files saved:
- CSV: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/forecast_20260219_rolling.csv
- JSON summary: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/analysis_20260219_rolling.json

Summary (both turbines t1 and t2)
- Forecast window: next 48 hours (issued 2026-02-19 18:00 UTC).
- Mean wind at hub ~7.94 m/s (per-model means: ECMWF 8.27, GFS 7.93, ICON 7.61). Ensemble spread moderate (mean spread 2.26 m/s, max 6.31 m/s) → uncertainty present.
- Modelled mean capacity factor: 0.434. Mean output over 48 h corresponds to energy-equivalent full-load hours (EFLH) = 20.82.
- Day-ahead (first 24 h) EFLH = 7.77.
- Forecast envelope: mean band width ~0.68 fraction of rated power; confidence flagged as low (high ensemble spread and no calibration history).
- Peak forecast hour (local): 2026-02-21 13:00 — max output ~0.708 fraction of rated power.
- Trough forecast hour (local): 2026-02-20 17:00 — min output ~0.093 fraction of rated power.
- Hours near rated: 0. Hours below cut-in: 0.
- No modelled discrete ramp events flagged in the analysis.

Recent performance
- No verified forecast hours in the last 14 days for either turbine (no bias/correction samples available). Calibration status: "no verified history yet - publishing uncorrected model output."

Input updates (check_input_updates)
- For both turbines the newest NWP runs materially revised the day-ahead forecast compared with yesterday’s longer-lead run. Summary of change over overlapping 24 h:
  - Mean absolute change: 0.1125 (fraction of rated power)
  - Mean signed change: +0.0141 (small net upward revision)
  - Maximum absolute change: 0.2726
  - Previous lead used: 48 h; current lead: 24 h
- Action: day-ahead forecast was revised with today's NWP runs. Expect some hours to have moved up or down by as much as ~0.27 of rated power relative to yesterday's day-ahead.

Operator briefing (for dispatchers)
- Expected energy next 48 h: total EFLH ~20.82 (both turbines combined metric is per-turbine; use per-turbine numbers for planning), with the first 24 h containing ~7.77 EFLH.
- Shape: moderate winds overall with a mid-day high on 2026-02-21 around 13:00 local and a low late on 2026-02-20 around 17:00 local. No sustained near-rated production expected; output stays broadly mid-range (mean capacity factor ~0.43).
- Ramps/risks: no discrete rapid ramps flagged, but ensemble spread is moderate-to-high and the latest NWP runs produced material revisions (some hours changed up to ~0.27 fraction of rated). This creates risk of intraday swings relative to earlier schedules.
- Confidence and staffing: overall confidence is low because (a) ensemble spread is elevated and (b) we have no recent verification/calibration data. Hold moderate upward/downward reserve around periods of larger NWP disagreement and around the local trough (2026-02-20 17:00) and peak (2026-02-21 13:00). If you must allocate reserves, plan for potential deviations up to ~0.25–0.30 fraction of rated power in the most-changed hours.

Notes
- Forecasts are uncalibrated model output (no verified bias samples yet). Monitor verified generation as it arrives to allow bias correction in upcoming cycles.
