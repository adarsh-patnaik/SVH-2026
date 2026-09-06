"use client";

import { formatEta, formatUpdatedAgo } from "@/lib/utils/format";
import type { Bus, Route, Stop } from "@/types/transit";

interface BusDetailsProps {
  bus: Bus;
  route?: Route;
  nextStop?: Stop;
  onViewRoute: () => void;
  onClose: () => void;
}

export function BusDetails({ bus, route, nextStop, onViewRoute, onClose }: BusDetailsProps) {
  const stale = bus.status === "unknown";

  return (
    <div>
      <div className="flex items-center gap-3">
        <span
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-lg text-white"
          style={{ backgroundColor: route?.color ?? "#2643C6" }}
          aria-hidden="true"
        >
          🚌
        </span>
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-foreground">Bus {bus.id}</h2>
          <p className="truncate text-sm text-muted">{route?.headsign ?? "Route unknown"}</p>
        </div>
      </div>

      <div className="mt-5 flex items-baseline gap-2">
        <span className={`tabular text-4xl font-semibold ${stale ? "text-muted" : "text-primary"}`}>
          {stale ? "—" : formatEta(bus.etaSeconds)}
        </span>
      </div>
      {nextStop && (
        <p className="mt-1 text-sm text-muted">
          Next stop: <span className="font-medium text-foreground">{nextStop.name}</span>
        </p>
      )}

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-border bg-background p-3">
          <p className="text-[11px] uppercase text-muted">Speed</p>
          <p className="tabular text-sm font-medium text-foreground">
            {bus.speed ? `${Math.round(bus.speed)} km/h` : "—"}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-background p-3">
          <p className="text-[11px] uppercase text-muted">Status</p>
          <p className="flex items-center gap-1.5 text-sm font-medium text-foreground">
            <span
              className={`h-2 w-2 rounded-full ${stale ? "bg-muted" : "bg-success"}`}
              aria-hidden="true"
            />
            {stale ? "Signal lost" : "Live"}
          </p>
        </div>
      </div>

      <p className="mt-4 text-xs text-muted">{formatUpdatedAgo(bus.updatedAt)}</p>

      <div className="mt-5 flex gap-2">
        <button
          type="button"
          onClick={onViewRoute}
          className="flex-1 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground active:scale-[0.98]"
        >
          View route
        </button>
        <button
          type="button"
          onClick={onClose}
          className="flex-1 rounded-xl border border-border px-4 py-2.5 text-sm font-medium text-foreground active:scale-[0.98]"
        >
          Close
        </button>
      </div>
    </div>
  );
}
