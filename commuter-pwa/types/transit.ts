// Core domain types for GatiSync Commuter PWA.
// These are the ONLY shapes React components should ever see —
// raw backend/demo payloads are normalized into these via lib/api/adapters.ts.

export type BusStatus = "on-time" | "delayed" | "unknown";

export interface LatLng {
  lat: number;
  lng: number;
}

export interface Bus {
  id: string;
  routeId: string;
  lat: number;
  lng: number;
  /** Previous known position, kept for marker interpolation. */
  prevLat: number;
  prevLng: number;
  /** km/h, optional — not all backends report it. */
  speed?: number;
  /** degrees, 0 = north, clockwise */
  heading?: number;
  etaSeconds?: number;
  nextStopId?: string;
  status: BusStatus;
  /** epoch ms of the last update this client received */
  updatedAt: number;
}

export interface Stop {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface RouteStopRef {
  stopId: string;
  /** order along the route, 0-indexed */
  sequence: number;
}

export interface Route {
  id: string;
  name: string;
  shortName: string;
  /** e.g. "Jalandhar Railway Station → Model Town" */
  headsign: string;
  color: string;
  path: LatLng[];
  stops: RouteStopRef[];
}

export type ConnectionState =
  | "CONNECTED"
  | "CONNECTING"
  | "RECONNECTING"
  | "DISCONNECTED"
  | "ERROR";

export type ThemeMode = "light" | "dark" | "system";

/** Raw shape the backend is expected to send over the WebSocket. */
export interface RawBusUpdate {
  busId?: string;
  vehicle_id?: string;
  routeId?: string;
  route_id?: string;
  lat?: number;
  latitude?: number;
  lng?: number;
  longitude?: number;
  speed?: number;
  heading?: number;
  timestamp?: number;
  nextStopId?: string;
  next_stop_id?: string;
  etaSeconds?: number;
  eta?: number;
}

export interface SearchResult {
  type: "bus" | "route" | "stop";
  id: string;
  title: string;
  subtitle?: string;
}
