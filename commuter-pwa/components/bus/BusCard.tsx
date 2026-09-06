"use client";

import { useEffect, useState } from "react";
import { formatEta, formatUpdatedAgo } from "@/lib/utils/format";
import type { Bus, Route, Stop } from "@/types/transit";

interface BusCardProps {
  bus: Bus;
  route?: Route;
  nextStop?: Stop;
  onOpenDetails: () => void;
}

export function BusCard({ bus, route, nextStop, onOpenDetails }: BusCardProps) {
  // Re-render once a second purely to keep "Updated N sec ago" fresh —
  // cheap, since it's a single text node, not a re-fetch.
  const [, forceTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => forceTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const stale = bus.status === "unknown";

  return (
    <button
      type="button"
      onClick={onOpenDetails}
      className="theme-transition group flex w-full flex-col gap-2 rounded-2xl border border-border bg-surface-elevated p-4 text-left shadow-[var(--shadow-elevated)] transition-transform active:scale-[0.99]"
    >
      <div className="flex items-center gap-2">
        <span
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
          style={{ backgroundColor: route?.color ?? "#2643C6" }}
          aria-hidden="true"
        >
          🚌
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-foreground">Bus {bus.id}</p>
          <p className="truncate text-xs text-muted">{route?.headsign ?? "Route unknown"}</p>
        </div>
      </div>

      <div className="flex items-end justify-between gap-3">
        <div>
          <p className={`tabular text-2xl font-semibold ${stale ? "text-muted" : "text-foreground"}`}>
            {stale ? "—" : formatEta(bus.etaSeconds)}
          </p>
          {nextStop && !stale && (
            <p className="text-xs text-muted">
              Next: <span className="text-foreground">{nextStop.name}</span>
            </p>
          )}
        </div>
        <p className="text-[11px] text-muted">
          {stale ? "Live data unavailable" : formatUpdatedAgo(bus.updatedAt)}
        </p>
      </div>
    </button>
  );
}
