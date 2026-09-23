import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { jobs, MAX_SALARY } from '../data/jobs'

const BRAND = '#1a365d'
const PIE_COLORS = ['#1a365d', '#3a6aa0', '#5f8abf', '#cdddee']

// 技术岗关键词（研发/设计/生产/质检等）
const TECH_KEYWORDS = [
  '工程师', '技术', '研发', '设计', '工艺', '电气', '机械', '开发', '测试', '运维',
  '程序员', '算法', '架构', '技师', '技术员', '研究员', '编程', '软件', '硬件', '机电',
  '自动化', '生产', '质检', '检验', '化验', '车间', '质量', '工程', '制图', '检测',
  '维修', '设备', '分析', '采样', '焊接', '配方', '配粉', '中控', '操作', '磨床',
  '脑机接口', '环境监控',
]
// 市场岗关键词（销售/营销/客户/运营等）
const MARKET_KEYWORDS = [
  '销售', '外贸', '业务', '市场', '营销', '客户', '招商', '推广', '运营', '商务',
  '采购', '翻译', '经营', '客服', '代表', '摄影', '摄像', '影音', '文案', '策划',
  '采编', '新媒体', '短视频', '影视', '船务', '课程顾问', '跟单', '导购', '店长',
  '主播', '直播', '新闻宣传',
]
// 职能岗关键词（财务/人力/行政/法务/物流等）
const FUNC_KEYWORDS = [
  '会计', '财务', '人事', '人力', '行政', '法务', '仓管', '仓储', '文员', '内勤',
  '管培生', '造价', '预决算', '管理', '专员', '主管', '经理', '秘书', '编审', '物流',
  '安全', '教师', '农技', '统计', '定额', '文字综合', '综合治理', '司机', '送货',
  '装卸', '美容', '头疗', '实习生', '法律事务', '医保', '图书', '文物考古', '林业',
  '环境事务', '产业服务',
]

function classifyJob(name: string): 'tech' | 'market' | 'func' | 'other' {
  if (TECH_KEYWORDS.some((k) => name.includes(k))) return 'tech'
  if (MARKET_KEYWORDS.some((k) => name.includes(k))) return 'market'
  if (FUNC_KEYWORDS.some((k) => name.includes(k))) return 'func'
  return 'other'
}

