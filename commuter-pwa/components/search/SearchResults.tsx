"use client";

import type { SearchResult } from "@/types/transit";

interface SearchResultsProps {
  results: SearchResult[];
  onSelect: (result: SearchResult) => void;
}

const ICON: Record<SearchResult["type"], string> = {
  bus: "🚌",
  route: "🛣️",
  stop: "📍",
};

export function SearchResults({ results, onSelect }: SearchResultsProps) {
  if (results.length === 0) return null;

  return (
    <ul
      role="listbox"
      className="absolute left-0 right-0 top-[calc(100%+8px)] z-30 max-h-80 overflow-y-auto rounded-2xl border border-border bg-surface-elevated p-1.5 shadow-[var(--shadow-elevated)]"
    >
      {results.map((result) => (
        <li key={`${result.type}-${result.id}`}>
          <button
            type="button"
            role="option"
            aria-selected={false}
            onClick={() => onSelect(result)}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left hover:bg-background"
          >
            <span aria-hidden="true">{ICON[result.type]}</span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium text-foreground">
                {result.title}
              </span>
              {result.subtitle && (
                <span className="block truncate text-xs text-muted">{result.subtitle}</span>
              )}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
