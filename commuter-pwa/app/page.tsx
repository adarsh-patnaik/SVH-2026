"use client";

import { Header } from "@/components/layout/Header";
import { OfflineBanner } from "@/components/layout/OfflineBanner";
import { LiveMapLoader } from "@/components/map/LiveMapLoader";
import { SearchBar } from "@/components/search/SearchBar";
import { BusList } from "@/components/bus/BusList";
import { BusCard } from "@/components/bus/BusCard";
import { BusCardSkeleton } from "@/components/ui/Skeleton";
import { BusDetails } from "@/components/bus/BusDetails";
import { StopDetails } from "@/components/stop/StopDetails";
import { EmptyState } from "@/components/ui/EmptyState";
import { BottomSheet } from "@/components/ui/BottomSheet";
import { useTransit } from "@/lib/state/TransitProvider";

// How much room (px) the persistent bottom card/skeleton/empty-state needs,
// so the floating zoom/locate controls can dock themselves above it instead
// of overlapping it. See .gs-map-controls in globals.css.
const BOTTOM_DOCK_CLEARANCE_PX = 190;

export default function Home() {
  const {
    buses,
    routes,
    stops,
    routesLoading,
    connectionState,
    selectedBusId,
    selectedStopId,
    selectBus,
    selectStop,
  } = useTransit();

  const selectedBus = buses.find((b) => b.id === selectedBusId) ?? null;
  const selectedStop = stops.find((s) => s.id === selectedStopId) ?? null;
  const cardBus = selectedBus ?? buses[0] ?? null;
  const sheetOpen = Boolean(selectedBus || selectedStop);

  // Exactly one of these occupies the bottom-docked slot on mobile at a
  // time — never stacked, never simultaneous — so there is only ever one
  // thing there for the map controls to dodge.
  const bottomSlot: "card" | "loading" | "empty" | null = sheetOpen
    ? null
    : cardBus
      ? "card"
      : routesLoading || connectionState === "CONNECTING" || connectionState === "RECONNECTING"
        ? "loading"
        : "empty";

  return (
    <div className="flex h-dvh flex-col bg-background">
      <Header />

      <div className="relative flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <aside className="hidden w-[360px] shrink-0 flex-col gap-4 overflow-y-auto border-r border-border bg-background p-4 md:flex">
          <SearchBar />
          {routes.length === 0 && !routesLoading ? (
            <EmptyState title="No route data" description="Couldn't load routes right now." />
          ) : (
            <BusList
              buses={buses}
              routes={routes}
              stops={stops}
              loading={routesLoading}
              onSelectBus={selectBus}
            />
          )}
        </aside>

        {/* Map */}
        <main className="relative flex-1">
          <LiveMapLoader
            dockedBottomPx={bottomSlot ? BOTTOM_DOCK_CLEARANCE_PX : undefined}
          />
          <OfflineBanner />

          {/* Mobile-only floating search */}
          <div className="pointer-events-none absolute left-3 right-3 top-3 z-20 md:hidden">
            <div className="pointer-events-auto">
              <SearchBar />
            </div>
          </div>

          {/* Mobile-only bottom-docked slot: card, loading skeleton, or
              empty state — always exactly one, never overlapping the map
              controls (which read bottomSlot via dockedBottomPx above) or
              each other. */}
          {bottomSlot && (
            <div className="pointer-events-none absolute inset-x-3 bottom-3 z-20 flex justify-center transition-opacity duration-200 md:hidden">
              <div className="pointer-events-auto w-full">
                {bottomSlot === "card" && cardBus && (
                  <BusCard
                    bus={cardBus}
                    route={routes.find((r) => r.id === cardBus.routeId)}
                    nextStop={stops.find((s) => s.id === cardBus.nextStopId)}
                    onOpenDetails={() => selectBus(cardBus.id)}
                  />
                )}
                {bottomSlot === "loading" && <BusCardSkeleton />}
                {bottomSlot === "empty" && (
                  <EmptyState title="No buses nearby" description="Check back in a moment." />
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      <BottomSheet
        open={sheetOpen}
        onClose={() => {
          selectBus(null);
          selectStop(null);
        }}
        title={selectedBus ? `Bus ${selectedBus.id}` : selectedStop?.name ?? "Details"}
      >
        {selectedBus && (
          <BusDetails
            bus={selectedBus}
            route={routes.find((r) => r.id === selectedBus.routeId)}
            nextStop={stops.find((s) => s.id === selectedBus.nextStopId)}
            onViewRoute={() => {
              /* Map already highlights the route on selection */
            }}
            onClose={() => selectBus(null)}
          />
        )}
        {selectedStop && (
          <StopDetails
            stop={selectedStop}
            upcomingBuses={buses.filter((b) => b.nextStopId === selectedStop.id)}
            routes={routes}
            onSelectBus={selectBus}
          />
        )}
      </BottomSheet>
    </div>
  );
}
