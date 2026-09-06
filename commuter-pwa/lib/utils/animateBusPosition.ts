import type { LatLng } from "@/types/transit";

/** Ease-out cubic — quick start, gentle settle, feels like a real vehicle arriving at a fix. */
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export interface AnimateBusPositionOptions {
  previousPosition: LatLng;
  nextPosition: LatLng;
  /** ms */
  duration: number;
  onFrame: (position: LatLng, progress: number) => void;
  onComplete?: () => void;
}

/**
 * Smoothly interpolates a bus marker between two GPS fixes using
 * requestAnimationFrame instead of snapping the marker to the new
 * coordinate. Returns a cancel function — always call it on unmount
 * or before starting a new animation for the same marker, otherwise
 * two rAF loops can fight over the same DOM node and cause jitter.
 */
export function animateBusPosition({
  previousPosition,
  nextPosition,
  duration,
  onFrame,
  onComplete,
}: AnimateBusPositionOptions): () => void {
  let rafId: number | null = null;
  let cancelled = false;
  const start = performance.now();

  // Nothing to animate — snap once and bail.
  if (
    previousPosition.lat === nextPosition.lat &&
    previousPosition.lng === nextPosition.lng
  ) {
    onFrame(nextPosition, 1);
    onComplete?.();
    return () => {};
  }

  function tick(now: number) {
    if (cancelled) return;
    const elapsed = now - start;
    const t = Math.min(1, duration <= 0 ? 1 : elapsed / duration);
    const eased = easeOutCubic(t);

    onFrame(
      {
        lat: previousPosition.lat + (nextPosition.lat - previousPosition.lat) * eased,
        lng: previousPosition.lng + (nextPosition.lng - previousPosition.lng) * eased,
      },
      t
    );

    if (t < 1) {
      rafId = requestAnimationFrame(tick);
    } else {
      onComplete?.();
    }
  }

  rafId = requestAnimationFrame(tick);

  return () => {
    cancelled = true;
    if (rafId !== null) cancelAnimationFrame(rafId);
  };
}
