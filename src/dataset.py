"""Assemble supervised training data by replaying historical forecast issues.

Every training row is produced the same way an operational forecast would be:
take the model runs from day D, read off their prediction for a specific hour
of day D+1 or D+2, attach only information that existed at 00Z on day D, and
pair it with the production that was actually measured later.

Weather inputs are a genuine multi-model ensemble. For each variable we keep
every model's own value *and* the ensemble consensus; for wind speed we also
keep the spread, because how much ECMWF, GFS and ICON disagree is the clearest
advance warning that a forecast is about to go wrong.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config, features, scada, weather

LEAD_DAYS = (1, 2)
DIRECTION_VARS = ("wind_direction_10m", "wind_direction_100m")


def circular_mean(frame: pd.DataFrame) -> pd.Series:
    """Mean of compass bearings, which cannot be averaged arithmetically.

    Naively averaging 350 deg and 10 deg gives 180 -- exactly backwards. Going
    through the unit circle gives 0, which is correct.
    """
    radians = np.deg2rad(frame.to_numpy(dtype=float))
    sin_mean = np.nanmean(np.sin(radians), axis=1)
    cos_mean = np.nanmean(np.cos(radians), axis=1)
    return pd.Series(np.rad2deg(np.arctan2(sin_mean, cos_mean)) % 360, index=frame.index)


def build_ensemble_frame(per_model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge each model's forecast into one wide frame plus consensus columns.

    Output carries, for every variable: `<model>__<var>` per member, and `<var>`
    as the ensemble consensus that downstream physics code consumes.
    """
    models = list(per_model)
    wide = per_model[models[0]][["time"]].copy()

    for model_name in models:
        source = per_model[model_name].set_index("time")
        for variable in config.WEATHER_VARIABLES:
            wide[f"{model_name}__{variable}"] = (
                wide["time"].map(source[variable]) if variable in source else np.nan
            )

    for variable in config.WEATHER_VARIABLES:
        member_cols = [f"{m}__{variable}" for m in models]
        members = wide[member_cols]
        wide[variable] = (
            circular_mean(members) if variable in DIRECTION_VARS else members.mean(axis=1)
        )

    # Spread statistics on hub-height wind: the ensemble's own uncertainty.
    hub = wide[[f"{m}__wind_speed_100m" for m in models]]
    wide["ws100_ens_std"] = hub.std(axis=1)
    wide["ws100_ens_min"] = hub.min(axis=1)
    wide["ws100_ens_max"] = hub.max(axis=1)
    wide["ws100_ens_range"] = wide["ws100_ens_max"] - wide["ws100_ens_min"]
    return wide


def load_weather_by_lead(
    turbine_key: str,
    start_date: str,
    end_date: str,
    lead_days: tuple[int, ...] = LEAD_DAYS,
) -> dict[int, pd.DataFrame]:
    """Download (or read from cache) the multi-model ensemble at each lead."""
    turbine = config.TURBINES[turbine_key]
    out: dict[int, pd.DataFrame] = {}
    for lead in lead_days:
        per_model = {
            name: weather.fetch_archive_chunked(
                turbine.latitude, turbine.longitude, start_date, end_date,
                lead_days=lead, nwp_model=name,
            )
            for name in config.NWP_MODELS
        }
        out[lead] = build_ensemble_frame(per_model)
    return out


def scada_utc(turbine_key: str) -> pd.DataFrame:
    """SCADA hourly production, re-expressed on the UTC clock."""
    hourly = scada.load_hourly(turbine_key)
    hourly["time"] = hourly["time"] - pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)
    return hourly


