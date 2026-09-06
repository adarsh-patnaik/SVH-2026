import type { LatLng } from "@/types/transit";

const EARTH_RADIUS_M = 6371000;

const toRad = (deg: number) => (deg * Math.PI) / 180;

/** Haversine distance in metres between two points. */
export function distanceMeters(a: LatLng, b: LatLng): number {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** Bearing in degrees (0 = north, clockwise) from a to b. */
export function bearing(a: LatLng, b: LatLng): number {
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const dLng = toRad(b.lng - a.lng);
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return (Math.atan2(y, x) * 180) / Math.PI + 360 === 360
    ? 0
    : ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

/** Linear interpolation between two points, t in [0,1]. Good enough for short hops. */
export function lerpLatLng(a: LatLng, b: LatLng, t: number): LatLng {
  return { lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t };
}

/** Total length of a polyline in metres. */
export function pathLength(path: LatLng[]): number {
  let total = 0;
  for (let i = 1; i < path.length; i++) total += distanceMeters(path[i - 1], path[i]);
  return total;
}

/** Given progress 0..1 along a polyline, return the point + heading there. */
export function pointAlongPath(
  path: LatLng[],
  progress: number
): { point: LatLng; heading: number } {
  if (path.length === 0) return { point: { lat: 0, lng: 0 }, heading: 0 };
  if (path.length === 1) return { point: path[0], heading: 0 };

  const total = pathLength(path);
  const target = Math.max(0, Math.min(1, progress)) * total;

  let covered = 0;
  for (let i = 1; i < path.length; i++) {
    const segLen = distanceMeters(path[i - 1], path[i]);
    if (covered + segLen >= target || i === path.length - 1) {
      const segT = segLen === 0 ? 0 : (target - covered) / segLen;
      return {
        point: lerpLatLng(path[i - 1], path[i], Math.max(0, Math.min(1, segT))),
        heading: bearing(path[i - 1], path[i]),
      };
    }
    covered += segLen;
  }
  return { point: path[path.length - 1], heading: 0 };
}
