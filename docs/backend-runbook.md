# Member 2 backend runbook

## Run locally

From `infra/`, run `docker compose up --build`. This starts EMQX on MQTT port `1883`, Redis, the Go ingestion worker, and the FastAPI gateway on port `8000`.

## Telemetry contract

Drivers publish a binary Protobuf `GPSPing` to `gps/<bus_id>/ping` at MQTT QoS 1. The canonical schema is [`ingestion-worker/proto/gps_ping.proto`](../ingestion-worker/proto/gps_ping.proto). The worker rejects malformed coordinates, invalid headings, and invalid identifiers.

Each accepted ping is written as `bus:<bus_id>:live` in Redis with a 90-second TTL, added to `route:<route_id>:buses`, and published as JSON on `bus-updates`. This makes stale vehicles disappear automatically.

## Gateway contracts

- `GET /healthz` provides a dependency check.
- `GET /gtfs-rt/vehicle-positions.pb` returns a GTFS-Realtime binary vehicle-position feed.
- `WS /ws/buses` streams the same normalized update objects to the commuter PWA.

For the hackathon compose profile, EMQX allows anonymous clients. Before a public deployment, configure TLS and one credential per driver device.
