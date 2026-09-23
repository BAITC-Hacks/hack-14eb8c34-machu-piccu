Forecast published (issue 2026-02-25T18:00 UTC). Files:
- CSV: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/forecast_20260225_rolling.csv
- JSON summary: /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/analysis_20260225_rolling.json

Summary (both turbines, 48 h):
- Energy (48 h, equivalent full-load hours): 30.95 EFLH (both t1 and t2).
- Day-ahead energy (first 24 h): 15.08 EFLH (both).
- Mean capacity factor: 0.645 (both).
- Forecast range: mean band width ~0.60–0.603; confidence flagged as "low".
- Peak output: 0.85 (model peak). Peak hour local: 2026-02-27 02:00 (both).
- Trough hour local: 2026-02-27 11:00 (both).
- Max/min modelled output over the 48 h: max 0.85, min 0.263 (both).
- Hours near-rated: 0; hours below cut-in: 0 (both).
- Ramps: none identified by the model for either turbine.
- Mean wind at hub: 9.85 m/s; per-model means: ECMWF 9.34 m/s, GFS 10.54 m/s, ICON 9.66 m/s.
- Ensemble spread: mean 1.8 m/s, max 5.24 m/s.

Recent performance and calibration:
- No verified forecast hours in the recent 14-day window for either turbine (no bias correction available). Calibration note: "no verified history yet - publishing uncorrected model output."

Input updates (comparison vs yesterday's issued forecast):
- Day-ahead forecast was revised with today's NWP runs for both turbines.
- Overlapping 24 h: mean absolute change 0.0701 (fraction of rated power); mean signed change -0.029 (net small downward move); max absolute change 0.2241.
- NWP lead used for the updated day-ahead is 24 h (previously 48 h).

Operational briefing for the control room (under 250 words)
- Expected energy: 30.95 EFLH over the next 48 h per turbine (15.08 EFLH in the coming day). Use this for day-ahead scheduling.
- Shape: steady-good production centered on a nocturnal peak at 2026-02-27 02:00 local; lowest output around 2026-02-27 11:00 local. No modelled near-rated hours; production stays well within turbine operating range.
- Ramps and reserves: the model did not flag discrete ramp events. However, the day-ahead values moved materially when refreshed with today's NWP (mean abs change ~0.07 p.u., max ~0.224 p.u.). That indicates potential for mid-size adjustments in the day-ahead block if conditions evolve — hold moderate flexible reserve to cover up to roughly the largest update magnitude observed (~0.22 p.u.) if you need strict risk control.
- Confidence and reason: confidence is low due to limited verified history (no bias correction) and moderate ensemble spread (mean 1.8 m/s, peaks to 5.24 m/s). Where model members diverge, consider the P10–P90 spread rather than relying on the point estimate.
- Actionable recommendation: schedule against the published 48-h CSV values but keep ~1–2 turbines' equivalent short-term upward/downward reserve available during the first 24 hours, and watch the next NWP runs for possible further revisions.

No calibration adjustments were applied because there is no verification history yet.
