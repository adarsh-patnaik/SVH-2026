import type { Bus, Route, Stop, SearchResult } from "@/types/transit";

export function searchTransit(
  query: string,
  { buses, routes, stops }: { buses: Bus[]; routes: Route[]; stops: Stop[] }
): SearchResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const results: SearchResult[] = [];

  for (const bus of buses) {
    if (bus.id.toLowerCase().includes(q)) {
      const route = routes.find((r) => r.id === bus.routeId);
      results.push({
        type: "bus",
        id: bus.id,
        title: `Bus ${bus.id}`,
        subtitle: route?.headsign,
      });
    }
  }

  for (const route of routes) {
    if (
      route.shortName.toLowerCase().includes(q) ||
      route.headsign.toLowerCase().includes(q) ||
      route.name.toLowerCase().includes(q)
    ) {
      results.push({ type: "route", id: route.id, title: route.name, subtitle: route.headsign });
    }
  }

  for (const stop of stops) {
    if (stop.name.toLowerCase().includes(q) || stop.id.toLowerCase().includes(q)) {
      results.push({ type: "stop", id: stop.id, title: stop.name, subtitle: `Stop ${stop.id}` });
    }
  }

  return results.slice(0, 8);
}
