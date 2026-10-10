export const SEVERITIES = ['info', 'low', 'medium', 'high', 'critical'];
export const EVENT_TYPES = [
  'page_access',
  'login_attempt',
  'sensitive_endpoint_access',
  'unusual_endpoint_access',
  'port_probe',
  'heartbeat',
  'other',
];
export const ORIGINS = ['simulator', 'esp32', 'authorized_test'];

export function formatDateTime(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(value));
}

export function formatShortTime(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
  }).format(new Date(value));
}

export function labelize(value) {
  if (!value) return '—';
  return String(value)
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function riskTone(score) {
  if (score >= 90) return 'critical';
  if (score >= 70) return 'high';
  if (score >= 45) return 'medium';
  if (score >= 20) return 'low';
  return 'info';
}

export function clampPageOffset(offset, limit, total) {
  if (total <= 0) return 0;
  return Math.min(offset, Math.floor((total - 1) / limit) * limit);
}
