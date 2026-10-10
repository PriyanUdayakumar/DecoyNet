import { labelize } from '../../utils/format';

const styles = {
  ok: 'bg-emerald-400 shadow-emerald-400/40',
  ready: 'bg-emerald-400 shadow-emerald-400/40',
  connected: 'bg-emerald-400 shadow-emerald-400/40',
  registered: 'bg-sky-400 shadow-sky-400/40',
  recently_seen: 'bg-emerald-400 shadow-emerald-400/40',
  stale: 'bg-amber-400 shadow-amber-400/40',
  disabled: 'bg-slate-500 shadow-slate-500/40',
  running: 'bg-cyan-400 shadow-cyan-400/40',
  completed: 'bg-emerald-400 shadow-emerald-400/40',
  failed: 'bg-red-400 shadow-red-400/40',
  rejected: 'bg-orange-400 shadow-orange-400/40',
  disconnected: 'bg-red-400 shadow-red-400/40',
};

export default function StatusDot({ status = 'ok', label }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-300">
      <span className={`h-2.5 w-2.5 rounded-full shadow-lg ${styles[status] || styles.ok}`} />
      {label || labelize(status)}
    </span>
  );
}
