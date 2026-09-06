interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon = "🚌", title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-border bg-surface p-6 text-center">
      <span className="text-2xl" aria-hidden="true">
        {icon}
      </span>
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="text-xs text-muted">{description}</p>}
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-2 rounded-full bg-primary px-4 py-2 text-xs font-medium text-primary-foreground active:scale-95"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
