"""Occupancy estimation.

Wraps the neural network behind a small service layer that adds caching,
input gathering and graceful fallbacks so a missing model or a failing
weather lookup never takes the API down.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date as Date, datetime
from threading import Lock
from time import monotonic

from src.db import Database, Venue, hour_to_label
from src.network import BluetoothData, InputData, Network, TimeData, WeatherData

log = logging.getLogger(__name__)

DEFAULT_MODEL = "Library"
DEFAULT_WEATHER = "Overcast"
WEATHER_TTL_SECONDS = 15 * 60
OPENING_HOUR = 8
CLOSING_HOUR = 20

BUSY_RATIO = 0.75
MID_RATIO = 0.4

_networks: dict[str, Network | None] = {}
_networks_lock = Lock()
_weather_cache: dict[str, tuple[float, WeatherData]] = {}
_weather_lock = Lock()


def status_from_ratio(ratio: float) -> str:
    """Bucket an occupancy ratio into the labels the frontend renders."""
    if ratio >= BUSY_RATIO:
        return "busy"
    if ratio >= MID_RATIO:
        return "mid"
    return "empty"


def current_hour_label(now: datetime | None = None) -> str | None:
    """Hour label for `now`, or None when the venue is outside opening hours."""
    hour = (now or datetime.now()).hour
    if OPENING_HOUR <= hour <= CLOSING_HOUR:
        return hour_to_label(hour)
    return None


def _get_network(venue_name: str) -> Network | None:
    """Load (and memoise) the model for a venue, falling back to the default."""
    with _networks_lock:
        if venue_name in _networks:
            return _networks[venue_name]

        network: Network | None = None
        for candidate in (venue_name, DEFAULT_MODEL):
            try:
                network = Network(candidate)
                break
            except (OSError, RuntimeError) as exc:
                log.warning("Could not load model %r: %s", candidate, exc)

        _networks[venue_name] = network
        return network


def _get_weather(location: str) -> WeatherData:
    """Current weather for a location, cached and with a safe default."""
    now = monotonic()
    with _weather_lock:
        cached = _weather_cache.get(location)
        if cached and now - cached[0] < WEATHER_TTL_SECONDS:
            return cached[1]

    try:
        weather = WeatherData(location)
    except Exception as exc:  # network/provider failures must not break the API
        log.warning("Weather lookup failed for %r: %s", location, exc)
        return WeatherData(DEFAULT_WEATHER)

    with _weather_lock:
        _weather_cache[location] = (now, weather)
    return weather


def _last_known_count(db: Database, venue_name: str) -> int | None:
    """Most recent stored reading for a venue, used when the model is absent."""
    today = Date.today()
    for entry in reversed(db.history.get_day(venue_name, today)):
        return entry.data
    return None


def estimate_occupancy(
    db: Database,
    venue: Venue,
    devices: int = 0,
    now: datetime | None = None,
) -> int:
    """Estimate the current head count for a venue, clamped to its capacity."""
    network = _get_network(venue.name)

    if network is None:
        fallback = _last_known_count(db, venue.name)
        log.info(
            "[estimate] venue=%r devices=%d no model, fallback=%s",
            venue.name,
            devices,
            fallback,
        )
        return 0 if fallback is None else fallback

    weather = _get_weather(venue.location)
    inputs = InputData(
        BluetoothData(devices),
        weather,
        TimeData(now),
        #normal_capacity=max(venue.max_capacity, 1),
    )

    try:
        guess = network.guess(inputs)
    except Exception as exc:
        log.exception("Model inference failed for %r: %s", venue.name, exc)
        fallback = _last_known_count(db, venue.name)
        return 0 if fallback is None else fallback

    clamped = max(0, min(guess, venue.max_capacity))
    log.info(
        "[estimate] venue=%r devices=%d weather=%s capacity=%d "
        "guess=%d clamped=%d",
        venue.name,
        devices,
        weather.weather,
        venue.max_capacity,
        guess,
        clamped,
    )
    return clamped


def record_estimate(
    db: Database, venue_name: str, count: int, now: datetime | None = None
) -> None:
    """Persist an estimate, skipping readings taken outside opening hours."""
    label = current_hour_label(now)
    if label is None:
        return
    db.history.add(venue_name, (now or datetime.now()).date(), label, count)
