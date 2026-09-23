Turbine forecasts published for 2026-02-17 (48 h). Files:
- CSV: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/forecast_20260217_rolling.csv
- JSON: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/analysis_20260217_rolling.json

Weather summary (both turbines)
- Mean wind at hub ~10.1 m/s (100 m). Model means: ECMWF 9.93, GFS 11.62, ICON 8.69.
- Wind range over 48 h: min 3.6 m/s, max 13.0 m/s.
- Ensemble spread moderate: mean spread ~1.6 m/s, max spread ~3.8 m/s. Where spread is larger, treat uncertainty higher and rely on P10–P90 bands.

Recent forecast performance
- No verified forecast hours in the past 14 days for either turbine. No calibration bias or band adjustments applied; forecasts are uncorrected model output.

Input update check
- Day-ahead forecast revised with today's NWP runs for both turbines. Mean absolute change vs yesterday’s day-ahead: 0.0257 (fraction of rated power); mean signed change +0.0047 (small increase); largest change 0.0919. Action: updated day-ahead values using current 24 h lead runs.

Forecast highlights (from model output)
- Mean capacity factor (48 h): 0.629 for each turbine.
- Day-ahead energy (equivalent full-load hours): 19.73 EFLH (per turbine over 48 h).
- Peak hour localized: 2026-02-18 14:00 local, max output ~0.937 p.u.
- Trough hour localized: 2026-02-19 22:00 local, min output ~0.079 p.u.
- Hours near rated output: 9 hours.
- Hours below cut-in: 0 hours.
- Mean forecast uncertainty (band width) is wide: mean band ~0.46 (fraction of rated power). Overall confidence flagged as "low" because there is no verified calibration history and ensemble spread is non-negligible.

Operator briefing (for dispatch)
- Expected energy: 19.73 full-load hours per turbine over the next 48 hours (so plan ~39.5 EFLH combined).
- Shape: wind is generally healthy through the period with a broad midday peak on 18 Feb (peak at 14:00 local) producing near-rated output for several hours (9 h near rated). Output falls toward the late second day, with the lowest hour around 22:00 local on 19 Feb.
- Ramps/risks: no model-flagged sharp ramp events in the analysis, but ensemble spread peaks where wind speed uncertainty reaches ~3.8 m/s — in those hours expect larger output uncertainty and possible moderate ramps. The day-ahead runs produced small positive revisions vs yesterday (mean signed change +0.0047 p.u.), max revision ~0.092 p.u. — watch those hours if you were holding reserve based on yesterday’s schedule.
- Confidence and recommendation: confidence is low due to no verified performance history and moderate ensemble spread. Use the P10–P90 bands (see published CSV) to size reserve; I recommend keeping extra contingency reserve during the high-uncertainty hours (periods where band width approaches the mean band ~0.46 p.u. and where ensemble spread peaks), and treat the midday peak on 18 Feb as reliable but not guaranteed to hit the point forecast.

Forecasts are published to the file paths above.
