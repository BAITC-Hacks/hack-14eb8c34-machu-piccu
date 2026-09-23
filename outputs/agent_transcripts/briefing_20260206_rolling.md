Turbine 1 — summary of inputs and model output
- Weather models: mean wind ~8.03 m/s at hub height over the next 48 h (models: ECMWF 7.89, GFS 7.76, ICON 8.45). Ensemble spread moderate (mean 1.5 m/s, max 3.33 m/s) — when models disagree, uncertainty increases.
- Calibration & recent performance: 14‑day verification shows the model tends to over-forecast (~+0.020 of rated power). Recent MAE 0.168, RMSE 0.216; P10–P90 coverage 0.81. Band widths scaled x1.136.
- Forecast highlights (48 h model run): energy_48h_eflh = 21.73; energy_day_ahead_24h_eflh = 7.9. Mean capacity factor 0.453; peak hour local 2026-02-08 19:00; trough 2026-02-07 08:00. Max output 0.92, min 0.034. Hours near rated: 5. Confidence: low. Notable ramp: +0.302 at 2026-02-08 16:00 local.

Turbine 2 — summary of inputs and model output
- Weather models: same wind picture as T1 (mean 8.03 m/s; ECMWF 7.89, GFS 7.76, ICON 8.45). Ensemble spread mean 1.5 m/s, max 3.33 m/s.
- Calibration & recent performance: 14‑day verification shows over-forecast bias ~+0.022. Recent MAE 0.175, RMSE 0.228; P10–P90 coverage 0.757. Band widths scaled x1.231.
- Forecast highlights (48 h model run): energy_48h_eflh = 21.67; energy_day_ahead_24h_eflh = 7.87. Mean capacity factor 0.451; peak hour local 2026-02-08 19:00; trough 2026-02-07 08:00. Max output 0.919, min 0.033. Hours near rated: 5. Confidence: low. Notable ramp: +0.302 at 2026-02-08 16:00 local.

Input updates (both turbines)
- check_input_updates: today's NWP runs revised the day-ahead (24 h) portion compared with yesterday’s longer-lead run. Overlapping 24 h mean absolute change ~0.092 of rated power, max hourly change ~0.171; mean signed change small (~+0.003–+0.004). Action: day-ahead forecasts updated using current NWP.

Recent performance note
- Both turbines have shown a small persistent over-forecast (~0.015–0.022) in the last 14 days. Coverage of the P10–P90 band is acceptable but not perfect (T2 lower). Given that, treat point forecasts as slightly optimistic; rely on the P10–P90 band when ensemble spread is larger.

Publication
- Forecast published: outputs/cycles/forecast_20260206_rolling.csv and analysis_20260206_rolling.json (96 rows).

Operator briefing (<=250 words)
- Expected energy per turbine: T1 energy_48h_eflh = 21.73 (48 h), day-ahead energy_day_ahead_24h_eflh = 7.9. T2 energy_48h_eflh = 21.67 (48 h), day-ahead energy_day_ahead_24h_eflh = 7.87.
- Shape of the day: winds moderate through the period (mean ~8 m/s). Overnight low around local 2026-02-07 08:00 corresponds to the trough hours with outputs near minimums; bump to peak around 2026-02-08 19:00 with 5 hours near rated across the 48 h window.
- Ramps and reserve advice: Expect a notable up-ramp of about +0.30 pu at ~16:00 local on 2026-02-08 (both turbines). This is the main fast change worth staffing for; consider holding additional upward reserve into that hour. Other hourly changes are moderate but model ensemble spread implies uncertainty.
- Confidence and reasoning: Confidence is low—ensemble spread is moderate and the forecasting model has shown a small persistent high bias over the last 14 days (bands have been widened per calibration). Day‑ahead forecast was materially revised by today's NWP (mean abs change ~0.09 pu), so use P10–P90 band for reserve sizing rather than relying solely on the point estimate.

If you want, I can extract and send the hourly CSV or the P10/P90 bands for both turbines to help set reserve schedules.
