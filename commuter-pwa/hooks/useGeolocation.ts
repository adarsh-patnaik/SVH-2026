"use client";

import { useCallback, useState } from "react";
import type { LatLng } from "@/types/transit";

interface GeolocationState {
  position: LatLng | null;
  error: string | null;
  loading: boolean;
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    position: null,
    error: null,
    loading: false,
  });

  const locate = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setState({ position: null, error: "GPS not available on this device", loading: false });
      return;
    }
    setState((s) => ({ ...s, loading: true, error: null }));
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          position: { lat: pos.coords.latitude, lng: pos.coords.longitude },
          error: null,
          loading: false,
        });
      },
      () => {
        setState((s) => ({ ...s, loading: false, error: "Couldn't get your location" }));
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 15000 }
    );
  }, []);

  return { ...state, locate };
}
