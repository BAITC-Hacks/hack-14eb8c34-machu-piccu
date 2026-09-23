T1 / T2 forecast published for 2026-02-15. Files:
- outputs/cycles/forecast_20260215_rolling.csv
- outputs/cycles/analysis_20260215_rolling.json

Weather summary (both turbines)
- Mean wind at hub ~9.3 m/s (100 m), range 5.4–11.5 m/s over 48 h.
- Different NWP centers diverge: GFS ~10.2 m/s, ECMWF ~9.4 m/s, ICON ~8.3 m/s. Ensemble spread mean 1.47 m/s, max 3.04 m/s — model disagreement is material. Use P10–P90 band where critical.

Input update note (both turbines)
- Compared to the previous run (2026-02-14) the day‑ahead 24‑h curve has been revised with today's NWP runs. Overlapping 24 h: mean absolute change ~0.124 (fraction of rated power), mean signed change −0.044 (small downward shift), max abs change 0.255. Expect some hours shifted down vs yesterday’s day‑ahead.

Recent performance
- No verified forecast history in the past 14 days for either turbine (no bias corrections available). Publishing uncorrected model output; treat point values with caution.

Forecast analysis (both turbines; values from run)
- energy_48h_eflh = 28.66
- energy_day_ahead_24h_eflh = 16.76
- mean_capacity_factor = 0.597
- max_output = 0.812, min_output = 0.168
- peak hour local: 2026-02-16 14:00 (both turbines)
- trough hour local: 2026-02-17 09:00 (both turbines)
- reported ramp event: 2026-02-17 06:00, drop ≈ 0.27 (fraction of rated power)
- mean ensemble spread 1.47 m/s; confidence flagged low. No calibration bias samples available.

Operator briefing (for dispatchers)
- Expected energy per turbine:
  - energy_48h_eflh = 28.66
  - energy_day_ahead_24h_eflh = 16.76
- Shape of the day: winds build toward a peak around 2026-02-16 14:00 local (highest output ~0.81 p.u.), then decline with a notable trough around 2026-02-17 09:00 (lowest ~0.17 p.u.). The day‑ahead 24‑h bulk of production is in the first day (16.76 eflh).
- Ramps and staffing: expect a pronounced down‑ramp starting around 2026-02-17 06:00 local with a drop of about 0.27 p.u.; that is the main ramp to staff for and may require additional reserve between ~06:00–09:00 local on 2026-02-17.
- Confidence and recommendation: confidence is low due to limited verification history and material NWP spread (models differ by ~1–2 m/s, max ensemble spread 3 m/s). Also, today's NWP runs lowered the day‑ahead slightly versus yesterday. Hold conservative upward reserve against the morning drop on 2026-02-17 and monitor updates; if you need tight scheduling, use the P10–P90 band rather than the point estimate.

Files published: outputs/cycles/forecast_20260215_rolling.csv and outputs/cycles/analysis_20260215_rolling.json.
