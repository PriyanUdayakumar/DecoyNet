import {
  Activity,
  FlaskConical,
  Gauge,
  Menu,
  Network,
  Router,
  ServerCog,
  Shield,
  X,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Overview', icon: Gauge },
  { to: '/events', label: 'Security Events', icon: Activity },
  { to: '/devices', label: 'Devices', icon: Router },
  { to: '/discovery', label: 'Network Discovery', icon: Network },
  { to: '/demo', label: 'Demo Lab', icon: FlaskConical },
  { to: '/system', label: 'System Status', icon: ServerCog },
];

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const sidebar = (
    <aside className={`flex h-full flex-col border-r border-slate-800 bg-navy-900/95 ${collapsed ? 'w-20' : 'w-72'} transition-all duration-200`}>
      <div className="flex h-16 items-center gap-3 border-b border-slate-800 px-5">
        <div className="rounded-xl bg-cyan-400/10 p-2 text-cyan-200 shadow-glow">
          <Shield className="h-6 w-6" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-lg font-bold tracking-tight text-white">DecoyNet</p>
            <p className="text-xs uppercase tracking-widest text-cyan-300/80">SOC Console</p>
          </div>
        )}
        <button type="button" onClick={onMobileClose} className="ml-auto rounded-lg p-1 text-slate-400 hover:text-white md:hidden">
          <X className="h-5 w-5" />
        </button>
      </div>
      <nav className="flex-1 space-y-2 px-3 py-5" aria-label="Primary navigation">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={onMobileClose}
            className={({ isActive }) =>
              `focus-ring flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${
                isActive
                  ? 'bg-cyan-400/12 text-cyan-100 ring-1 ring-cyan-400/20'
                  : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100'
              }`
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-800 p-3">
        <button type="button" onClick={onToggle} className="focus-ring hidden w-full items-center justify-center gap-2 rounded-xl border border-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 md:flex">
          <Menu className="h-4 w-4" />
          {!collapsed && 'Collapse'}
        </button>
      </div>
    </aside>
  );

  return (
    <>
      <div className="hidden md:block">{sidebar}</div>
      {mobileOpen && <div className="fixed inset-0 z-40 bg-black/60 md:hidden" onClick={onMobileClose}>{sidebar}</div>}
    </>
  );
}
