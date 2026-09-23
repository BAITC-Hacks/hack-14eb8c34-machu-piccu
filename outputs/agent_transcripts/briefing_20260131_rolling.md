Turbine 1:
- Weather summary (48 h): mean wind ~7.99 m/s at 100 m, model means diverge (ECMWF ~7.7, GFS ~10.35, ICON ~5.92). Ensemble spread moderate to high (mean spread 2.62 m/s, peak spread 5.55 m/s). Temps near 0.9°C. Expect variable winds with model disagreement through the period; rely on P10–P90 band for risk.
- Input update: Day-ahead hours were materially revised by today's NWP runs vs yesterday (overlap 24 h). Mean absolute change 0.096 of rated power, mean signed change -0.0538 (net downward), max abs change 0.2646. Action: today's runs lowered the DA point forecast on average but introduced some hours with sizable moves.
- Recent performance: 14-day verification shows the model tends to over-forecast (bias +0.0375) with MAE 0.1618 and RMSE 0.2164. P10–P90 coverage 76.5%. Cal adjustments applied in analysis.

Turbine 2:
- Weather summary (48 h): same as T1 (site close): mean wind ~7.99 m/s, per-model spread ECMWF 7.7 / GFS 10.35 / ICON 5.92. Ensemble spread mean 2.62 m/s (max 5.55 m/s). Expect variable winds and model disagreement; P10–P90 band important.
- Input update: Day-ahead hours materially revised by today's NWP runs vs yesterday (overlap 24 h). Mean abs change 0.0968, mean signed change -0.0547 (net downward), max abs change 0.2621. Action: DA point forecast nudged lower overall but with some large-hour adjustments.
- Recent performance: 14-day verification: bias +0.0417 (over-forecasting), MAE 0.1658, RMSE 0.2259, P10–P90 coverage 74.1%. Calibration applied.

Publication:
- The 48-hour forecast files have been written: outputs/cycles/forecast_20260131_rolling.csv and outputs/cycles/analysis_20260131_rolling.json (96 hourly rows).

Operator briefing (for dispatchers; <250 words)
- Expected energy per turbine:
  - Turbine 1 energy_48h_eflh = 17.92; energy_day_ahead_24h_eflh = 4.6
  - Turbine 2 energy_48h_eflh = 17.8; energy_day_ahead_24h_eflh = 4.54
- Shape of the day: Low output overnight into early morning (trough around local 2026-02-01 01:00). Winds build into the second day with a peak mid-afternoon (local 2026-02-02 14:00) then a notable down-ramp late evening (local 2026-02-02 19:00) of roughly -0.27 of rated power.
- Ramps/staffing: Expect a significant downward ramp around 2026-02-02 19:00 (~0.266–0.268 p.u.). Also allow for variable gustiness during daytime peaks due to model disagreement. If holding reserves, plan for ~0.3 p.u. contingency for that ramp and additional margin given uncertainty.
- Confidence and reason: Confidence rated low. Ensemble spread and inter-model disagreement are substantial; recent verification shows a systematic over-forecast bias which has been corrected in calibration but reduces trust in point values. Use the provided P10–P90 band for reserve sizing and treat day-ahead point values as biased-high without calibration.

Published by duty forecaster for Shelek corridor site — forecast issued 2026-01-31 18:00 UTC.
