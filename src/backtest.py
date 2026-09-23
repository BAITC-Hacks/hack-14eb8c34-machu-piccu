"""Sequential replay: issue a forecast each day, exactly as it would have been.

Run:
    python -m src.backtest --policy rolling                       # February 2026 deliverable
    python -m src.backtest --policy strict                        # conservative variant
    python -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified --policy rolling

The default window produces the competition deliverable: a forecast issued on
31 January for local days 1-2 February, then a new one each day through
27 February. A window where production is known replays the same pipeline so
it can be scored honestly.

Each cycle sees only what existed at its issue moment -- archived weather at
the right lead, SCADA up to that instant, and the system's own verified errors.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from src import agent, config, metrics, pipeline


def run_backtest(
    start: str,
    end: str,
    label: str,
    policy: str = config.DEFAULT_POLICY,
    warmup_days: int = 30,
    verbose: bool = True,
) -> dict:
    """Replay every issue date in the window, one cycle per day.

    A warm-up replay runs first over the `warmup_days` immediately before the
    window. Its forecasts are discarded, but recording them populates the
    verification log, so the online calibration is already trained by the time
    the scored window begins -- matching a system that has been running for a
    while rather than one booted this morning.
    """
    label = f"{label}_{policy}"
    engine = pipeline.ForecastPipeline(mode="archive", policy=policy)
    wind_agent = agent.WindAgent(engine)

    if warmup_days:
        warm_start = pd.Timestamp(start) - pd.Timedelta(days=warmup_days)
        warm_end = pd.Timestamp(start) - pd.Timedelta(days=1)
        if verbose:
            print(f"  policy={policy}  warm-up {warm_start.date()}..{warm_end.date()} (populating verification log)")
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
        engine.record(result.run)          # closes the loop for tomorrow's calibration and revision check
        frame = result.run.combined()
        if not frame.empty:
            collected.append(frame)
        briefings.append({
            "issue_date": issue.strftime("%Y-%m-%d"),
            "issue_time_utc": engine.issue_moment(issue).isoformat(),
            "analysis": result.run.analysis,
            "revisions": result.run.revisions,
            "notes": result.run.notes,
        })
        if verbose and issue.day % 7 == 1:
            print(f"  issued {issue.date()} ...")

    if not collected:
        raise RuntimeError("no forecasts produced")

    forecasts = pd.concat(collected, ignore_index=True)
    forecasts = _attach_actuals(forecasts, engine)

    report = _score(forecasts, briefings, label, policy, verbose)
    _write(forecasts, briefings, report, label)
    return report


def _attach_actuals(forecasts: pd.DataFrame, engine: pipeline.ForecastPipeline) -> pd.DataFrame:
    """Join measured production where it exists (absent for the test month)."""
    parts = []
    for turbine_key, group in forecasts.groupby("turbine"):
        actual = engine.scada(turbine_key)[["time", "power", "is_anomaly_hour"]]
        parts.append(group.merge(actual, left_on="time_utc", right_on="time", how="left").drop(columns="time"))
    return pd.concat(parts, ignore_index=True)


def _revision_summary(briefings: list[dict]) -> dict:
    """How often, and by how much, fresher NWP runs moved the day-ahead forecast."""
    checks = [
        rev for b in briefings for rev in b.get("revisions", {}).values()
        if "mean_abs_change" in rev
    ]
    if not checks:
        return {"cycles_checked": 0}
    changes = np.array([c["mean_abs_change"] for c in checks])
    return {
        "cycles_checked": int(len(checks)),
        "cycles_with_material_change": int(sum(c["changed"] for c in checks)),
        "threshold": pipeline.REVISION_THRESHOLD,
        "mean_abs_change": round(float(changes.mean()), 4),
        "max_abs_change": round(float(max(c["max_abs_change"] for c in checks)), 4),
    }


def _score(forecasts: pd.DataFrame, briefings: list[dict], label: str, policy: str, verbose: bool) -> dict:
    """Score the day-ahead window, and measure what the daily refresh buys."""
    verified = forecasts.dropna(subset=["power"])
    lead_da = int(forecasts.loc[forecasts["horizon_day"] == 1, "nwp_lead_hours"].iloc[0])
    lead_d2 = int(forecasts.loc[forecasts["horizon_day"] == 2, "nwp_lead_hours"].iloc[0]) if (forecasts["horizon_day"] == 2).any() else None
    report: dict = {
        "label": label,
        "policy": policy,
        "nwp_lead_hours": {"day_ahead": lead_da, "day_2": lead_d2},
        "issue_dates": int(forecasts["issue_date"].nunique()),
        "forecast_hours": int(len(forecasts)),
        "verified_hours": int(len(verified)),
        "turbines": sorted(forecasts["turbine"].unique()),
        "input_updates": _revision_summary(briefings),
    }

    if verified.empty:
        report["note"] = (
            "No measured production available for this window, so accuracy cannot be "
            "scored here. See the 'verified' backtest for out-of-sample skill."
        )
        if verbose:
            print(f"\n{report['note']}")
        return report

    day_ahead = verified[verified["horizon_day"] == 1]
    report["overall"] = metrics.point_metrics(verified["power"], verified["forecast"])
    report["day_ahead"] = metrics.point_metrics(day_ahead["power"], day_ahead["forecast"])
    report["coverage"] = metrics.interval_coverage(verified["power"], verified["p10"], verified["p90"])
    report["by_nwp_lead"] = {
        f"{int(lead)}h": metrics.point_metrics(g["power"], g["forecast"])
        for lead, g in verified.groupby("nwp_lead_hours")
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
        for name, key in [("All hours (D+1 and D+2)", "overall"), (f"Day-ahead ({lead_da} h NWP lead)", "day_ahead")]:
            m = report[key]
            print(f"  {name:28s} MAE {m['mae']:.4f}  RMSE {m['rmse']:.4f}  "
                  f"bias {m['bias']:+.4f}  R2 {m['r2']:.3f}")
        cov = report["coverage"]
        print(f"  P10-P90 coverage {cov['coverage']:.3f} (target 0.80), width {cov['mean_width']:.3f}")
        rg = report["revision_gain"]
        if rg.get("hours"):
            print(f"\n  Daily refresh: re-forecasting the same hours one day closer cut MAE "
                  f"{rg['mae_day_2']:.4f} -> {rg['mae_day_ahead']:.4f} ({rg['improvement_pct']:.1f}% better, "
                  f"n={rg['hours']})")
        iu = report["input_updates"]
        if iu.get("cycles_checked"):
            print(f"  Input updates: {iu['cycles_with_material_change']} of {iu['cycles_checked']} cycles moved the "
                  f"day-ahead forecast by more than {iu['threshold']:.2f} (mean |change| {iu['mean_abs_change']:.3f})")
    return report


def _revision_gain(verified: pd.DataFrame) -> dict:
    """Quantify the value of recomputing when fresher inputs arrive.

    Every hour is forecast twice: first as day D+2, then again the next day as
    day D+1 from newer model runs. Comparing the two on identical hours is a
    direct measure of what the daily update cycle is worth.
    """
    early = verified[verified["horizon_day"] == 2][["turbine", "time_utc", "forecast", "power"]]
    late = verified[verified["horizon_day"] == 1][["turbine", "time_utc", "forecast"]]
    paired = early.merge(late, on=["turbine", "time_utc"], suffixes=("_early", "_late"))
    if paired.empty:
        return {"hours": 0}

    mae_early = float((paired["forecast_early"] - paired["power"]).abs().mean())
    mae_late = float((paired["forecast_late"] - paired["power"]).abs().mean())
    return {
        "hours": int(len(paired)),
        "mae_day_2": round(mae_early, 4),
        "mae_day_ahead": round(mae_late, 4),
        "improvement_pct": round(100 * (1 - mae_late / mae_early), 1) if mae_early else float("nan"),
        "mean_absolute_revision": round(float((paired["forecast_late"] - paired["forecast_early"]).abs().mean()), 4),
    }


def _write(forecasts: pd.DataFrame, briefings: list[dict], report: dict, label: str) -> None:
    out = config.OUTPUT_DIR
    columns = [c for c in pipeline.PUBLISH_COLUMNS if c in forecasts] + \
              [c for c in ("power",) if c in forecasts]

    forecasts[columns].to_csv(out / f"{label}_hourly_all_leads.csv", index=False)
    day_ahead = forecasts[forecasts["horizon_day"] == 1].sort_values(["turbine", "time_utc"])
    day_ahead[columns].to_csv(out / f"{label}_hourly_day_ahead.csv", index=False)

    _write_submission(forecasts, label)
    (out / f"{label}_report.json").write_text(json.dumps(report, indent=2, default=float))
    (out / f"{label}_daily_briefings.json").write_text(json.dumps(briefings, indent=2, default=str))
    print(f"\nWrote {label}_hourly_day_ahead.csv ({len(day_ahead)} rows) and 3 companion files to {out}")


def _write_submission(forecasts: pd.DataFrame, label: str) -> None:
    """Write the graded deliverable on the site's own local clock.

    Every target day is a local day, so the cycle issued on 31 January covers
    local 1 February in full; the 28 cycles 31 Jan .. 27 Feb tile the month
    exactly. Each hour is published once, from the freshest cycle that covered
    it (its day-ahead value); the D+2 values are kept in `_hourly_all_leads`.
    """
    day_ahead = forecasts[forecasts["horizon_day"] == 1].copy()
    local_day = day_ahead["time_local"].dt.normalize()
    window = (local_day >= pd.Timestamp(config.TEST_START)) & (local_day <= pd.Timestamp(config.TEST_END))
    if not window.any():
        return  # this replay does not cover the graded test window; nothing to submit

    submission = day_ahead[window].sort_values(["turbine", "time_local", "issue_date"])
    # Belt and braces: if two issues ever covered the same hour, keep the fresher.
    submission = submission.groupby(["turbine", "time_local"], as_index=False).last()

    columns = ["turbine", "time_local", "time_utc", "policy", "issue_date", "issue_time_local",
               "lead_hours", "nwp_lead_hours", "forecast", "p10", "p50", "p90"]
    submission = submission.sort_values(["turbine", "time_local"])[columns].copy()
    for column in ("time_local", "time_utc", "issue_time_local"):
        submission[column] = pd.to_datetime(submission[column]).dt.strftime("%Y-%m-%d %H:%M:%S")
    submission["issue_date"] = pd.to_datetime(submission["issue_date"]).dt.strftime("%Y-%m-%d")
    path = config.OUTPUT_DIR / f"{label}_submission_local.csv"
    submission.to_csv(path, index=False)

    expected = 24 * (pd.Timestamp(config.TEST_END) - pd.Timestamp(config.TEST_START)).days + 24
    per_turbine = submission.groupby("turbine").size()
    if (per_turbine < expected / 2).all():
        return  # only clipping the edge of the window -- not a real submission
    print(f"Submission: {path.name} - {len(submission)} rows; "
          f"per turbine {per_turbine.to_dict()} (expected {expected} each)")
    gaps = {t: int(expected - n) for t, n in per_turbine.items() if n != expected}
    if gaps:
        print(f"  WARNING incomplete hours: {gaps}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay daily forecast cycles")
    parser.add_argument("--start", default=config.FIRST_ISSUE_DATE)
    parser.add_argument("--end", default=config.LAST_ISSUE_DATE)
    parser.add_argument("--label", default="february_2026")
    parser.add_argument("--policy", choices=sorted(config.ASOF_POLICIES), default=config.DEFAULT_POLICY,
                        help="as-of policy: 'rolling' (24 h NWP lead, issue = end of day D) "
                             "or 'strict' (48 h NWP lead, issue = start of day D)")
    parser.add_argument("--warmup-days", type=int, default=30,
                        help="days replayed before the window to train the calibrator")
    args = parser.parse_args()
    run_backtest(args.start, args.end, args.label, policy=args.policy, warmup_days=args.warmup_days)


if __name__ == "__main__":
    main()
