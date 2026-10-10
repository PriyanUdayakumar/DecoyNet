import { AlertTriangle, X } from 'lucide-react';

export default function ConfirmDialog({ open, title, message, confirmLabel, onCancel, onConfirm, busy }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="w-full max-w-lg rounded-2xl border border-red-400/30 bg-navy-850 p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-red-400/10 p-2 text-red-200">
              <AlertTriangle className="h-5 w-5" />
            </span>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
          </div>
          <button type="button" onClick={onCancel} className="focus-ring rounded-lg p-1 text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-300">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onCancel} className="focus-ring rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800">
            Cancel
          </button>
          <button type="button" disabled={busy} onClick={onConfirm} className="focus-ring rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 hover:bg-red-400">
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
