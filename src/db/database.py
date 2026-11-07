import sqlite3
from dataclasses import dataclass
from datetime import date as Date, timedelta
from pathlib import Path

from .hours import HOURS, hour_to_label, validate_label

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "venues.sqlite3"
RETENTION_DAYS = 30

SCHEMA = """
CREATE TABLE IF NOT EXISTS venues (
    venue    TEXT PRIMARY KEY,
    location TEXT NOT NULL,
    max_capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_data (
    venue TEXT NOT NULL,
    date  TEXT NOT NULL,
    hour  TEXT NOT NULL,
    data  INTEGER NOT NULL,
    PRIMARY KEY (venue, date, hour)
);

CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_data (date);
"""


def _as_iso(value: Date | str) -> str:
    return value.isoformat() if isinstance(value, Date) else Date.fromisoformat(value).isoformat()


@dataclass(frozen=True)
class HistoricalEntry:
    venue: str
    date: Date
    hour: str
    data: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "HistoricalEntry":
        return cls(row["venue"], Date.fromisoformat(row["date"]), row["hour"], row["data"])


@dataclass(frozen=True)
class Venue:
    name: str
    location: str
    max_capacity: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Venue":
        return cls(row["venue"], row["location"], row["max_capacity"])


class Database:
    """Owns the sqlite connection, the schema and the repositories."""

    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

        self.history = HistoricalDataRepository(self)
        self.venues = VenueRepository(self)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_) -> None:
        self.close()


class VenueRepository:
    def __init__(self, db: Database):
        self._db = db

    def add(self, name: str, location: str, max_capacity: int) -> Venue:
        """Insert or update a venue's location."""
        self._db.connection.execute(
            "INSERT INTO venues (venue, location, max_capacity) VALUES (?, ?, ?) "
            "ON CONFLICT(venue) DO UPDATE SET location = excluded.location, max_capacity = excluded.max_capacity",
            (name, location, max_capacity),
        )
        self._db.connection.commit()
        return Venue(name, location, max_capacity)

    def get(self, name: str) -> Venue | None:
        row = self._db.connection.execute(
            "SELECT venue, location, max_capacity FROM venues WHERE venue = ?", (name,)
        ).fetchone()
        return Venue.from_row(row) if row else None

    def all(self) -> list[Venue]:
        rows = self._db.connection.execute(
            "SELECT venue, location, max_capacity FROM venues ORDER BY venue"
        ).fetchall()
        return [Venue.from_row(row) for row in rows]

    def remove(self, name: str) -> None:
        self._db.connection.execute("DELETE FROM venues WHERE venue = ?", (name,))
        self._db.connection.commit()


class HistoricalDataRepository:
    def __init__(self, db: Database, retention_days: int = RETENTION_DAYS):
        self._db = db
        self.retention_days = retention_days

    def add(self, venue: str, date: Date | str, hour: str | int, data: int) -> HistoricalEntry:
        """Store a capacity reading, replacing any existing one, then prune old rows."""
        label = hour_to_label(hour) if isinstance(hour, int) else validate_label(hour)
        iso = _as_iso(date)

        self._db.connection.execute(
            "INSERT INTO historical_data (venue, date, hour, data) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(venue, date, hour) DO UPDATE SET data = excluded.data",
            (venue, iso, label, int(data)),
        )
        self.prune(commit=False)
        self._db.connection.commit()
        return HistoricalEntry(venue, Date.fromisoformat(iso), label, int(data))

    def prune(self, today: Date | None = None, commit: bool = True) -> int:
        """Delete anything older than the retention window. Returns rows removed."""
        cutoff = (today or Date.today()) - timedelta(days=self.retention_days)
        cursor = self._db.connection.execute(
            "DELETE FROM historical_data WHERE date < ?", (cutoff.isoformat(),)
        )
        if commit:
            self._db.connection.commit()
        return cursor.rowcount

    def get_day(self, venue: str, date: Date | str) -> list[HistoricalEntry]:
        """All readings for one venue on one day, ordered by hour."""
        rows = self._db.connection.execute(
            "SELECT venue, date, hour, data FROM historical_data WHERE venue = ? AND date = ?",
            (venue, _as_iso(date)),
        ).fetchall()
        return self._sorted(HistoricalEntry.from_row(row) for row in rows)

    def get_days(
        self, venue: str, start: Date | str, end: Date | str
    ) -> list[HistoricalEntry]:
        """All readings for one venue between two dates (inclusive)."""
        rows = self._db.connection.execute(
            "SELECT venue, date, hour, data FROM historical_data "
            "WHERE venue = ? AND date BETWEEN ? AND ? ORDER BY date",
            (venue, _as_iso(start), _as_iso(end)),
        ).fetchall()
        entries = [HistoricalEntry.from_row(row) for row in rows]
        return sorted(entries, key=lambda e: (e.date, HOURS.index(e.hour)))

    def hourly_averages(
        self,
        venue: str,
        start: Date | str | None = None,
        end: Date | str | None = None,
    ) -> dict[str, float]:
        """Average capacity per hour label over the given (optional) date range."""
        query = "SELECT hour, AVG(data) AS mean FROM historical_data WHERE venue = ?"
        params: list[str] = [venue]

        if start is not None:
            query += " AND date >= ?"
            params.append(_as_iso(start))
        if end is not None:
            query += " AND date <= ?"
            params.append(_as_iso(end))

        query += " GROUP BY hour"
        rows = self._db.connection.execute(query, params).fetchall()
        averages = {row["hour"]: float(row["mean"]) for row in rows}
        return {hour: averages[hour] for hour in HOURS if hour in averages}

    @staticmethod
    def _sorted(entries) -> list[HistoricalEntry]:
        return sorted(entries, key=lambda e: HOURS.index(e.hour))
