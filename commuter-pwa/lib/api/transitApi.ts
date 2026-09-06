import type { Route, Stop } from "@/types/transit";
import { DEMO_ROUTES, DEMO_STOPS } from "@/lib/demo/demoData";
import { distanceMeters } from "@/lib/utils/geo";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function safeFetchJson<T>(path: string): Promise<T | null> {
  if (!API_URL) return null;
  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null; // network failure — caller falls back to demo/cached data
  }
}

export async function getRoutes(): Promise<Route[]> {
  const data = await safeFetchJson<Route[]>("/routes");
  return data ?? DEMO_ROUTES;
}

export async function getRoute(routeId: string): Promise<Route | undefined> {
  const data = await safeFetchJson<Route>(`/routes/${routeId}`);
  return data ?? DEMO_ROUTES.find((r) => r.id === routeId);
}

export async function getStops(): Promise<Stop[]> {
  const data = await safeFetchJson<Stop[]>("/stops");
  return data ?? DEMO_STOPS;
}

export async function getStop(stopId: string): Promise<Stop | undefined> {
  const data = await safeFetchJson<Stop>(`/stops/${stopId}`);
  return data ?? DEMO_STOPS.find((s) => s.id === stopId);
}

export async function getNearbyStops(
  lat: number,
  lng: number,
  radiusMeters = 1500
): Promise<Stop[]> {
  const data = await safeFetchJson<Stop[]>(`/stops/nearby?lat=${lat}&lng=${lng}`);
  if (data) return data;

  return DEMO_STOPS.filter(
    (s) => distanceMeters({ lat, lng }, { lat: s.lat, lng: s.lng }) <= radiusMeters
  );
}
