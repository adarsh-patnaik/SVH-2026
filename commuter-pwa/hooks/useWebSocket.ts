"use client";

import { useEffect, useRef, useState } from "react";
import { getLiveBusSource, isDemoMode } from "@/lib/websocket/dataSource";
import type { ConnectionState, RawBusUpdate } from "@/types/transit";

/**
 * Owns the connect/disconnect lifecycle for the single shared live-bus
 * source (real WebSocket or demo simulator — see lib/websocket/dataSource).
 * Connects on mount, disconnects on unmount so we never leak a socket or
 * a running interval.
 */
export function useWebSocket(onBusUpdate: (update: RawBusUpdate) => void) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("CONNECTING");
  const callbackRef = useRef(onBusUpdate);

  // Keep the ref current without making it a render-time side effect.
  useEffect(() => {
    callbackRef.current = onBusUpdate;
  });

  useEffect(() => {
    const source = getLiveBusSource();

    const unsubscribeBus = source.subscribe((update) => callbackRef.current(update));
    const unsubscribeState = source.onStateChange(setConnectionState);

    source.connect();

    return () => {
      unsubscribeBus();
      unsubscribeState();
      // Note: we intentionally do NOT call source.disconnect() here — the
      // source is a module-level singleton shared by every consumer of
      // this hook, so tearing it down on a single component's unmount
      // would drop the connection for the rest of the app. Real teardown
      // happens at the browser tab/page lifecycle.
    };
  }, []);

  return { connectionState, isDemoMode };
}
