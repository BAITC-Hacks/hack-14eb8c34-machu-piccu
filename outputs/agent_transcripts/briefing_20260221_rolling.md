Forecast published: outputs/cycles/forecast_20260221_rolling.csv and outputs/cycles/analysis_20260221_rolling.json

Weather summary (both turbines)
- Mean 100 m AGL wind ~6.84 m/s over the 48 h, min 1.16 m/s, max 12.15 m/s.
- Models disagree: per-model means ecmwf 7.0, gfs 7.79, icon 5.73 m/s. Ensemble spread mean 2.07 m/s, max spread 4.99 m/s → notable uncertainty in timing and magnitude of winds.

Recent performance
- No verified forecast hours in the past 14 days for either turbine (no calibration samples yet).

Input updates (day‑ahead)
- Today's NWP runs materially revised the day‑ahead relative to yesterday: overlapping 24h mean absolute change 0.1965 (fraction of rated power), mean signed change −0.0219 (slight net downward), max abs change 0.5029. Action: day‑ahead forecast revised with today's NWP runs.

Forecast highlights (both turbines; values from model output)
- energy_48h_eflh: 19.52
- energy_day_ahead_24h_eflh: 10.26
- mean_capacity_factor: 0.407
- peak hour local: 2026-02-22 15:00:00 (max_output 0.893)
- trough hour local: 2026-02-22 04:00:00 (min_output 0.055)
- hours near rated: 0; hours below cut-in: 0
- mean ensemble band width ~0.50 (low confidence)
- Calibration: none (no verified history yet) — publishing uncorrected model output.

Operator briefing (for reserve decisions)
Expected energy per turbine: 48h = 19.52 eflh; day‑ahead 24h = 10.26 eflh. Shape: diurnal low overnight (~04:00 trough), rising to a mid‑afternoon peak (~15:00 local) on 22 Feb (single broad daytime maximum). No discrete fast ramps flagged by the model run, but ensemble disagreement implies timing uncertainty of the daytime peak. Confidence: low — reasons: no verification/calibration samples yet and substantial model spread (up to ~5 m/s). Day‑ahead was revised with today’s NWP (mean absolute change ~0.197 fraction of rated power; slight net decrease). Recommendation: hold moderate upward reserve around the expected afternoon peak window to cover model timing error and possible stronger winds; overnight reserve requirements lower but maintain flexibility in case of model underprediction.
