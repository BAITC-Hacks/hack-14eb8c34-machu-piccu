Turbine forecasts published for 2026-02-12 (48 h). Files: forecast_20260212_rolling.csv and analysis_20260212_rolling.json.

Summary (interpretation and key points)

- Models and uncertainty
  - Mean wind at hub ~5.2 m/s; model ensemble mean differs by turbine (ECMWF ~4.7, GFS ~6.0, ICON ~4.8). Ensemble spread is large (mean 1.97 m/s, up to 5.2 m/s) — treat the P10–P90 band as more informative than the single point forecast.
  - Both turbines show low confidence in point values due to high ensemble spread and low mean wind speeds near cut-in.

- Numerical forecast and calibration
  - Run completed and published. Mean capacity factors: t1 0.18, t2 0.191 over 48 h. Max hourly outputs ~0.72–0.74 rated.
  - Recent calibration shows the model has been systematically over-forecasting: t1 bias +0.077, t2 bias +0.059 (14-day calibration). Bands widened slightly (scale factors ~1.09 for t1, 1.08 for t2).

- Recent performance
  - Last 14 days: t1 MAE 0.194, RMSE 0.239, bias +0.027 (over-forecast); t2 MAE 0.206, RMSE 0.250, bias +0.0095 (over-forecast). P10–P90 coverage: t1 0.80, t2 0.67.

- Input updates (compared to yesterday)
  - Day-ahead hours were revised with today's NWP runs for both turbines.
  - t1: mean absolute change 0.070 of rated power; mean signed change −0.0165 (slightly lower on average); max change 0.2645.
  - t2: mean absolute change 0.082; mean signed change −0.0274 (slightly lower on average); max change 0.2671.
  - Action: day-ahead forecasts were adjusted downward in places after new runs — check P10–P90 for operational decisions.

Operator briefing (under 250 words)

Expected energy: t1 ~8.63 full-load hours, t2 ~9.19 FLH over the next 48 h (published). Average output low: ~18–19% capacity. Peak hourly output around local 02:00 on 2026-02-14 (~0.72–0.74 rated). Long stretches near cut-in: expect ~19–21 hours below cut-in across turbines (reduced/zero output at times).

Shape and ramps: overall light winds with intermittent ups around late local night leading to a modest peak at 02:00 on 2026-02-14. No large sustained ramps flagged by the model; however, individual hours see step changes (max input-update moves up to ~0.26 of rated power). Recent NWP updates nudged the day-ahead forecast slightly lower.

Staffing/reserve advice: hold modest upward reserve capacity for short-notice increases during the late-night peak window (low-probability <25% chance of outputs near 0.7). Because model bias shows small over-forecasting and ensemble spread is large, conservatively plan for lower actual output than the point forecast — use the P10–P90 band for reserve sizing.

Confidence: low. Reasons: mean winds near cut-in, large inter-model disagreement (ECMWF vs GFS spread), recent over-forecast bias, and widened uncertainty bands. Rely on the published P10–P90 band if needing quantitative reserve margins.
