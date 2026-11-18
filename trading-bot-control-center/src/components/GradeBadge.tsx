import type { SetupGrade } from '../types';

const GRADE_STYLES: Record<SetupGrade | 'N/A', string> = {
  'A++': 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  'A+': 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  'A': 'border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300',
  'B': 'border-amber-500/35 bg-amber-500/12 text-amber-700 dark:text-amber-300',
  'Bad': 'border-red-500/35 bg-red-500/15 text-red-700 dark:text-red-300',
  'N/A': 'border-slate-400/35 bg-slate-400/10 text-slate-600 dark:text-slate-300',
};

export function GradeBadge({ grade }: { grade: SetupGrade | 'N/A' }) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded border px-1.5 py-0.5 font-mono text-[11px] font-semibold tabular-nums whitespace-nowrap ${GRADE_STYLES[grade]}`}
    >
      {grade}
    </span>
  );
}
