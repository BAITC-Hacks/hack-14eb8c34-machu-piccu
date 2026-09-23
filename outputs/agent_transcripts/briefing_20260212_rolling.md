Forecast published for 2026-02-12 (48 h, both turbines). Files: outputs/cycles/forecast_20260212_rolling.csv and outputs/cycles/analysis_20260212_rolling.json.

Summary — weather and model inputs
- Mean forecast wind at hub ~5.18 m/s; model disagreement present: GFS ~6.04 m/s while ECMWF and ICON are lower (~4.7–4.8 m/s). Ensemble spread moderate (mean spread 1.97 m/s, max spread 5.19 m/s). Expect model uncertainty through the run; when models diverge prefer the P10–P90 band.
- Latest NWP runs materially revised the day‑ahead: for t1 the day‑ahead hours were revised (mean absolute change 0.0756, mean signed change -0.0218, max abs change 0.2655) — net downward adjustment. For t2 the day‑ahead was also revised (mean abs change 0.0861, mean signed change -0.031, max abs change 0.2685) — net downward adjustment. Action: day‑ahead forecast revised with today's NWP runs.

Forecast model performance and calibration
- Recent 14‑day record shows a tendency to over‑forecast. Calibration applied:
  - t1: bias ≈ 0.069 over-forecast; band scaled ×1.1506.
  - t2: bias ≈ 0.049 over-forecast; band scaled ×1.1916.
- Recent verification (14 d) MAE/RMSE and coverage:
  - t1: mae 0.194, rmse 0.2377, bias over‑forecasting; P10–P90 coverage 0.78.
  - t2: mae 0.2062, rmse 0.2486, bias over‑forecasting; P10–P90 coverage 0.636.
- Because of the over‑forecast tendency and model spread, overall confidence: low.

Key forecast numbers (do not invent other values)
- t1:
  - energy_48h_eflh = 8.87
  - energy_day_ahead_24h_eflh = 1.64
  - mean_capacity_factor = 0.185
  - max_output = 0.725; min_output = 0.0
  - hours_below_cutin = 20
  - peak_hour_local = 2026-02-14 02:00:00; trough_hour_local = 2026-02-13 00:00:00
  - mean_ensemble_spread_ms = 1.97
- t2:
  - energy_48h_eflh = 9.52
  - energy_day_ahead_24h_eflh = 1.82
  - mean_capacity_factor = 0.198
  - max_output = 0.744; min_output = 0.0
  - hours_below_cutin = 17
  - peak_hour_local = 2026-02-14 02:00:00; trough_hour_local = 2026-02-13 00:00:00
  - mean_ensemble_spread_ms = 1.97
- No significant ramp events flagged by the model in the 48 h window.

Operator briefing (under 250 words)
- Expected energy per turbine: t1 48‑h = 8.87 eflh (day‑ahead 24‑h = 1.64 eflh); t2 48‑h = 9.52 eflh (day‑ahead 24‑h = 1.82 eflh).
- Shape of the day: generally light winds with most hours near or below cut‑in (t1: 20 hours below cut‑in, t2: 17 hours below cut‑in). A modest peak around local 02:00 on 2026‑02‑14; the lowest point around local 00:00 on 2026‑02‑13.
- Ramps/staffing: no model‑flagged high ramps in the 48‑h forecast; however the recent NWP update produced some large hour‑to‑hour revisions (single‑hour changes up to ~0.27 of rated power between yesterday's and today's day‑ahead runs). Be ready for short notice adjustments if observed winds follow the higher GFS solution.
- Confidence and recommendation: confidence low due to model disagreement (GFS higher than ECMWF/ICON), moderate ensemble spread, and a recent small warm bias in the forecast that has been corrected in calibration. Hold conservative upward reserve relative to forecasted output for the day‑ahead block in case winds trend toward the higher model (GFS), but also expect many low‑output hours; reserve strategy: retain flexibility rather than fixed additional downward reserve.
