"""Tests a reviewer can run offline: the replay must never see the future.

    python -m pytest -q

Everything here reads the committed weather cache and the committed model, so
no network access and no API key are needed.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src import calibration, config, dataset, features, pipeline

ISSUES = ["2025-11-10", "2026-01-31", "2026-02-14", "2026-02-27"]


def test_issue_moment_semantics():
    d = pd.Timestamp("2026-01-31")
    tz = pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)
    assert features.issue_moment_utc(d, "rolling") == pd.Timestamp("2026-02-01") - tz   # end of day D
    assert features.issue_moment_utc(d, "strict") == pd.Timestamp("2026-01-31") - tz    # start of day D


@pytest.mark.parametrize("policy", sorted(config.ASOF_POLICIES))
@pytest.mark.parametrize("issue", ISSUES)
def test_no_nwp_output_from_after_the_issue_moment(policy, issue):
    """Every hour's NWP input was produced nwp_lead_hours before it; that instant must predate the issue moment."""
    engine = pipeline.ForecastPipeline(mode="archive", policy=policy)
    block = features.build_block(engine.fetch_weather("t1", pd.Timestamp(issue)), pd.Timestamp(issue), policy=policy)
    assert len(block) == 48, "a cycle covers two local days"
    produced_at = block["time"] - pd.to_timedelta(block["nwp_lead_hours"], unit="h")
    assert (produced_at <= block["issue_time_utc"]).all(), "NWP output newer than the issue moment leaked in"
    assert set(block["nwp_lead_hours"].unique()) == {24.0 * (1 + engine.offset), 24.0 * (2 + engine.offset)}


def test_blocks_are_local_days():
    engine = pipeline.ForecastPipeline(mode="archive", policy="rolling")
    issue = pd.Timestamp("2026-01-31")
    block = features.build_block(engine.fetch_weather("t1", issue), issue, policy="rolling")
    local = block["time"] + pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)
    assert local.iloc[0] == pd.Timestamp("2026-02-01 00:00") and local.iloc[-1] == pd.Timestamp("2026-02-02 23:00")
    assert (local.dt.normalize().value_counts() == 24).all()


def test_turbine_state_reads_only_before_the_issue_moment():
    times = pd.date_range("2026-01-30 00:00", "2026-02-01 23:00", freq="h")
    hist = pd.DataFrame({"time": times, "power": np.where(times < pd.Timestamp("2026-01-31 18:00"), 0.5, 0.0),
                         "is_anomaly_hour": False})
    state = dataset.persistence_state(hist, pd.Timestamp("2026-01-31 18:00"))
    assert state["last_power_24h"] == pytest.approx(0.5) and state["last_availability_24h"] == 1.0
    assert all(np.isnan(v) for v in dataset.persistence_state(hist, pd.Timestamp("2026-02-05")).values())


def test_calibration_uses_only_verified_hours_before_as_of():
    log = pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=400, freq="h"),
        "forecast": 0.6, "p10": 0.4, "p50": 0.6, "p90": 0.8, "power": 0.5,
    })
    cal = calibration.ForecastCalibrator()
    assert cal.fit(log, as_of=pd.Timestamp("2026-01-01")).bias_samples == 0
    state = cal.fit(log, as_of=pd.Timestamp("2026-01-10"))
    assert 0 < state.bias_samples <= 24 * 9 and state.bias == pytest.approx(0.1)


def test_error_grows_with_nwp_lead():
    summary = json.loads((config.ARTIFACT_DIR / "validation_summary.json").read_text())
    mae = {int(k): v["mae"] for k, v in summary["by_nwp_lead_hours"].items()}
    assert mae[24] < mae[48] < mae[72], "archived leads must behave like real forecasts, not relabelled analysis"


def test_february_replay_is_complete_and_coherent(tmp_path, monkeypatch):
    """Three cycles end to end, written to a temp dir: shape, coverage of the local days, ordered quantiles."""
    from src import backtest
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(config, "TEST_START", "2026-02-01")
    monkeypatch.setattr(config, "TEST_END", "2026-02-03")
    backtest.run_backtest("2026-01-31", "2026-02-02", "t", policy="rolling", warmup_days=2, verbose=False)
    sub = pd.read_csv(tmp_path / "t_rolling_submission_local.csv")
    assert len(sub) == 2 * 3 * 24 and sub["forecast"].between(0, 1).all()
    assert (sub["p10"] <= sub["p50"]).all() and (sub["p50"] <= sub["p90"]).all()
    assert set(sub["nwp_lead_hours"]) == {24.0}
    briefings = json.loads((tmp_path / "t_rolling_daily_briefings.json").read_text())
    assert all("mean_abs_change" in rev for b in briefings for rev in b["revisions"].values()), \
        "every cycle must measure how much fresher inputs moved the forecast"
