export default function MetricCard({ title, value, subtitle, icon: Icon, tone = 'cyan' }) {
  const tones = {
    cyan: 'from-cyan-400/20 to-cyan-400/0 text-cyan-200 border-cyan-400/20',
    emerald: 'from-emerald-400/20 to-emerald-400/0 text-emerald-200 border-emerald-400/20',
    amber: 'from-amber-400/20 to-amber-400/0 text-amber-200 border-amber-400/20',
    red: 'from-red-400/20 to-red-400/0 text-red-200 border-red-400/20',
    purple: 'from-purple-400/20 to-purple-400/0 text-purple-200 border-purple-400/20',
  };
  return (
    <section className="panel overflow-hidden p-5">
      <div className={`rounded-xl border bg-gradient-to-br p-4 ${tones[tone] || tones.cyan}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-400">{title}</p>
            <p className="mt-2 text-3xl font-bold tabular-nums text-white">{value ?? '—'}</p>
          </div>
          {Icon ? <Icon className="h-6 w-6" aria-hidden="true" /> : null}
        </div>
        {subtitle ? <p className="mt-3 text-sm text-slate-400">{subtitle}</p> : null}
      </div>
    </section>
  );
}
