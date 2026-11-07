"""HTTP routes for venue data.

Mounted at `/api/venues`, which is what the Vite dev server proxies.
"""

from __future__ import annotations

from datetime import date as Date, timedelta

from flask import Blueprint, abort, jsonify, request

from src.db import HOURS, Database, HistoricalEntry, Venue

from .estimator import estimate_occupancy, record_estimate, status_from_ratio
from .live import LIVE_VENUE, is_live_venue, live_counter

venues_bp = Blueprint("venues", __name__, url_prefix="/api/venues")

MAX_HISTORY_DAYS = 30


def _ratio(count: int, max_capacity: int) -> float:
    return count / max_capacity if max_capacity > 0 else 0.0


def _venue_payload(venue: Venue, capacity: int) -> dict:
    payload = {
        "name": venue.name,
        "location": venue.location,
        "capacity": capacity,
        "max_capacity": venue.max_capacity,
        "status": status_from_ratio(_ratio(capacity, venue.max_capacity)),
        "live": is_live_venue(venue.name),
    }
    if payload["live"]:
        payload["scanning"] = live_counter.available
    return payload


def _entry_payload(entry: HistoricalEntry) -> dict:
    return {
        "date": entry.date.isoformat(),
        "hour": entry.hour,
        "capacity": entry.data,
    }


def _int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        abort(400, description=f"{name!r} must be an integer")
    return max(minimum, min(value, maximum))


def _require_venue(db: Database, venue_name: str) -> Venue:
    if is_live_venue(venue_name):
        return LIVE_VENUE
    venue = db.venues.get(venue_name)
    if venue is None:
        abort(404, description=f"Unknown venue: {venue_name!r}")
    return venue


@venues_bp.get("")
@venues_bp.get("/")
def list_venues():
    """All venues with their latest known occupancy and status.

    The LIVE venue is listed first and always re-estimated from the
    current Bluetooth device count.
    """
    today = Date.today()
    with Database() as db:
        live_capacity = estimate_occupancy(
            db, LIVE_VENUE, devices=live_counter.count
        )
        payload = [_venue_payload(LIVE_VENUE, live_capacity)]

        for venue in db.venues.all():
            if is_live_venue(venue.name):
                continue
            readings = db.history.get_day(venue.name, today)
            capacity = readings[-1].data if readings else 0
            payload.append(_venue_payload(venue, capacity))
    return jsonify(payload)


@venues_bp.get("/<venue_name>")
def get_venue(venue_name: str):
    """A fresh occupancy estimate for a single venue.

    For the LIVE venue the device count comes from the running Bluetooth
    scanner; otherwise it is taken from the `devices` query parameter.
    """
    with Database() as db:
        venue = _require_venue(db, venue_name)
        devices = (
            live_counter.count
            if is_live_venue(venue.name)
            else _int_arg("devices", default=0, minimum=0, maximum=10_000)
        )
        capacity = estimate_occupancy(db, venue, devices=devices)
        record_estimate(db, venue.name, capacity)
        return jsonify(_venue_payload(venue, capacity))


@venues_bp.get("/<venue_name>/history")
def get_venue_history(venue_name: str):
    """Stored readings for a venue over the last `days` days (default 7)."""
    days = _int_arg("days", default=7, minimum=1, maximum=MAX_HISTORY_DAYS)
    end = Date.today()
    start = end - timedelta(days=days - 1)

    with Database() as db:
        _require_venue(db, venue_name)
        entries = db.history.get_days(venue_name, start, end)
        return jsonify(
            {
                "venue": venue_name,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "history": [_entry_payload(e) for e in entries],
            }
        )


@venues_bp.get("/<venue_name>/averages")
def get_venue_averages(venue_name: str):
    """Average occupancy per opening hour over the last `days` days."""
    days = _int_arg("days", default=MAX_HISTORY_DAYS, minimum=1, maximum=MAX_HISTORY_DAYS)
    end = Date.today()
    start = end - timedelta(days=days - 1)

    with Database() as db:
        venue = _require_venue(db, venue_name)
        averages = db.history.hourly_averages(venue_name, start=start, end=end)
        return jsonify(
            {
                "venue": venue_name,
                "max_capacity": venue.max_capacity,
                "averages": [
                    {"hour": hour, "capacity": round(averages[hour], 1)}
                    for hour in HOURS
                    if hour in averages
                ],
            }
        )
