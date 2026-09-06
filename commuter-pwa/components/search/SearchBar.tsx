"use client";

import { useMemo, useRef, useState } from "react";
import { useTransit } from "@/lib/state/TransitProvider";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { searchTransit } from "@/lib/utils/search";
import { SearchResults } from "./SearchResults";
import type { SearchResult } from "@/types/transit";

export function SearchBar() {
  const { buses, routes, stops, selectBus, selectStop } = useTransit();
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debouncedQuery = useDebouncedValue(query, 180);

  const results = useMemo(
    () => searchTransit(debouncedQuery, { buses, routes, stops }),
    [debouncedQuery, buses, routes, stops]
  );

  function handleSelect(result: SearchResult) {
    if (result.type === "bus") selectBus(result.id);
    else if (result.type === "stop") selectStop(result.id);
    else {
      // Route selected — select its first matching live bus, if any.
      const bus = buses.find((b) => b.routeId === result.id);
      if (bus) selectBus(bus.id);
    }
    setQuery("");
    setFocused(false);
    inputRef.current?.blur();
  }

  return (
    <div className="relative">
      <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2.5 shadow-[var(--shadow-elevated)] transition-shadow focus-within:shadow-md">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="shrink-0 text-muted">
          <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8" />
          <path d="m20 20-3.2-3.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <input
          ref={inputRef}
          type="search"
          role="combobox"
          aria-expanded={focused && results.length > 0}
          aria-controls="search-results"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 120)}
          placeholder="Search bus, route or stop…"
          className="w-full bg-transparent text-sm text-foreground placeholder:text-muted focus:outline-none"
        />
      </div>
      {focused && <SearchResults results={results} onSelect={handleSelect} />}
    </div>
  );
}
