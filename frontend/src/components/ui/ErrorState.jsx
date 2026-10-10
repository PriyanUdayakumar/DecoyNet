import { AlertTriangle, WifiOff } from 'lucide-react';

export default function ErrorState({ error, title, onRetry }) {
  const isNetwork = error?.name === 'NetworkError' || error?.code === 'network_error';
  const Icon = isNetwork ? WifiOff : AlertTriangle;
  return (
    <div className="panel border-red-400/20 bg-red-950/20 p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <Icon className="h-6 w-6 shrink-0 text-red-300" aria-hidden="true" />
        <div className="flex-1">
          <h3 className="text-base font-semibold text-red-100">
            {title || (isNetwork ? 'Backend disconnected' : 'Request failed')}
          </h3>
          <p className="mt-1 text-sm text-red-100/80">
            {error?.message || 'DecoyNet could not complete this request.'}
          </p>
          {error?.status ? <p className="mt-2 text-xs text-red-100/60">HTTP {error.status}</p> : null}
        </div>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="focus-ring rounded-lg border border-red-300/30 px-3 py-2 text-sm font-semibold text-red-100 hover:bg-red-400/10"
          >
            Retry
          </button>
        ) : null}
      </div>
    </div>
  );
}
