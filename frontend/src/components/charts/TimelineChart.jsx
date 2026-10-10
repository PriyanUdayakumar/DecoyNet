import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatShortTime } from '../../utils/format';

function TooltipContent({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-700 bg-navy-900/95 p-3 text-sm shadow-xl">
      <p className="font-semibold text-white">{formatShortTime(label)}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="mt-1 text-slate-300">
          <span style={{ color: entry.color }}>●</span> {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
}

export default function TimelineChart({ data = [] }) {
  const chartData = data.map((point) => ({
    ...point,
    label: point.bucket_start,
    event_count: Number(point.event_count || 0),
    high_risk_count: Number(point.high_risk_count || 0),
  }));

  return (
    <div className="panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Event Timeline</h2>
          <p className="text-sm text-slate-400">Hourly event volume and high-risk activity.</p>
        </div>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="eventsFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f87171" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#f87171" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="label" tickFormatter={formatShortTime} stroke="#94a3b8" tick={{ fontSize: 12 }} minTickGap={28} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} allowDecimals={false} />
            <Tooltip content={<TooltipContent />} />
            <Area type="monotone" dataKey="event_count" name="Events" stroke="#22d3ee" strokeWidth={2} fill="url(#eventsFill)" />
            <Area type="monotone" dataKey="high_risk_count" name="High risk" stroke="#f87171" strokeWidth={2} fill="url(#riskFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
