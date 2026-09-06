/** Formats ETA seconds into commuter-friendly copy. Never shows decimal minutes. */
export function formatEta(etaSeconds: number | undefined): string {
  if (etaSeconds === undefined || etaSeconds < 0) return "—";
  const minutes = Math.round(etaSeconds / 60);

  if (minutes < 2) return "Arriving";
  if (minutes <= 10) return `Arriving in ${minutes} min`;
  if (minutes <= 60) return `${minutes} min`;

  const hours = Math.floor(minutes / 60);
  const rem = minutes % 60;
  return rem === 0 ? `${hours}h` : `${hours}h ${rem} min`;
}

/** Short badge form used inside compact cards, e.g. "5 min" / "Arriving". */
export function formatEtaShort(etaSeconds: number | undefined): string {
  if (etaSeconds === undefined || etaSeconds < 0) return "—";
  const minutes = Math.round(etaSeconds / 60);
  if (minutes < 2) return "Now";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rem = minutes % 60;
  return rem === 0 ? `${hours}h` : `${hours}h ${rem}m`;
}

/** "Updated 8 sec ago" style relative freshness copy. */
export function formatUpdatedAgo(updatedAt: number, now: number = Date.now()): string {
  const diffSec = Math.max(0, Math.round((now - updatedAt) / 1000));
  if (diffSec < 5) return "Updated just now";
  if (diffSec < 60) return `Updated ${diffSec} sec ago`;
  const min = Math.floor(diffSec / 60);
  if (min < 60) return `Updated ${min} min ago`;
  const hr = Math.floor(min / 60);
  return `Updated ${hr}h ago`;
}

/** Data is considered stale if we haven't heard from the backend in a while. */
export function isStale(updatedAt: number, staleAfterMs = 45_000, now: number = Date.now()): boolean {
  return now - updatedAt > staleAfterMs;
}
