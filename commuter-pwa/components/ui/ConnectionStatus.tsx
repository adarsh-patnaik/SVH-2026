"use client";

import { useTransit } from "@/lib/state/TransitProvider";

const COPY: Record<string, { label: string; dotClass: string; pulse: boolean }> = {
  CONNECTED: { label: "Live", dotClass: "bg-success", pulse: true },
  CONNECTING: { label: "Connecting", dotClass: "bg-live", pulse: true },
  RECONNECTING: { label: "Reconnecting", dotClass: "bg-live", pulse: true },
  DISCONNECTED: { label: "Offline", dotClass: "bg-danger", pulse: false },
  ERROR: { label: "Connection issue", dotClass: "bg-danger", pulse: false },
};

export function ConnectionStatus() {
  const { connectionState, isOnline, isDemoMode } = useTransit();
  const effectiveState = !isOnline ? "DISCONNECTED" : connectionState;
  const info = COPY[effectiveState] ?? COPY.DISCONNECTED;

  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-xs font-medium text-foreground"
      role="status"
      aria-live="polite"
    >
      <span className="relative flex h-2 w-2 shrink-0">
        <span className={`h-2 w-2 rounded-full ${info.dotClass}`} />
        {info.pulse && (
          <span
            className={`absolute inline-flex h-2 w-2 rounded-full ${info.dotClass}`}
            style={{ animation: "live-pulse 1.8s ease-out infinite" }}
            aria-hidden="true"
          />
        )}
      </span>
      <span>{info.label}</span>
      {isDemoMode && (
        <span className="ml-1 rounded border border-border px-1 text-[10px] uppercase tracking-wide text-muted">
          Demo
        </span>
      )}
    </div>
  );
}
