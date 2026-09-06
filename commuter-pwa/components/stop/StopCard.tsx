"use client";

import type { Stop } from "@/types/transit";

interface StopCardProps {
  stop: Stop;
  onSelect: (id: string) => void;
}

export function StopCard({ stop, onSelect }: StopCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(stop.id)}
      className="flex w-full items-center gap-3 rounded-xl border border-border bg-surface px-3 py-2.5 text-left hover:bg-background active:scale-[0.99]"
    >
      <span aria-hidden="true">📍</span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium text-foreground">{stop.name}</span>
        <span className="block text-xs text-muted">Stop {stop.id}</span>
      </span>
    </button>
  );
}
