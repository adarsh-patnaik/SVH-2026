import type { ConnectionState, RawBusUpdate } from "@/types/transit";
import type {
  Unsubscribe,
  WebSocketInboundMessage,
  WebSocketManagerOptions,
} from "./websocketTypes";

type BusListener = (update: RawBusUpdate) => void;
type StateListener = (state: ConnectionState) => void;

/**
 * Owns exactly one WebSocket connection for the whole app.
 * Multiple hooks/components can subscribe() without opening extra sockets.
 */
export class WebSocketManager {
  private url: string;
  private socket: WebSocket | null = null;
  private state: ConnectionState = "DISCONNECTED";
  private busListeners = new Set<BusListener>();
  private stateListeners = new Set<StateListener>();
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyClosed = false;
  private readonly baseBackoffMs: number;
  private readonly maxBackoffMs: number;

  constructor(options: WebSocketManagerOptions) {
    this.url = options.url;
    this.baseBackoffMs = options.baseBackoffMs ?? 1000;
    this.maxBackoffMs = options.maxBackoffMs ?? 30_000;
    if (options.onBusUpdate) this.busListeners.add(options.onBusUpdate);
    if (options.onStateChange) this.stateListeners.add(options.onStateChange);
  }

  connect(): void {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return; // already connecting/connected — never open a second socket
    }

    this.manuallyClosed = false;
    this.setState(this.reconnectAttempt > 0 ? "RECONNECTING" : "CONNECTING");

    try {
      this.socket = new WebSocket(this.url);
    } catch {
      this.setState("ERROR");
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.setState("CONNECTED");
    };

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data);
    };

    this.socket.onerror = () => {
      this.setState("ERROR");
    };

    this.socket.onclose = () => {
      if (this.manuallyClosed) {
        this.setState("DISCONNECTED");
        return;
      }
      this.scheduleReconnect();
    };
  }

  disconnect(): void {
    this.manuallyClosed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.socket?.close();
    this.socket = null;
    this.setState("DISCONNECTED");
  }

  subscribe(listener: BusListener): Unsubscribe {
    this.busListeners.add(listener);
    return () => this.busListeners.delete(listener);
  }

  onStateChange(listener: StateListener): Unsubscribe {
    this.stateListeners.add(listener);
    listener(this.state);
    return () => this.stateListeners.delete(listener);
  }

  getState(): ConnectionState {
    return this.state;
  }

  private scheduleReconnect(): void {
    if (this.manuallyClosed) return;
    this.setState("RECONNECTING");
    const delay = Math.min(
      this.baseBackoffMs * 2 ** this.reconnectAttempt,
      this.maxBackoffMs
    );
    this.reconnectAttempt += 1;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  private setState(state: ConnectionState): void {
    this.state = state;
    this.stateListeners.forEach((l) => l(state));
  }

  private handleMessage(raw: string): void {
    let parsed: WebSocketInboundMessage;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return; // ignore malformed frames rather than crash the app
    }

    if (parsed.type === "bus_update" && parsed.data) {
      this.busListeners.forEach((l) => l(parsed.data));
    } else if (parsed.type === "bus_updates" && Array.isArray(parsed.data)) {
      parsed.data.forEach((update) => this.busListeners.forEach((l) => l(update)));
    }
    // "ping" and anything else is intentionally ignored.
  }
}
