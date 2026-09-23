"""Sequential replay: issue a forecast each day, exactly as it would have been.

Run:
    python -m src.backtest --start 2026-01-31 --end 2026-02-27 --label february_2026
    python -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified

The first command produces the competition deliverable: a forecast issued on
31 January for 1-2 February, then a new one each day through the month. The
second replays a window where production is known, so the same pipeline can be
scored honestly.

Each cycle sees only what existed at its issue time -- archived weather at the
right lead, SCADA up to that instant, and the system's own verified errors.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from src import agent, config, metrics, pipeline


def run_backtest(
    start: str, end: str, label: str, warmup_days: int = 30, verbose: bool = True
) -> dict:
    """Replay every issue date in the window, one cycle per day.

    A warm-up replay runs first over the `warmup_days` immediately before the
    window. Its forecasts are discarded, but recording them populates the
    verification log, so the online calibration is already trained by the time
    the scored window begins -- matching a system that has been running for a
    while rather than one booted this morning.
    """
    engine = pipeline.ForecastPipeline(mode="archive")
    wind_agent = agent.WindAgent(engine)

    if warmup_days:
        warm_start = pd.Timestamp(start) - pd.Timedelta(days=warmup_days)
        warm_end = pd.Timestamp(start) - pd.Timedelta(days=1)
        if verbose:
            print(f"  warm-up {warm_start.date()}..{warm_end.date()} (populating verification log)")
        for issue in pd.date_range(warm_start, warm_end, freq="D"):
            engine.record(wind_agent.run_cycle(issue.strftime("%Y-%m-%d"), publish=False).run)
        if verbose:
            verified = int(engine.verification_log["power"].notna().sum())
            print(f"  warm-up complete: {verified} verified hours available to the calibrator")

    issues = pd.date_range(start, end, freq="D")
    collected: list[pd.DataFrame] = []
    briefings: list[dict] = []

    for issue in issues:
        result = wind_agent.run_cycle(issue.strftime("%Y-%m-%d"), publish=False)
        engine.record(result.run)          # closes the loop for tomorrow's calibration
        frame = result.run.combined()
        if not frame.empty:
            collected.append(frame)
        briefings.append({
            "issue_date": issue.strftime("%Y-%m-%d"),
            "analysis": result.run.analysis,
            "notes": result.run.notes,
        })
        if verbose and issue.day % 7 == 1:
            print(f"  issued {issue.date()} ...")

    if not collected:
        raise RuntimeError("no forecasts produced")

    forecasts = pd.concat(collected, ignore_index=True)
    forecasts = _attach_actuals(forecasts, engine)

    report = _score(forecasts, label, verbose)
    _write(forecasts, briefings, report, label)
    return report


def _attach_actuals(forecasts: pd.DataFrame, engine: pipeline.ForecastPipeline) -> pd.DataFrame:
    """Join measured production where it exists (absent for the test month)."""
    parts = []
    for turbine_key, group in forecasts.groupby("turbine"):
        actual = engine.scada(turbine_key)[["time", "power", "is_anomaly_hour"]]
        parts.append(group.merge(actual, left_on="time_utc", right_on="time", how="left").drop(columns="time"))
    return pd.concat(parts, ignore_index=True)


def _score(forecasts: pd.DataFrame, label: str, verbose: bool) -> dict:
    """Score the day-ahead window, and measure what the daily refresh buys."""
    verified = forecasts.dropna(subset=["power"])
    report: dict = {
        "label": label,
        "issue_dates": int(forecasts["issue_time_utc"].nunique()),
        "forecast_hours": int(len(forecasts)),
        "verified_hours": int(len(verified)),
        "turbines": sorted(forecasts["turbine"].unique()),
    }

    if verified.empty:
        report["note"] = (
            "No measured production available for this window, so accuracy cannot be "
            "scored here. See the 'verified' backtest for out-of-sample skill."
        )
        if verbose:
            print(f"\n{report['note']}")
        return report

    # Day-ahead (lead 24-47 h) is the window the brief asks to be judged on.
    day_ahead = verified[verified["lead_hours"] < 48]
    report["overall"] = metrics.point_metrics(verified["power"], verified["forecast"])
    report["day_ahead_24_47h"] = metrics.point_metrics(day_ahead["power"], day_ahead["forecast"])
    report["coverage"] = metrics.interval_coverage(verified["power"], verified["p10"], verified["p90"])
    report["by_lead_day"] = {
        ("24-47h" if int(lead) < 48 else "48-71h"): metrics.point_metrics(g["power"], g["forecast"])
        for lead, g in verified.groupby(verified["lead_hours"] // 24)
    }
    report["per_turbine"] = {
        key: metrics.point_metrics(g["power"], g["forecast"])
        for key, g in day_ahead.groupby("turbine")
    }
    report["revision_gain"] = _revision_gain(verified)

    if verbose:
        print(f"\n=== Backtest '{label}' ===")
        print(f"{report['issue_dates']} daily cycles, {report['forecast_hours']} forecast hours, "
              f"{report['verified_hours']} verified")
        for name, key in [("All leads (24-71 h)", "overall"), ("Day-ahead (24-47 h)", "day_ahead_24_47h")]:
            m = report[key]
            print(f"  {name:22s} MAE {m['mae']:.4f}  RMSE {m['rmse']:.4f}  "
                  f"bias {m['bias']:+.4f}  R2 {m['r2']:.3f}")
        cov = report["coverage"]
        print(f"  P10-P90 coverage {cov['coverage']:.3f} (target 0.80), width {cov['mean_width']:.3f}")
        rg = report["revision_gain"]
        if rg.get("hours"):
            print(f"\n  Daily refresh: re-forecasting the same hours one day closer cut MAE "
                  f"{rg['mae_48_71h']:.4f} -> {rg['mae_24_47h']:.4f} ({rg['improvement_pct']:.1f}% better, "
                  f"n={rg['hours']})")
    return report


def _revision_gain(verified: pd.DataFrame) -> dict:
    """Quantify the value of recomputing when fresher inputs arrive.

    Every hour is forecast twice: once at 48-71 h lead, then again the next day
    at 24-47 h from a newer model run. Comparing the two on identical hours is
    a direct measure of what the daily update cycle is worth.
    """
    early = verified[verified["lead_hours"] >= 48][["turbine", "time_utc", "forecast", "power"]]
    late = verified[verified["lead_hours"] < 48][["turbine", "time_utc", "forecast"]]
    paired = early.merge(late, on=["turbine", "time_utc"], suffixes=("_early", "_late"))
    if paired.empty:
        return {"hours": 0}

    mae_early = float((paired["forecast_early"] - paired["power"]).abs().mean())
    mae_late = float((paired["forecast_late"] - paired["power"]).abs().mean())
    return {
        "hours": int(len(paired)),
        "mae_48_71h": round(mae_early, 4),
        "mae_24_47h": round(mae_late, 4),
        "improvement_pct": round(100 * (1 - mae_late / mae_early), 1) if mae_early else float("nan"),
        "mean_absolute_revision": round(float((paired["forecast_late"] - paired["forecast_early"]).abs().mean()), 4),
    }


def _write(forecasts: pd.DataFrame, briefings: list[dict], report: dict, label: str) -> None:
    out = config.OUTPUT_DIR
    columns = [c for c in pipeline.PUBLISH_COLUMNS if c in forecasts] + \
              [c for c in ("power",) if c in forecasts]

    forecasts[columns].to_csv(out / f"{label}_hourly_all_leads.csv", index=False)
    day_ahead = forecasts[forecasts["lead_hours"] < 48].sort_values(["turbine", "time_utc"])
    day_ahead[columns].to_csv(out / f"{label}_hourly_day_ahead.csv", index=False)

    _write_submission(forecasts, label)
    (out / f"{label}_report.json").write_text(json.dumps(report, indent=2, default=float))
    (out / f"{label}_daily_briefings.json").write_text(json.dumps(briefings, indent=2, default=str))
    print(f"\nWrote {label}_hourly_day_ahead.csv ({len(day_ahead)} rows) and 3 companion files to {out}")


def _write_submission(forecasts: pd.DataFrame, label: str) -> None:
    """Write the graded deliverable on the site's own local clock.

    SCADA timestamps are local (UTC+6), so the requested 1-28 February window
    is a *local* one. Day-ahead slices from consecutive issue dates tile the
    UTC hours continuously, so selecting the local window from them keeps every
    hour at a genuine 24-47 h lead -- it just needs the cycle issued on
    30 January to supply local 1 February 00:00-05:00.
    """
    day_ahead = forecasts[forecasts["lead_hours"] < 48].copy()
    local_day = day_ahead["time_local"].dt.normalize()
    window = (local_day >= pd.Timestamp(config.TEST_START)) & (local_day <= pd.Timestamp(config.TEST_END))
    submission = day_ahead[window].sort_values(["turbine", "time_local", "issue_time_utc"])
    # Belt and braces: if two issues ever covered the same hour, keep the fresher.
    submission = submission.groupby(["turbine", "time_local"], as_index=False).last()

    columns = ["turbine", "time_local", "time_utc", "issue_time_utc", "lead_hours",
               "forecast", "p10", "p50", "p90"]
    submission = submission.sort_values(["turbine", "time_local"])[columns]
    path = config.OUTPUT_DIR / f"{label}_submission_local.csv"
    submission.to_csv(path, index=False)

    expected = 24 * (pd.Timestamp(config.TEST_END) - pd.Timestamp(config.TEST_START)).days + 24
    per_turbine = submission.groupby("turbine").size()
    print(f"Submission: {path.name} - {len(submission)} rows; "
          f"per turbine {per_turbine.to_dict()} (expected {expected} each)")
    gaps = {t: int(expected - n) for t, n in per_turbine.items() if n != expected}
    if gaps:
        print(f"  WARNING incomplete hours: {gaps}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay daily forecast cycles")
    parser.add_argument("--start", default=config.FIRST_ISSUE_DATE)
    parser.add_argument("--end", default="2026-02-27")
    parser.add_argument("--label", default="february_2026")
    parser.add_argument("--warmup-days", type=int, default=30,
                        help="days replayed before the window to train the calibrator")
    args = parser.parse_args()
    run_backtest(args.start, args.end, args.label, warmup_days=args.warmup_days)


if __name__ == "__main__":
    main()