def persistence_state(scada_hist: pd.DataFrame, issue_time: pd.Timestamp) -> dict:
    """Summarise turbine behaviour over the window ending at `issue_time`.

    Strictly causal: nothing at or after the issue instant is read. Availability
    is the share of the last day for which the machine reported healthy output,
    which is the model's only handle on an outage that is still ongoing.
    """
    recent = scada_hist[
        (scada_hist["time"] < issue_time)
        & (scada_hist["time"] >= issue_time - pd.Timedelta(hours=24))
    ]
    if recent.empty:
        return {"last_power_3h": np.nan, "last_power_24h": np.nan, "last_availability_24h": np.nan}

    last3 = recent[recent["time"] >= issue_time - pd.Timedelta(hours=3)]
    healthy = recent["power"].notna() & ~recent["is_anomaly_hour"].astype(bool)
    return {
        "last_power_3h": last3["power"].mean() if not last3.empty else np.nan,
        "last_power_24h": recent["power"].mean(),
        "last_availability_24h": healthy.sum() / 24.0,
    }


def build_dataset(
    turbine_key: str,
    issue_start: str,
    issue_end: str,
    weather_by_lead: dict[int, pd.DataFrame] | None = None,
    scada_hist: pd.DataFrame | None = None,
    with_target: bool = True,
) -> pd.DataFrame:
    """Replay every issue date in the window into a flat feature table."""
    if weather_by_lead is None:
        pad_end = (pd.Timestamp(issue_end) + pd.Timedelta(days=3)).strftime("%Y-%m-%d")
        weather_by_lead = load_weather_by_lead(turbine_key, issue_start, pad_end)
    if scada_hist is None:
        scada_hist = scada_utc(turbine_key)

    rows: list[pd.DataFrame] = []
    for issue in pd.date_range(issue_start, issue_end, freq="D"):
        block = features.build_block(weather_by_lead, issue)
        if block.empty or block["wind_speed_100m"].isna().all():
            continue
        state = persistence_state(scada_hist, issue)
        rows.append(features.build_features(block, power_curve=None, persistence=state))

    if not rows:
        return pd.DataFrame()

    frame = pd.concat(rows, ignore_index=True)
    frame["turbine"] = turbine_key

    if with_target:
        frame = frame.merge(
            scada_hist[
                # ws_scada is the measured nacelle wind. It is a *label-side*
                # column used only to fit the NWP debiasing model on training
                # rows; it is never a model feature.
                [
                    "time", "power", "ws_scada", "is_anomaly_hour",
                    "is_curtailed_hour", "is_stuck_hour", "n_samples",
                ]
            ],
            on="time",
            how="left",
        )
    return frame


def fit_effective_power_curve(train: pd.DataFrame) -> pd.DataFrame:
    """Fit the NWP-to-power curve on training rows only.

    Deliberately fitted against the *forecast* wind speed rather than the
    nacelle anemometer, so the curve absorbs the NWP's own speed bias instead
    of assuming the two agree.
    """
    clean = train[train["power"].notna() & ~train["is_anomaly_hour"].astype(bool)]
    return scada.fit_power_curve(clean["ws_density_corrected"], clean["power"])


def attach_power_curve_prior(frame: pd.DataFrame, curve: pd.DataFrame) -> pd.DataFrame:
    """Add power-curve priors, per ensemble member and in consensus.

    Pushing each member through the power curve before comparing them measures
    disagreement in the units we actually care about. Two models differing by
    2 m/s matters enormously near the curve's knee and not at all above rated,
    and the wind-speed spread alone cannot tell those cases apart.
    """
    out = frame.copy()
    out["pc_prior"] = scada.apply_power_curve(curve, out["ws_density_corrected"])
    out["pc_prior_roll3"] = out.groupby("issue_time")["pc_prior"].transform(
        lambda s: s.rolling(3, center=True, min_periods=1).mean()
    )

    member_priors = []
    for model_name in config.NWP_MODELS:
        column = f"{model_name}__wind_speed_100m"
        if column not in out:
            continue
        name = f"pc_prior__{model_name}"
        out[name] = scada.apply_power_curve(curve, out[column])
        member_priors.append(name)

    if member_priors:
        priors = out[member_priors]
        out["pc_prior_std"] = priors.std(axis=1)
        out["pc_prior_range"] = priors.max(axis=1) - priors.min(axis=1)
    return out
