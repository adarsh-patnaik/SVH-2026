import { WebSocketManager } from "./websocketManager";
import { DemoSimulator } from "@/lib/demo/demoSimulator";
import type { ConnectionState, RawBusUpdate } from "@/types/transit";

export interface LiveBusSource {
  connect(): void;
  disconnect(): void;
  subscribe(listener: (update: RawBusUpdate) => void): () => void;
  onStateChange(listener: (state: ConnectionState) => void): () => void;
}

let singleton: LiveBusSource | null = null;
export let isDemoMode = false;

/**
 * Single seam for choosing demo vs. real backend. Switching to production
 * is a config change (NEXT_PUBLIC_WS_URL set + NEXT_PUBLIC_DEMO_MODE
 * unset) — no UI or component rewrite required, per the architecture
 * requirement that demo and real data share one pipeline.
 */
export function getLiveBusSource(): LiveBusSource {
  if (singleton) return singleton;

  const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
  const forceDemo = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

  if (wsUrl && !forceDemo) {
    isDemoMode = false;
    singleton = new WebSocketManager({ url: wsUrl });
  } else {
    isDemoMode = true;
    singleton = new DemoSimulator();
  }

  return singleton;
}
