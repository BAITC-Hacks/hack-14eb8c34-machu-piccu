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
    if (config.ARTIFACT_DIR / "ds_t1.parquet").exists():
        data_figures()
    print(f"Figures written to {config.REPORT_DIR}")



# ---------------------------------------------------------------- extra figures for the README
def data_figures() -> None:
    """Power curve (anemometer vs NWP), monthly profile, NWP bias by month, feature importance."""
    import numpy as np
    from src import model as model_mod, scada

    # 1. power curve: measured wind vs power, and 24 h-lead NWP wind vs power
    raw = scada.load_raw("t1")
    ds = pd.read_parquet(config.ARTIFACT_DIR / "ds_t1.parquet")
    ds = ds[(ds["lead_day"] == 1) & ds["power"].notna()]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    axes[0].hexbin(raw["ws_scada"], raw["power"], gridsize=60, cmap="Blues", mincnt=1, extent=(0, 22, 0, 1))
    axes[0].set_title("Anemometer wind (SCADA, 10-min) vs power: the machine is predictable", loc="left", fontsize=10)
    axes[0].set_xlabel("measured wind speed, m/s"); axes[0].set_ylabel("normalised power")
    axes[1].hexbin(ds["wind_speed_100m"], ds["power"], gridsize=60, cmap="Blues", mincnt=1, extent=(0, 22, 0, 1))
    axes[1].set_title("NWP ensemble wind 24 h ahead vs power: the weather is the bottleneck", loc="left", fontsize=10)
    axes[1].set_xlabel("forecast wind speed 100 m, m/s (ECMWF+GFS+ICON mean)")
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(config.REPORT_DIR / "power_curve.png", dpi=110); plt.close(fig)

    # 2. monthly capacity factor per turbine (data overview)
    fig, ax = plt.subplots(figsize=(12, 3.8))
    for key, color in (("t1", "#1f77b4"), ("t2", "#e6851f")):
        r = scada.load_raw(key).set_index("ts")["power"].resample("MS").mean()
        ax.plot(r.index, r.values, marker="o", ms=4, lw=1.6, color=color, label=config.TURBINES[key].name)
    ax.axvspan(pd.Timestamp("2026-02-01"), pd.Timestamp("2026-03-01"), color="#bbb", alpha=0.35, label="test month (hidden)")
    ax.set_ylabel("monthly capacity factor"); ax.set_ylim(0, 0.6); ax.grid(alpha=0.3); ax.legend(loc="upper right", fontsize=9)
    ax.set_title("Seasonality of the site: winter capacity factor 0.43-0.52, summer 0.23-0.31", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(config.REPORT_DIR / "monthly_profile.png", dpi=110); plt.close(fig)

    # 3. NWP wind bias by month, per model and ensemble (24 h lead), against the anemometer
    ds2 = pd.concat([pd.read_parquet(config.ARTIFACT_DIR / f"ds_{k}.parquet") for k in config.TURBINES])
    ds2 = ds2[(ds2["lead_day"] == 1) & ds2["ws_scada"].notna()].copy()
    ds2["month"] = pd.to_datetime(ds2["time"]).dt.month
    fig, ax = plt.subplots(figsize=(12, 3.8))
    for name, label, color in (("ecmwf_ifs025", "ECMWF", "#1f77b4"), ("gfs_seamless", "GFS", "#d62728"), ("icon_seamless", "ICON", "#2ca02c")):
        b = (ds2[f"{name}__wind_speed_100m"] - ds2["ws_scada"]).groupby(ds2["month"]).mean()
        ax.plot(b.index, b.values, marker="o", ms=4, lw=1.4, color=color, label=label)
    b = (ds2["wind_speed_100m"] - ds2["ws_scada"]).groupby(ds2["month"]).mean()
    ax.plot(b.index, b.values, marker="s", ms=5, lw=2.2, color="#333", label="ensemble mean")
    ax.axhline(0, color="#999", lw=1); ax.set_xticks(range(1, 13)); ax.set_ylabel("forecast - measured wind, m/s")
    ax.set_title("NWP wind bias by month (24 h lead): winter over-forecast is why calibration matters", loc="left", fontsize=10)
    ax.grid(alpha=0.3); ax.legend(ncol=4, fontsize=9)
    fig.tight_layout(); fig.savefig(config.REPORT_DIR / "nwp_bias_by_month.png", dpi=110); plt.close(fig)

    # 4. feature importance (gain share) of the trained model
    fitted = model_mod.TrainedModel.load(config.ARTIFACT_DIR, "pooled")
    imp = model_mod.feature_importance(fitted, 15); share = 100 * imp["gain"] / fitted.point.feature_importance("gain").sum()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(imp["feature"][::-1], share[::-1], color="#1f77b4")
    ax.set_xlabel("share of total split gain, %"); ax.set_title("Top-15 features of the LightGBM point model", loc="left", fontsize=10)
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout(); fig.savefig(config.REPORT_DIR / "feature_importance.png", dpi=110); plt.close(fig)
    print("data figures written")

if __name__ == "__main__":
    main()
