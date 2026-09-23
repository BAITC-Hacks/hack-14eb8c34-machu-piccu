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
# variables expose, for every target hour T, what the weather models predicted
# N*24 hours before T. That is what lets us replay a forecast with only the
# information that existed at the time.
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

# --- As-of policy -----------------------------------------------------------
# `previous_dayN` is a *fixed offset*: the value for target hour T comes from
# the model run that was N*24 h old at T, not from one 00Z run of day D. The
# policy therefore fixes which N serves each target day, and with it what
# "the forecast issued on day D" means. Target days are *local* days.
#
#   rolling  issue moment = end of local day D (00:00 local of D+1).
#            Local day D+1 <- previous_day1, day D+2 <- previous_day2.
#            Every hour uses NWP output produced 24 h (48 h) before that hour,
#            i.e. runs initialised during day D (D-1). Nothing produced after
#            the issue moment is used. This is the operational "24 h ahead"
#            product and the primary deliverable.
#   strict   issue moment = start of local day D (00:00 local of D).
#            Local day D+1 <- previous_day2, day D+2 <- previous_day3.
#            Nothing initialised on day D itself is used; one full day of
#            freshness is given up. The conservative reading of the brief.
ASOF_POLICIES: dict[str, int] = {"rolling": 0, "strict": 1}  # NWP lead offset, days
DEFAULT_POLICY = "rolling"

# NWP leads the model is trained on (24, 48 and 72 h), so one model serves
# both policies: lead_day is a model feature.
LEAD_DAYS_TRAINED: tuple[int, ...] = (1, 2, 3)
HORIZON_DAYS = 2  # target days per cycle: D+1 (day-ahead) and D+2
# Last day of the archived weather window that training and replays share
# (TEST_END plus the longest trained lead plus one day of padding).
ARCHIVE_END = "2026-03-04"

# --- Time windows ---------------------------------------------------------
SCADA_START = "2023-03-11"
SCADA_END = "2026-01-31"
TEST_START = "2026-02-01"
TEST_END = "2026-02-28"
# Per the brief: the first forecast is issued on 31 Jan 2026 for the next
# 24-48 h (local days 1-2 February); the last one on 27 Feb for 28-29 Feb.
FIRST_ISSUE_DATE = "2026-01-31"
LAST_ISSUE_DATE = "2026-02-27"

# Site timezone. Established empirically: cross-correlating SCADA against NWP
# at 10-minute resolution puts wind speed's peak at 6.00 h and temperature's
# at 6.83 h (the extra lag is nacelle-sensor thermal inertia), stable across
# both turbines and across Kazakhstan's 2024 UTC+6 -> UTC+5 switch. The logger
# evidently kept a fixed UTC+6 clock, so we treat the offset as constant.
SITE_TZ_OFFSET_HOURS = 6

# --- Modelling ------------------------------------------------------------
TARGET = "power"
QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)
HORIZON_HOURS = 24 * HORIZON_DAYS
