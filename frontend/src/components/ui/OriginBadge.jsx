import { FlaskConical, Shield, Wrench } from 'lucide-react';
import { labelize } from '../../utils/format';

const styles = {
  simulator: 'border-purple-400/30 bg-purple-400/10 text-purple-200',
  esp32: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200',
  authorized_test: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200',
};

const icons = {
  simulator: FlaskConical,
  esp32: Shield,
  authorized_test: Wrench,
};

export default function OriginBadge({ origin = 'simulator' }) {
  const normalized = styles[origin] ? origin : 'simulator';
  const Icon = icons[normalized];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[normalized]}`}
      title={normalized === 'simulator' ? 'Simulated demo event, not ESP32-origin telemetry' : undefined}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {labelize(normalized)}
    </span>
  );
}
