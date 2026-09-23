import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import JobCard from '../components/JobCard'
import MultiSelect from '../components/MultiSelect'
import Pagination from '../components/Pagination'
import RangeSlider from '../components/RangeSlider'
import { useDebouncedValue } from '../hooks/useDebounce'
import { jobs, stats, starToNumber, MAX_SALARY } from '../data/jobs'

const PAGE_SIZE = 20

const UNKNOWN = '未知'

// 选项构建
const industryOptions = Object.keys(stats['各产业链岗位数']).map((v) => ({ value: v, label: v }))
const educationOptions = [
  { value: '本科', label: '本科' },
  { value: '大专', label: '大专' },
  { value: '硕士', label: '硕士' },
  { value: '博士', label: '博士' },
  { value: '高中及以下', label: '高中及以下' },
  { value: UNKNOWN, label: '未知/暂无要求' },
]
const starOptions = [
  { value: '5星', label: '5 星' },
  { value: '4星', label: '4 星' },
  { value: '3星', label: '3 星' },
  { value: '2星', label: '2 星' },
  { value: '1星', label: '1 星' },
  { value: UNKNOWN, label: '未知/未评定' },
]

type SortKey = 'default' | 'star' | 'salary' | 'exp'
const sortOptions: { value: SortKey; label: string }[] = [
  { value: 'default', label: '默认排序' },
  { value: 'star', label: '按紧缺星级降序' },
  { value: 'salary', label: '按年薪降序' },
  { value: 'exp', label: '按工作经验降序' },
]

