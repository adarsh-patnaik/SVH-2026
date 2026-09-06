export default function OfflinePage() {
  return (
    <div className="flex h-dvh flex-col items-center justify-center gap-3 bg-background px-6 text-center">
      <span className="text-3xl" aria-hidden="true">
        ⚠️
      </span>
      <h1 className="text-lg font-semibold text-foreground">You&apos;re offline</h1>
      <p className="max-w-xs text-sm text-muted">
        GatiSync needs a connection to show live buses. Reconnect and reopen the app — your last
        known bus data will appear automatically.
      </p>
    </div>
  );
}
