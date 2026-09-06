"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "./useWebSocket";
import { normalizeBusUpdate } from "@/lib/websocket/normalizeBusUpdate";
import { animateBusPosition } from "@/lib/utils/animateBusPosition";
import { isStale } from "@/lib/utils/format";
import type { Bus, RawBusUpdate } from "@/types/transit";

const MARKER_ANIMATION_MS = 1600; // ~ the demo simulator's tick interval

/**
 * Maintains the live bus roster: normalizes raw messages, keeps each bus's
 * on-screen position animating smoothly between fixes (never teleporting),
 * and marks buses "delayed"/stale when updates stop arriving.
 */
export function useLiveBuses() {
  const [buses, setBuses] = useState<Record<string, Bus>>({});
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const cancelAnimations = useRef<Map<string, () => void>>(new Map());
  const reduceMotion = useRef(false);

  useEffect(() => {
    reduceMotion.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = () => (reduceMotion.current = mq.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const handleUpdate = useCallback((raw: RawBusUpdate) => {
    setBuses((prev) => {
      const previousBus = prev[String(raw.busId ?? raw.vehicle_id)];
      const normalized = normalizeBusUpdate(raw, previousBus);
      if (!normalized) return prev; // malformed — dropped silently

      // Cancel any in-flight animation for this bus before starting a new one.
      cancelAnimations.current.get(normalized.id)?.();

      const startLat = previousBus?.lat ?? normalized.lat;
      const startLng = previousBus?.lng ?? normalized.lng;

      if (reduceMotion.current || !previousBus) {
        return { ...prev, [normalized.id]: normalized };
      }

      const cancel = animateBusPosition({
        previousPosition: { lat: startLat, lng: startLng },
        nextPosition: { lat: normalized.lat, lng: normalized.lng },
        duration: MARKER_ANIMATION_MS,
        onFrame: (pos) => {
          setBuses((cur) => {
            const existing = cur[normalized.id];
            if (!existing) return cur;
            return { ...cur, [normalized.id]: { ...existing, lat: pos.lat, lng: pos.lng } };
          });
        },
      });
      cancelAnimations.current.set(normalized.id, cancel);

      // Commit the authoritative (final) fields immediately; lat/lng will
      // keep animating toward normalized.lat/lng via the frames above.
      return {
        ...prev,
        [normalized.id]: { ...normalized, lat: startLat, lng: startLng },
      };
    });
    setLastUpdated(Date.now());
  }, []);

  const { connectionState, isDemoMode } = useWebSocket(handleUpdate);

  useEffect(() => {
    const animations = cancelAnimations.current;
    return () => {
      animations.forEach((cancel) => cancel());
      animations.clear();
    };
  }, []);

  const busList = Object.values(buses).map((bus) => ({
    ...bus,
    status: isStale(bus.updatedAt) ? ("unknown" as const) : bus.status,
  }));

  return { buses: busList, connectionState, isDemoMode, lastUpdated };
}
