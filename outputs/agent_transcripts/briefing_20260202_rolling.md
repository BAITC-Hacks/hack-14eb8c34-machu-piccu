Forecast published for issue 2026-02-02 (rolling). Files:
- CSV: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/forecast_20260202_rolling.csv
- JSON: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/analysis_20260202_rolling.json

Forecast highlights (48 h, per-turbine — units are fraction of rated power unless stated):

Turbine t1
- 48‑hour mean capacity factor: 0.297
- Day‑ahead energy (equivalent full‑load hours): 6.73
- Max hourly output: 0.649
- Min hourly output: 0.048
- Peak hour (local): 2026-02-04 23:00:00
- Trough hour (local): 2026-02-03 12:00:00
- Hours near rated: 0
- Hours below cut‑in: 0
- Mean ensemble band width: 0.621
- Mean wind speed (100 m): 6.48 m/s
- Confidence: low
- Calibration note: recent 14‑day record shows the model running over‑forecast by ~0.0108 of rated power; uncertainty band scaled ×1.0419
- Ramp events identified by the model: none

Turbine t2
- 48‑hour mean capacity factor: 0.298
- Day‑ahead energy (equivalent full‑load hours): 6.75
- Max hourly output: 0.649
- Min hourly output: 0.049
- Peak hour (local): 2026-02-04 23:00:00
- Trough hour (local): 2026-02-03 12:00:00
- Hours near rated: 0
- Hours below cut‑in: 0
- Mean ensemble band width: 0.673
- Mean wind speed (100 m): 6.48 m/s
- Confidence: low
- Calibration note: recent 14‑day record shows the model running over‑forecast by ~0.0099 of rated power; uncertainty band scaled ×1.1434
- Ramp events identified by the model: none

Recent performance (last 14 days, verified hours ~612 per turbine)
- t1: MAE 0.1695, RMSE 0.2239, bias +0.0273 (over‑forecasting)
- t2: MAE 0.1741, RMSE 0.2338, bias +0.0277 (over‑forecasting)
- P10–P90 coverage: t1 0.788, t2 0.752

Check-input-updates
- The automated check_input_updates calls returned an error/unavailable for this cycle; I therefore have no system flag about whether the newest NWP runs materially shifted yesterday’s day‑ahead. The forecast products above were generated from the current run (see published files); treat any short‑lead changes as possible given the model ensemble spread.

Operator briefing (for dispatchers)
- Expected energy next 48 h: roughly 6.7 full‑load hours per turbine (day‑ahead figures: t1=6.73, t2=6.75).
- Shape: moderate winds overall with a daytime trough around local 2026‑02‑03 12:00 and a peak late on 2026‑02‑04 23:00. No hours near rated power; lowest hours remain above cut‑in.
- Ramps: model did not flag discrete ramp events. Ensemble spread and band widths are relatively wide and the model has shown a small persistent high bias recently, so small-to-moderate hour‑to‑hour swings are possible.
- Confidence and reserve guidance: Confidence rated low due to ensemble spread and recent over‑forecast bias. Hold moderate short‑notice reserve capacity for the overnight-to-daytime trough (around local Feb‑3 midday) and late‑day peak on Feb‑4; reserves can be relaxed slightly outside those windows but monitor short‑range updates because check_input_updates was unavailable for this run.

If you want, I can re-run an immediate short‑range update (if new NWP runs are available) and report any material shifts.
