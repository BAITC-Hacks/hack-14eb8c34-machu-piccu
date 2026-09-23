T1/T2 forecast published for 2026-02-21 (48 h). Files saved and CSV/JSON pointers included in the record.

Weather summary (both turbines)
- Mean 100 m wind ~6.8 m/s over next 48 h (models: ECMWF ~7.0, GFS ~7.8, ICON ~5.7).
- Max model wind ~12.2 m/s, min ~1.2 m/s.
- Ensemble spread moderate: mean spread ~2.1 m/s, peak spread ~5.0 m/s — models disagree at times, especially on timing and magnitude of the stronger wind pulse.

Forecast diagnostics and recent performance
- Forecast run completed at 2026-02-21T18:00 UTC and published. No verified hours in the last 14 days for either turbine, so no online bias correction applied; outputs are uncorrected model-based.
- Mean capacity factor (48 h): 0.407 for each turbine.
- Energy equivalent over 48 h: 19.52 full-load hours per turbine; day-ahead energy (first 24 h) = 10.26 FLH.
- Forecast range: max output 0.893, min 0.055 (fraction of rated power).
- Mean predictive band width ~0.50 (fraction of rated) and overall confidence flagged as LOW because of lack of verified history and moderate ensemble spread.

Input updates since yesterday
- check_input_updates: day-ahead portion was materially revised by today's NWP runs for both turbines.
  - Overlapping 24 h: mean absolute change ~0.197 (fraction of rated), mean signed change -0.022 (slight down), max single-hour change 0.503.
  - Action: day-ahead forecast revised with today's NWP runs. Net effect: mostly small downward adjustments on average but up to ~50% of rated power difference in a few hours where the models shifted the timing/intensity of the wind pulse.

Ramps and operational notes
- Peak hour local: 2026-02-22 15:00 local (both turbines) — highest output near that hour, but not at rated power.
- Trough hour local: 2026-02-22 04:00 local.
- No hours near rated; no hours below cut-in expected.
- No discrete ramp events flagged by the automated routine, but model ensemble spread indicates uncertainty in timing of the stronger pulse — short ramps (within ±0.5 p.u. over a few hours) are possible if the higher-wind model consensus verifies.

Operator briefing (under 250 words)
Expected energy: ~10.26 FLH for the next 24 h and ~19.52 FLH over 48 h per turbine (48-h mean capacity factor ~0.41). The day is characterized by low-to-moderate winds with a stronger pulse centered around the afternoon of 2026-02-22 (peak ~15:00 local). Overnight hours (around 04:00 local) are the weakest.

Ramps/staffing: No large sustained ramps flagged, but the models disagree on timing/intensity of the afternoon pulse (ensemble spread up to ~5 m/s). Expect possible short ramps of up to ~0.5 p.u. over a few hours if higher-wind runs verify; hold moderate upward reserve around the 15:00 local peak window and be ready to curtail if the higher pulse arrives earlier.

Confidence and why: Confidence is LOW. There are no recent verified forecasts for calibration, and ensemble spread shows meaningful disagreement between models. Today's NWP updates materially revised the day-ahead forecast (mean absolute change ~0.20 p.u.; max ~0.50 p.u.), so treat the day-ahead numbers as subject to change and monitor updates through next NWP cycle.

Files published: CSV and JSON saved to the forecast record.
