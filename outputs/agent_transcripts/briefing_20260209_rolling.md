Turbine forecasts published for 2026-02-09 (48 h). Files: forecast_20260209_rolling.csv and analysis_20260209_rolling.json.

Inspection of inputs and verification
- Weather models (both turbines): mean wind at 100 m ~8.43 m/s (models: ECMWF 8.03, GFS 8.88, ICON 8.39). Ensemble spread moderate: mean sigma 2.69 m/s, max spread 7.53 m/s — expect notable uncertainty where ensembles diverge.
- Recent performance (last 14 days):
  - T1: MAE 0.1613, RMSE 0.2134, small positive bias 0.0266 (model tends to over-forecast). P10–P90 coverage 0.906.
  - T2: MAE 0.1632, RMSE 0.2203, small positive bias 0.0086 (slight over-forecast). P10–P90 coverage 0.844.
- Input updates: both turbines had material day‑ahead changes vs yesterday (overlapping 24h). Mean absolute change ~0.092 of rated power; mean signed change small positive (~+0.01). Max single-hour revision ~0.215 — today's NWP runs meaningfully revised the DA curve.

Forecast summary (analysis outputs)
- T1 (48 h):
  - Mean capacity factor: 0.456; mean wind 8.43 m/s.
  - Energy equivalent full-load hours (48 h window): 21.87; day‑ahead energy: 6.90 FLH.
  - Peak hourly output: 0.907 of rated; trough: 0.102.
  - Hours near rated: 3; hours below cut‑in: 0.
  - Notable ramp: drop of ~0.289 of rated at 2026-02-11 06:00 local.
  - Uncertainty/confidence: mean ensemble spread 2.69 m/s; forecast confidence = low. Calibration: recent 14d bias shows over-forecast of +0.014 so small downward adjustment applied; band scaled ×0.987.
- T2 (48 h):
  - Mean capacity factor: 0.471; mean wind 8.43 m/s.
  - Energy equivalent full-load hours: 22.60; day‑ahead energy: 7.27 FLH.
  - Peak hourly output: 0.922; trough: 0.118.
  - Hours near rated: 3; hours below cut‑in: 0.
  - Same ramp: −0.289 at 2026-02-11 06:00 local.
  - Uncertainty/confidence: mean ensemble spread 2.69 m/s; forecast confidence = low. Calibration: recent 14d bias small under-forecast (−0.001) so tiny upward tweak; band scaled ×1.052.

What changed with the latest NWP runs
- Both turbines: Day‑ahead period (first 24 h) was materially revised compared with the previous-issue DA curve. Mean absolute change ~0.09 of rated power; some hours moved by ~0.21. The new runs bumped the DA curve slightly upward on average (mean signed change +0.01) — but calibration adjustments reduce systematic bias for T1 and slightly raise T2.

Operator briefing (under 250 words)
- Expected energy (next 48 h): T1 ~21.9 FLH, T2 ~22.6 FLH (outputs in analysis file). Expect mean capacity ~0.46–0.47 of rated across the period.
- Shape and timing: Moderate winds with a daytime peak on 2026-02-11 around 21:00 local (highest single-hour output ~0.91–0.92). Lowest output ~0.10–0.12 around 2026-02-10 17:00 local. Three hours near-rated output across the window.
- Ramps and staffing: A rapid drop of ~0.29 of rated power is forecast at 2026-02-11 06:00 local — this is the primary ramp to plan for. Because ensemble spread is moderate-to-high and DA runs were revised materially, hold reserves to cover ~0.3 of rated power during that interval.
- Confidence and caveats: Overall confidence is low due to ensemble disagreement (mean spread 2.69 m/s, max spread up to 7.5 m/s) and material day‑ahead revisions today. Recent verification shows small systematic biases (T1 slight over-forecast; T2 nearly unbiased), so we've applied small calibration tweaks. Use the P10–P90 bands in the published JSON for reserve sizing; if you need a single number, expect ±~0.25–0.30 of rated uncertainty around the ramp window.

Files have been written to the control-room directory (CSV + JSON).
