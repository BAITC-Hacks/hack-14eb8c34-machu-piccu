T1 and T2 48-hour forecast published for issue 2026-01-31 (files: outputs/cycles/forecast_20260131_rolling.csv, outputs/cycles/analysis_20260131_rolling.json).

Input changes since yesterday
- t1: day-ahead hours revised by today's NWP runs. Overlapping 24h mean signed change -0.0538 (down); mean absolute change 0.0964; max abs change 0.2646. Current run uses shorter lead NWP (24h) vs yesterday's 48h.
- t2: day-ahead hours revised by today's NWP runs. Overlapping 24h mean signed change -0.0547 (down); mean absolute change 0.0968; max abs change 0.2621. Current run uses shorter lead NWP (24h) vs yesterday's 48h.

Recent model performance (14-day)
- t1: verified 672 hours. MAE 0.1618, RMSE 0.2164, bias +0.0375 (model over-forecasts), P10–P90 coverage 0.765.
- t2: verified 672 hours. MAE 0.1658, RMSE 0.2259, bias +0.0417 (model over-forecasts), P10–P90 coverage 0.741.

Weather summary (from NWPs)
- Mean wind ~8.0 m/s across the site for the 48h window; ensemble spread moderately large (mean spread 2.62 m/s), producing low confidence in point estimates.
- Forecast concentrates higher winds into the second day with a broad peak around local 2026-02-02 14:00; a drop/ramp is signalled near local 2026-02-02 19:00.

Key forecast numbers (model outputs)
- t1: energy_48h_eflh = 17.92; energy_day_ahead_24h_eflh = 4.6. Mean CF 0.373. Peak hourly output 0.892, trough 0.029. Mean band width 0.57. Confidence: low. Ensemble-driven ramp: -0.268 at 2026-02-02 19:00 local.
- t2: energy_48h_eflh = 17.8; energy_day_ahead_24h_eflh = 4.54. Mean CF 0.371. Peak hourly output 0.889, trough 0.027. Mean band width 0.589. Confidence: low. Ensemble-driven ramp: -0.266 at 2026-02-02 19:00 local.
- Calibration note: recent 14-day record shows systematic over-forecasting (t1 bias 0.028; t2 bias 0.031) and band widths scaled up (t1 x1.09; t2 x1.14).

Operator briefing (for reserves; under 250 words)
- Expected energy per turbine: t1 48h = 17.92 eflh (day-ahead 24h = 4.6 eflh); t2 48h = 17.8 eflh (day-ahead 24h = 4.54 eflh).
- Shape of the day: relatively low output overnight into day 1 with a significant rise through day 2 peaking around local 2026-02-02 14:00, then a notable drop in the evening of day 2.
- Ramps/staffing: plan for a downward ramp around local 2026-02-02 19:00 of roughly 0.27 of rated power per turbine (model median); this is the main event to cover with reserve. Smaller hour-to-hour variability expected otherwise due to ensemble spread.
- Confidence and caveats: low confidence in point values because ensemble spread is substantial and recent model bias shows small systematic over-forecasting. Today's NWP updates reduced the day-ahead median slightly versus yesterday (mean signed change ≈ -0.054). Use the P10–P90 band for reserve sizing rather than the median; bands have been broadened by calibration.
