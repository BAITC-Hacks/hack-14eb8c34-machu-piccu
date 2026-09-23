Turbine 1 / T1 — weather summary (48 h)
- Mean wind at hub ~8.5 m/s, range 2.0–15.2 m/s.
- NWP model means: GFS highest (~9.6 m/s), ECMWF ~8.1 m/s, ICON ~7.9 m/s.
- Ensemble spread moderate (mean 2.47 m/s, peak spread ~7.1 m/s) — model disagreement during some hours, so rely on P10–P90 band for uncertainty.

Turbine 2 / T2 — weather summary (48 h)
- Same as T1 (identical site exposure): mean 8.5 m/s, 2.0–15.2 m/s.
- Same per-model differences. Ensemble spread similar.

Input updates since yesterday (day-ahead hours)
- Both turbines: Today's NWP runs materially revised the day‑ahead (0–24 h) forecast vs yesterday's longer‑lead run.
- Overlapping 24 h: mean absolute change ~0.103 (fraction of rated power), mean signed change +0.0345 (net small upward tweak), max hourly change 0.26.
- Action: Day‑ahead forecast has been updated using current NWP runs (lead reduced from 48 to 24 h).

Recent performance
- No verified forecast hours in the last 14 days for either turbine — no calibration bias adjustments available.

Forecast analysis and notes
- The model run produced identical hourly outputs for both turbines (outputs published).
- Key statistics (from run): 48‑hour energy per turbine 24.67 eflh; day‑ahead 24 h energy 13.88 eflh.
- Mean capacity factor ~0.514; peak hourly power 0.904 pu at 2026-02-22 16:00 local; trough 0.053 pu at 2026-02-22 07:00 local.
- Hours near rated: 1; hours below cut‑in: 0.
- Confidence: low — ensemble spread and lack of calibration history increase uncertainty.
- No sharp ramp events flagged by the model, but max abs update 0.26 pu implies some hours changed substantially in the day‑ahead update.

Operator briefing (for dispatchers, under 250 words)
- Expected energy per turbine: energy_48h_eflh = 24.67; energy_day_ahead_24h_eflh = 13.88.
- Shape of the day: Moderate winds through both days, with a low in the morning of 22 Feb (~0.053 pu at 07:00) and a single high around 16:00 on 22 Feb (~0.904 pu). Overall mean capacity ~0.51.
- Ramps / staffing: No model‑flagged rapid ramps, but the day‑ahead update included individual hourly changes up to 0.26 pu. Watch the early morning trough and ramp into the afternoon peak on 22 Feb; hold some flexible reserve for potential upward ramp into the peak.
- Confidence and reason: Low confidence. Ensemble spread is moderate to high in parts of the window and we have no recent verification to correct model bias. Use the P10–P90 range when planning margins and treat the point forecast as indicative rather than exact.

Files published: outputs/cycles/forecast_20260220_rolling.csv and outputs/cycles/analysis_20260220_rolling.json.
