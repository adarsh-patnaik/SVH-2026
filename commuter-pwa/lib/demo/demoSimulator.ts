import type { ConnectionState, RawBusUpdate } from "@/types/transit";
import { DEMO_BUS_SEEDS, DEMO_ROUTES } from "./demoData";
import { pathLength, pointAlongPath } from "@/lib/utils/geo";

type BusListener = (update: RawBusUpdate) => void;
type StateListener = (state: ConnectionState) => void;

/**
 * Simulates the live-bus WebSocket feed for the hackathon demo / offline
 * development. It exposes the exact same connect/disconnect/subscribe
 * surface as WebSocketManager so the rest of the app (state store, hooks,
 * map) never needs to know which source is active.
 */
export class DemoSimulator {
  private busListeners = new Set<BusListener>();
  private stateListeners = new Set<StateListener>();
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private progress = new Map<string, number>();
  private readonly tickMs = 2000;

  constructor() {
    DEMO_BUS_SEEDS.forEach((seed) => this.progress.set(seed.id, seed.pathProgress));
  }

  connect(): void {
    this.setState("CONNECTING");
    // Small artificial delay so the connection indicator reads naturally.
    setTimeout(() => {
      this.setState("CONNECTED");
      this.tick(); // emit an immediate frame so the UI isn't empty
      this.intervalId = setInterval(() => this.tick(), this.tickMs);
    }, 400);
  }

  disconnect(): void {
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = null;
    this.setState("DISCONNECTED");
  }

  subscribe(listener: BusListener) {
    this.busListeners.add(listener);
    return () => this.busListeners.delete(listener);
  }

  onStateChange(listener: StateListener) {
    this.stateListeners.add(listener);
    listener("DISCONNECTED");
    return () => this.stateListeners.delete(listener);
  }

  private setState(state: ConnectionState) {
    this.stateListeners.forEach((l) => l(state));
  }

  private tick() {
    for (const seed of DEMO_BUS_SEEDS) {
      const route = DEMO_ROUTES.find((r) => r.id === seed.routeId);
      if (!route) continue;

      const current = this.progress.get(seed.id) ?? 0;
      const totalMetres = pathLength(route.path);
      const metresPerTick = ((seed.speedKmh * 1000) / 3600) * (this.tickMs / 1000);
      const deltaProgress = totalMetres > 0 ? metresPerTick / totalMetres : 0;

      // Loop back to the start once the bus reaches the end of the route.
      let next = current + deltaProgress;
      if (next >= 1) next -= 1;
      this.progress.set(seed.id, next);

      const { point, heading } = pointAlongPath(route.path, next);
      const remainingMetres = (1 - next) * totalMetres;
      const etaSeconds = seed.speedKmh > 0 ? (remainingMetres / (seed.speedKmh * 1000)) * 3600 : 0;

      const nextStop = route.stops[Math.min(route.stops.length - 1, Math.floor(next * route.stops.length))];

      const update: RawBusUpdate = {
        busId: seed.id,
        routeId: seed.routeId,
        lat: point.lat,
        lng: point.lng,
        speed: seed.speedKmh,
        heading,
        timestamp: Math.floor(Date.now() / 1000),
        nextStopId: nextStop?.stopId,
        etaSeconds: Math.max(0, Math.round(etaSeconds)),
      };

      this.busListeners.forEach((l) => l(update));
    }
  }
}
