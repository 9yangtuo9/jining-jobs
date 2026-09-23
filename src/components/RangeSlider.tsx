interface RangeSliderProps {
  min: number
  max: number
  step?: number
  value: [number, number]
  onChange: (next: [number, number]) => void
}

export default function RangeSlider({
  min,
  max,
  step = 1,
  value,
  onChange,
}: RangeSliderProps) {
  const [lo, hi] = value
  const loPct = ((lo - min) / (max - min)) * 100
  const hiPct = ((hi - min) / (max - min)) * 100

  return (
    <div>
      <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
        <span>{min} 万</span>
        <span className="text-brand-600 font-medium">
          {lo} – {hi} 万
        </span>
        <span>{max} 万</span>
      </div>
      <div className="dual-range">
        {/* 轨道 */}
        <div className="absolute left-0 right-0 top-[14px] h-1.5 rounded-full bg-slate-200" />
        {/* 选中填充 */}
        <div
          className="absolute top-[14px] h-1.5 rounded-full bg-brand-400"
          style={{ left: `${loPct}%`, right: `${100 - hiPct}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={lo}
          onChange={(e) => {
            const v = Number(e.target.value)
            onChange([Math.min(v, hi), hi])
          }}
          style={{ zIndex: lo > max - (max - min) * 0.05 ? 5 : 3 }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={hi}
          onChange={(e) => {
            const v = Number(e.target.value)
            onChange([lo, Math.max(v, lo)])
          }}
          style={{ zIndex: 4 }}
        />
      </div>
    </div>
  )
}
