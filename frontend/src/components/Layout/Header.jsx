import { Menu, WifiOff } from 'lucide-react';
import { API_BASE_URL } from '../../api/client';
import StatusDot from '../ui/StatusDot';

export default function Header({ onMenu, health, disconnected }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-navy-900/80 px-4 backdrop-blur md:px-6">
      <div className="flex items-center gap-3">
        <button type="button" onClick={onMenu} className="focus-ring rounded-lg p-2 text-slate-300 hover:bg-slate-800 md:hidden">
          <Menu className="h-5 w-5" />
        </button>
        <div>
          <p className="text-sm text-slate-400">IoT cyber threat and lateral movement detection</p>
          <h1 className="text-lg font-semibold text-white">Security Operations Dashboard</h1>
        </div>
      </div>
      <div className="hidden items-center gap-4 text-sm sm:flex">
        <span className="max-w-[20rem] truncate text-xs text-slate-500">{API_BASE_URL}</span>
        {disconnected ? (
          <span className="inline-flex items-center gap-2 rounded-full border border-red-400/30 bg-red-500/10 px-3 py-1.5 text-red-100">
            <WifiOff className="h-4 w-4" /> Disconnected
          </span>
        ) : (
          <StatusDot status={health?.status || 'ok'} label={health?.app ? `${health.app} ${health.environment}` : 'Backend'} />
        )}
      </div>
    </header>
  );
}
