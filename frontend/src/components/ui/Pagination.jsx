import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function Pagination({ limit, offset, total, onChange }) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const canPrev = offset > 0;
  const canNext = offset + limit < total;

  return (
    <div className="flex flex-col gap-3 border-t border-slate-800 px-4 py-4 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
      <span>
        Showing <span className="text-slate-200">{total === 0 ? 0 : offset + 1}</span>–
        <span className="text-slate-200">{Math.min(offset + limit, total)}</span> of{' '}
        <span className="text-slate-200">{total}</span>
      </span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={!canPrev}
          onClick={() => onChange(Math.max(0, offset - limit))}
          className="focus-ring inline-flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-2 text-slate-200 disabled:cursor-not-allowed disabled:opacity-40 hover:not-disabled:bg-slate-800"
        >
          <ChevronLeft className="h-4 w-4" /> Previous
        </button>
        <span className="px-2 text-slate-300">
          Page {currentPage} / {totalPages}
        </span>
        <button
          type="button"
          disabled={!canNext}
          onClick={() => onChange(offset + limit)}
          className="focus-ring inline-flex items-center gap-1 rounded-lg border border-slate-700 px-3 py-2 text-slate-200 disabled:cursor-not-allowed disabled:opacity-40 hover:not-disabled:bg-slate-800"
        >
          Next <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
