import { Radar } from 'lucide-react';
import { useState } from 'react';

export default function DiscoveryJobForm({ onSubmit, busy }) {
  const [target, setTarget] = useState('192.168.1.0/30');
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(target);
      }}
      className="panel p-5"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-white">Authorized Discovery Job</h2>
          <p className="mt-1 text-sm text-slate-400">Requests are sent to the backend only. Browser-side subnet scanning is never performed.</p>
          <label className="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Target CIDR
            <input value={target} onChange={(event) => setTarget(event.target.value)} placeholder="192.168.1.0/30" className="focus-ring mt-1 w-full rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm normal-case text-white" />
          </label>
        </div>
        <button type="submit" disabled={busy} className="focus-ring inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-bold text-navy-950 disabled:opacity-50 hover:bg-cyan-300">
          <Radar className="h-4 w-4" /> {busy ? 'Submitting…' : 'Start Discovery'}
        </button>
      </div>
    </form>
  );
}
