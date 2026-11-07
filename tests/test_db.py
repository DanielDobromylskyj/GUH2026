import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src.db import (
    Database,
    HistoricalEntry,
    Venue,
    hour_to_label,
    label_to_hour,
    HOURS,
)
from src.db.database import RETENTION_DAYS


class TestHours(unittest.TestCase):
    def test_hour_to_label(self):
        self.assertEqual(hour_to_label(8), "8am")
        self.assertEqual(hour_to_label(12), "12pm")
        self.assertEqual(hour_to_label(13), "1pm")
        self.assertEqual(hour_to_label(20), "8pm")

    def test_hour_to_label_invalid(self):
        with self.assertRaises(ValueError) as ctx:
            hour_to_label(7)
        self.assertIn("outside of opening hours", str(ctx.exception))

        with self.assertRaises(ValueError):
            hour_to_label(21)

    def test_label_to_hour(self):
        self.assertEqual(label_to_hour("8am"), 8)
        self.assertEqual(label_to_hour("12pm"), 12)
        self.assertEqual(label_to_hour("1pm"), 13)
        self.assertEqual(label_to_hour("8pm"), 20)

    def test_label_to_hour_invalid(self):
        with self.assertRaises(ValueError) as ctx:
            label_to_hour("7am")
        self.assertIn("Invalid hour label", str(ctx.exception))

        with self.assertRaises(ValueError):
            label_to_hour("9pm")

    def test_hours_constant(self):
        self.assertEqual(len(HOURS), 13)
        self.assertEqual(HOURS[0], "8am")
        self.assertEqual(HOURS[-1], "8pm")

    def test_roundtrip(self):
        for hour in range(8, 21):
            label = hour_to_label(hour)
            self.assertEqual(label_to_hour(label), hour)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()

    def test_database_creation(self):
        self.assertTrue(self.db_path.exists())
        self.assertIsInstance(self.db.connection, sqlite3.Connection)

    def test_schema_exists(self):
        cursor = self.db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        self.assertIn("venues", tables)
        self.assertIn("historical_data", tables)

    def test_context_manager(self):
        with Database(self.db_path) as db:
            self.assertIsInstance(db, Database)
        # Connection should be closed after context


class TestVenueRepository(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()

    def test_add_venue(self):
        venue = self.db.venues.add("Library", "Campus North", 100)
        self.assertEqual(venue.name, "Library")
        self.assertEqual(venue.location, "Campus North")
        self.assertEqual(venue.max_capacity, 100)

    def test_add_venue_upsert(self):
        self.db.venues.add("Library", "Campus North", 100)
        venue = self.db.venues.add("Library", "Campus South", 200)
        self.assertEqual(venue.location, "Campus South")
        self.assertEqual(venue.max_capacity, 200)

        venues = self.db.venues.all()
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].location, "Campus South")
        self.assertEqual(venues[0].max_capacity, 200)

    def test_get_venue(self):
        self.db.venues.add("Library", "Campus North", 150)
        venue = self.db.venues.get("Library")
        self.assertIsNotNone(venue)
        self.assertEqual(venue.name, "Library")
        self.assertEqual(venue.location, "Campus North")
        self.assertEqual(venue.max_capacity, 150)

    def test_get_nonexistent_venue(self):
        venue = self.db.venues.get("Nonexistent")
        self.assertIsNone(venue)

    def test_all_venues(self):
        self.db.venues.add("Library", "Campus North", 100)
        self.db.venues.add("Cafeteria", "Building 5", 80)
        self.db.venues.add("Gym", "Sports Complex", 50)

        venues = self.db.venues.all()
        self.assertEqual(len(venues), 3)
        names = {v.name for v in venues}
        self.assertEqual(names, {"Library", "Cafeteria", "Gym"})

    def test_all_venues_ordered(self):
        self.db.venues.add("Zoo", "Far away", 30)
        self.db.venues.add("Cafeteria", "Building 5", 80)
        self.db.venues.add("Library", "Campus North", 100)

        venues = self.db.venues.all()
        names = [v.name for v in venues]
        self.assertEqual(names, ["Cafeteria", "Library", "Zoo"])

    def test_remove_venue(self):
        self.db.venues.add("Library", "Campus North", 100)
        self.db.venues.remove("Library")
        venue = self.db.venues.get("Library")
        self.assertIsNone(venue)

    def test_remove_nonexistent_venue(self):
        self.db.venues.remove("Nonexistent")


