Forecast published for issue 2026-02-05 (rolling). Files written: CSV and JSON (paths in system). Summary below.

Key model/weather signals
- Weather models (ECMWF, GFS, ICON) give similar mean 100 m wind (~8.4–8.8 m/s) but ensemble spread is non-negligible (mean spread ~1.8 m/s, max ~4.8 m/s). This drives forecast uncertainty; we flag the 48‑hr as low confidence.
- Latest NWP runs materially changed the day‑ahead compared with yesterday: the DA hours were revised (overlap 24 h), mean absolute change ~0.048 of rated power and a mean signed change slightly negative (~‑0.017), i.e. today’s input nudged the DA forecast down relative to yesterday. Max single‑hour change up to ~0.148 of rated power.

Recent forecast performance
- Last 14 days: model MAE ~0.16–0.17, RMSE ~0.21–0.22; small persistent positive bias (model tending to over‑forecast) of ~0.008–0.011 of rated power. P10–P90 calibration coverage ~82–86%. Bands have been scaled to account for the recent bias and spread.

Forecast highlights (per turbine)
- Energy equivalent full‑load hours (48 h): t1 = 22.04 h, t2 = 22.13 h.
- Day‑ahead energy (EFLH, the DA slab): t1 = 14.12 h, t2 = 14.16 h.
- Mean capacity factor over 48 h: t1 ~0.459, t2 ~0.461.
- Peak hourly output around local 2026-02-06 20:00 for both turbines; trough around local 2026-02-07 08:00.
- Hours near rated: 9 hours each; no hours below cut‑in.
- Max hourly outputs ~0.92–0.925 of rated power; min hourly outputs ~0.067–0.069 of rated power.
- Mean forecast uncertainty (band width) is elevated and bands were scaled (t1 band scale ~1.04, t2 ~1.14) due to recent over‑forecasting and ensemble spread.
- No modelled sharp ramp events flagged in the analysis.

Operator briefing (for reserve decision)
- Expected energy: roughly 14 full‑load hours in the day‑ahead window (per turbine), with mean capacity factor ~0.46. Treat this as a moderate‑production period.
- Shape: production rises into an evening peak (local ~20:00 on 2026‑02‑06) then falls to a low in the early morning (~08:00 on 2026‑02‑07). Nine hours around the peak approach rated output.
- Ramps/staffing: No large discrete ramp events were flagged by the forecast. However, the DA run today moved several hours downward (mean signed change ~‑0.017 of rated), and individual hour revisions of up to ~0.148 occurred vs yesterday’s DA — consider keeping some flexible reserve ready around the transition into the evening peak in case actual winds fall on the low side of ensembles.
- Confidence: LOW. Ensemble spread is moderate to high, and recent model bias shows slight over‑forecasting; bands have been widened accordingly. Use the P10–P90 band (provided in the published files) for reserve sizing rather than the point forecast when uncertainty matters.

Notes
- Forecast and uncertainty files are saved (CSV/JSON). If you want a dispatchable hourly table extracted or a P10/P90 summary for reserve scheduling, I can pull that next.
