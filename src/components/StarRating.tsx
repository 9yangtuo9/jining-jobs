interface StarRatingProps {
  star: string | null
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = { sm: 'text-xs', md: 'text-sm', lg: 'text-base' }

export default function StarRating({ star, size = 'sm' }: StarRatingProps) {
  if (!star) {
    return <span className="text-slate-300 text-xs">未评定</span>
  }
  const m = star.match(/(\d)/)
  const n = m ? parseInt(m[1], 10) : 0
  return (
    <span className={`inline-flex items-center gap-0.5 ${sizeMap[size]}`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span key={i} className={i < n ? 'text-amber-400' : 'text-slate-200'}>
          ★
        </span>
      ))}
      <span className="ml-1 text-slate-500">{star}</span>
    </span>
  )
}
