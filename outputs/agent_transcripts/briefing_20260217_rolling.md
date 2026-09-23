T1 and T2 forecasts published.

Summary of weather and input changes
- Models: ECMWF, GFS and ICON disagree modestly on mean wind (ECMWF ~9.9 m/s, GFS ~11.6 m/s, ICON ~8.7 m/s). Ensemble spread averages 1.6 m/s and peaks ~3.8 m/s — indicates moderate forecast uncertainty. Mean 100m wind ~10.1 m/s, min ~3.6 m/s, max ~13.0 m/s over the 48 h.
- Latest NWP runs materially revised the day‑ahead hours vs yesterday: the 24‑hour overlapping window shows a mean absolute change of 0.0257 (fraction of rated power), max change 0.0919. Mean signed change small (0.0047) — net change near zero but individual hours moved enough to warrant note. Action: day‑ahead revised with today's NWP runs for both turbines.

Recent performance and calibration
- No verified forecast history in the last 14 days for either turbine (no verified hours), so calibration is uncorrected model output. Treat point forecasts cautiously.

Forecast highlights (from run_forecast_cycle)
- Both turbines: energy_48h_eflh = 30.2; energy_day_ahead_24h_eflh = 19.73.
- Mean capacity factor (48h) = 0.629; mean wind speed ~10.08 m/s.
- Peak hourly output at local 2026-02-18 14:00; trough at local 2026-02-19 22:00.
- Max output 0.937, min 0.079; about 9 hours near rated power; zero hours below cut-in.
- Ramp events: none flagged by the model.
- Confidence: low — because ensemble spread is moderate and there is no recent verification/calibration.

Operator briefing (for dispatchers; <250 words)
- Expected energy per turbine:
  - energy_48h_eflh = 30.2
  - energy_day_ahead_24h_eflh = 19.73
- Shape of the day: winds are generally strong through the first day with a peak around 14:00 local on 2026-02-18, producing multiple hours near rated output (9 hours). Output then tapers into the second day with the lowest hourly forecast at 22:00 local on 2026-02-19.
- Ramps/staffing: the model did not flag discrete ramp events. However, ensemble spread peaks indicate moderate uncertainty in timing and magnitude of peaks — watch the afternoon peak (Feb 18 ~14:00) for +/- up to ~0.09 change in fraction of rated power relative to yesterday’s run. No expectation of cut‑out or extended lull (min output still above cut‑in).
- Confidence and reserve recommendation: confidence is low due to modest model disagreement (ECMWF/GFS/ICON spread) and no recent calibration. Hold conservative upward/downward reserves around anticipated peak hours — plan for possible +/- ~0.1 (fraction of rated power) intra‑day swing during the highest-uncertainty hours.

Files written: outputs/cycles/forecast_20260217_rolling.csv and outputs/cycles/analysis_20260217_rolling.json.
