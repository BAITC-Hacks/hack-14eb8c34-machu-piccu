T1 and T2 forecasts published for 2026-02-22 (48 h). Files:
- outputs/cycles/forecast_20260222_rolling.csv
- outputs/cycles/analysis_20260222_rolling.json

Weather summary (both turbines)
- Model mean wind at hub (~100 m): 7.7 m/s (48 h mean). Model spread moderate: mean ensemble spread 1.63 m/s, max ensemble spread 2.83 m/s. Individual model means: ECMWF ~6.78 m/s, GFS ~8.00 m/s, ICON ~8.27 m/s — some model disagreement with ICON/GFS faster than ECMWF.
- Conditions: temps around 1.9°C, 48-h wind speeds range ~2.1–12.4 m/s. Expect generally moderate winds with a brief higher-speed period.

Input updates since previous run (both turbines)
- Day-ahead hours were revised by today's NWP runs (previous run 48-h lead vs now 24-h lead). The day-ahead mean change was a decrease (mean signed change -0.0436 fraction of rated), mean absolute change 0.0626, max single-hour change 0.351. In short: the newest runs mostly reduced the day-ahead outputs but with some hours moved substantially (up to ~0.35 p.u.).

Recent performance
- No verified forecast history in the last 14 days for either turbine (no scoring data). Treat model output as uncorrected/unverified.

Forecast analysis (both turbines; values from the model run)
- energy_48h_eflh: 21.75 per turbine
- energy_day_ahead_24h_eflh: 8.21 per turbine
- mean_capacity_factor: 0.453
- peak hour (local): 2026-02-24 01:00 — max_output 0.903
- trough hour (local): 2026-02-23 08:00 — min_output 0.056
- hours near rated: 1
- hours below cut-in: 0
- ensemble uncertainty: mean band width ~0.48 p.u.; confidence flagged as low
- calibration note: no verified history yet — publishing uncorrected model output

Operator briefing (for dispatchers)
- Expected energy per turbine: energy_48h_eflh = 21.75; day‑ahead 24‑h = 8.21 (both exact).
- Shape of the day: Moderate winds overall with low output overnight into the morning of 2026-02-23 (deep trough at ~08:00 local, down to ~0.056 p.u.), rising into a brief higher-speed window late on 2026-02-24 with a peak to ~0.903 p.u. around 01:00 local. Most hours are in a mid-range (mean CF ~0.45).
- Ramps/operational concerns: The input updates moved many day‑ahead hours downward on average; there are individual hours with large adjustments (max change ~0.351 p.u.) — these represent potential short notice reductions. No high-frequency extreme ramps flagged by the model, but the spread indicates notable uncertainty so reserve should cover a few tenths of rated per turbine.
- Confidence and recommendation: Confidence is low due to unresolved model disagreement (ECMWF slower than GFS/ICON) and no verification history to calibrate bias. Hold moderate upward reserve for the morning trough (in case winds are lower than expected) and consider ~0.3 p.u. contingency per turbine for any single-hour shortfalls given the max input revision seen. If system economics permit, treat the late-night peak as firm only with limited certainty.

Files published to control room: outputs/cycles/forecast_20260222_rolling.csv and outputs/cycles/analysis_20260222_rolling.json.
