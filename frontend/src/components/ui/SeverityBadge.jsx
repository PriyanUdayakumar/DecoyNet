import { AlertTriangle, Info, RadioTower, ShieldAlert, ShieldCheck } from 'lucide-react';
import { labelize } from '../../utils/format';

const styles = {
  info: 'border-sky-400/30 bg-sky-400/10 text-sky-200',
  low: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200',
  medium: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
  high: 'border-orange-400/30 bg-orange-400/10 text-orange-200',
  critical: 'border-red-400/40 bg-red-500/15 text-red-200',
};

const icons = {
  info: Info,
  low: ShieldCheck,
  medium: RadioTower,
  high: AlertTriangle,
  critical: ShieldAlert,
};

export default function SeverityBadge({ severity = 'info', compact = false }) {
  const normalized = styles[severity] ? severity : 'info';
  const Icon = icons[normalized];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[normalized]}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {!compact && labelize(normalized)}
    </span>
  );
}
