import { Inbox } from 'lucide-react';

export default function EmptyState({ title = 'No data yet', message, action }) {
  return (
    <div className="panel flex min-h-44 items-center justify-center p-8 text-center">
      <div className="max-w-md">
        <Inbox className="mx-auto h-10 w-10 text-slate-500" aria-hidden="true" />
        <h3 className="mt-4 text-lg font-semibold text-white">{title}</h3>
        {message ? <p className="mt-2 text-sm text-slate-400">{message}</p> : null}
        {action ? <div className="mt-5">{action}</div> : null}
      </div>
    </div>
  );
}
