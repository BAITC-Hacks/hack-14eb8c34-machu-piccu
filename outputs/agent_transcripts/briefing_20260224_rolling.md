Forecast published for issue 2026-02-24. Files:
- /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/forecast_20260224_rolling.csv
- /Users/admin/Desktop/hack-14eb8c34-machu-piccu/outputs/analysis_20260224_rolling.json

Turbine-level summary (interpreting model output; units: fraction of rated power unless otherwise stated)

T1 and T2 (forecasts are effectively identical)
- Period: next 48 hours from issue time 2026-02-24 18:00 UTC
- Mean wind speed at 100 m: 6.62 m/s (per-model means: ECMWF 6.78, GFS 6.98, ICON 6.10)
- Ensemble spread (mean): 1.79 m/s, max spread 4.44 m/s — models disagree moderately, so expect higher uncertainty; rely on P10–P90 bands for dispatch decisions.
- Mean capacity factor: 0.394
- Day-ahead energy (first 24 h) equivalent full-load hours: 3.12
- 48-h energy equivalent full-load hours: 18.9
- Peak hour (local): 2026-02-26 04:00 (max output 0.822)
- Trough hour (local): 2026-02-25 00:00 (min output 0.048)
- Hours near rated power: 0
- Hours below cut-in: 0
- Mean ensemble band width (power): ~0.498 (T1) / 0.494 (T2)
- Confidence: low — no verified forecast history to calibrate bias or bands.

Input updates since yesterday
- check_input_updates: Day-ahead (first 24 h) revised materially by today's NWP runs for both turbines.
  - Mean absolute change over overlapping day-ahead hours: 0.250 fraction of rated power.
  - Mean signed change: -0.250 (forecast decreased vs yesterday).
  - Max single-hour change: 0.665 downwards.
  - Action: day-ahead forecast revised with today's NWP; use the new runs (lead reduced from 48 to 24 h).

Recent performance
- No verified forecast hours in the last 14 days for either turbine — model output published uncorrected (no bias correction available).

Operator briefing (under 250 words)
- Expected energy: 3.12 full-load hours in the coming day (day-ahead); 18.9 FLH over the 48-hour window. Mean capacity ~39% of rated per turbine.
- Shape: low overnight output through local midnight (trough ~0.048 p.u.), rising to a single broad peak around local 04:00 on 2026-02-26 (peak ~0.82 p.u.). No sustained periods near rated power; output mostly in the low-to-mid capacity range.
- Ramps/staffing: today’s day-ahead was revised down significantly vs yesterday (mean -0.25 p.u., up to -0.665 p.u. in an hour). Although no modelled discrete ramp events are flagged, the large input changes indicate potential for notable hour-to-hour variability in the first 24 hours — hold some upward reserve and be ready to accept lower generation than yesterday expected.
- Confidence and reason: Low confidence. Ensemble spread and inter-model differences are moderate (spread up to 4.44 m/s), and there is no verification history to calibrate bias or uncertainty bands. Rely on published P10–P90 bands (files contain full hourly bands) rather than the single expected value for reserve decisions.

Files published to the paths above contain full hourly values, P10–P90 bands, and metadata.
