import { Power, PowerOff, RefreshCw } from 'lucide-react';
import { formatDateTime, labelize } from '../../utils/format';
import EmptyState from '../ui/EmptyState';
import Pagination from '../ui/Pagination';
import StatusDot from '../ui/StatusDot';

export default function DeviceTable({ devices = [], meta, selectedId, onSelect, onToggleDisabled, onPageChange, busyId }) {
  if (!devices.length) {
    return <EmptyState title="No registered decoys" message="Register a lab decoy or ingest telemetry with a known device ID." />;
  }
  return (
    <section className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-navy-900/70">
            <tr>
              <th className="table-head-cell">Device</th>
              <th className="table-head-cell">Personality</th>
              <th className="table-head-cell">IP Address</th>
              <th className="table-head-cell">Last Seen</th>
              <th className="table-head-cell">Status</th>
              <th className="table-head-cell">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {devices.map((device) => (
              <tr key={device.id} className={selectedId === device.id ? 'bg-cyan-400/5' : 'hover:bg-slate-800/40'}>
                <td className="table-cell">
                  <button type="button" onClick={() => onSelect(device)} className="focus-ring text-left font-semibold text-white hover:text-cyan-200">{device.name}</button>
                  <div className="mt-1 text-xs text-slate-500">{device.firmware_version || 'No firmware version'}</div>
                </td>
                <td className="table-cell">{labelize(device.device_type)}</td>
                <td className="table-cell font-mono text-cyan-100">{device.ip_address || '—'}</td>
                <td className="table-cell text-slate-300">{formatDateTime(device.last_seen_at)}</td>
                <td className="table-cell"><StatusDot status={device.status} /></td>
                <td className="table-cell">
                  <button type="button" disabled={busyId === device.id} onClick={() => onToggleDisabled(device)} className="focus-ring inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 disabled:opacity-50 hover:bg-slate-800">
                    {busyId === device.id ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : device.status === 'disabled' ? <Power className="h-3.5 w-3.5" /> : <PowerOff className="h-3.5 w-3.5" />}
                    {device.status === 'disabled' ? 'Enable' : 'Disable'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {meta ? <Pagination {...meta} onChange={onPageChange} /> : null}
    </section>
  );
}
