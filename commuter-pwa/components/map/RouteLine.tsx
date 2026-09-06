"use client";

import { memo } from "react";
import { Polyline } from "react-leaflet";
import type { Route } from "@/types/transit";

interface RouteLineProps {
  route: Route;
  highlighted: boolean;
}

function RouteLineImpl({ route, highlighted }: RouteLineProps) {
  return (
    <Polyline
      positions={route.path.map((p) => [p.lat, p.lng])}
      pathOptions={{
        color: route.color,
        weight: highlighted ? 4.5 : 2.5,
        opacity: highlighted ? 0.95 : 0.45,
        lineCap: "round",
        lineJoin: "round",
      }}
    />
  );
}

export const RouteLine = memo(RouteLineImpl);
