"use client";

import { BusCard } from "./BusCard";
import { BusCardSkeleton } from "@/components/ui/Skeleton";
import type { Bus, Route, Stop } from "@/types/transit";

interface BusListProps {
  buses: Bus[];
  routes: Route[];
  stops: Stop[];
  loading: boolean;
  onSelectBus: (id: string) => void;
}

export function BusList({ buses, routes, stops, loading, onSelectBus }: BusListProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        <BusCardSkeleton />
        <BusCardSkeleton />
        <BusCardSkeleton />
      </div>
    );
  }

  if (buses.length === 0) {
    return (
      <p className="rounded-2xl border border-border bg-surface p-4 text-sm text-muted">
        No buses nearby right now.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {buses.map((bus) => (
        <BusCard
          key={bus.id}
          bus={bus}
          route={routes.find((r) => r.id === bus.routeId)}
          nextStop={stops.find((s) => s.id === bus.nextStopId)}
          onOpenDetails={() => onSelectBus(bus.id)}
        />
      ))}
    </div>
  );
}
