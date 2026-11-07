# API Module

Flask JSON API serving venue occupancy data to the frontend.

## Layout

| File | Responsibility |
| --- | --- |
| `app.py` | Application factory, CORS, JSON error handlers, `/api/health` |
| `routes.py` | `/api/venues` blueprint and response serialisation |
| `estimator.py` | Occupancy estimation, model/weather caching, fallbacks |
| `main.py` | Entry point (`python -m src.api.main`) |

## Running

```bash
pip install -r requirements.txt
python -m src.api.main           # http://127.0.0.1:8000
```

Environment: `API_HOST`, `API_PORT` (default `8000`), `API_DEBUG`.

All routes are namespaced under `/api`. The Vite dev server proxies
`/api` to port `8000`, and the frontend client defaults to an `/api`
base (override with `VITE_API_BASE`).

## Endpoints

### `GET /api/health`
```json
{ "status": "ok" }
```

### `GET /api/venues`
All venues with their latest stored reading for today.
```json
[{ "name": "Kilburn LF1", "location": "Manchester",
   "capacity": 152, "max_capacity": 300, "status": "mid" }]
```

### `GET /api/venues/{name}?devices=<int>`
Runs a fresh estimate and stores it. `devices` is the Bluetooth device
count (default `0`, clamped to `0..10000`).
```json
{ "name": "Kilburn LF1", "location": "Manchester",
  "capacity": 152, "max_capacity": 300, "status": "mid" }
```

### `GET /api/venues/{name}/history?days=<1..30>`
Stored readings, oldest first (default `7` days).
```json
{ "venue": "Kilburn LF1", "start": "2026-11-01", "end": "2026-11-07",
  "history": [{ "date": "2026-11-07", "hour": "4pm", "capacity": 152 }] }
```

### `GET /api/venues/{name}/averages?days=<1..30>`
Mean occupancy per opening hour, ordered `8am`..`8pm`.
```json
{ "venue": "Kilburn LF1", "max_capacity": 300,
  "averages": [{ "hour": "4pm", "capacity": 152.0 }] }
```

## Status buckets

Derived from `capacity / max_capacity`, matching the frontend thresholds:

| Ratio | Status |
| --- | --- |
| `>= 0.75` | `busy` |
| `>= 0.40` | `mid` |
| otherwise | `empty` |

## Errors

All errors return JSON: `{ "error": "Not Found", "message": "..." }`
with `400` for malformed query params and `404` for unknown venues.

## Estimation behaviour

`estimator.py` keeps the API resilient:

- Models load from `locations/{venue}.net`, falling back to `Library.net`.
  Loaded models are cached per venue.
- Weather is fetched per location and cached for 15 minutes; lookup
  failures fall back to `Overcast`.
- If no model is available or inference fails, the most recent stored
  reading is returned instead.
- Estimates are clamped to `0..max_capacity` and only persisted during
  opening hours (8am–8pm).
