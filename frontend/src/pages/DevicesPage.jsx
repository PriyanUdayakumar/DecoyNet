import { Plus, Router } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../api/endpoints';
import DeviceTable from '../components/devices/DeviceTable';
import EventTable from '../components/events/EventTable';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';
import Toast from '../components/ui/Toast';
import { formatDateTime } from '../utils/format';

const defaultForm = { name: '', device_type: 'camera', ip_address: '', firmware_version: '', location: '', model: '', role: 'decoy', notes: '', lab_label: '' };

export default function DevicesPage() {
  const [filters, setFilters] = useState({ limit: 25, offset: 0 });
  const [state, setState] = useState({ loading: true, error: null, devices: [], meta: null });
  const [selected, setSelected] = useState(null);
  const [events, setEvents] = useState({ loading: false, items: [], meta: null });
  const [form, setForm] = useState(defaultForm);
  const [busyId, setBusyId] = useState(null);
  const [toast, setToast] = useState(null);

  const loadDevices = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      const data = await api.listDevices(filters);
      setState({ loading: false, error: null, devices: data.items || [], meta: data.meta });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error }));
    }
  };

  const loadDeviceEvents = async (device, offset = 0) => {
    if (!device) return;
    setSelected(device);
    setEvents((prev) => ({ ...prev, loading: true }));
    try {
      const data = await api.deviceEvents(device.id, { limit: 10, offset });
      setEvents({ loading: false, items: data.items || [], meta: data.meta });
    } catch (error) {
      setToast({ type: 'error', message: error.message });
      setEvents({ loading: false, items: [], meta: null });
    }
  };

  useEffect(() => {
    loadDevices();
  }, [filters.limit, filters.offset]);

  const createDevice = async (event) => {
    event.preventDefault();
    try {
      const metadata = Object.fromEntries(
        ['location', 'model', 'role', 'notes', 'lab_label'].map((key) => [key, form[key]]).filter(([, value]) => value),
      );
      const created = await api.createDevice({
        name: form.name,
        device_type: form.device_type,
        ip_address: form.ip_address || null,
        firmware_version: form.firmware_version || null,
        metadata,
      });
      setToast({ type: 'success', message: `Registered ${created.name}` });
      setForm(defaultForm);
      loadDevices();
    } catch (error) {
      setToast({ type: 'error', message: error.message });
    }
  };

  const toggleDisabled = async (device) => {
    setBusyId(device.id);
    try {
      const updated = await api.updateDevice(device.id, { disabled: device.status !== 'disabled' });
      setToast({ type: 'success', message: `${updated.name} is now ${updated.status}` });
      setSelected(updated);
      loadDevices();
    } catch (error) {
      setToast({ type: 'error', message: error.message });
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300/80">Inventory</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Registered Decoys</h1>
        <p className="mt-2 text-slate-400">Manage lab decoy identity and inspect recent linked events.</p>
      </div>
      <form onSubmit={createDevice} className="panel p-5">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white"><Plus className="h-5 w-5 text-cyan-300" /> Register Device</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-5">
          {['name', 'device_type', 'ip_address', 'firmware_version', 'location'].map((key) => (
            <input key={key} required={key === 'name' || key === 'device_type'} value={form[key]} onChange={(event) => setForm((prev) => ({ ...prev, [key]: event.target.value }))} placeholder={key.replaceAll('_', ' ')} className="focus-ring rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
          ))}
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          {['model', 'role', 'notes', 'lab_label'].map((key) => (
            <input key={key} value={form[key]} onChange={(event) => setForm((prev) => ({ ...prev, [key]: event.target.value }))} placeholder={key.replaceAll('_', ' ')} className="focus-ring rounded-xl border border-slate-700 bg-navy-900 px-3 py-2.5 text-sm text-white placeholder:text-slate-500" />
          ))}
        </div>
        <button type="submit" className="focus-ring mt-4 inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950 hover:bg-cyan-300"><Router className="h-4 w-4" /> Register Decoy</button>
      </form>
      {state.error ? <ErrorState error={state.error} onRetry={loadDevices} /> : null}
      {state.loading ? <LoadingState label="Loading devices…" /> : <DeviceTable devices={state.devices} meta={state.meta} selectedId={selected?.id} onSelect={loadDeviceEvents} onToggleDisabled={toggleDisabled} onPageChange={(offset) => setFilters((prev) => ({ ...prev, offset }))} busyId={busyId} />}
      {selected ? (
        <section className="panel p-5">
          <h2 className="text-lg font-semibold text-white">{selected.name}</h2>
          <p className="mt-1 text-sm text-slate-400">Registered {formatDateTime(selected.registered_at)} • Metadata {JSON.stringify(selected.metadata)}</p>
          <div className="mt-4">
            {events.loading ? <LoadingState label="Loading device events…" /> : <EventTable events={events.items} meta={events.meta} onPageChange={(offset) => loadDeviceEvents(selected, offset)} />}
          </div>
        </section>
      ) : null}
      <Toast message={toast?.message} type={toast?.type} onDismiss={() => setToast(null)} />
    </div>
  );
}