class TestHistoricalDataRepository(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.db = Database(self.db_path)
        self.today = date.today()

    def tearDown(self):
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()

    def test_add_entry_with_int_hour(self):
        entry = self.db.history.add("Library", self.today, 13, 240)
        self.assertEqual(entry.venue, "Library")
        self.assertEqual(entry.date, self.today)
        self.assertEqual(entry.hour, "1pm")
        self.assertEqual(entry.data, 240)

    def test_add_entry_with_label(self):
        entry = self.db.history.add("Library", self.today, "1pm", 240)
        self.assertEqual(entry.hour, "1pm")
        self.assertEqual(entry.data, 240)

    def test_add_entry_with_string_date(self):
        entry = self.db.history.add("Library", "2026-11-07", "1pm", 240)
        self.assertEqual(entry.date, date(2026, 11, 7))

    def test_add_entry_invalid_hour(self):
        with self.assertRaises(ValueError):
            self.db.history.add("Library", self.today, "7am", 100)

        with self.assertRaises(ValueError):
            self.db.history.add("Library", self.today, 7, 100)

    def test_add_entry_upsert(self):
        self.db.history.add("Library", self.today, "1pm", 240)
        entry = self.db.history.add("Library", self.today, "1pm", 300)
        self.assertEqual(entry.data, 300)

        entries = self.db.history.get_day("Library", self.today)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].data, 300)

    def test_get_day(self):
        self.db.history.add("Library", self.today, "8am", 100)
        self.db.history.add("Library", self.today, "1pm", 200)
        self.db.history.add("Library", self.today, "8pm", 150)

        entries = self.db.history.get_day("Library", self.today)
        self.assertEqual(len(entries), 3)
        self.assertEqual([e.hour for e in entries], ["8am", "1pm", "8pm"])
        self.assertEqual([e.data for e in entries], [100, 200, 150])

    def test_get_day_ordered(self):
        self.db.history.add("Library", self.today, "8pm", 150)
        self.db.history.add("Library", self.today, "8am", 100)
        self.db.history.add("Library", self.today, "1pm", 200)

        entries = self.db.history.get_day("Library", self.today)
        self.assertEqual([e.hour for e in entries], ["8am", "1pm", "8pm"])

    def test_get_day_empty(self):
        entries = self.db.history.get_day("Library", self.today)
        self.assertEqual(entries, [])

    def test_get_day_different_venue(self):
        self.db.history.add("Library", self.today, "8am", 100)
        self.db.history.add("Cafeteria", self.today, "8am", 200)

        entries = self.db.history.get_day("Library", self.today)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].data, 100)

    def test_get_days_range(self):
        day1 = self.today - timedelta(days=2)
        day2 = self.today - timedelta(days=1)
        day3 = self.today

        self.db.history.add("Library", day1, "8am", 100)
        self.db.history.add("Library", day2, "1pm", 200)
        self.db.history.add("Library", day3, "8pm", 150)

        entries = self.db.history.get_days("Library", day1, day3)
        self.assertEqual(len(entries), 3)
        self.assertEqual([e.date for e in entries], [day1, day2, day3])

    def test_get_days_ordered_by_date_and_hour(self):
        day1 = self.today - timedelta(days=1)
        day2 = self.today

        self.db.history.add("Library", day2, "8am", 400)
        self.db.history.add("Library", day1, "8pm", 200)
        self.db.history.add("Library", day1, "8am", 100)
        self.db.history.add("Library", day2, "1pm", 500)

        entries = self.db.history.get_days("Library", day1, day2)
        expected = [
            (day1, "8am", 100),
            (day1, "8pm", 200),
            (day2, "8am", 400),
            (day2, "1pm", 500),
        ]
        actual = [(e.date, e.hour, e.data) for e in entries]
        self.assertEqual(actual, expected)

    def test_hourly_averages(self):
        day1 = self.today - timedelta(days=2)
        day2 = self.today - timedelta(days=1)

        self.db.history.add("Library", day1, "8am", 100)
        self.db.history.add("Library", day2, "8am", 200)
        self.db.history.add("Library", day1, "1pm", 150)
        self.db.history.add("Library", day2, "1pm", 250)

        avgs = self.db.history.hourly_averages("Library")
        self.assertEqual(avgs["8am"], 150.0)
        self.assertEqual(avgs["1pm"], 200.0)
        self.assertEqual(len(avgs), 2)

    def test_hourly_averages_with_date_range(self):
        day1 = self.today - timedelta(days=2)
        day2 = self.today - timedelta(days=1)
        day3 = self.today

        self.db.history.add("Library", day1, "8am", 100)
        self.db.history.add("Library", day2, "8am", 200)
        self.db.history.add("Library", day3, "8am", 300)

        avgs = self.db.history.hourly_averages("Library", start=day2, end=day3)
        self.assertEqual(avgs["8am"], 250.0)

        avgs_start = self.db.history.hourly_averages("Library", start=day3)
        self.assertEqual(avgs_start["8am"], 300.0)

        avgs_end = self.db.history.hourly_averages("Library", end=day1)
        self.assertEqual(avgs_end["8am"], 100.0)

    def test_hourly_averages_ordered(self):
        self.db.history.add("Library", self.today, "8pm", 100)
        self.db.history.add("Library", self.today, "8am", 200)
        self.db.history.add("Library", self.today, "1pm", 150)

        avgs = self.db.history.hourly_averages("Library")
        keys = list(avgs.keys())
        self.assertEqual(keys, ["8am", "1pm", "8pm"])

    def test_hourly_averages_different_venue(self):
        self.db.history.add("Library", self.today, "8am", 100)
        self.db.history.add("Cafeteria", self.today, "8am", 200)

        avgs = self.db.history.hourly_averages("Library")
        self.assertEqual(avgs["8am"], 100.0)

    def test_prune_old_data(self):
        old_date = self.today - timedelta(days=RETENTION_DAYS + 1)
        recent_date = self.today - timedelta(days=1)

        # Insert both directly to bypass auto-prune
        self.db.connection.execute(
            "INSERT INTO historical_data (venue, date, hour, data) VALUES (?, ?, ?, ?)",
            ("Library", old_date.isoformat(), "8am", 100),
        )
        self.db.connection.execute(
            "INSERT INTO historical_data (venue, date, hour, data) VALUES (?, ?, ?, ?)",
            ("Library", recent_date.isoformat(), "8am", 200),
        )
        self.db.connection.commit()

        # Manual prune
        removed = self.db.history.prune()
        self.assertEqual(removed, 1)

        entries = self.db.history.get_day("Library", old_date)
        self.assertEqual(len(entries), 0)

        entries = self.db.history.get_day("Library", recent_date)
        self.assertEqual(len(entries), 1)

    def test_prune_on_add(self):
        old_date = self.today - timedelta(days=RETENTION_DAYS + 1)

        # Insert old data directly to bypass auto-prune
        self.db.connection.execute(
            "INSERT INTO historical_data (venue, date, hour, data) VALUES (?, ?, ?, ?)",
            ("Library", old_date.isoformat(), "8am", 100),
        )
        self.db.connection.commit()
        entries = self.db.history.get_day("Library", old_date)
        self.assertEqual(len(entries), 1)

        # Adding new data should trigger prune
        self.db.history.add("Library", self.today, "8am", 200)
        entries = self.db.history.get_day("Library", old_date)
        self.assertEqual(len(entries), 0)

    def test_prune_with_custom_today(self):
        anchor = date(2026, 11, 1)
        old_date = anchor - timedelta(days=RETENTION_DAYS + 1)
        recent_date = anchor - timedelta(days=1)

        # Insert directly to bypass auto-prune
        self.db.connection.execute(
            "INSERT INTO historical_data (venue, date, hour, data) VALUES (?, ?, ?, ?)",
            ("Library", old_date.isoformat(), "8am", 100),
        )
        self.db.connection.execute(
            "INSERT INTO historical_data (venue, date, hour, data) VALUES (?, ?, ?, ?)",
            ("Library", recent_date.isoformat(), "8am", 200),
        )
        self.db.connection.commit()

        removed = self.db.history.prune(today=anchor)
        self.assertEqual(removed, 1)

    def test_retention_boundary(self):
        boundary_date = self.today - timedelta(days=RETENTION_DAYS)
        old_date = boundary_date - timedelta(days=1)

        self.db.history.add("Library", boundary_date, "8am", 100)
        self.db.history.add("Library", old_date, "8am", 200)

        self.db.history.prune()

        boundary_entries = self.db.history.get_day("Library", boundary_date)
        self.assertEqual(len(boundary_entries), 1)

        old_entries = self.db.history.get_day("Library", old_date)
        self.assertEqual(len(old_entries), 0)


if __name__ == "__main__":
    unittest.main()
