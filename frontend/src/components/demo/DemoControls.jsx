import { FlaskConical, Play, RotateCcw } from 'lucide-react';
import { labelize } from '../../utils/format';

export default function DemoControls({ scenarios = [], onRun, onReset, runningScenario, disabled }) {
  return (
    <section className="panel p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white"><FlaskConical className="h-5 w-5 text-purple-300" /> Safe Demo Scenarios</h2>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-400">Demo events are marked with origin <span className="font-semibold text-purple-200">simulator</span>. They are intentionally distinct from ESP32-origin telemetry and are safe to reset through the backend demo policy.</p>
        </div>
        <button type="button" onClick={onReset} disabled={disabled} className="focus-ring inline-flex items-center justify-center gap-2 rounded-xl border border-red-400/30 px-4 py-2.5 text-sm font-semibold text-red-100 disabled:opacity-50 hover:bg-red-400/10">
          <RotateCcw className="h-4 w-4" /> Reset Demo Data
        </button>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {scenarios.map((scenario) => (
          <button key={scenario} type="button" disabled={disabled || runningScenario === scenario} onClick={() => onRun(scenario)} className="focus-ring rounded-xl border border-slate-700 bg-navy-900 p-4 text-left hover:border-purple-300/40 hover:bg-purple-400/10 disabled:cursor-not-allowed disabled:opacity-50">
            <div className="flex items-center justify-between gap-3">
              <span className="font-semibold text-white">{labelize(scenario)}</span>
              <Play className="h-4 w-4 text-purple-300" />
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-400">Run backend scenario and persist simulator-labeled detection events.</p>
          </button>
        ))}
      </div>
    </section>
  );
}
