import { Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/endpoints';
import DiscoveryJobForm from '../components/discovery/DiscoveryJobForm';
import HostTable from '../components/discovery/HostTable';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';
import StatusDot from '../components/ui/StatusDot';
import Toast from '../components/ui/Toast';
import { formatDateTime } from '../utils/format';

export default function DiscoveryPage() {
  const [hosts, setHosts] = useState({ loading: true, error: null, items: [] });
  const [job, setJob] = useState(null);
  const [jobId, setJobId] = useState('');
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);

  const loadHosts = async () => {
    try {
      setHosts((prev) => ({ ...prev, loading: true, error: null }));
      const data = await api.listDiscoveryHosts({ limit: 100, offset: 0 });
      setHosts({ loading: false, error: null, items: data || [] });
    } catch (error) {
      setHosts((prev) => ({ ...prev, loading: false, error }));
    }
  };

  useEffect(() => {
    loadHosts();
  }, []);

  const startJob = async (target) => {
    setBusy(true);
    try {
      const data = await api.startDiscoveryJob(target);
      setJob(data);
      setToast({ type: 'success', message: `Discovery completed with ${data.host_count} host(s)` });
      loadHosts();
    } catch (error) {
      setToast({ type: 'error', message: error.message });
    } finally {
      setBusy(false);
    }
  };

  const lookupJob = async (event) => {
    event.preventDefault();
    if (!jobId) return;
    setBusy(true);
    try {
      setJob(await api.getDiscoveryJob(jobId));
    } catch (error) {
      setToast({ type: 'error', message: error.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300/80">Network Discovery</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Authorized Host Observation</h1>
        <p className="mt-2 text-slate-400">Discovery is backend-controlled, disabled by default and constrained by configured CIDR allowlists.</p>
      </div>
      <DiscoveryJobForm onSubmit={startJob} busy={busy} />
      <form onSubmit={lookupJob} className="panel flex flex-col gap-3 p-5 md:flex-row md:items-end">
        <label className="flex-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Discovery job ID
          <input value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="UUID returned by POST /discovery/jobs" className="focus-ring mt-1 w-full rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm normal-case text-white placeholder:text-slate-500" />
        </label>
        <button type="submit" className="focus-ring inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800"><Search className="h-4 w-4" /> Lookup Job</button>
      </form>
      {job ? (
        <section className="panel p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Discovery Job</h2>
              <p className="mt-1 font-mono text-xs text-slate-500">{job.id}</p>
              <p className="mt-2 text-sm text-slate-400">{job.target_cidr} • requested {formatDateTime(job.requested_at)}</p>
            </div>
            <StatusDot status={job.status} />
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-slate-800 bg-navy-900 p-4"><p className="text-xs text-slate-500">Started</p><p className="mt-1 text-sm text-white">{formatDateTime(job.started_at)}</p></div>
            <div className="rounded-xl border border-slate-800 bg-navy-900 p-4"><p className="text-xs text-slate-500">Completed</p><p className="mt-1 text-sm text-white">{formatDateTime(job.completed_at)}</p></div>
            <div className="rounded-xl border border-slate-800 bg-navy-900 p-4"><p className="text-xs text-slate-500">Hosts</p><p className="mt-1 text-sm text-white">{job.host_count}</p></div>
          </div>
          {job.error ? <p className="mt-4 text-sm text-red-200">{job.error}</p> : null}
        </section>
      ) : null}
      {hosts.error ? <ErrorState error={hosts.error} onRetry={loadHosts} /> : null}
      {hosts.loading ? <LoadingState label="Loading discovered hosts…" /> : <HostTable hosts={hosts.items} />}
      <Toast message={toast?.message} type={toast?.type} onDismiss={() => setToast(null)} />
    </div>
  );
}
