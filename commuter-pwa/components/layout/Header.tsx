import { ConnectionStatus } from "@/components/ui/ConnectionStatus";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function Header() {
  return (
    <header className="flex items-center justify-between gap-3 border-b border-border bg-surface/90 px-4 py-3 backdrop-blur-sm md:px-6">
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-semibold tracking-tight text-foreground">GatiSync</span>
        <span className="hidden text-xs text-muted sm:inline">Live Transit</span>
      </div>
      <div className="flex items-center gap-2">
        <ConnectionStatus />
        <ThemeToggle />
      </div>
    </header>
  );
}
