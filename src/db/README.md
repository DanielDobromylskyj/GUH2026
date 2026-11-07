# Database Module

SQLite-based storage for venue locations and historical capacity data.

## Quick Start

```python
from datetime import date
from src.db import Database

with Database() as db:
    # Add venues
    db.venues.add("Library", "Campus North")
    
    # Store capacity readings
    db.history.add("Library", date.today(), "1pm", 240)
    db.history.add("Library", date.today(), 13, 240)  # same as above
    
    # Query
    entries = db.history.get_day("Library", date.today())
    averages = db.history.hourly_averages("Library")
```

## Tables

### `venues`
- `venue` (TEXT, PRIMARY KEY) - venue name
- `location` (TEXT) - physical location
- `max_capacity` (INTEGER) - maximum capacity

### `historical_data`
- Composite primary key: `(venue, date, hour)`
- `data` (INTEGER) - capacity at this time
- Auto-pruned to 30 days on every insert

## API

### `Database(path="src/db/venues.sqlite3")`
- `.venues` → `VenueRepository`
- `.history` → `HistoricalDataRepository`

### `VenueRepository`
- `add(name, location)` - upsert
- `get(name)` - returns `Venue | None`
- `all()` - sorted by name
- `remove(name)`

### `HistoricalDataRepository`
- `add(venue, date, hour, data)` - upsert + auto-prune
  - `hour` accepts int (8-20) or label ("8am"-"8pm")
  - `date` accepts `datetime.date` or ISO string
- `get_day(venue, date)` - ordered by hour
- `get_days(venue, start, end)` - ordered by date, hour
- `hourly_averages(venue, start=None, end=None)` - `dict[str, float]`
- `prune(today=None)` - manual retention cleanup

### Hours
```python
from src.db import HOURS, hour_to_label, label_to_hour

HOURS  # ("8am", "9am", ..., "8pm")
hour_to_label(13)  # "1pm"
label_to_hour("1pm")  # 13
```

## Testing

```bash
python3 -m unittest tests.test_db -v
```

36 tests covering:
- Hour label conversions
- Schema creation
- Venue CRUD + upserts
- Historical data CRUD + upserts
- Date range queries
- Hourly averages (filtered & unfiltered)
- Auto-pruning (30-day retention)
- Ordering guarantees
