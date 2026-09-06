import type { Route, Stop } from "@/types/transit";

// Demo city: Jalandhar, Punjab — a representative Tier-2 city.
// Coordinates are approximate but real (not randomly generated), so the
// map looks and feels like an actual city rather than a toy grid.
export const DEMO_CITY = {
  name: "Jalandhar",
  center: { lat: 31.326, lng: 75.5762 },
  zoom: 13,
};

export const DEMO_STOPS: Stop[] = [
  { id: "STOP01", name: "Bus Stand", lat: 31.3260, lng: 75.5762 },
  { id: "STOP02", name: "Ladowali Road", lat: 31.3212, lng: 75.5820 },
  { id: "STOP03", name: "Model Town Chowk", lat: 31.3305, lng: 75.5960 },
  { id: "STOP04", name: "Civil Lines", lat: 31.3260, lng: 75.5680 },
  { id: "STOP05", name: "Railway Station", lat: 31.3160, lng: 75.5690 },
  { id: "STOP06", name: "Urban Estate", lat: 31.3410, lng: 75.5750 },
  { id: "STOP07", name: "PAP Chowk", lat: 31.3395, lng: 75.5870 },
  { id: "STOP08", name: "Nakodar Chowk", lat: 31.3050, lng: 75.5860 },
];

const byId = (id: string) => DEMO_STOPS.find((s) => s.id === id)!;

export const DEMO_ROUTES: Route[] = [
  {
    id: "R12",
    name: "Route 12",
    shortName: "R12",
    headsign: "Railway Station → Model Town",
    color: "#2643C6",
    stops: [
      { stopId: "STOP05", sequence: 0 },
      { stopId: "STOP01", sequence: 1 },
      { stopId: "STOP02", sequence: 2 },
      { stopId: "STOP03", sequence: 3 },
    ],
    path: [
      byId("STOP05"),
      { lat: 31.3200, lng: 75.5730 },
      byId("STOP01"),
      byId("STOP02"),
      { lat: 31.3260, lng: 75.5890 },
      byId("STOP03"),
    ],
  },
  {
    id: "R14",
    name: "Route 14",
    shortName: "R14",
    headsign: "Bus Stand → Civil Lines",
    color: "#F2A93B",
    stops: [
      { stopId: "STOP01", sequence: 0 },
      { stopId: "STOP04", sequence: 1 },
    ],
    path: [byId("STOP01"), { lat: 31.3260, lng: 75.5720 }, byId("STOP04")],
  },
  {
    id: "R18",
    name: "Route 18",
    shortName: "R18",
    headsign: "Urban Estate → Railway Station",
    color: "#1F9D66",
    stops: [
      { stopId: "STOP06", sequence: 0 },
      { stopId: "STOP07", sequence: 1 },
      { stopId: "STOP01", sequence: 2 },
      { stopId: "STOP08", sequence: 3 },
      { stopId: "STOP05", sequence: 4 },
    ],
    path: [
      byId("STOP06"),
      byId("STOP07"),
      { lat: 31.3330, lng: 75.5810 },
      byId("STOP01"),
      { lat: 31.3150, lng: 75.5810 },
      byId("STOP08"),
      { lat: 31.3100, lng: 75.5760 },
      byId("STOP05"),
    ],
  },
];

/** Static seed for demo buses — the simulator moves these along their route path. */
export const DEMO_BUS_SEEDS: {
  id: string;
  routeId: string;
  pathProgress: number; // 0..1 starting position along the route path
  speedKmh: number;
}[] = [
  { id: "402", routeId: "R12", pathProgress: 0.05, speedKmh: 28 },
  { id: "405", routeId: "R12", pathProgress: 0.55, speedKmh: 24 },
  { id: "410", routeId: "R14", pathProgress: 0.2, speedKmh: 20 },
  { id: "415", routeId: "R18", pathProgress: 0.1, speedKmh: 32 },
  { id: "421", routeId: "R18", pathProgress: 0.6, speedKmh: 26 },
  { id: "430", routeId: "R14", pathProgress: 0.7, speedKmh: 22 },
];
