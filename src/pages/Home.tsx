import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import StatCard from '../components/StatCard'
import { stats } from '../data/jobs'

const BRAND = '#1a365d'
const PIE_COLORS = ['#1a365d', '#3a6aa0', '#5f8abf', '#9bbcd9', '#cdddee', '#a8b3c2']

export default function Home() {
  const navigate = useNavigate()

  const industryData = useMemo(
    () =>
      Object.entries(stats['各产业链岗位数'])
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value),
    [],
  )

  const educationData = useMemo(() => {
    // 将"未知"合并为"不限/其他"，避免数据看起来不完整
    const merged: Record<string, number> = {}
    for (const [name, value] of Object.entries(stats['各学历要求分布'])) {
      const key = name === '未知' ? '不限/其他' : name
      merged[key] = (merged[key] ?? 0) + value
    }
    return Object.entries(merged)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [])

  const top10Data = useMemo(
    () => stats['热门岗位TOP20'].slice(0, 10).map((j) => ({ name: j.岗位名称, value: j.记录数 })),
    [],
  )

  return (
    <div className="space-y-6">
      {/* 标题区 */}
      <div className="card p-6 bg-gradient-to-r from-brand-500 to-brand-400 text-white border-0">
        <h1 className="text-2xl sm:text-3xl font-bold">济宁热门工作岗位分析</h1>
        <p className="mt-2 text-white/80 text-sm sm:text-base">
          覆盖 {Object.keys(stats['各产业链岗位数']).length} 条产业链 · {stats['总岗位数(去重后)']} 个去重岗位 ·
          数据采集于 {new Date('2026-09-23').toLocaleDateString('zh-CN')}
        </p>
      </div>

      {/* 4 数据卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="总岗位数"
          value={stats['总岗位数(去重后)']}
          unit="个"
          icon="💼"
          accent="blue"
          onClick={() => navigate('/jobs')}
        />
        <StatCard
          label="5 星紧缺岗位"
          value={stats['各紧缺星级分布']['5星'] ?? 0}
          unit="个"
          icon="⭐"
          accent="amber"
          onClick={() => navigate('/jobs?star=5')}
        />
        <StatCard
          label="平均年薪"
          value={stats['平均年薪(万元)'].toFixed(2)}
          unit="万元"
          icon="💰"
          accent="emerald"
          onClick={() => navigate('/dashboard')}
        />
        <StatCard
          label="覆盖产业链"
          value={Object.keys(stats['各产业链岗位数']).length}
          unit="条"
          icon="🏭"
          accent="purple"
          onClick={() => navigate('/jobs')}
        />
      </div>

      {/* 图表区：产业链柱状图 + 学历饼图 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="card p-5 lg:col-span-3">
          <h2 className="text-lg font-semibold text-brand-600 mb-1">各产业链岗位数量</h2>
          <p className="text-xs text-slate-400 mb-4">按岗位数量降序，共 {industryData.length} 条产业链</p>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart
              data={industryData}
              margin={{ top: 8, right: 16, bottom: 60, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="name"
                angle={-35}
                textAnchor="end"
                interval={0}
                height={70}
                tick={{ fontSize: 11, fill: '#64748b' }}
              />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                cursor={{ fill: 'rgba(26,54,93,0.05)' }}
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
              />
              <Bar dataKey="value" name="岗位数" fill={BRAND} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5 lg:col-span-2">
          <h2 className="text-lg font-semibold text-brand-600 mb-1">学历要求分布</h2>
          <p className="text-xs text-slate-400 mb-4">全部岗位按学历要求占比</p>
          <ResponsiveContainer width="100%" height={420}>
            <PieChart>
              <Pie
                data={educationData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={130}
                innerRadius={60}
                label={(e) => `${e.name} ${e.value}`}
                labelLine={false}
                onClick={(data: { name?: string }) => {
                  if (data?.name) navigate(`/jobs?edu=${encodeURIComponent(data.name)}`)
                }}
              >
                {educationData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 横向柱状图：热门岗位 TOP10 */}
      <div className="card p-5">
        <h2 className="text-lg font-semibold text-brand-600 mb-1">热门岗位 TOP10</h2>
        <p className="text-xs text-slate-400 mb-4">按记录数排名前十的岗位名称</p>
        <ResponsiveContainer width="100%" height={420}>
          <BarChart
            data={top10Data}
            layout="vertical"
            margin={{ top: 8, right: 24, bottom: 8, left: 80 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
            <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
            <YAxis
              type="category"
              dataKey="name"
              width={80}
              tick={{ fontSize: 12, fill: '#475569' }}
            />
            <Tooltip
              cursor={{ fill: 'rgba(26,54,93,0.05)' }}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Bar
              dataKey="value"
              name="记录数"
              fill={BRAND}
              radius={[0, 4, 4, 0]}
              onClick={(data: { name?: string }) => {
                if (data?.name) navigate(`/jobs?q=${encodeURIComponent(data.name)}`)
              }}
              cursor="pointer"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 数据来源说明 */}
      <div className="text-xs text-slate-400 text-center px-4">
        数据来源：济宁市人社局《标志性产业链重点人才需求蓝皮书（2026版）》、济宁市属事业单位公开招聘公告、
        汶上县招聘公告、济宁直聘网等公开渠道。原始记录 {stats['总记录数(去重前)']} 条，
        去重聚合后保留 {stats['总岗位数(去重后)']} 条。其中 {stats['有年薪数据岗位数']} 条具备年薪数据，
        平均年薪 {stats['平均年薪(万元)'].toFixed(2)} 万元。本页面仅供分析参考，不作为求职决策唯一依据。
      </div>
    </div>
  )
}
