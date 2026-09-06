"use client";

import { memo } from "react";
import { Marker } from "react-leaflet";
import { busIcon } from "@/lib/map/icons";
import { formatEtaShort } from "@/lib/utils/format";
import type { Bus, Route } from "@/types/transit";

interface BusMarkerProps {
  bus: Bus;
  route?: Route;
  selected: boolean;
  onSelect: (id: string) => void;
}

function BusMarkerImpl({ bus, route, selected, onSelect }: BusMarkerProps) {
  const color = route?.color ?? "#2643C6";
  const label = `Bus ${bus.id}, ${route?.headsign ?? "route unknown"}, ${
    bus.status === "unknown" ? "last seen a while ago" : formatEtaShort(bus.etaSeconds) + " away"
  }`;

  return (
    <Marker
      position={[bus.lat, bus.lng]}
      icon={busIcon(color, bus.heading ?? 0, selected)}
      alt={label}
      keyboard
      eventHandlers={{ click: () => onSelect(bus.id) }}
    />
  );
}

// Buses re-render every animation frame while moving — memoize hard so
// only the marker that actually changed re-renders, not the whole fleet.
export const BusMarker = memo(BusMarkerImpl, (prev, next) => {
  return (
    prev.bus.lat === next.bus.lat &&
    prev.bus.lng === next.bus.lng &&
    prev.bus.heading === next.bus.heading &&
    prev.bus.status === next.bus.status &&
    prev.bus.etaSeconds === next.bus.etaSeconds &&
    prev.selected === next.selected &&
    prev.route?.color === next.route?.color
  );
});
