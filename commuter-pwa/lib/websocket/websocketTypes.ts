import type { ConnectionState, RawBusUpdate } from "@/types/transit";

export type WebSocketInboundMessage =
  | { type: "bus_update"; data: RawBusUpdate }
  | { type: "bus_updates"; data: RawBusUpdate[] }
  | { type: "ping" };

export interface WebSocketManagerOptions {
  url: string;
  /** Called with every normalized connection-state transition. */
  onStateChange?: (state: ConnectionState) => void;
  onBusUpdate?: (update: RawBusUpdate) => void;
  /** Base backoff step in ms. Doubles each retry up to maxBackoffMs. */
  baseBackoffMs?: number;
  maxBackoffMs?: number;
}

export type Unsubscribe = () => void;
