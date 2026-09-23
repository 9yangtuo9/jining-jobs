import { useEffect, useRef, useState } from 'react'

interface Option {
  value: string
  label: string
}

interface MultiSelectProps {
  title: string
  options: Option[]
  selected: string[]
  onChange: (next: string[]) => void
}

export default function MultiSelect({ title, options, selected, onChange }: MultiSelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  function toggle(value: string) {
    onChange(
      selected.includes(value)
        ? selected.filter((v) => v !== value)
        : [...selected, value],
    )
  }

  function clear() {
    onChange([])
  }

  return (
    <div className="relative" ref={ref}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">{title}</span>
        {selected.length > 0 && (
          <button
            onClick={clear}
            className="text-xs text-brand-400 hover:text-brand-600"
          >
            清除
          </button>
        )}
      </div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="mt-1.5 w-full flex items-center justify-between rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-600 hover:border-brand-300"
      >
        <span className={selected.length === 0 ? 'text-slate-400' : 'text-slate-700'}>
          {selected.length === 0 ? '全部' : `已选 ${selected.length} 项`}
        </span>
        <span className={`transition text-slate-400 ${open ? 'rotate-180' : ''}`}>▾</span>
      </button>
      {open && (
        <div className="absolute z-20 mt-1 w-full max-h-56 overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          {options.map((opt) => (
            <label
              key={opt.value}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-700 hover:bg-brand-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selected.includes(opt.value)}
                onChange={() => toggle(opt.value)}
                className="accent-brand-500 h-3.5 w-3.5"
              />
              {opt.label}
            </label>
          ))}
        </div>
      )}
    </div>
  )
}
