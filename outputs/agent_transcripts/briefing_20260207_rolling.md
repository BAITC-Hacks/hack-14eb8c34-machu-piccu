Forecast issued 2026-02-07 (rolling). Files written to the control room: forecast_20260207_rolling.csv and analysis_20260207_rolling.json.

Key points — model/weather
- Weather summary (both turbines): mean 100 m wind ~12.4 m/s over next 48 h; max ~18.8 m/s, min ~1.2 m/s. Models (ECMWF, GFS, ICON) show mean winds 11.9–13.1 m/s. Ensemble spread moderately high: mean spread ~1.97 m/s, max spread ~4.1 m/s. This disagreement drives our uncertainty.
- Recent forecast performance: past 14 days the models have tended to run slightly high. Verified bias: t1 +0.0122, t2 +0.0115 (over-forecasting). MAE ~0.16–0.17; P10–P90 coverage ~0.81–0.87.
- Input updates: today’s NWP runs materially revised the day‑ahead (overlap 24 h). Mean absolute change ~0.073 of rated power; mean signed change positive (t1 +0.0257, t2 +0.0392) so today's runs nudged forecasts higher in the day‑ahead window. Largest individual-hour change up to ~0.31 of rated power.

Forecast summary (from published files)
- Turbine t1 (48 h)
  - Mean capacity factor: 0.685
  - Day-ahead energy (EFH): 14.56 full-load hours
  - Peak output: 0.912 of rated at 2026-02-08 21:00 local
  - Trough: 0.04 of rated at 2026-02-08 12:00 local
  - Hours near rated: 11
  - Confidence: low (due to ensemble spread + recent over-forecast bias)
  - Notable ramp: ~+0.293 of rated at 2026-02-08 15:00 local (rapid increase)

- Turbine t2 (48 h)
  - Mean capacity factor: 0.700
  - Day-ahead energy (EFH): 14.90 full-load hours
  - Peak output: 0.926 of rated at 2026-02-08 21:00 local
  - Trough: 0.054 of rated at 2026-02-08 12:00 local
  - Hours near rated: 12
  - Confidence: low
  - Notable ramp: ~+0.293 of rated at 2026-02-08 15:00 local (same ramp timing as t1)

Calibration/actions applied
- Model bias correction applied: t1 bias ~+0.023 (14d), t2 bias ~+0.009 (14d) and ensemble bands scaled (t1 x1.09, t2 x1.14) so P10–P90 widened to reflect recent undercoverage and spread.

Operator briefing (under 250 words)
Expected energy next 48 h: t1 ≈ 14.6 EFH, t2 ≈ 14.9 EFH (see published CSV for hourly values). The near-term day (first 24 h) shows sustained strong winds with a dip around local midday on 2026-02-08 (~hourly trough ~0.04–0.05 rated power near 12:00), then a recovery and peak late evening (21:00 local) approaching rated output. There is a notable ramp around 15:00 on 2026-02-08 where output climbs ~0.29 of rated power within an hour — plan for reserve activation or fast response capacity around that time. Confidence is low: ensemble spread is elevated and recent runs have nudged the day‑ahead forecast upward; additionally the model has had a small consistent over-forecast bias. Hold reserves sufficient for the reported uncertainty band (P10–P90 widened per calibration) and expect possible further revisions as new NWP runs arrive. If you need a specific reserve MW figure, use the published hourly P10–P90 bands in analysis_20260207_rolling.json; they reflect the wider uncertainty and the applied bias correction.

Files saved: forecast_20260207_rolling.csv, analysis_20260207_rolling.json.
