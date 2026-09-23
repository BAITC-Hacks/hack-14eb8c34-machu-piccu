"""Central configuration for the WindAgent forecasting system."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset"
CACHE_DIR = ROOT / "cache"
ARTIFACT_DIR = ROOT / "artifacts"
OUTPUT_DIR = ROOT / "outputs"
REPORT_DIR = ROOT / "reports"

for _d in (CACHE_DIR, ARTIFACT_DIR, OUTPUT_DIR, REPORT_DIR):
    _d.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Turbine:
    """A single turbine: its coordinates and its SCADA source file."""

    key: str
    name: str
    latitude: float
    longitude: float
    csv_glob: str


TURBINES: dict[str, Turbine] = {
    "t1": Turbine("t1", "Turbine 1", 43.645150, 78.535604, "*turbine 1.csv"),
    "t2": Turbine("t2", "Turbine 2", 43.643198, 78.538828, "*turbine 2.csv"),
}

# --- Weather source -------------------------------------------------------
# Open-Meteo "historical forecast" archive. The `_previous_dayN` suffixed
# variables expose what each model run actually predicted N days earlier,
# which is what lets us replay a forecast exactly as it was available then.
HISTORICAL_FORECAST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
LIVE_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Independent numerical weather models with lead-time archives at this site.
# Their disagreement is itself a feature: ensemble spread is the best available
# predictor of how wrong the forecast is about to be.
NWP_MODELS: tuple[str, ...] = ("ecmwf_ifs025", "gfs_seamless", "icon_seamless")

WEATHER_VARIABLES: tuple[str, ...] = (
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_direction_10m",
    "wind_direction_100m",
    "wind_gusts_10m",
    "temperature_2m",
    "surface_pressure",
    "relative_humidity_2m",
)

# The lead-time archive (`previous_dayN`) begins in early 2024; anything before
# that only has analysis-grade data, which would not be an honest replay.
LEAD_ARCHIVE_START = "2024-03-01"

# --- Time windows ---------------------------------------------------------
SCADA_START = "2023-03-11"
SCADA_END = "2026-01-31"
TEST_START = "2026-02-01"
TEST_END = "2026-02-28"
# First forecast is issued on 31 Jan 2026 for the 24-48h window, per the brief.
FIRST_ISSUE_DATE = "2026-01-31"

# Site timezone. Established empirically in notebooks/01_alignment: cross-correlating
# SCADA against NWP at 10-minute resolution puts wind speed's peak at 6.00 h and
# temperature's at 6.83 h (the extra lag is nacelle-sensor thermal inertia), stable
# across both turbines and across Kazakhstan's 2024 UTC+6 -> UTC+5 switch. The
# logger evidently kept a fixed UTC+6 clock, so we treat the offset as constant.
SITE_TZ_OFFSET_HOURS = 6

# --- Modelling ------------------------------------------------------------
TARGET = "power"
QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)
HORIZON_HOURS = 48
