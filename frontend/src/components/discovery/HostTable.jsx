import { formatDateTime, labelize } from '../../utils/format';
import EmptyState from '../ui/EmptyState';

export default function HostTable({ hosts = [] }) {
  if (!hosts.length) {
    return <EmptyState title="No discovered hosts" message="Discovery is disabled by default. When enabled, authorized backend jobs populate this table." />;
  }
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-slate-800 p-5">
        <h2 className="text-lg font-semibold text-white">Observed Hosts</h2>
        <p className="text-sm text-slate-400">Data returned by the FastAPI discovery service.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-navy-900/70">
            <tr>
              <th className="table-head-cell">IP</th>
              <th className="table-head-cell">Method</th>
              <th className="table-head-cell">Discovered</th>
              <th className="table-head-cell">Hostname</th>
              <th className="table-head-cell">Evidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {hosts.map((host) => (
              <tr key={host.id} className="hover:bg-slate-800/40">
                <td className="table-cell font-mono text-cyan-100">{host.ip_address}</td>
                <td className="table-cell">{labelize(host.method)}</td>
                <td className="table-cell text-slate-300">{formatDateTime(host.discovered_at)}</td>
                <td className="table-cell">{host.hostname || '—'}</td>
                <td className="table-cell max-w-lg text-slate-400">{host.evidence || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
