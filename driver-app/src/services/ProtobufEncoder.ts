import protobuf from 'protobufjs';
import { GpsFix } from './LocationService';

/**
 * Inlined copy of src/proto/gps_ping.proto, so protobufjs can parse it at
 * runtime without a Metro asset-loader config for .proto files.
 *
 * IMPORTANT: keep this in sync with src/proto/gps_ping.proto (which is
 * kept around as the readable source-of-truth / for sharing with the
 * backend dev). If the backend .proto changes, update BOTH.
 */
const GPS_PING_PROTO_SOURCE = `
  syntax = "proto3";
  package gatisync.telemetry;

  message GPSPing {
    string bus_id = 1;
    string route_id = 2;
    double latitude = 3;
    double longitude = 4;
    float speed_mps = 5;
    float heading_degrees = 6;
    int64 captured_at_unix_ms = 7;
  }
`;

let cachedGPSPingType: protobuf.Type | null = null;

function getGPSPingType(): protobuf.Type {
  if (cachedGPSPingType) {
    return cachedGPSPingType;
  }
  const root = protobuf.parse(GPS_PING_PROTO_SOURCE).root;
  cachedGPSPingType = root.lookupType('gatisync.telemetry.GPSPing');
  return cachedGPSPingType;
}

export type GPSPingPayload = {
  busId: string;
  routeId: string;
  latitude: number;
  longitude: number;
  speedMps: number;
  headingDegrees: number;
  capturedAtUnixMs: number;
};

/**
 * Validation ranges mirror the Go worker's `valid()` function exactly
 * (ingestion-worker/cmd/worker/main.go). Pings that fail these checks
 * would be silently discarded server-side anyway — better to catch and
 * fix client-side (e.g. clamp speed, skip a corrupt fix) than to burn
 * battery/bandwidth sending pings the backend will throw away.
 */
export function validateGPSPingPayload(payload: GPSPingPayload): string | null {
  if (!payload.busId || payload.busId.length > 64 || /[{}\r\n]/.test(payload.busId)) {
    return 'invalid bus_id';
  }
  if (!payload.routeId || payload.routeId.length > 64) {
    return 'invalid route_id';
  }
  if (
    Number.isNaN(payload.latitude) ||
    Number.isNaN(payload.longitude) ||
    payload.latitude < -90 ||
    payload.latitude > 90 ||
    payload.longitude < -180 ||
    payload.longitude > 180
  ) {
    return 'invalid coordinates';
  }
  if (payload.speedMps < 0 || payload.speedMps > 70) {
    return 'invalid speed';
  }
  if (payload.headingDegrees < 0 || payload.headingDegrees >= 360) {
    return 'invalid heading';
  }
  return null; // valid
}

/**
 * Converts a raw GpsFix (from LocationService) into the wire payload
 * shape, clamping/defaulting values the Go worker requires but that
 * Android's GPS API sometimes returns as null (speed/heading when the
 * device is stationary).
 */
export function toGPSPingPayload(
  fix: GpsFix,
  busId: string,
  routeId: string,
): GPSPingPayload {
  const speedMps = fix.speed !== null ? Math.min(Math.max(fix.speed, 0), 70) : 0;
  const headingDegrees =
    fix.heading !== null && fix.heading >= 0 && fix.heading < 360 ? fix.heading : 0;

  return {
    busId,
    routeId,
    latitude: fix.latitude,
    longitude: fix.longitude,
    speedMps,
    headingDegrees,
    capturedAtUnixMs: fix.timestamp,
  };
}

/**
 * Encodes a payload into the exact Protobuf binary format the Go
 * ingestion worker unmarshals with proto.Unmarshal(). Field names here
 * are camelCase (protobufjs convention) but map 1:1 to the proto's
 * snake_case wire fields via the schema above.
 */
export function encodeGPSPing(payload: GPSPingPayload): Uint8Array {
  const GPSPing = getGPSPingType();
  const message = GPSPing.create(payload);
  return GPSPing.encode(message).finish();
}
