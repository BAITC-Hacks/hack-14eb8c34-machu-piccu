Turbine expected energy (per turbine)
- energy_48h_eflh: 20.46
- energy_day_ahead_24h_eflh: 17.5

Summary of the forecast and inputs
- Published the 48-hour hourly forecast (files: outputs/cycles/forecast_20260227_rolling.csv and outputs/cycles/analysis_20260227_rolling.json).
- Model peak output hour: 2026-02-28 11:00 (local). Trough hour: 2026-03-01 18:00 (local).
- Mean modeled wind speed at 100 m: 7.5 m/s; mean ensemble spread 2.19 m/s (max spread 3.47 m/s). Per-model mean winds diverge (ECMWF ~6.36, ICON ~6.67, GFS ~9.45 m/s) — the models disagree notably, which increases uncertainty.
- Calibration: no verified forecast history yet; output is the uncorrected model run.

Input updates (day‑ahead change)
- For both turbines the day‑ahead hours were materially revised by today's NWP runs compared with the previous issue:
  - overlapping hours: 24
  - mean absolute change: 0.0543 (fraction of rated power)
  - mean signed change: +0.0384 (net increase)
  - maximum absolute change: 0.1948
  - action: day‑ahead forecast revised with today's NWP runs
- In plain terms: the day‑ahead curve was nudged higher on average; some hours changed substantially (up to ~0.195 of rated).

Performance and confidence
- No verified forecast hours in the recent 14-day window for either turbine, so no bias correction available.
- Confidence: low. Reasons: lack of verification history, significant ensemble spread and inter-model differences (GFS higher), and the calibration flag shows uncorrected model output.

Operational implications for dispatchers
- Expect roughly 17.5 eflh in the next 24 h and 20.46 eflh over 48 h per turbine.
- Generation is moderate through the day with a peak around late morning on 2026-02-28; no modelled fast ramps flagged by the forecast (no ramp events), but individual hour changes of up to ~0.195 of rated occurred between model runs — maintain some contingency.
- Recommendation: hold modest upward reserve given low confidence and model disagreement; be ready for hour-to-hour changes particularly late tonight through tomorrow morning when models diverge most.
