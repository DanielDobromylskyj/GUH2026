# Venue Capacity Checker — Frontend

Two-panel dashboard for a Bluetooth-based venue/cafe capacity checker.
React + TypeScript + Vite, plain CSS (no UI framework).

## Run

```bash
pnpm install
pnpm dev      # http://localhost:5173
pnpm build
pnpm lint
```

## Backend API

| Endpoint          | Returns                               |
| ----------------- | ------------------------------------- |
| `GET /venues`     | `[{ name, status }]` — `busy`/`mid`/`empty` |
| `GET /venues/{name}` | `{ capacity, maxCapacity }` (`max_capacity` also accepted) |

In dev, `/venues` is proxied to `http://localhost:8000` (override with
`VITE_API_TARGET`). For a deployed backend on another origin set `VITE_API_BASE`.

If the API is unreachable the UI falls back to mock venues and shows a
"demo data" badge, so it stays demoable offline. Data refreshes every 15s.

## Colours

| Token      | Hex       | Use                   |
| ---------- | --------- | --------------------- |
| `--ink`    | `#003844` | Page background, text |
| `--frame`  | `#f6e7cb` | Internal frames/cards |
| `--busy`   | `#a1172e` | Very busy             |
| `--mid`    | `#f19a3e` | A bit busy            |
| `--empty`  | `#74d3ae` | Not busy              |

## Bluetooth hook

`src/hooks/useBluetoothScan.ts` tries the experimental Web Bluetooth
`navigator.bluetooth.requestLEScan` API and falls back to a mock advertisement
feed when unsupported or denied. It exposes `devices` (with RSSI),
`estimatedPeople` (RSSI-weighted device count), and `startScan`/`stopScan` —
a drop-in point for real foot-traffic estimation.

## Structure

```
src/
  App.tsx                      layout, selection state, polling
  components/VenueSidebar      venue list + status dots + legend
  components/VenueDetailPanel  header, capacity counter, chart slot
  components/BluetoothEstimator scanner card + RSSI list
  hooks/useBluetoothScan.ts    Web Bluetooth / mock scanning
  lib/api.ts                   API client + mock fallback
  lib/types.ts                 shared types, status colours
```
