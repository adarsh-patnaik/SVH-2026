"use client";

import { MapContainer, TileLayer, Marker, useMap } from "react-leaflet";
import { useEffect } from "react";
import { BusMarker } from "./BusMarker";
import { StopMarker } from "./StopMarker";
import { RouteLine } from "./RouteLine";
import { MapControls, fitToBounds } from "./MapControls";
import { userLocationIcon } from "@/lib/map/icons";
import { TILE_ATTRIBUTION, TILE_URL, MAX_ZOOM } from "@/lib/map/mapConfig";
import { DEMO_CITY } from "@/lib/demo/demoData";
import { useTransit } from "@/lib/state/TransitProvider";
import { useGeolocation } from "@/hooks/useGeolocation";

function FitToSelectedRoute({ routeId }: { routeId: string | null }) {
  const map = useMap();
  const { routes } = useTransit();

  useEffect(() => {
    if (!routeId) return;
    const route = routes.find((r) => r.id === routeId);
    if (!route) return;
    fitToBounds(
      map,
      route.path.map((p) => [p.lat, p.lng])
    );
  }, [routeId, routes, map]);

  return null;
}

interface LiveMapProps {
  /** px to dock the zoom/locate controls above on mobile, so they never overlap the persistent bottom bus card. */
  dockedBottomPx?: number;
}

export function LiveMap({ dockedBottomPx }: LiveMapProps) {
  const { buses, routes, stops, selectedBusId, selectedStopId, selectBus, selectStop } =
    useTransit();
  const { position, locate } = useGeolocation();

  const selectedBus = buses.find((b) => b.id === selectedBusId);

  return (
    <MapContainer
      center={[DEMO_CITY.center.lat, DEMO_CITY.center.lng]}
      zoom={DEMO_CITY.zoom}
      zoomControl={false}
      className="h-full w-full"
      attributionControl={true}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} maxZoom={MAX_ZOOM} />

      {routes.map((route) => (
        <RouteLine key={route.id} route={route} highlighted={selectedBus?.routeId === route.id} />
      ))}

      {stops.map((stop) => (
        <StopMarker
          key={stop.id}
          stop={stop}
          selected={stop.id === selectedStopId}
          onSelect={selectStop}
        />
      ))}

      {buses.map((bus) => (
        <BusMarker
          key={bus.id}
          bus={bus}
          route={routes.find((r) => r.id === bus.routeId)}
          selected={bus.id === selectedBusId}
          onSelect={selectBus}
        />
      ))}

      {position && (
        <Marker
          position={[position.lat, position.lng]}
          icon={userLocationIcon()}
          alt="Your current location"
          keyboard={false}
        />
      )}

      <MapControls onLocateRequest={locate} userPosition={position} dockedBottomPx={dockedBottomPx} />
      <FitToSelectedRoute routeId={selectedBus?.routeId ?? null} />
    </MapContainer>
  );
}
