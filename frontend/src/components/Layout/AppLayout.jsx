import { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { api } from '../../api/endpoints';
import Header from './Header';
import Sidebar from './Sidebar';

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [health, setHealth] = useState(null);
  const [disconnected, setDisconnected] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const data = await api.health();
        if (!alive) return;
        setHealth(data);
        setDisconnected(false);
      } catch {
        if (!alive) return;
        setDisconnected(true);
      }
    };
    load();
    const timer = setInterval(load, 30000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="flex min-h-screen bg-transparent text-slate-100">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenu={() => setMobileOpen(true)} health={health} disconnected={disconnected} />
        {disconnected && (
          <div className="border-b border-red-400/20 bg-red-500/10 px-4 py-2 text-sm text-red-100 md:px-6">
            DecoyNet backend is unreachable. Start the FastAPI server or update VITE_API_BASE_URL.
          </div>
        )}
        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
