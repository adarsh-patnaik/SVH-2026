# GatiSync Driver Emitter App

React Native (Android-first) driver app. Background GPS tracking,
Protobuf serialization, and MQTT publishing to the real backend.

## Status: integration complete against the confirmed backend contract

Everything below is wired against the **actual** backend repo
(`SVH-2026-Backend-Development`), not assumptions:

| Piece | Source of truth | Status |
|---|---|---|
| `.proto` schema | `ingestion-worker/proto/gps_ping.proto` | ✅ copied exactly (`src/proto/gps_ping.proto`) |
| Wire format | `ingestion-worker/internal/telemetry/ping.go` | ✅ matched in `ProtobufEncoder.ts` |
| Validation rules | `ingestion-worker/cmd/worker/main.go`'s `valid()` | ✅ mirrored client-side before publish |
| MQTT topic | `infra/docker-compose.yml` (`gps/+/ping`) | ✅ publishes to `gps/<busId>/ping`, QoS 1 |
| Broker | EMQX, `tcp://emqx:1883`, anonymous allowed (MVP) | ✅ `MqttService.ts` connects with no auth |
| Auth / routes API | **does not exist yet** in either repo | ⚠️ see below |

## What changed from the earlier draft

- **Removed the fake login screen.** There is no `/auth` endpoint anywhere
  in the backend, and MQTT itself needs no credentials
  (`EMQX_ALLOW_ANONYMOUS: "true"`). Pretending a JWT flow existed would
  have been misleading. `SetupScreen.tsx` now just asks the driver for
  **Bus ID** and **Route ID** directly — these map straight onto the
  proto's `bus_id`/`route_id` fields.
- **Removed the mock trip-picker.** No `/routes` endpoint exists either.
- **`BackgroundTask.ts` now actually publishes.** Every GPS fix is
  converted to a `GPSPing` payload, validated against the same rules the
  Go worker enforces, Protobuf-encoded, and published over MQTT.

## Files

```
src/
├── proto/gps_ping.proto          # exact copy of backend's schema (source of truth reference)
├── services/
│   ├── LocationService.ts        # GPS permission + continuous watching
│   ├── ProtobufEncoder.ts        # encodes GpsFix -> GPSPing wire bytes, validates first
│   ├── MqttService.ts            # connects to EMQX, publishes to gps/<busId>/ping
│   └── BackgroundTask.ts         # foreground service; wires GPS -> encode -> publish
├── screens/
│   ├── SetupScreen.tsx           # bus ID + route ID entry (no auth API exists)
│   └── TrackingScreen.tsx        # start/stop, live fix display, MQTT status, ping counters
├── store/driverStore.ts          # session (busId/routeId) + tracking state
├── utils/
│   ├── constants.ts              # broker host/port, API URL — confirmed real values
│   ├── mockLocationCheck.ts      # anti-GPS-spoofing
│   └── batteryOptimization.ts    # Doze exemption + OEM-specific guidance
└── navigation/AppNavigator.tsx   # Setup -> Tracking
```

## Running it end-to-end

**1. Start the backend locally** (from the backend repo, not this one):
```bash
cd SVH-2026-Backend-Development/infra
docker-compose up
```
This brings up EMQX (port 1883), Redis, the Go ingestion worker, and the
API gateway (port 8000).

**2. Point the app at the right host.**
In `src/utils/constants.ts`:
- **Android emulator** → leave `MQTT_BROKER_HOST = 'localhost'`; emulators
  route `localhost` to the host machine automatically via `10.0.2.2`
  under the hood for most RN setups — if it doesn't resolve, use
  `10.0.2.2` explicitly.
- **Physical Android device** → replace `'localhost'` with your laptop's
  LAN IP (`ipconfig` on Windows), and make sure phone + laptop are on the
  same Wi-Fi network.

**3. Generate the native Android project** (not included — this is
source-only):
```bash
npx react-native init  # or equivalent, then merge index.js/app.json/src/ in
```
Copy permissions from `android-manifest-permissions.xml` into the real
generated `AndroidManifest.xml`.

**4. Install and run:**
```bash
npm install
npx react-native run-android
```

**5. Verify the round trip.** Enter a Bus ID/Route ID, hit Start Trip.
Watch the `ingestion-worker` container logs — you should see:
```
stored bus=BUS-402 route=R-7
```
If you instead see `discarded malformed protobuf`, see the important
caveat below before debugging further.

## ⚠️ One thing to verify before trusting it fully

`MqttService.ts` base64-encodes the Protobuf bytes before calling
`sp-react-native-mqtt`'s `publish()`. This is a common workaround for RN's
JS↔native bridge not handling raw byte arrays well, but **whether this
specific library decodes it back to raw bytes before publishing (vs.
publishing the base64 text itself) needs a real device/emulator test** —
I couldn't verify this without running it. The code has a comment marking
exactly where to check and what to do if the worker logs
`discarded malformed protobuf`.

## Known gaps (not blockers, just be aware)

- No real device auth — anyone who knows a Bus ID can publish as that bus.
  Fine for a hackathon MVP (matches `EMQX_ALLOW_ANONYMOUS=true`), flag it
  in the "Security & Privacy" part of your pitch as a noted limitation.
- No `/routes` endpoint to validate that a typed Route ID actually exists
  — SetupScreen accepts any non-empty string. Wire up validation once
  Member 6's GTFS static data + an endpoint exist.
- Geofencing (auto-detect bus stop arrival) is listed as "Advanced" scope
  in the project doc — not built, matches the MVP cutoff.
