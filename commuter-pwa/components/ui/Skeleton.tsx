export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-md ${className}`} aria-hidden="true" />;
}

export function BusCardSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4" aria-hidden="true">
      <div className="flex items-center gap-2">
        <Skeleton className="h-8 w-8 rounded-full" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="mt-3 h-3 w-40" />
      <Skeleton className="mt-4 h-7 w-20" />
      <Skeleton className="mt-3 h-3 w-32" />
    </div>
  );
}

export function MapSkeleton() {
  return (
    <div className="skeleton absolute inset-0" role="status" aria-label="Loading map">
      <span className="sr-only">Loading map…</span>
    </div>
  );
}
