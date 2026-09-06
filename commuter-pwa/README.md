# GatiSync Commuter PWA

Ultra-light real-time public transit tracking for Tier-2 and Tier-3 Indian
cities. This is the **Member 4 (Frontend)** deliverable for the GatiSync /
TransitLite project — the commuter-facing PWA and its WebSocket integration
with the live map. It does not include the driver app, ML backend, or admin
dashboard.

## Stack

Next.js 16 (App Router) · React 19 · TypeScript (strict) · Tailwind CSS v4 ·
Leaflet / react-leaflet · native WebSocket · a hand-written service worker
(no Workbox) · zero web-font downloads (system font stack).

## Getting started

```bash
npm install
npm run dev      # http://localhost:3000 — runs in Demo Mode out of the box
npm run build    # production build
npm run start    # serve the production build
npm run lint     # ESLint
```

`.env.local` ships with `NEXT_PUBLIC_DEMO_MODE=true` so the app runs fully
standalone with six simulated buses moving across three real Jalandhar
routes — no backend required for a demo.

## Environment variables

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI REST service (routes/stops). Unset → bundled demo data. |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for the live-bus feed, e.g. `wss://api.gatisync.in/ws/buses`. Unset → Demo Mode simulator. |
| `NEXT_PUBLIC_DEMO_MODE` | Force Demo Mode even if `NEXT_PUBLIC_WS_URL` is set. |
| `NEXT_PUBLIC_MAP_URL` | Optional override for the map tile URL template. |

## Backend WebSocket contract expected

The frontend expects JSON frames shaped like:

```json
{ "type": "bus_update", "data": { "busId": "402", "routeId": "R12", "lat": 31.326, "lng": 75.5762, "speed": 32, "heading": 120, "timestamp": 1725540000, "nextStopId": "STOP14", "etaSeconds": 300 } }
```

`{ "type": "bus_updates", "data": [ ... ] }` is also accepted for batched
frames. Field names may vary (`vehicle_id`/`latitude`/`longitude`/`eta` are
all accepted too) — see `lib/websocket/normalizeBusUpdate.ts`, the single
seam that adapts backend payloads into the frontend's `Bus` type.

## Switching from Demo Mode to the real backend

Set `NEXT_PUBLIC_WS_URL` (and unset `NEXT_PUBLIC_DEMO_MODE`) — no UI or
component changes required. Every component reads from `useTransit()` /
`useLiveBuses()`, which sit on top of `lib/websocket/dataSource.ts`, the one
place that decides between `WebSocketManager` (real backend) and
`DemoSimulator` (bundled demo). Both implement the identical
connect/disconnect/subscribe interface.

## Project structure

```
app/                  routes: / (main screen), /offline (SW fallback)
components/
  layout/             Header, OfflineBanner, ServiceWorkerRegister
  map/                LiveMap, BusMarker, StopMarker, RouteLine, MapControls
  bus/                BusCard, BusDetails, BusList
  stop/                StopCard, StopDetails
  search/             SearchBar, SearchResults
  ui/                 ThemeToggle, ConnectionStatus, BottomSheet, Skeleton, EmptyState
lib/
  websocket/          WebSocketManager, normalizeBusUpdate, dataSource (demo/live switch)
  demo/                demoData.ts (Jalandhar routes/stops/buses), demoSimulator.ts
  api/                transitApi.ts (REST abstraction w/ demo fallback)
  map/                mapConfig.ts (tile provider seam), icons.ts (divIcons)
  state/              TransitProvider (app-wide context)
  utils/              geo.ts, animateBusPosition.ts, format.ts, search.ts
hooks/                useWebSocket, useLiveBuses, useTheme, useNetworkStatus, useGeolocation, useDebouncedValue
types/transit.ts      shared domain types
public/               manifest.json, sw.js, icons/
```

## Performance & bandwidth notes

- No web fonts are downloaded — the UI uses each OS's native system font.
- Map tiles: a single light tile set (CARTO Voyager) is reused in dark mode
  via a CSS filter instead of fetching a second dark tile set — halves map
  tile bandwidth.
- Live map is code-split (`next/dynamic`, `ssr:false`) — Leaflet only loads
  once the map is actually needed.
- Bus markers are custom inline-SVG `divIcon`s (no image requests) and are
  memoized so only the marker that moved re-renders.
- Marker movement is interpolated client-side with `requestAnimationFrame`;
  the backend only needs to push a fix every few seconds, not every frame.
- The service worker is hand-written (no Workbox) and caches the app shell
  + static assets with stale-while-revalidate, with network-first for
  navigations and a dedicated `/offline` fallback.

## Known limitations

- If a real `NEXT_PUBLIC_WS_URL` is configured but the backend is
  unreachable, the UI will show "Reconnecting"/"Offline" via the existing
  backoff logic rather than auto-falling-back to Demo Mode — for the
  hackathon, toggle `NEXT_PUBLIC_DEMO_MODE` explicitly.
- Mapbox GL swap-in is designed for (see `lib/map/mapConfig.ts`) but not
  implemented — Leaflet ships by default for bandwidth reasons.
- Route search matches by name/number substring only; no fuzzy matching.
