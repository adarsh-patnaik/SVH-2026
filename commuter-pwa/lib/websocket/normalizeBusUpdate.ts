import type { Bus, RawBusUpdate } from "@/types/transit";

/**
 * Backend field names have drifted across services (Go worker vs FastAPI vs
 * demo simulator all disagree slightly). This is the single seam that
 * absorbs that drift so every component downstream only ever sees the
 * clean `Bus` shape from types/transit.ts.
 */
export function normalizeBusUpdate(
  message: RawBusUpdate,
  previous?: Bus
): Bus | null {
  const id = message.busId ?? message.vehicle_id;
  const lat = message.lat ?? message.latitude;
  const lng = message.lng ?? message.longitude;

  if (!id || typeof lat !== "number" || typeof lng !== "number") {
    // Malformed message — drop it rather than crash the map.
    return null;
  }

  // Guard against wildly invalid coordinates (e.g. 0,0 sentinel from a
  // dropped GPS fix, or NaN from a bad decode).
  if (
    Number.isNaN(lat) ||
    Number.isNaN(lng) ||
    Math.abs(lat) > 90 ||
    Math.abs(lng) > 180 ||
    (lat === 0 && lng === 0)
  ) {
    return null;
  }

  return {
    id: String(id),
    routeId: message.routeId ?? message.route_id ?? previous?.routeId ?? "",
    lat,
    lng,
    prevLat: previous?.lat ?? lat,
    prevLng: previous?.lng ?? lng,
    speed: message.speed ?? previous?.speed,
    heading: message.heading ?? previous?.heading,
    etaSeconds: message.etaSeconds ?? message.eta ?? previous?.etaSeconds,
    nextStopId: message.nextStopId ?? message.next_stop_id ?? previous?.nextStopId,
    status: previous?.status ?? "on-time",
    updatedAt: message.timestamp
      ? message.timestamp > 1e12
        ? message.timestamp // already ms
        : message.timestamp * 1000 // seconds -> ms
      : Date.now(),
  };
}
