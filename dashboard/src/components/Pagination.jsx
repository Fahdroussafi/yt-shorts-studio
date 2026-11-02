import React from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';

export default function Pagination({
  currentPage,
  totalItems,
  perPage,
  onPageChange,
  onPerPageChange,
  perPageOptions = [5, 10, 20, 50],
}) {
  const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
  const safePage = Math.min(Math.max(1, currentPage), totalPages);
  const startItem = totalItems === 0 ? 0 : (safePage - 1) * perPage + 1;
  const endItem = Math.min(totalItems, safePage * perPage);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-slate-900/60 border-t border-slate-800/80 text-xs">
      <div className="flex items-center space-x-3 text-slate-400">
        <span>
          Showing <span className="font-mono font-bold text-white">{startItem}</span> - <span className="font-mono font-bold text-white">{endItem}</span> of <span className="font-mono font-bold text-white">{totalItems}</span>
        </span>
        <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800">
          <span className="text-slate-400">Per page:</span>
          <select
            value={perPage}
            onChange={(e) => {
              onPerPageChange(Number(e.target.value));
              onPageChange(1);
            }}
            className="bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1 outline-none font-mono focus:border-violet-500 cursor-pointer transition text-xs"
          >
            {perPageOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <span className="text-slate-400 font-mono text-xs pr-1">
          Page {safePage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(Math.max(1, safePage - 1))}
          disabled={safePage <= 1}
          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition"
          title="Previous Page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-1">
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((p) => p === 1 || p === totalPages || Math.abs(p - safePage) <= 1)
            .reduce((acc, p, idx, arr) => {
              if (idx > 0 && p - arr[idx - 1] > 1) {
                acc.push({ type: 'ellipsis', key: `ell-${p}` });
              }
              acc.push({ type: 'page', page: p, key: `page-${p}` });
              return acc;
            }, [])
            .map((item) =>
              item.type === 'ellipsis' ? (
                <span key={item.key} className="px-1 text-slate-600 font-mono">...</span>
              ) : (
                <button
                  key={item.key}
                  onClick={() => onPageChange(item.page)}
                  className={`min-w-[28px] h-7 px-2 rounded-lg font-mono font-bold transition text-xs ${
                    safePage === item.page
                      ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                      : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {item.page}
                </button>
              )
            )}
        </div>

        <button
          onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
          disabled={safePage >= totalPages}
          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition"
          title="Next Page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
