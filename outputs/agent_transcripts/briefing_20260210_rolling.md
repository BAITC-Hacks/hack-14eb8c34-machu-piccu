T1 and T2 48-hour forecast published (issue 2026-02-10 18:00 UTC). Files written and archived.

Key notes and interpretation
- Model outputs: both turbines show moderate winds (mean ~8.2 m/s at 100 m) with per-model means ranging from ~7.5 (ECMWF) to 9.5 m/s (GFS). Ensemble spread is substantial (mean spread 2.46 m/s, max spread 7.77 m/s) — treat point values cautiously and rely on the P10–P90 band where decisions demand uncertainty.
- Forecast summary (model run analysis):
  - T1: 48-hr mean capacity factor 0.431, EFLH 20.68, day-ahead EFLH 13.82. Peak hourly output 0.869 (local 2026-02-11 21:00), trough 0.026 (local 2026-02-12 12:00). Confidence flagged low. Mean ensemble spread 2.46 m/s. Model calibration: recent 14d over-forecast ~+0.027 of rated power; calibration applied and uncertainty band scaled ×1.10.
  - T2: 48-hr mean capacity factor 0.447, EFLH 21.48, day-ahead EFLH 14.22. Peak 0.886 (2026-02-11 21:00), trough 0.042 (2026-02-12 12:00). Confidence low. Mean ensemble spread 2.46 m/s. Calibration: recent 14d over-forecast ~+0.011; band scaled ×1.13.
- Recent performance: over the last 14 days both turbines have been biased high (T1 bias +0.031; T2 bias +0.015). MAE ~0.14–0.15, RMSE ~0.19–0.20. P10–P90 coverage acceptable (T1 0.886, T2 0.811) but bands were widened per calibration.
- Input updates: today’s NWP runs materially revised the day-ahead hours for both turbines vs yesterday’s longer-lead run. Mean absolute change ≈0.056 (fraction of rated), mean signed change ≈ −0.048 for T1 and −0.047 for T2 — i.e., day-ahead outputs were reduced on average. Max single-hour revision ~0.15. Action: day-ahead forecast updated with 24-h lead NWP.

Operationally relevant details (for dispatchers)
- Expected energy: combined site EFLH over the 48 h ≈ 20.68 + 21.48 = 42.16 full-load-hours equivalent (this is the sum of each turbine’s model EFLH reported by the system).
- Shape and ramps:
  - Broad pattern: moderate production through the run with a peak evening hour on 2026-02-11 21:00 local (both turbines near their highest outputs). A trough around midday 2026-02-12 (both turbines) with outputs down to ~0.03–0.04 of rated.
  - Notable ramp: a down-ramp around 2026-02-11 06:00 local of ~−0.32 fraction of rated power (both turbines). This is the largest step the model flagged — consider scheduling reserve or monitoring around that time.
- Confidence and caveats:
  - Overall confidence: low. Large ensemble spread and recent small systematic over-forecast bias drive greater uncertainty. Bands have been widened (×1.10–×1.13) to account for this.
  - Directional change: today’s NWP reduced the day-ahead expected output vs yesterday; treat yesterday’s schedules as likely slightly high.
  - Use P10–P90 bands for reserve decisions when possible because deterministic point forecasts understate uncertainty in this situation.

Operator briefing (≤250 words)
Expected combined energy for the next 48 hours is ~42.2 full-load-hours equivalent. Expect moderate generation with highest outputs around 2026-02-11 21:00 local and lowest around 2026-02-12 12:00 local. The main operational issue is a sharp down-ramp at ~06:00 on 2026-02-11 of roughly −0.32 of rated power at each turbine; staff/reserve that window if you need firm capacity. Today’s NWP runs reduced the day-ahead forecast overall (mean ~−0.05 of rated) compared with yesterday’s run — previous schedules are likely optimistic. Confidence is low due to substantial ensemble spread and a recent tendency for the model to over-forecast (biases +0.031 T1, +0.015 T2); we widened uncertainty bands accordingly. Recommend holding upward reserve around the 06:00 ramp and using P10–P90 ranges for day-ahead reserve sizing.
