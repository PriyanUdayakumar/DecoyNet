import { Search, X } from 'lucide-react';
import { EVENT_TYPES, ORIGINS, SEVERITIES, labelize } from '../../utils/format';

export default function EventFilters({ filters, onChange, onReset }) {
  const update = (key, value) => onChange({ ...filters, [key]: value, offset: 0 });
  return (
    <section className="panel p-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
        <label className="relative xl:col-span-2">
          <span className="sr-only">Search events</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={filters.search || ''}
            onChange={(event) => update('search', event.target.value)}
            placeholder="Search path, IP, explanation"
            className="focus-ring w-full rounded-xl border border-slate-700 bg-navy-900 py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-slate-500"
          />
        </label>
        <select value={filters.severity || ''} onChange={(event) => update('severity', event.target.value)} className="focus-ring rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm text-white">
          <option value="">All severities</option>
          {SEVERITIES.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
        </select>
        <select value={filters.event_type || ''} onChange={(event) => update('event_type', event.target.value)} className="focus-ring rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm text-white">
          <option value="">All event types</option>
          {EVENT_TYPES.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
        </select>
        <select value={filters.origin || ''} onChange={(event) => update('origin', event.target.value)} className="focus-ring rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm text-white">
          <option value="">All origins</option>
          {ORIGINS.map((item) => <option key={item} value={item}>{labelize(item)}</option>)}
        </select>
        <input value={filters.source_ip || ''} onChange={(event) => update('source_ip', event.target.value)} placeholder="Source IP" className="focus-ring rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
        <button type="button" onClick={onReset} className="focus-ring inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 px-3 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800">
          <X className="h-4 w-4" /> Reset
        </button>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Start time
          <input type="datetime-local" value={filters.start_time || ''} onChange={(event) => update('start_time', event.target.value)} className="focus-ring mt-1 w-full rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm normal-case text-white" />
        </label>
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          End time
          <input type="datetime-local" value={filters.end_time || ''} onChange={(event) => update('end_time', event.target.value)} className="focus-ring mt-1 w-full rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm normal-case text-white" />
        </label>
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Page size
          <select value={filters.limit} onChange={(event) => update('limit', Number(event.target.value))} className="focus-ring mt-1 w-full rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm normal-case text-white">
            {[10, 25, 50, 100, 200].map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
      </div>
    </section>
  );
}
