"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLiveBuses } from "@/hooks/useLiveBuses";
import { useTheme } from "@/hooks/useTheme";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { getRoutes, getStops } from "@/lib/api/transitApi";
import type {
  Bus,
  ConnectionState,
  Route,
  Stop,
  ThemeMode,
} from "@/types/transit";

interface TransitContextValue {
  buses: Bus[];
  routes: Route[];
  stops: Stop[];
  routesLoading: boolean;
  selectedBusId: string | null;
  selectedStopId: string | null;
  selectBus: (id: string | null) => void;
  selectStop: (id: string | null) => void;
  connectionState: ConnectionState;
  isOnline: boolean;
  isDemoMode: boolean;
  lastUpdated: number | null;
  theme: { mode: ThemeMode; resolvedTheme: "light" | "dark"; setMode: (m: ThemeMode) => void; toggle: () => void };
}

const TransitContext = createContext<TransitContextValue | null>(null);

export function TransitProvider({ children }: { children: ReactNode }) {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [routesLoading, setRoutesLoading] = useState(true);
  const [selectedBusId, setSelectedBusId] = useState<string | null>(null);
  const [selectedStopId, setSelectedStopId] = useState<string | null>(null);

  const { buses, connectionState, isDemoMode, lastUpdated } = useLiveBuses();
  const theme = useTheme();
  const isOnline = useNetworkStatus();

  useEffect(() => {
    let cancelled = false;
    Promise.all([getRoutes(), getStops()]).then(([r, s]) => {
      if (cancelled) return;
      setRoutes(r);
      setStops(s);
      setRoutesLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<TransitContextValue>(
    () => ({
      buses,
      routes,
      stops,
      routesLoading,
      selectedBusId,
      selectedStopId,
      selectBus: (id) => {
        setSelectedBusId(id);
        if (id) setSelectedStopId(null);
      },
      selectStop: (id) => {
        setSelectedStopId(id);
        if (id) setSelectedBusId(null);
      },
      connectionState,
      isOnline,
      isDemoMode,
      lastUpdated,
      theme,
    }),
    [
      buses,
      routes,
      stops,
      routesLoading,
      selectedBusId,
      selectedStopId,
      connectionState,
      isOnline,
      isDemoMode,
      lastUpdated,
      theme,
    ]
  );

  return <TransitContext.Provider value={value}>{children}</TransitContext.Provider>;
}

export function useTransit() {
  const ctx = useContext(TransitContext);
  if (!ctx) throw new Error("useTransit must be used within a TransitProvider");
  return ctx;
}
