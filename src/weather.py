"""Open-Meteo client for archived and live weather forecasts.

Two axes matter here.

*Lead time.* The historical-forecast archive exposes two flavours of each
variable: `wind_speed_100m` is the most recent run's estimate (~0-24 h lead),
while `wind_speed_100m_previous_dayN` is what the run from N days earlier
predicted. Only the second is an honest answer to "what did we know back then",
and every backtest forecast in this project is built from it.

*Model.* ECMWF, GFS and ICON are independent numerical weather models. They
disagree, often sharply, and that disagreement is the single most useful
uncertainty signal available -- so we fetch each one separately rather than
accepting a pre-blended best guess.
"""
from __future__ import annotations

import hashlib
import time as _time
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from src import config

_SESSION = requests.Session()
KMH_TO_MS = 1 / 3.6


class WeatherFetchError(RuntimeError):
    """Raised when Open-Meteo cannot satisfy a request after retries."""


def _cache_path(url: str, params: dict) -> Path:
    payload = url + repr(sorted((k, str(v)) for k, v in params.items()))
    digest = hashlib.sha256(payload.encode()).hexdigest()[:20]
    return config.CACHE_DIR / f"om_{digest}.parquet"


def _request(url: str, params: dict, retries: int = 4) -> dict:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            response = _SESSION.get(url, params=params, timeout=90)
            if response.status_code == 429:
                _time.sleep(10 * (attempt + 1))
                continue
            response.raise_for_status()
            payload = response.json()
            if "reason" in payload:
                raise WeatherFetchError(payload["reason"])
            return payload
        except Exception as exc:  # noqa: BLE001 - surfaced after the retry budget
            last = exc
            _time.sleep(3 * (attempt + 1))
    raise WeatherFetchError(f"Open-Meteo request failed: {last}")


def _tidy(payload: dict, variables: Iterable[str], suffix: str) -> pd.DataFrame:
    """Reshape an Open-Meteo response, normalising units and missing variables.

    Not every model carries every variable (ECMWF has no 10 m gust field, for
    example). Missing ones become all-NaN columns, which LightGBM handles
    natively -- better than silently dropping a model from the ensemble.
    """
    hourly = payload["hourly"]
    frame = pd.DataFrame({"time": pd.to_datetime(hourly["time"])})
    for var in variables:
        values = hourly.get(f"{var}{suffix}")
        frame[var] = pd.Series(values, dtype="float64") if values is not None else float("nan")
    for column in frame.columns:
        if column.startswith(("wind_speed", "wind_gusts")):
            frame[column] = frame[column] * KMH_TO_MS
    return frame


def fetch_archive(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    lead_days: int | None = 1,
    nwp_model: str = "best_match",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Fetch one model's archived forecast, valid between two dates.

    `lead_days=N` returns the forecast issued N days before each valid time.
    `lead_days=None` returns the analysis-grade best estimate, used only for
    diagnostics -- never as a model input in the backtest.
    """
    suffix = "" if lead_days is None else f"_previous_day{lead_days}"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(f"{v}{suffix}" for v in config.WEATHER_VARIABLES),
        "models": nwp_model,
        "timezone": "GMT",
    }
    cache_file = _cache_path(config.HISTORICAL_FORECAST_URL, params)
    if use_cache and cache_file.exists():
        return pd.read_parquet(cache_file)

    frame = _tidy(_request(config.HISTORICAL_FORECAST_URL, params), config.WEATHER_VARIABLES, suffix)
    frame.to_parquet(cache_file, index=False)
    return frame


def fetch_archive_chunked(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    lead_days: int | None = 1,
    nwp_model: str = "best_match",
    chunk_months: int = 6,
) -> pd.DataFrame:
    """Fetch a long date range in chunks, so one failure costs little."""
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    edges = [start, *pd.date_range(start, end, freq=f"{chunk_months}MS"), end + pd.Timedelta(days=1)]
    edges = sorted({e for e in edges if start <= e <= end + pd.Timedelta(days=1)})

    parts = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        hi_inclusive = hi - pd.Timedelta(days=1)
        if hi_inclusive < lo:
            continue
        parts.append(
            fetch_archive(
                latitude, longitude,
                lo.strftime("%Y-%m-%d"), hi_inclusive.strftime("%Y-%m-%d"),
                lead_days=lead_days, nwp_model=nwp_model,
            )
        )
    frame = pd.concat(parts, ignore_index=True).drop_duplicates("time").sort_values("time")
    return frame.reset_index(drop=True)


def fetch_live(
    latitude: float,
    longitude: float,
    forecast_days: int = 3,
    nwp_model: str = "best_match",
) -> pd.DataFrame:
    """Fetch the *current* operational forecast.

    This is the path the agent takes when it runs today rather than replaying
    February 2026, so the same model can serve a live control room.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(config.WEATHER_VARIABLES),
        "forecast_days": forecast_days,
        "models": nwp_model,
        "timezone": "GMT",
    }
    return _tidy(_request(config.LIVE_FORECAST_URL, params), config.WEATHER_VARIABLES, "")
