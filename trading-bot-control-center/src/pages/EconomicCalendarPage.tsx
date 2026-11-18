import { CalendarDays, ExternalLink } from 'lucide-react';

const FOREX_FACTORY_CALENDAR_URL = 'https://www.forexfactory.com/calendar';

export function EconomicCalendarPage() {
  return (
    <div className="space-y-5">
      <header>
        <div className="flex items-center gap-2">
          <CalendarDays className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Economic Calendar
          </h1>
        </div>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Open the free Forex Factory calendar to view scheduled economic events.
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#0E141F]">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          View the calendar on Forex Factory
        </h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          The calendar opens on the Forex Factory website in a new tab.
        </p>
        <a
          href={FOREX_FACTORY_CALENDAR_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Open Forex Factory calendar
          <ExternalLink className="h-4 w-4" aria-hidden="true" />
        </a>
      </section>

      <p className="text-xs text-slate-500 dark:text-slate-400">
        The bot does not download calendar events. No official free API or permission for
        automated access has been verified, so this page does not scrape the site. No paid
        subscription or calendar API key is needed.
      </p>
    </div>
  );
}
