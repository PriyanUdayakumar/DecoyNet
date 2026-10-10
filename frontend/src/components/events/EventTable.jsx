import { Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDateTime, labelize } from '../../utils/format';
import EmptyState from '../ui/EmptyState';
import OriginBadge from '../ui/OriginBadge';
import Pagination from '../ui/Pagination';
import SeverityBadge from '../ui/SeverityBadge';

export default function EventTable({ events = [], meta, onPageChange }) {
  if (!events.length) {
    return <EmptyState title="No matching security events" message="Adjust the filters or run a demo scenario to populate the event stream." />;
  }
  return (
    <section className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-navy-900/70">
            <tr>
              <th className="table-head-cell">Timestamp</th>
              <th className="table-head-cell">Source</th>
              <th className="table-head-cell">Decoy</th>
              <th className="table-head-cell">Endpoint</th>
              <th className="table-head-cell">Origin</th>
              <th className="table-head-cell">Severity</th>
              <th className="table-head-cell">Risk</th>
              <th className="table-head-cell">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {events.map((event) => (
              <tr key={event.id} className="hover:bg-slate-800/40">
                <td className="table-cell whitespace-nowrap text-slate-300">{formatDateTime(event.event_timestamp)}</td>
                <td className="table-cell font-mono text-cyan-100">{event.source_ip}</td>
                <td className="table-cell font-mono text-slate-300">{event.destination_ip}:{event.destination_port}</td>
                <td className="table-cell min-w-56">
                  <div className="font-medium text-white">{event.request_path || '—'}</div>
                  <div className="text-xs text-slate-500">{labelize(event.event_type)}</div>
                </td>
                <td className="table-cell"><OriginBadge origin={event.origin} /></td>
                <td className="table-cell"><SeverityBadge severity={event.severity} /></td>
                <td className="table-cell"><span className="font-semibold tabular-nums text-white">{event.risk_score}</span><span className="text-slate-500">/100</span></td>
                <td className="table-cell">
                  <Link to={`/events/${event.id}`} className="focus-ring inline-flex items-center gap-1 rounded-lg border border-slate-700 px-2.5 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-800">
                    <Eye className="h-3.5 w-3.5" /> View
                  </Link>
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