export default function Jobs() {
  const [searchParams] = useSearchParams()

  // 从 URL 读取筛选参数（首页/看板跳转时带参）
  const initQ = searchParams.get('q') ?? ''
  const initIndustry = (searchParams.get('industry') ?? '').split(',').filter(Boolean)
  const initEdu = (searchParams.get('edu') ?? '').split(',').filter(Boolean)
  // star 参数支持 "5" → "5星" 或直接 "5星"
  const initStar = (searchParams.get('star') ?? '')
    .split(',')
    .filter(Boolean)
    .map((s) => (/^\d+$/.test(s) ? `${s}星` : s))
  const initMin = Math.max(0, Number(searchParams.get('salaryMin') ?? 0) || 0)
  const initMax = Math.min(MAX_SALARY, Number(searchParams.get('salaryMax') ?? MAX_SALARY) || MAX_SALARY)

  const [keyword, setKeyword] = useState(initQ)
  const debouncedKeyword = useDebouncedValue(keyword, 300)
  const [industries, setIndustries] = useState<string[]>(initIndustry)
  const [educations, setEducations] = useState<string[]>(initEdu)
  const [stars, setStars] = useState<string[]>(initStar)
  const [sort, setSort] = useState<SortKey>('default')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [salaryRange, setSalaryRange] = useState<[number, number]>([initMin, initMax])

  // 过滤 + 排序
  const filtered = useMemo(() => {
    const kw = debouncedKeyword.trim().toLowerCase()
    let list = jobs.filter((j) => {
      if (kw && !j.岗位名称.toLowerCase().includes(kw)) return false
      if (industries.length > 0 && !industries.includes(j.所属产业链)) return false

      // 学历
      if (educations.length > 0) {
        const eduArr = j.学历要求 ?? []
        const nonUnknownSelected = educations.filter((e) => e !== UNKNOWN)
        const matchUnknown = educations.includes(UNKNOWN) && eduArr.length === 0
        const matchNormal = eduArr.some((e) => nonUnknownSelected.includes(e))
        if (!matchUnknown && !matchNormal) return false
      }

      // 紧缺星级
      if (stars.length > 0) {
        const starVal = j.紧缺星级
        const matchUnknown = stars.includes(UNKNOWN) && starVal == null
        const matchNormal = starVal != null && stars.includes(starVal)
        if (!matchUnknown && !matchNormal) return false
      }

      // 薪资：仅当范围未全开时过滤
      if (!(salaryRange[0] === 0 && salaryRange[1] === MAX_SALARY)) {
        const s = j['年薪均值（万元）']
        if (s == null || s < salaryRange[0] || s > salaryRange[1]) return false
      }
      return true
    })

    list = list.sort((a, b) => {
      const sa = starToNumber(a.紧缺星级)
      const sb = starToNumber(b.紧缺星级)
      const ea = a['年薪均值（万元）']
      const eb = b['年薪均值（万元）']
      const xa = a.工作经验年数
      const xb = b.工作经验年数
      switch (sort) {
        case 'star': return cmpDesc(sa, sb)
        case 'salary': return cmpDesc(ea, eb)
        case 'exp': return cmpDesc(xa, xb)
        default: return 0
      }
    })
    return list
  }, [debouncedKeyword, industries, educations, stars, salaryRange, sort])

  // 筛选条件变动时回到第一页
  useEffect(() => {
    setPage(1)
  }, [debouncedKeyword, industries, educations, stars, salaryRange, sort])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageData = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const hasFilter =
    industries.length + educations.length + stars.length > 0 ||
    debouncedKeyword !== '' ||
    !(salaryRange[0] === 0 && salaryRange[1] === MAX_SALARY)

  function resetAll() {
    setKeyword('')
    setIndustries([])
    setEducations([])
    setStars([])
    setSalaryRange([0, MAX_SALARY])
    setSort('default')
  }

  return (
    <div className="space-y-4">
      {/* 搜索框 */}
      <div className="card p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="按岗位名称搜索，如「机械工程师」「外贸」"
              className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>
          <button
            className="lg:hidden rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600"
            onClick={() => setShowFilters((s) => !s)}
          >
            筛选 {hasFilter ? '●' : ''}
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[280px_1fr] gap-4">
        {/* 筛选面板 */}
        <aside className={`${showFilters ? 'block' : 'hidden'} lg:block`}>
          <div className="card p-4 space-y-4 lg:sticky lg:top-6">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-brand-600">筛选条件</h2>
              {hasFilter && (
                <button onClick={resetAll} className="text-xs text-brand-400 hover:text-brand-600">
                  重置全部
                </button>
              )}
            </div>
            <MultiSelect title="产业链" options={industryOptions} selected={industries} onChange={setIndustries} />
            <MultiSelect title="学历要求" options={educationOptions} selected={educations} onChange={setEducations} />
            <MultiSelect title="紧缺星级" options={starOptions} selected={stars} onChange={setStars} />
            <div>
              <span className="text-sm font-medium text-slate-700">年薪范围</span>
              <div className="mt-1.5">
                <RangeSlider min={0} max={MAX_SALARY} step={1} value={salaryRange} onChange={setSalaryRange} />
              </div>
            </div>
          </div>
        </aside>

        {/* 结果区 */}
        <section>
          {/* 已选条件标签 */}
          {hasFilter && (
            <div className="card p-3 mb-4 flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-400 shrink-0">已选条件：</span>
              {debouncedKeyword && (
                <button
                  onClick={() => setKeyword('')}
                  className="chip hover:bg-brand-100"
                >
                  🔍 {debouncedKeyword} <span className="ml-1 opacity-60">×</span>
                </button>
              )}
              {industries.map((v) => (
                <button
                  key={`i-${v}`}
                  onClick={() => setIndustries(industries.filter((x) => x !== v))}
                  className="chip hover:bg-brand-100"
                >
                  🏭 {v} <span className="ml-1 opacity-60">×</span>
                </button>
              ))}
              {educations.map((v) => (
                <button
                  key={`e-${v}`}
                  onClick={() => setEducations(educations.filter((x) => x !== v))}
                  className="chip hover:bg-brand-100"
                >
                  🎓 {v === UNKNOWN ? '未知/暂无要求' : v} <span className="ml-1 opacity-60">×</span>
                </button>
              ))}
              {stars.map((v) => (
                <button
                  key={`s-${v}`}
                  onClick={() => setStars(stars.filter((x) => x !== v))}
                  className="chip hover:bg-brand-100"
                >
                  ⭐ {v === UNKNOWN ? '未知/未评定' : v} <span className="ml-1 opacity-60">×</span>
                </button>
              ))}
              {!(salaryRange[0] === 0 && salaryRange[1] === MAX_SALARY) && (
                <button
                  onClick={() => setSalaryRange([0, MAX_SALARY])}
                  className="chip hover:bg-brand-100"
                >
                  💰 {salaryRange[0]}-{salaryRange[1]}万 <span className="ml-1 opacity-60">×</span>
                </button>
              )}
            </div>
          )}

          {/* 结果栏：数量 + 排序 */}
          <div className="card p-3 mb-4 flex items-center justify-between gap-2">
            <span className="text-sm text-slate-600">
              共 <span className="font-semibold text-brand-600">{filtered.length}</span> 个岗位
              {filtered.length !== jobs.length && (
                <span className="text-slate-400"> / 总 {jobs.length}</span>
              )}
            </span>
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400">排序</label>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortKey)}
                className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-700 focus:outline-none focus:border-brand-400"
              >
                {sortOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 列表 / 空状态 */}
          {pageData.length === 0 ? (
            <div className="card p-10 text-center">
              <div className="text-5xl mb-3">🔎</div>
              <p className="text-lg font-medium text-slate-600">没有找到符合条件的岗位</p>
              <p className="mt-2 text-sm text-slate-400">
                试试放宽筛选条件，或
                <button onClick={resetAll} className="text-brand-500 hover:underline mx-1">重置全部</button>
                重新查看。
              </p>
            </div>
          ) : (
            <>
              <div
                key={`${currentPage}-${debouncedKeyword}-${sort}-${industries.join()}-${educations.join()}-${stars.join()}-${salaryRange.join()}`}
                className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3 fade-in"
              >
                {pageData.map((job) => (
                  <JobCard key={`${job.岗位名称}-${job.所属产业链}`} job={job} />
                ))}
              </div>
              <div className="mt-5">
                <Pagination page={currentPage} totalPages={totalPages} onChange={setPage} />
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

// 降序比较，null/undefined 排最后
function cmpDesc<T extends number | null | undefined>(a: T, b: T): number {
  if (a == null && b == null) return 0
  if (a == null) return 1
  if (b == null) return -1
  return (b as number) - (a as number)
}
