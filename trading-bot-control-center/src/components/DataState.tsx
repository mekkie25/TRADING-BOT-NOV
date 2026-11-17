import type { ReactNode } from 'react';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';

interface PanelSkeletonProps {
  rows?: number;
  heightClass?: string;
}

export function PanelSkeleton({ rows = 4, heightClass }: PanelSkeletonProps) {
  if (heightClass) {
    return (
      <div className={`w-full rounded-lg bg-slate-200/80 dark:bg-slate-800/40 animate-pulse ${heightClass}`} />
    );
  }
  return (
    <div className="space-y-3 py-2" aria-busy="true" aria-label="Loading panel data">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-9 w-full rounded-md bg-slate-200/80 dark:bg-slate-800/50 animate-pulse"
          style={{ opacity: 1 - i * 0.12 }}
        />
      ))}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-slate-100 text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        {icon || <Inbox className="h-5 w-5" />}
      </div>
      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{title}</p>
      <p className="mt-1 max-w-md text-xs text-slate-500 dark:text-slate-400">{description}</p>
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 rounded-md border border-slate-300 bg-slate-100 px-3.5 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg border border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400">
        <AlertCircle className="h-5 w-5" />
      </div>
      <p className="text-sm font-medium text-red-700 dark:text-red-300">Unable to load panel data</p>
      <p className="mt-1 max-w-md text-xs text-slate-500 dark:text-slate-400">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-slate-100 px-3.5 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      )}
    </div>
  );
}

interface PanelShellProps {
  title: string;
  subtitle?: string;
  headerRight?: ReactNode;
  isLoading: boolean;
  error: string | null;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  onRetry?: () => void;
  skeletonHeightClass?: string;
  skeletonRows?: number;
  children: ReactNode;
  className?: string;
}

export function PanelShell({
  title,
  subtitle,
  headerRight,
  isLoading,
  error,
  isEmpty = false,
  emptyTitle = 'No records available',
  emptyDescription = 'Adjust your filters or wait for new data from the backend.',
  emptyActionLabel,
  onEmptyAction,
  onRetry,
  skeletonHeightClass,
  skeletonRows = 4,
  children,
  className = '',
}: PanelShellProps) {
  return (
    <section
      className={`rounded-xl border border-slate-200 bg-white dark:border-slate-800/90 dark:bg-[#111824] p-5 ${className}`}
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            {title}
          </h2>
          {subtitle && (
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
          )}
        </div>
        {headerRight && <div className="flex items-center gap-2 shrink-0">{headerRight}</div>}
      </div>

      {isLoading ? (
        <PanelSkeleton rows={skeletonRows} heightClass={skeletonHeightClass} />
      ) : error ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : isEmpty ? (
        <EmptyState
          title={emptyTitle}
          description={emptyDescription}
          actionLabel={emptyActionLabel}
          onAction={onEmptyAction}
        />
      ) : (
        children
      )}
    </section>
  );
}
