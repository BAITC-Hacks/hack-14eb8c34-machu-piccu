Turbine briefing and publication notes.

Inputs and model checks
- Both turbines: today's NWP runs show mean 100 m wind ~10.0 m/s over the 48 h, with model disagreement (per-model means: ECMWF 10.18, GFS 11.54, ICON 8.37). Ensemble spread averaged 1.83 m/s (max spread 3.62 m/s). This disagreement is the primary source of uncertainty.
- Recent performance: no verified forecast hours in the past 14 days for either turbine (no bias corrections yet).
- Input updates: compared with the previous run (2026-02-15) the day-ahead (next 24 h) forecast has been materially revised by today's NWP runs. Mean absolute change ~0.0828 (fraction of rated power), mean signed change -0.0665 (net downward), max hourly change 0.2015. In short: the DA forecast was revised lower in many hours but with some individual up moves.

What I published
- The 48-hour hourly forecast has been written to outputs/cycles/forecast_20260216_rolling.csv and summary outputs/cycles/analysis_20260216_rolling.json.
- Run metadata: issue_time_utc 2026-02-16T18:00:00, mode archive, policy rolling.

Forecast summary (do not state numbers not returned by tools)
- Both turbines have identical model outputs for this cycle: mean capacity factor ~0.623, peak hour local 2026-02-18 14:00, trough hour local 2026-02-17 09:00. Max hourly output ~0.931, min ~0.133. Hours near rated: 8; no hours below cut-in.
- Uncertainty: ensemble spread and differing NWP means produce low confidence in the point estimate; rely on the provided uncertainty bands rather than the single expected output where possible.

Operator briefing (for dispatchers)
- Expected energy per turbine:
  - energy_48h_eflh = 29.91
  - energy_day_ahead_24h_eflh = 10.3
- Shape of the day: winds moderate to strong through the period with a trough around local 2026-02-17 09:00 and a peak around local 2026-02-18 14:00. The first 24 h were revised downward on average from yesterday's forecast; later hours recover toward the peak.
- Ramps/staffing: no sharp ramp events flagged by the model, but the day-ahead changes from yesterday include individual hour moves up to ~0.20 pu — monitor DA market gate if you are scheduling fast reserves. Expect gradual increase toward the peak rather than abrupt step-changes.
- Confidence and reason: confidence = low. Main reasons: inter-model disagreement (ECMWF/GFS/ICON spread) and no recent verified forecast history to correct bias. Use the P10–P90 band for reserve planning and treat the point forecast cautiously.

Files published: outputs/cycles/forecast_20260216_rolling.csv and outputs/cycles/analysis_20260216_rolling.json.
