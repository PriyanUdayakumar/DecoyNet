import { CheckCircle2, XCircle } from 'lucide-react';

export default function Toast({ message, type = 'success', onDismiss }) {
  if (!message) return null;
  const Icon = type === 'error' ? XCircle : CheckCircle2;
  const style = type === 'error' ? 'border-red-400/30 bg-red-950/80 text-red-100' : 'border-emerald-400/30 bg-emerald-950/80 text-emerald-100';
  return (
    <div className={`fixed bottom-5 right-5 z-40 flex max-w-md items-start gap-3 rounded-xl border p-4 shadow-2xl backdrop-blur ${style}`}>
      <Icon className="mt-0.5 h-5 w-5 shrink-0" />
      <p className="text-sm">{message}</p>
      <button type="button" onClick={onDismiss} className="ml-2 text-xs opacity-70 hover:opacity-100">Dismiss</button>
    </div>
  );
}
