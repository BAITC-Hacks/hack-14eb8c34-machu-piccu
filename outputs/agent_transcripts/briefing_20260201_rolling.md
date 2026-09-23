Turbine energy (exact from model)
- T1: energy_48h_eflh = 18.35 ; energy_day_ahead_24h_eflh = 13.53
- T2: energy_48h_eflh = 18.23 ; energy_day_ahead_24h_eflh = 13.47

What changed with today's inputs
- check_input_updates: both turbines — day-ahead hours were revised with today's NWP runs (previous lead 48h → current 24h). The overlapping 24h mean absolute change ~0.069 and mean signed change slightly positive (~+0.0087), with max hour change ~0.225. In short: the day‑ahead profile shifted materially in places; the revision direction is mixed but on average slightly higher.

Weather and uncertainty
- Mean wind ~7.96 m/s, model spread moderate (mean ensemble spread 2.35 m/s, max spread up to 4.75 m/s). Per‑model means disagree (ECMWF ~8.02, GFS ~9.16, ICON ~6.72) → ensemble disagreement is the main uncertainty. Confidence flagged as low.

Recent forecast performance
- Last 14 days: both turbines show a small persistent over‑forecast bias (t1 bias ≈ 0.0289–0.0328 range; t2 bias ≈ 0.0313–0.0353 depending on the report). MAE and RMSE indicate moderate errors. Bands have been scaled up in calibration.

Notable ramps and schedule impacts
- Significant downward ramp for both turbines at 2026-02-02 18:00 local: delta ≈ -0.342 of rated power. Peak output around 2026-02-02 14:00 local; trough around 2026-02-03 13:00 local.
- No expected hours at or above rated; no cut‑in issues flagged.

Dispatcher guidance (reserve & staffing)
- Hold increased downward reserve around 2026-02-02 18:00 local for the ~0.34 p.u. drop. Because ensemble spread and model bias are non‑trivial and confidence is low, plan conservative upward and downward reserves for the afternoon‑evening transition on 2026-02-02.
- Use the reported day‑ahead energy numbers above (13.53 and 13.47 eflh) for scheduling; expect uncertainty around those values given ensemble disagreement and modest over‑forecast bias.

Forecast files published: outputs/cycles/forecast_20260201_rolling.csv and analysis_20260201_rolling.json.
