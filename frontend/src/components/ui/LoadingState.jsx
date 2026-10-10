export default function LoadingState({ label = 'Loading DecoyNet telemetry…' }) {
  return (
    <div className="panel flex min-h-48 items-center justify-center p-8 text-center">
      <div>
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-cyan-300/30 border-t-cyan-300" />
        <p className="mt-4 text-sm text-slate-300">{label}</p>
      </div>
    </div>
  );
}
