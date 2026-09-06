"use client";

import { memo } from "react";
import { Marker } from "react-leaflet";
import { stopIcon } from "@/lib/map/icons";
import type { Stop } from "@/types/transit";

interface StopMarkerProps {
  stop: Stop;
  selected: boolean;
  onSelect: (id: string) => void;
}

function StopMarkerImpl({ stop, selected, onSelect }: StopMarkerProps) {
  return (
    <Marker
      position={[stop.lat, stop.lng]}
      icon={stopIcon(selected)}
      alt={`${stop.name} bus stop`}
      keyboard
      eventHandlers={{ click: () => onSelect(stop.id) }}
    />
  );
}

export const StopMarker = memo(StopMarkerImpl);
