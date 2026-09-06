/**
 * Single configuration seam for the map provider. GatiSync defaults to
 * Leaflet + a vector-friendly raster tile source (light on bandwidth,
 * no SDK to bundle). To move to Mapbox GL later: swap LiveMap.tsx's
 * internals for a MapboxMap implementation behind the same props
 * (buses, stops, routes, selection, center, onSelectBus, onSelectStop) —
 * no other component needs to change.
 */
export const TILE_URL =
  process.env.NEXT_PUBLIC_MAP_URL ??
  "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";

export const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

export const MAX_ZOOM = 19;
