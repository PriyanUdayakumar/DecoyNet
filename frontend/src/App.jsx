import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/Layout/AppLayout';
import DemoLabPage from './pages/DemoLabPage';
import DevicesPage from './pages/DevicesPage';
import DiscoveryPage from './pages/DiscoveryPage';
import EventDetailPage from './pages/EventDetailPage';
import EventsPage from './pages/EventsPage';
import OverviewPage from './pages/OverviewPage';
import SystemStatusPage from './pages/SystemStatusPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<OverviewPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="events/:id" element={<EventDetailPage />} />
        <Route path="devices" element={<DevicesPage />} />
        <Route path="discovery" element={<DiscoveryPage />} />
        <Route path="demo" element={<DemoLabPage />} />
        <Route path="system" element={<SystemStatusPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
