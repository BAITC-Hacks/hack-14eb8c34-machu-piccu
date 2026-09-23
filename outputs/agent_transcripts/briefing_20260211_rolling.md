Turbine forecasts (issued 2026-02-11 18:00 UTC)

Forecasts published to control room: 
- CSV: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/forecast_20260211_rolling.csv
- JSON summary: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/analysis_20260211_rolling.json

Forecast summary — both turbines
- Horizon: 48 hours (local times shown in files). Issue time 2026-02-11 18:00 UTC.
- Mean wind speed (100 m): 4.33 m/s, min 1.01 m/s, max 9.56 m/s.
- Ensemble spread (mean): 1.86 m/s; max spread 4.34 m/s — models disagree moderately to strongly at times, so use the P10–P90 band where possible.
- No hours near rated power; no cut-in hours expected.
- Lead-run update: today's NWP runs materially revised the day‑ahead hours versus yesterday (mean absolute change ~0.14 of rated; signed change ~ –0.07), so the day‑ahead is lower than yesterday's longer‑lead forecast on average.

Turbine t1 (summary from model run)
- Energy equivalent (48h): 7.19 full-load hours.
- Day-ahead (DA) energy: 5.20 FLH.
- Mean capacity factor: 0.15; max output 0.556; min 0.029.
- Peak hour (local): 2026-02-12 01:00.
- Trough hour (local): 2026-02-13 07:00.
- Mean ensemble spread (wind): 1.86 m/s.
- Online calibration: recent 14-day record shows model running high by ≈0.024 of rated; band scaled ×0.9448.
- Recent skill (14d): MAE 0.1675, RMSE 0.2143, bias +0.0264 (over-forecast), P10–P90 coverage 85.6%.
- Confidence: low (due to ensemble spread and model bias).

Turbine t2 (summary from model run)
- Energy equivalent (48h): 7.95 full-load hours.
- Day-ahead (DA) energy: 5.58 FLH.
- Mean capacity factor: 0.166; max output 0.572; min 0.045.
- Peak hour (local): 2026-02-12 01:00.
- Trough hour (local): 2026-02-13 07:00.
- Mean ensemble spread (wind): 1.86 m/s.
- Online calibration: recent 14-day record shows model running high by ≈0.008 of rated; band scaled ×0.9560.
- Recent skill (14d): MAE 0.1745, RMSE 0.2224, bias +0.0093 (over-forecast), P10–P90 coverage 76.1%.
- Confidence: low.

Input updates (what changed with latest runs)
- For both turbines the new NWP runs changed the day‑ahead forecast materially: mean absolute change ≈0.14 of rated power across overlapping 24h, with the average change negative (day‑ahead lower by ~0.07). Maximum single‑hour revision up to ~0.34. Action: day‑ahead forecast revised using today's NWP runs.

Operational notes for dispatch (under 250 words)
- Expected 48‑h energy: t1 ≈ 7.19 FLH, t2 ≈ 7.95 FLH (see published files for hourly CF and P10–P90 bands).
- Shape: a modest overnight peak around local 01:00 on 12 Feb for both turbines, then gradual fall to a trough early on 13 Feb (07:00 local). No high wind events; outputs remain well below rated.
- Ramps/risks: no modelled rapid ramps flagged; however ensemble spread is moderate to high (mean 1.86 m/s, max 4.34 m/s) and the day‑ahead was revised down versus yesterday — expect possible hour‑to‑hour variability and some downside relative to point forecast. Largest single‑hour forecast revision in this update was ~0.34 of rated, so hold some flexible reserve for potential shortfalls during the first 24 hours.
- Confidence: low. Reasons: notable ensemble disagreement, recent tendency for the model to slightly over‑forecast (especially t1), and today's NWP runs materially lowered the day‑ahead. Use the P10–P90 bands in the JSON/CSV for reserve sizing; for conservative dispatch assume outputs closer to P10 during the early window if reserves are tight.

Files have been written to the control-room locations noted above.
