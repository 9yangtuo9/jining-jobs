interface PaginationProps {
  page: number
  totalPages: number
  onChange: (page: number) => void
}

export default function Pagination({ page, totalPages, onChange }: PaginationProps) {
  if (totalPages <= 1) return null

  // 生成页码（首尾+当前页附近，过多用省略号）
  const pages: (number | string)[] = []
  const push = (n: number | string) => pages.push(n)
  push(1)
  const start = Math.max(2, page - 1)
  const end = Math.min(totalPages - 1, page + 1)
  if (start > 2) push('…')
  for (let i = start; i <= end; i++) push(i)
  if (end < totalPages - 1) push('…')
  if (totalPages > 1) push(totalPages)

  const btn =
    'min-w-[32px] h-8 px-2 rounded-lg text-sm flex items-center justify-center transition'

  return (
    <div className="flex items-center justify-center gap-1.5 flex-wrap">
      <button
        className={`${btn} border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40`}
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        上一页
      </button>
      {pages.map((p, i) =>
        typeof p === 'number' ? (
          <button
            key={i}
            className={`${btn} ${
              p === page
                ? 'bg-brand-500 text-white border border-brand-500'
                : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
            onClick={() => onChange(p)}
          >
            {p}
          </button>
        ) : (
          <span key={i} className="px-1 text-slate-400">
            {p}
          </span>
        ),
      )}
      <button
        className={`${btn} border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40`}
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        下一页
      </button>
    </div>
  )
}
