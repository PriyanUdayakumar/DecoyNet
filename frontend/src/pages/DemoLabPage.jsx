import { useEffect, useState } from 'react';
import { api } from '../api/endpoints';
import DemoControls from '../components/demo/DemoControls';
import EventTable from '../components/events/EventTable';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import ErrorState from '../components/ui/ErrorState';
import LoadingState from '../components/ui/LoadingState';
import Toast from '../components/ui/Toast';

export default function DemoLabPage() {
  const [scenarios, setScenarios] = useState({ loading: true, error: null, items: [] });
  const [events, setEvents] = useState({ loading: true, error: null, items: [], meta: null });
  const [runningScenario, setRunningScenario] = useState(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const [toast, setToast] = useState(null);

  const loadScenarios = async () => {
    try {
      setScenarios({ loading: true, error: null, items: [] });
      setScenarios({ loading: false, error: null, items: await api.listDemoScenarios() });
    } catch (error) {
      setScenarios({ loading: false, error, items: [] });
    }
  };

  const loadSimulatorEvents = async () => {
    try {
      setEvents((prev) => ({ ...prev, loading: true, error: null }));
      const data = await api.listEvents({ origin: 'simulator', limit: 25, offset: 0 });
      setEvents({ loading: false, error: null, items: data.items || [], meta: data.meta });
    } catch (error) {
      setEvents((prev) => ({ ...prev, loading: false, error }));
    }
  };

  useEffect(() => {
    loadScenarios();
    loadSimulatorEvents();
  }, []);

  const runScenario = async (scenario) => {
    setRunningScenario(scenario);
    try {
      const result = await api.runDemoScenario(scenario);
      setToast({ type: 'success', message: `${scenario} generated ${result.length} simulator response(s)` });
      loadSimulatorEvents();
    } catch (error) {
      setToast({ type: 'error', message: error.message });
    } finally {
      setRunningScenario(null);
    }
  };

  const resetDemo = async () => {
    try {
      const result = await api.resetDemo();
      setToast({ type: 'success', message: `Removed ${result.deleted_events} simulator event(s). ESP32 and authorized-test records are preserved by backend policy.` });
      setConfirmReset(false);
      loadSimulatorEvents();
    } catch (error) {
      setToast({ type: 'error', message: error.message });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-purple-300/80">Demo Lab</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Safe Simulator Scenarios</h1>
        <p className="mt-2 text-slate-400">Generate labeled demo telemetry from actual backend scenario endpoints. Demo mode may be disabled by configuration.</p>
      </div>
      {scenarios.error ? <ErrorState error={scenarios.error} onRetry={loadScenarios} /> : null}
      {scenarios.loading ? <LoadingState label="Loading demo scenarios…" /> : <DemoControls scenarios={scenarios.items} onRun={runScenario} onReset={() => setConfirmReset(true)} runningScenario={runningScenario} disabled={false} />}
      {events.error ? <ErrorState error={events.error} onRetry={loadSimulatorEvents} /> : null}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-white">Recent Simulator Events</h2>
        {events.loading ? <LoadingState label="Loading simulator events…" /> : <EventTable events={events.items} meta={events.meta} onPageChange={() => {}} />}
      </section>
      <ConfirmDialog
        open={confirmReset}
        title="Reset simulator demo data?"
        message="This calls POST /demo/reset. The backend reset policy removes simulator-origin events only and preserves ESP32-origin and authorized-test records. Continue?"
        confirmLabel="Reset Demo Data"
        onCancel={() => setConfirmReset(false)}
        onConfirm={resetDemo}
      />
      <Toast message={toast?.message} type={toast?.type} onDismiss={() => setToast(null)} />
    </div>
  );
}
