interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  icon: string
  accent?: 'blue' | 'amber' | 'emerald' | 'purple'
  onClick?: () => void
}

const accentMap: Record<string, string> = {
  blue: 'from-brand-500 to-brand-400',
  amber: 'from-amber-500 to-amber-400',
  emerald: 'from-emerald-500 to-emerald-400',
  purple: 'from-purple-500 to-purple-400',
}

export default function StatCard({ label, value, unit, icon, accent = 'blue', onClick }: StatCardProps) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      className={`card card-hover p-5 overflow-hidden relative text-left w-full ${onClick ? 'cursor-pointer transition-transform hover:scale-[1.02] hover:shadow-lg' : ''}`}
    >
      <div
        className={`absolute -right-6 -top-6 w-24 h-24 rounded-full bg-gradient-to-br ${accentMap[accent]} opacity-10`}
      />
      <div className="flex items-start justify-between gap-3 relative">
        <div>
          <p className="text-sm text-slate-500 font-medium">{label}</p>
          <p className="mt-2 text-3xl font-bold text-brand-600">
            {value}
            {unit && <span className="ml-1 text-base font-normal text-slate-500">{unit}</span>}
          </p>
        </div>
        <span className="text-2xl">{icon}</span>
      </div>
    </Tag>
  )
}
