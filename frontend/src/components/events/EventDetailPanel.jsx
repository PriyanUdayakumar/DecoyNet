import { ArrowLeft, Database } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDateTime, labelize } from '../../utils/format';
import OriginBadge from '../ui/OriginBadge';
import SeverityBadge from '../ui/SeverityBadge';

function Field({ label, value, mono }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-navy-900/60 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 break-words text-sm text-slate-100 ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</p>
    </div>
  );
}

export default function EventDetailPanel({ event, analysis }) {
  return (
    <div className="space-y-6">
      <Link to="/events" className="focus-ring inline-flex items-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800">
        <ArrowLeft className="h-4 w-4" /> Back to events
      </Link>
      <section className="panel p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm text-slate-400">Security event</p>
            <h1 className="mt-1 text-2xl font-bold text-white">{labelize(event.event_type)}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">{event.explanation}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <OriginBadge origin={event.origin} />
            <SeverityBadge severity={event.severity} />
          </div>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Source event ID" value={event.source_event_id} mono />
        <Field label="Event ID" value={event.id} mono />
        <Field label="Event time" value={formatDateTime(event.event_timestamp)} />
        <Field label="Received" value={formatDateTime(event.received_timestamp)} />
        <Field label="Source IP" value={event.source_ip} mono />
        <Field label="Decoy IP" value={event.destination_ip} mono />
        <Field label="Transport" value={`${event.transport_protocol}/${event.application_protocol}`} />
        <Field label="Endpoint" value={`${event.http_method || '—'} ${event.request_path || '—'}`} mono />
      </section>
      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white"><Database className="h-5 w-5 text-cyan-300" /> Detection Analysis</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <Field label="Risk score" value={`${analysis?.risk_score ?? event.risk_score}/100`} />
            <Field label="Severity" value={labelize(analysis?.severity || event.severity)} />
            <Field label="Status" value={labelize(event.processing_status)} />
          </div>
          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Triggered rules</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {(analysis?.detection_rule_ids || event.detection_rule_ids || []).length ? (
                (analysis?.detection_rule_ids || event.detection_rule_ids).map((rule) => (
                  <span key={rule} className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-semibold text-cyan-100">{labelize(rule)}</span>
                ))
              ) : (
                <span className="text-sm text-slate-400">No detection rules triggered.</span>
              )}
            </div>
          </div>
          <p className="mt-5 text-sm leading-6 text-slate-300">{analysis?.explanation || event.explanation}</p>
        </div>
        <div className="panel p-6">
          <h2 className="text-lg font-semibold text-white">Metadata & Contributions</h2>
          <pre className="mt-4 max-h-96 overflow-auto rounded-xl border border-slate-800 bg-navy-950 p-4 text-xs leading-5 text-slate-300">{JSON.stringify({ metadata: event.metadata, score_contributions: analysis?.score_contributions || [] }, null, 2)}</pre>
        </div>
      </section>
    </div>
  );
}