export default function Dashboard() {
  // 1. 各产业链平均年薪（仅含年薪数据岗位）
  const industrySalary = useMemo(() => {
    const map = new Map<string, { sum: number; count: number }>()
    for (const j of jobs) {
      const s = j['年薪均值（万元）']
      if (s == null) continue
      const cur = map.get(j.所属产业链) ?? { sum: 0, count: 0 }
      cur.sum += s
      cur.count += 1
      map.set(j.所属产业链, cur)
    }
    return Array.from(map.entries())
      .map(([name, { sum, count }]) => ({ name, avg: Number((sum / count).toFixed(2)), count }))
      .sort((a, b) => b.avg - a.avg)
  }, [])

  // 2. 技术岗 / 市场岗 / 职能岗占比
  const categoryData = useMemo(() => {
    let tech = 0, market = 0, func = 0, other = 0
    for (const j of jobs) {
      const c = classifyJob(j.岗位名称)
      if (c === 'tech') tech++
      else if (c === 'market') market++
      else if (c === 'func') func++
      else other++
    }
    return [
      { name: '技术岗', value: tech },
      { name: '市场岗', value: market },
      { name: '职能岗', value: func },
      { name: '其他', value: other },
    ]
  }, [])

  // 3. 薪资区间分布（直方图）—— 更细的 8 档区间
  const salaryBins = useMemo(() => {
    const bins = [
      { name: '0-3万', min: 0, max: 3, value: 0 },
      { name: '3-6万', min: 3, max: 6, value: 0 },
      { name: '6-9万', min: 6, max: 9, value: 0 },
      { name: '9-12万', min: 9, max: 12, value: 0 },
      { name: '12-15万', min: 12, max: 15, value: 0 },
      { name: '15-20万', min: 15, max: 20, value: 0 },
      { name: '20-30万', min: 20, max: 30, value: 0 },
      { name: '30万+', min: 30, max: Infinity, value: 0 },
    ]
    for (const j of jobs) {
      const s = j['年薪均值（万元）']
      if (s == null) continue
      const bin = bins.find((b) => s >= b.min && s < b.max)
      if (bin) bin.value++
    }
    return bins
  }, [])

  // 主流薪资区间（岗位数最多的区间）
  const topBin = salaryBins.reduce((a, b) => (b.value > a.value ? b : a), salaryBins[0])

  const navigate = useNavigate()
  function onSalaryBarClick(data: { payload?: { min: number; max: number } }) {
    const min = data?.payload?.min ?? 0
    const max = data?.payload?.max ?? MAX_SALARY
    navigate(`/jobs?salaryMin=${min}&salaryMax=${max === Infinity ? MAX_SALARY : max}`)
  }

  const totalWithSalary = industrySalary.reduce((s, i) => s + i.count, 0)
  const techPct = ((categoryData[0].value / jobs.length) * 100).toFixed(1)

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="card p-6 bg-gradient-to-r from-brand-500 to-brand-400 text-white border-0">
        <h1 className="text-2xl font-bold">数据分析看板</h1>
        <p className="mt-2 text-white/80 text-sm">
          基于 {jobs.length} 条去重岗位 · {totalWithSalary} 条具备年薪数据 · 数据口径与岗位查询页一致
        </p>
      </div>

      {/* 概览指标 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-xs text-slate-400">有年薪数据岗位</p>
          <p className="mt-1 text-2xl font-bold text-brand-600">{totalWithSalary}<span className="text-sm font-normal text-slate-400"> / {jobs.length}</span></p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-400">产业链平均年薪最高</p>
          <p className="mt-1 text-2xl font-bold text-brand-600">{industrySalary[0]?.name ?? '-'}</p>
          <p className="text-xs text-slate-400">{industrySalary[0]?.avg ?? 0} 万/年</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-400">技术岗占比</p>
          <p className="mt-1 text-2xl font-bold text-brand-600">{techPct}%</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-400">主流薪资区间</p>
          <p className="mt-1 text-2xl font-bold text-brand-600">{topBin?.name ?? '-'}</p>
          <p className="text-xs text-slate-400">{topBin?.value ?? 0} 个岗位</p>
        </div>
      </div>

      {/* 图表1：各产业链平均年薪对比 */}
      <div className="card p-5">
        <h2 className="text-lg font-semibold text-brand-600 mb-1">各产业链平均年薪对比</h2>
        <p className="text-xs text-slate-400 mb-4">按平均年薪降序，仅统计有年薪数据的岗位</p>
        <ResponsiveContainer width="100%" height={460}>
          <BarChart data={industrySalary} margin={{ top: 8, right: 16, bottom: 60, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis
              dataKey="name"
              angle={-35}
              textAnchor="end"
              interval={0}
              height={70}
              tick={{ fontSize: 11, fill: '#64748b' }}
            />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} unit="万" />
            <Tooltip
              cursor={{ fill: 'rgba(26,54,93,0.05)' }}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
              formatter={(v: number) => [`${v} 万/年`, '平均年薪']}
            />
            <Bar dataKey="avg" name="平均年薪" fill={BRAND} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 图表2 + 图表3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 技术岗 vs 市场岗 */}
        <div className="card p-5">
          <h2 className="text-lg font-semibold text-brand-600 mb-1">岗位类型需求占比</h2>
          <p className="text-xs text-slate-400 mb-4">按岗位名称关键词分类：技术岗 / 市场岗 / 职能岗 / 其他</p>
          <ResponsiveContainer width="100%" height={360}>
            <PieChart>
              <Pie
                data={categoryData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={120}
                innerRadius={55}
                label={(e) => `${e.name} ${e.value}`}
                labelLine={false}
              >
                {categoryData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 薪资区间分布直方图 */}
        <div className="card p-5">
          <h2 className="text-lg font-semibold text-brand-600 mb-1">年薪区间分布</h2>
          <p className="text-xs text-slate-400 mb-4">各年薪区间的岗位数量（点击柱状图可跳转查询页筛选该区间）</p>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={salaryBins} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                cursor={{ fill: 'rgba(26,54,93,0.05)' }}
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
                formatter={(v: number) => [`${v} 个岗位`, '岗位数']}
              />
              <Bar
                dataKey="value"
                name="岗位数"
                fill={BRAND}
                radius={[4, 4, 0, 0]}
                onClick={onSalaryBarClick}
                cursor="pointer"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 说明 */}
      <div className="text-xs text-slate-400 text-center px-4">
        数据口径说明：年薪均值来源于清洗后的 jobs_clean.json，与岗位查询页共用同一数据源；
        技术岗/市场岗按岗位名称关键词匹配分类，无法归类的归入「其他岗」；
        薪资区间为左闭右开区间（30+ 为 ≥30 万）。本看板仅供分析参考。
      </div>
    </div>
  )
}
