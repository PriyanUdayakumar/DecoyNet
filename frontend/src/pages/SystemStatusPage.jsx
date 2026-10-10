import { Database, Server, Wifi } from 'lucide-react';
import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../api/client';
import { api } from '../api/endpoints';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';
import MetricCard from '../components/ui/MetricCard';
import StatusDot from '../components/ui/StatusDot';

export default function SystemStatusPage() {
  const [state, setState] = useState({ loading: true, error: null, health: null, ready: null });

  const load = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      const [health, ready] = await Promise.all([api.health(), api.readiness()]);
      setState({ loading: false, error: null, health, ready });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error }));
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (state.loading) return <LoadingState label="Checking backend status…" />;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300/80">System</p>
        <h1 className="mt-2 text-3xl font-bold text-white">System Status</h1>
        <p className="mt-2 text-slate-400">Backend health, database readiness and frontend API connectivity.</p>
      </div>
      {state.error ? <ErrorState error={state.error} onRetry={load} /> : null}
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="API Connectivity" value={state.error ? 'Down' : 'Connected'} subtitle={API_BASE_URL} icon={Wifi} tone={state.error ? 'red' : 'emerald'} />
        <MetricCard title="Backend" value={state.health?.status || 'Unknown'} subtitle={`${state.health?.app || 'DecoyNet'} • ${state.health?.environment || 'n/a'}`} icon={Server} tone="cyan" />
        <MetricCard title="Database" value={state.ready?.database || 'Unknown'} subtitle={state.ready?.status || 'readiness unavailable'} icon={Database} tone="purple" />
      </div>
      <section className="panel p-6">
        <h2 className="text-lg font-semibold text-white">Endpoint Checks</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-navy-900 p-4"><StatusDot status={state.health?.status || (state.error ? 'disconnected' : 'ok')} label="GET /health" /></div>
          <div className="rounded-xl border border-slate-800 bg-navy-900 p-4"><StatusDot status={state.ready?.status || (state.error ? 'disconnected' : 'ready')} label="GET /health/ready" /></div>
        </div>
        <pre className="mt-5 overflow-auto rounded-xl border border-slate-800 bg-navy-950 p-4 text-xs text-slate-300">{JSON.stringify({ apiBaseUrl: API_BASE_URL, health: state.health, readiness: state.ready }, null, 2)}</pre>
      </section>
    </div>
  );
}
