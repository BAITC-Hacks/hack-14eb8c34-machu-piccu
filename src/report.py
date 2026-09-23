"""Figures for the README, drawn from the replay outputs.

Run:  python -m src.report            (after the 'verified' backtests exist)

Two figures:
  reports/forecast_overview.png   a fortnight of January 2026: measured power
                                  against the day-ahead forecast and its P10-P90 band
  reports/error_vs_lead.png       MAE by NWP lead for both policies, next to the
                                  baselines every forecast has to beat
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import config

WINDOW = ("2026-01-12", "2026-01-26")


def forecast_overview(policy: str = config.DEFAULT_POLICY) -> None:
    path = config.OUTPUT_DIR / f"verified_{policy}_hourly_day_ahead.csv"
    frame = pd.read_csv(path, parse_dates=["time_local"])
    lead = int(frame["nwp_lead_hours"].iloc[0])

    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    for ax, turbine in zip(axes, config.TURBINES):
        g = frame[(frame["turbine"] == turbine)].set_index("time_local").loc[WINDOW[0]:WINDOW[1]]
        ax.fill_between(g.index, g["p10"], g["p90"], color="#9ecae1", alpha=0.6, label="P10-P90")
        ax.plot(g.index, g["forecast"], color="#08519c", lw=1.4, label=f"day-ahead forecast ({lead} h NWP lead)")
        ax.plot(g.index, g["power"], color="#252525", lw=1.0, alpha=0.85, label="measured")
        mae = (g["forecast"] - g["power"]).abs().mean()
        ax.set_title(f"{config.TURBINES[turbine].name}: {WINDOW[0]} .. {WINDOW[1]} (local time), MAE {mae:.3f}", loc="left", fontsize=11)
        ax.set_ylim(0, 1.02)
        ax.set_ylabel("normalised power")
        ax.grid(alpha=0.3)
    axes[0].legend(loc="upper right", ncol=3, fontsize=9)
    axes[1].set_xlabel("local time (UTC+6)")
    fig.suptitle(f"WindAgent replay, policy '{policy}': forecast issued every day for the following local day", fontsize=12)
    fig.tight_layout()
    fig.savefig(config.REPORT_DIR / "forecast_overview.png", dpi=110)
    plt.close(fig)


def error_vs_lead() -> None:
    val = json.loads((config.ARTIFACT_DIR / "validation_summary.json").read_text())
    rows = []
    for policy in config.ASOF_POLICIES:
        path = config.OUTPUT_DIR / f"verified_{policy}_report.json"
        if not path.exists():
            continue
        rep = json.loads(path.read_text())
        for lead, m in rep["by_nwp_lead"].items():
            rows.append({"policy": policy, "lead_h": int(lead.rstrip("h")), "mae": m["mae"]})
    table = pd.DataFrame(rows)
    ct = val["comparison_table"]["mae"]

    fig, ax = plt.subplots(figsize=(9, 5))
    for policy, marker, dy in (("rolling", "o", 9), ("strict", "s", -14)):
        g = table[table["policy"] == policy].sort_values("lead_h")
        if g.empty:
            continue
        ax.plot(g["lead_h"], g["mae"], marker=marker, lw=2, label=f"WindAgent, policy '{policy}'")
        for _, r in g.iterrows():
            ax.annotate(f"{policy[0]}: {r['mae']:.3f}", (r["lead_h"], r["mae"]), textcoords="offset points",
                        xytext=(0, dy), ha="center", fontsize=9)
    for name, label, color in (("power_curve", "power curve on NWP wind, no ML", "#6a51a3"),
                               ("climatology", "climatology", "#969696"),
                               ("persistence", "persistence (yesterday repeated)", "#cb181d")):
        ax.axhline(ct[name], ls="--", color=color, lw=1.2, label=f"{label}: {ct[name]:.3f}")
    ax.set_xlabel("NWP lead behind the forecast, hours")
    ax.set_ylabel("MAE, fraction of rated power (122-day replay)")
    ax.set_xticks([24, 48, 72])
    ax.set_ylim(0, 0.4)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title("Error grows with NWP lead; every policy beats the baselines", loc="left")
    fig.tight_layout()
    fig.savefig(config.REPORT_DIR / "error_vs_lead.png", dpi=110)
    plt.close(fig)


def main() -> None:
    forecast_overview()
    error_vs_lead()
    print(f"Figures written to {config.REPORT_DIR}")


if __name__ == "__main__":
    main()
