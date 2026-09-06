"use client";

import { formatEtaShort, formatUpdatedAgo } from "@/lib/utils/format";
import type { Bus, Route, Stop } from "@/types/transit";

interface StopDetailsProps {
  stop: Stop;
  upcomingBuses: Bus[];
  routes: Route[];
  onSelectBus: (id: string) => void;
}

export function StopDetails({ stop, upcomingBuses, routes, onSelectBus }: StopDetailsProps) {
  const sorted = [...upcomingBuses].sort(
    (a, b) => (a.etaSeconds ?? Infinity) - (b.etaSeconds ?? Infinity)
  );

  return (
    <div>
      <div className="flex items-center gap-3">
        <span
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-lg"
          aria-hidden="true"
        >
          📍
        </span>
        <div>
          <h2 className="text-lg font-semibold uppercase tracking-tight text-foreground">
            {stop.name}
          </h2>
          <p className="text-sm text-muted">Stop {stop.id}</p>
        </div>
      </div>

      <p className="mt-5 text-xs font-medium uppercase text-muted">Next buses</p>

      {sorted.length === 0 ? (
        <p className="mt-2 rounded-xl border border-border bg-background p-3 text-sm text-muted">
          No buses heading here right now.
        </p>
      ) : (
        <ul className="mt-2 flex flex-col divide-y divide-border rounded-xl border border-border bg-background">
          {sorted.map((bus) => {
            const route = routes.find((r) => r.id === bus.routeId);
            return (
              <li key={bus.id}>
                <button
                  type="button"
                  onClick={() => onSelectBus(bus.id)}
                  className="flex w-full items-center justify-between gap-3 px-3 py-3 text-left hover:bg-surface active:scale-[0.99]"
                >
                  <span className="flex items-center gap-2 min-w-0">
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: route?.color ?? "#2643C6" }}
                      aria-hidden="true"
                    />
                    <span className="truncate text-sm font-medium text-foreground">
                      Bus {bus.id}
                    </span>
                  </span>
                  <span className="tabular text-sm font-semibold text-primary">
                    {formatEtaShort(bus.etaSeconds)}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {sorted[0] && (
        <p className="mt-3 text-xs text-muted">{formatUpdatedAgo(sorted[0].updatedAt)}</p>
      )}
    </div>
  );
}
