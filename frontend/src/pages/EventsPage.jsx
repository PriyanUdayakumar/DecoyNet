import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/endpoints';
import EventFilters from '../components/events/EventFilters';
import EventTable from '../components/events/EventTable';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';

const initialFilters = {
  limit: 25,
  offset: 0,
  search: '',
  severity: '',
  event_type: '',
  origin: '',
  source_ip: '',
  start_time: '',
  end_time: '',
};

function apiParams(filters) {
  return {
    limit: filters.limit,
    offset: filters.offset,
    severity: filters.severity,
    event_type: filters.event_type,
    origin: filters.origin,
    source_ip: filters.source_ip,
    start_time: filters.start_time ? new Date(filters.start_time).toISOString() : undefined,
    end_time: filters.end_time ? new Date(filters.end_time).toISOString() : undefined,
  };
}

export default function EventsPage() {
  const [filters, setFilters] = useState(initialFilters);
  const [state, setState] = useState({ loading: true, error: null, events: [], meta: null });

  const load = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      const data = await api.listEvents(apiParams(filters));
      setState({ loading: false, error: null, events: data.items || [], meta: data.meta });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error }));
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, [filters.limit, filters.offset, filters.severity, filters.event_type, filters.origin, filters.source_ip, filters.start_time, filters.end_time]);

  const visibleEvents = useMemo(() => {
    const search = filters.search.trim().toLowerCase();
    if (!search) return state.events;
    return state.events.filter((event) =>
      [event.source_ip, event.destination_ip, event.request_path, event.explanation, event.event_type, event.origin]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(search)),
    );
  }, [state.events, filters.search]);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300/80">Event Stream</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Security Events</h1>
        <p className="mt-2 text-slate-400">Filter and inspect real backend event telemetry. Simulator-origin entries are visibly labeled.</p>
      </div>
      <EventFilters filters={filters} onChange={setFilters} onReset={() => setFilters(initialFilters)} />
      {state.error ? <ErrorState error={state.error} onRetry={load} /> : null}
      {state.loading ? <LoadingState label="Loading events…" /> : <EventTable events={visibleEvents} meta={state.meta} onPageChange={(offset) => setFilters((prev) => ({ ...prev, offset }))} />}
    </div>
  );
}
