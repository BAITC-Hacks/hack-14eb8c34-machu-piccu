Forecast published for issue 2026-02-19 (48 h) — files: outputs/cycles/forecast_20260219_rolling.csv and outputs/cycles/analysis_20260219_rolling.json.

Summary (both turbines t1 and t2)
- energy_48h_eflh: 20.82
- energy_day_ahead_24h_eflh: 7.77
- Mean capacity factor: 0.434; mean wind speed ~7.94 m/s.
- Point forecast peak hour local: 2026-02-21 13:00; trough: 2026-02-20 17:00.
- Max forecast output: 0.708; min: 0.093.
- Ramp events: none flagged by the model.
- Confidence: low (ensemble spread mean 2.26 m/s, max spread 6.31 m/s).
- Recent performance: no verified forecast hours in the last 14 days (no bias correction available).

Input updates (day-ahead)
- Today's NWP runs materially revised the day-ahead (overlapping 24 h) compared with yesterday: mean_abs_change 0.1125 (fraction of rated power), max_abs_change 0.2726. Mean_signed_change 0.0141 indicates a very small net upward move on average, but individual hours moved up to +0.2726 or down similarly. Action: day-ahead forecast revised with today's NWP runs.

Operational briefing for dispatch (under 250 words)
Expected energy per turbine: energy_48h_eflh = 20.82; energy_day_ahead_24h_eflh = 7.77. The day begins with moderate winds (~7–8 m/s), a dip toward the late first-day afternoon (trough at 2026-02-20 17:00), then builds to a peak early on the second day (peak 2026-02-21 13:00). No model-identified fast ramps, but the ensemble spread is relatively large (mean 2.26 m/s, max 6.31 m/s), so uncertain hour-to-hour swings are possible—some hours changed by up to ~0.27 of rated power between successive NWP updates. Because there is no verified forecast history (no bias correction), treat the absolute point values with caution and rely more on the P10–P90 band (ensemble spread) for reserve planning. Recommendation: hold moderate upward and downward reserve through the day-ahead window to cover potential +/- shortfalls around the trough and the afternoon-to-next-day increase; staffing not required for scheduled curtailment or immediate manual intervention unless real-time SCADA shows larger-than-expected deviations.

Published files are available at outputs/cycles/forecast_20260219_rolling.csv and outputs/cycles/analysis_20260219_rolling.json.
