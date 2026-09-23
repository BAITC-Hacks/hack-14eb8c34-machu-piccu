"""Feature engineering: turn a raw NWP forecast into model inputs.

The unit of work is a *forecast block*: the hourly rows a forecast cycle of
day D covers, i.e. the local days D+1 and D+2. Which archived NWP lead serves
each target day is decided by the as-of policy (see `config.ASOF_POLICIES`).
Building features per block rather than on one long concatenated series
matters: a lag or rolling feature computed across a block boundary would mix
in NWP output that did not exist when the forecast was issued.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config

R_DRY = 287.058  # J/(kg K)
R_VAPOUR = 461.495
RHO_STANDARD = 1.225  # kg/m3, IEC reference air density

# NWP lag/lead offsets (hours) used for ramp awareness.
NEIGHBOUR_OFFSETS = (-3, -2, -1, 1, 2, 3)


# --------------------------------------------------------------------------
# Block assembly
# --------------------------------------------------------------------------
def issue_moment_utc(issue_date, policy: str = config.DEFAULT_POLICY) -> pd.Timestamp:
    """The instant a cycle-D forecast is declared issued, in UTC.

    `rolling`: end of local day D (00:00 local of D+1). `strict`: start of
    local day D (00:00 local of D). Everything the cycle reads -- NWP output,
    SCADA state, its own verified errors -- must predate this instant.
    """
    local_midnight = pd.Timestamp(issue_date).normalize()
    if policy == "rolling":
        local_midnight += pd.Timedelta(days=1)
    return local_midnight - pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)


def build_block(
    weather_by_lead: dict[int, pd.DataFrame],
    issue_date: pd.Timestamp,
    horizon_days: int = config.HORIZON_DAYS,
    policy: str = config.DEFAULT_POLICY,
) -> pd.DataFrame:
    """Assemble the forecast block of cycle date D under an as-of policy.

    Target days are *local* days D+1 .. D+horizon. Under `rolling` local day
    D+k is read from `previous_day{k}`; under `strict` from `previous_day{k+1}`.
    Each row records `horizon_day` (which target day it belongs to) and
    `lead_day` (how many days old its NWP input is -- a model feature).
    """
    if policy not in config.ASOF_POLICIES:
        raise ValueError(f"unknown as-of policy {policy!r}; choose from {list(config.ASOF_POLICIES)}")
    offset = config.ASOF_POLICIES[policy]
    issue = pd.Timestamp(issue_date).normalize()
    tz = pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)

    parts: list[pd.DataFrame] = []
    for day in range(1, horizon_days + 1):
        lead = day + offset
        source = weather_by_lead.get(lead)
        if source is None:
            continue
        start_utc = issue + pd.Timedelta(days=day) - tz   # local midnight of D+day
        window = source[
            (source["time"] >= start_utc)
            & (source["time"] < start_utc + pd.Timedelta(days=1))
        ].copy()
        if window.empty:
            continue
        window["horizon_day"] = day
        window["lead_day"] = lead
        parts.append(window)

    if not parts:
        return pd.DataFrame()

    block = pd.concat(parts, ignore_index=True).sort_values("time").reset_index(drop=True)
    block["issue_time"] = issue                      # cycle date D (local calendar day)
    block["policy"] = policy
    block["issue_time_utc"] = issue_moment_utc(issue, policy)
    # Hours from the declared issue moment to the target hour (the horizon),
    # and the age of the NWP output behind each hour (the honest lead).
    block["lead_hours"] = (block["time"] - block["issue_time_utc"]).dt.total_seconds() / 3600.0
    block["nwp_lead_hours"] = 24.0 * block["lead_day"]
    return block


# --------------------------------------------------------------------------
# Physics
# --------------------------------------------------------------------------
def air_density(temperature_c: pd.Series, pressure_hpa: pd.Series, rh_pct: pd.Series) -> pd.Series:
    """Moist-air density from temperature, station pressure and humidity.

    Power scales linearly with density, so a cold February day genuinely yields
    more power than a hot July day at identical wind speed -- roughly 15% more
    across this site's temperature range.
    """
    t_kelvin = temperature_c + 273.15
    pressure_pa = pressure_hpa * 100.0
    # Magnus formula for saturation vapour pressure (Pa).
    sat_vp = 610.94 * np.exp(17.625 * temperature_c / (temperature_c + 243.04))
    vapour_pa = (rh_pct.clip(0, 100) / 100.0) * sat_vp
    dry_pa = pressure_pa - vapour_pa
    return dry_pa / (R_DRY * t_kelvin) + vapour_pa / (R_VAPOUR * t_kelvin)


def physical_features(block: pd.DataFrame) -> pd.DataFrame:
    """Derive the wind-physics features a power model actually needs."""
    out = block.copy()

    ws10 = out["wind_speed_10m"].clip(lower=0.1)
    ws100 = out["wind_speed_100m"].clip(lower=0.0)

    # Wind shear: the power-law exponent between the two reported heights.
    # A stable nocturnal boundary layer gives a high exponent and a very
    # different hub-height wind than a well-mixed afternoon.
    out["shear_alpha"] = (np.log(ws100.clip(lower=0.1)) - np.log(ws10)) / np.log(100 / 10)
    out["shear_alpha"] = out["shear_alpha"].clip(-0.5, 1.0)

    rho = air_density(out["temperature_2m"], out["surface_pressure"], out["relative_humidity_2m"])
    out["air_density"] = rho
    # IEC 61400-12 density normalisation: an equivalent standard-density wind speed.
    out["ws_density_corrected"] = ws100 * (rho / RHO_STANDARD) ** (1 / 3)

    out["ws100_sq"] = ws100**2
    out["ws100_cube"] = ws100**3
    out["wind_power_density"] = 0.5 * rho * ws100**3

    # Gust factor is a usable proxy for turbulence intensity, which suppresses
    # the power curve around the knee.
    out["gust_factor"] = (out["wind_gusts_10m"] / ws10).clip(0, 5)
    out["gust_excess"] = (out["wind_gusts_10m"] - out["wind_speed_10m"]).clip(lower=0)

    for height in (10, 100):
        radians = np.deg2rad(out[f"wind_direction_{height}m"])
        out[f"dir{height}_sin"] = np.sin(radians)
        out[f"dir{height}_cos"] = np.cos(radians)

    # Directional veer between the two heights, wrapped to +/-180 deg.
    veer = out["wind_direction_100m"] - out["wind_direction_10m"]
    out["veer"] = (veer + 180) % 360 - 180

    return out


def neighbour_features(block: pd.DataFrame) -> pd.DataFrame:
    """Ramp and local-variability features, computed strictly within a block."""
    out = block.copy()
    ws = out["wind_speed_100m"]

    for offset in NEIGHBOUR_OFFSETS:
        out[f"ws100_off{offset:+d}"] = ws.shift(-offset)

    out["ws100_ramp_1h"] = ws.diff()
    out["ws100_ramp_3h"] = ws.diff(3)
    for window in (3, 6, 12):
        out[f"ws100_roll_mean_{window}"] = ws.rolling(window, center=True, min_periods=1).mean()
        out[f"ws100_roll_std_{window}"] = ws.rolling(window, center=True, min_periods=1).std()
    out["ws100_block_mean"] = ws.mean()
    out["ws100_block_std"] = ws.std()

    neighbour_cols = [c for c in out.columns if c.startswith("ws100_off")]
    out[neighbour_cols] = out[neighbour_cols].bfill().ffill()
    return out.fillna({c: 0.0 for c in out.columns if c.startswith("ws100_roll_std")})


def calendar_features(block: pd.DataFrame) -> pd.DataFrame:
    """Time-of-day and season, encoded cyclically in *local* site time."""
    out = block.copy()
    local = out["time"] + pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)
    hour = local.dt.hour + local.dt.minute / 60
    doy = local.dt.dayofyear

    out["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    out["local_hour"] = hour
    return out


def build_features(
    block: pd.DataFrame,
    power_curve: pd.DataFrame | None = None,
    persistence: dict | None = None,
) -> pd.DataFrame:
    """Full feature pipeline for one forecast block."""
    from src import scada  # local import keeps the module import graph acyclic

    out = calendar_features(neighbour_features(physical_features(block)))

    if power_curve is not None:
        # A physics-informed prior: what the site's own fitted power curve says
        # about this density-corrected wind speed. The model learns corrections
        # on top of it rather than rediscovering the curve from scratch.
        out["pc_prior"] = scada.apply_power_curve(power_curve, out["ws_density_corrected"])
        out["pc_prior_roll3"] = out["pc_prior"].rolling(3, center=True, min_periods=1).mean()

    # State known at issue time: how the turbine was actually behaving. This is
    # what lets the model carry an ongoing outage forward instead of promising
    # power from a machine that is down.
    if persistence is not None:
        out["last_power_3h"] = persistence.get("last_power_3h", np.nan)
        out["last_power_24h"] = persistence.get("last_power_24h", np.nan)
        out["last_availability_24h"] = persistence.get("last_availability_24h", np.nan)
        out["hours_since_obs"] = out["lead_hours"]

    return out


FEATURE_COLUMNS: list[str] = [
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_gusts_10m",
    "temperature_2m",
    "surface_pressure",
    "relative_humidity_2m",
    "shear_alpha",
    "air_density",
    "ws_density_corrected",
    "ws100_sq",
    "ws100_cube",
    "wind_power_density",
    "gust_factor",
    "gust_excess",
    "dir10_sin",
    "dir10_cos",
    "dir100_sin",
    "dir100_cos",
    "veer",
    *[f"ws100_off{o:+d}" for o in NEIGHBOUR_OFFSETS],
    "ws100_ramp_1h",
    "ws100_ramp_3h",
    *[f"ws100_roll_{stat}_{w}" for w in (3, 6, 12) for stat in ("mean", "std")],
    "ws100_block_mean",
    "ws100_block_std",
    "hour_sin",
    "hour_cos",
    "doy_sin",
    "doy_cos",
    "local_hour",
    "pc_prior",
    "pc_prior_roll3",
    "last_power_3h",
    "last_power_24h",
    "last_availability_24h",
    # Ensemble disagreement, in wind-speed units and in power units.
    "ws100_ens_std",
    "ws100_ens_min",
    "ws100_ens_max",
    "ws100_ens_range",
    "pc_prior_std",
    "pc_prior_range",
    # Each member's own hub-height wind and its implied power, so the model can
    # learn that a given model is reliable in some regimes and not in others.
    *[f"{m}__wind_speed_100m" for m in config.NWP_MODELS],
    *[f"{m}__wind_speed_10m" for m in config.NWP_MODELS],
    *[f"pc_prior__{m}" for m in config.NWP_MODELS],
]
