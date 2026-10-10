import { Activity, AlertTriangle, Router, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/endpoints';
import TimelineChart from '../components/charts/TimelineChart';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';
import MetricCard from '../components/ui/MetricCard';
import OriginBadge from '../components/ui/OriginBadge';
import SeverityBadge from '../components/ui/SeverityBadge';
import { formatDateTime, labelize } from '../utils/format';

export default function OverviewPage() {
  const [state, setState] = useState({ loading: true, error: null, data: null });

  const load = async () => {
    try {
      setState((prev) => ({ ...prev, error: null }));
      const [health, summary, timeline, alerts] = await Promise.all([
        api.health(),
        api.dashboardSummary(),
        api.timeline(24),
        api.recentAlerts(10),
      ]);
      setState({ loading: false, error: null, data: { health, summary, timeline, alerts } });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error }));
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 15000);
    return () => clearInterval(timer);
  }, []);

  if (state.loading) return <LoadingState />;
  if (state.error && !state.data) return <ErrorState error={state.error} onRetry={load} />;

  const { summary, timeline, alerts } = state.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300/80">Overview</p>
          <h1 className="mt-2 text-3xl font-bold text-white">DecoyNet Operations</h1>
          <p className="mt-2 text-slate-400">Live backend data, refreshed every 15 seconds.</p>
        </div>
        {state.error ? <ErrorState error={state.error} onRetry={load} /> : null}
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Total Events" value={summary.total_events} subtitle={`${summary.unique_events} unique source event IDs`} icon={Activity} tone="cyan" />
        <MetricCard title="High Risk Events" value={summary.high_risk_events} subtitle="Risk score ≥ 70" icon={AlertTriangle} tone="red" />
        <MetricCard title="Registered Decoys" value={summary.registered_devices} subtitle={`${summary.recently_seen_devices} recently seen`} icon={Router} tone="emerald" />
        <MetricCard title="Backend Status" value="Ready" subtitle={`${state.data.health.app} • ${state.data.health.environment}`} icon={ShieldCheck} tone="purple" />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <TimelineChart data={timeline} />
        <section className="panel p-5">
          <h2 className="text-lg font-semibold text-white">Recent Alerts</h2>
          <p className="mt-1 text-sm text-slate-400">Recent medium and high-risk detections.</p>
          <div className="mt-4 space-y-3">
            {alerts.length ? (
              alerts.map((alert) => (
                <Link key={alert.event_id} to={`/events/${alert.event_id}`} className="focus-ring block rounded-xl border border-slate-800 bg-navy-900/70 p-4 hover:border-cyan-400/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-white">{labelize(alert.event_type)}</p>
                      <p className="mt-1 text-xs text-slate-500">{formatDateTime(alert.event_timestamp)} • {alert.source_ip}</p>
                    </div>
                    <SeverityBadge severity={alert.severity} compact />
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <OriginBadge origin={alert.origin} />
                    <span className="text-xs text-slate-400">Risk {alert.risk_score}/100</span>
                  </div>
                </Link>
              ))
            ) : (
              <EmptyState title="No recent alerts" message="No medium/high risk detections have been recorded yet." />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
