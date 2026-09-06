"use client";

import { formatUpdatedAgo } from "@/lib/utils/format";
import { useTransit } from "@/lib/state/TransitProvider";

export function OfflineBanner() {
  const { isOnline, lastUpdated } = useTransit();

  if (isOnline) return null;

  return (
    <div
      role="alert"
      className="absolute left-1/2 top-3 z-20 w-[calc(100%-1.5rem)] max-w-sm -translate-x-1/2 rounded-2xl border border-border bg-surface-elevated px-4 py-3 shadow-[var(--shadow-elevated)]"
    >
      <p className="flex items-center gap-2 text-sm font-medium text-foreground">
        <span aria-hidden="true">⚠️</span> You&apos;re offline
      </p>
      <p className="mt-0.5 text-xs text-muted">
        Showing last known bus data
        {lastUpdated ? ` · ${formatUpdatedAgo(lastUpdated)}` : ""}
      </p>
    </div>
  );
}
