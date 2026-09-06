"use client";

import { useMap } from "react-leaflet";
import { useEffect, useRef, type CSSProperties } from "react";
import L from "leaflet";
import type { LatLng } from "@/types/transit";

interface MapControlsProps {
  onLocateRequest: () => void;
  userPosition: LatLng | null;
  /** px to dock above, on mobile only (see .gs-map-controls in globals.css) — pass when a persistent bottom card/empty-state is on screen so controls never overlap it. */
  dockedBottomPx?: number;
}

export function MapControls({ onLocateRequest, userPosition, dockedBottomPx }: MapControlsProps) {
  const map = useMap();
  const hasFlownTo = useRef(false);

  useEffect(() => {
    if (userPosition && !hasFlownTo.current) {
      hasFlownTo.current = true;
      map.flyTo([userPosition.lat, userPosition.lng], Math.max(map.getZoom(), 15), {
        duration: 0.6,
      });
    }
  }, [userPosition, map]);

  return (
    <div
      className="gs-map-controls pointer-events-none absolute right-3 z-20 flex flex-col items-end gap-2"
      style={dockedBottomPx ? ({ "--dock-offset": `${dockedBottomPx}px` } as CSSProperties) : undefined}
    >
      <div className="pointer-events-auto flex flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[var(--shadow-elevated)]">
        <button
          type="button"
          aria-label="Zoom in"
          onClick={() => map.zoomIn()}
          className="flex h-9 w-9 items-center justify-center text-lg text-foreground hover:bg-background active:scale-95"
        >
          +
        </button>
        <div className="h-px w-full bg-border" />
        <button
          type="button"
          aria-label="Zoom out"
          onClick={() => map.zoomOut()}
          className="flex h-9 w-9 items-center justify-center text-lg text-foreground hover:bg-background active:scale-95"
        >
          −
        </button>
      </div>

      <button
        type="button"
        onClick={() => {
          hasFlownTo.current = false;
          onLocateRequest();
        }}
        aria-label="Locate me"
        className="pointer-events-auto flex h-11 items-center gap-2 rounded-full border border-border bg-surface px-4 text-sm font-medium text-foreground shadow-[var(--shadow-elevated)] hover:bg-background active:scale-95"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="M12 2v3M12 19v3M22 12h-3M5 12H2"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
        Locate me
      </button>
    </div>
  );
}

export function fitToBounds(map: L.Map, points: [number, number][]) {
  if (points.length === 0) return;
  map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 16 });
}
