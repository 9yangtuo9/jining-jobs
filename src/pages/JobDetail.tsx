import { Link, useParams } from 'react-router-dom'
import StarRating from '../components/StarRating'
import { findJobById, formatSalary } from '../data/jobs'
import type { JobRecord } from '../types'

// 通用：空值兜底显示
function na(v: unknown, fallback = '暂无数据'): string {
  if (v === null || v === undefined) return fallback
  if (Array.isArray(v) && v.length === 0) return fallback
  if (typeof v === 'string' && v.trim() === '') return fallback
  return String(v)
}

function joinList(arr: string[] | null, fallback = '暂无数据'): string {
  if (!arr || arr.length === 0) return fallback
  return arr.join('、')
}

// 信息行：左侧标签 + 右侧值
function InfoRow({ label, value, full }: { label: string; value: React.ReactNode; full?: boolean }) {
  return (
    <div className={`flex gap-3 ${full ? 'sm:col-span-2' : ''}`}>
      <dt className="w-28 shrink-0 text-sm text-slate-400">{label}</dt>
      <dd className="flex-1 text-sm text-slate-700">{value}</dd>
    </div>
  )
}

export default function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const job: JobRecord | undefined = id ? findJobById(id) : undefined

  if (!job) {
    return (
      <div className="card p-10 text-center">
        <div className="text-5xl mb-3">⚠️</div>
        <p className="text-lg font-medium text-slate-600">未找到该岗位</p>
        <p className="mt-2 text-sm text-slate-400">岗位可能已下线或链接有误。</p>
        <Link to="/jobs" className="mt-4 inline-block text-brand-500 hover:underline">
          ← 返回岗位查询
        </Link>
      </div>
    )
  }

  const salary = job['年薪均值（万元）']
  const estimated = job.年薪是否估算
  const exp = job.工作经验年数

  return (
    <div className="space-y-4">
      <Link to="/jobs" className="inline-flex items-center gap-1 text-sm text-brand-500 hover:text-brand-700">
        ← 返回岗位查询
      </Link>

      {/* 头部卡片 */}
      <div className="card p-6 bg-gradient-to-br from-brand-500 to-brand-400 text-white border-0">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold break-words">{job.岗位名称}</h1>
            <p className="mt-1.5 text-white/85 text-sm">{job.所属产业链}</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">{salary != null ? `${salary.toFixed(2)} 万/年` : '面议'}</p>
            {estimated != null && (
              <p className="text-xs text-white/70 mt-1">
                {estimated ? '（月薪估算值）' : '（蓝皮书原值）'}
              </p>
            )}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="inline-flex items-center gap-1 bg-white/20 rounded-full px-3 py-1">
            <StarRating star={job.紧缺星级} size="sm" />
          </span>
          {job.学历要求 && job.学历要求.length > 0 && (
            <span className="bg-white/20 rounded-full px-3 py-1">🎓 {job.学历要求.join(' / ')}</span>
          )}
          {exp != null && (
            <span className="bg-white/20 rounded-full px-3 py-1">⏱ {exp} 年经验</span>
          )}
        </div>
      </div>

      {/* 基本信息 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-4">基本信息</h2>
        <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-4">
          <InfoRow label="所属产业链" value={job.所属产业链} />
          <InfoRow
            label="紧缺星级"
            value={
              job.紧缺星级 ? (
                <StarRating star={job.紧缺星级} size="sm" />
              ) : (
                <span className="text-slate-400">未评定</span>
              )
            }
          />
          <InfoRow label="学历要求" value={joinList(job.学历要求, '暂无要求')} />
          <InfoRow label="工作经验" value={exp != null ? `${exp} 年` : '暂无数据'} />
          <InfoRow
            label="年薪均值"
            value={
              salary != null ? (
                <span className="text-emerald-600 font-medium">{formatSalary(salary)}</span>
              ) : (
                <span className="text-slate-400">面议</span>
              )
            }
          />
          <InfoRow
            label="年薪来源"
            value={
              estimated == null
                ? '暂无数据'
                : estimated
                  ? '月薪估算（非蓝皮书）'
                  : '蓝皮书 2026 版原值'
            }
          />
        </dl>
      </div>

      {/* 专业要求 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">专业要求</h2>
        {job.专业要求 && job.专业要求.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {job.专业要求.map((m, i) => (
              <span key={i} className="chip">{m}</span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">暂无数据</p>
        )}
      </div>

      {/* 任职能力要求 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">任职能力要求</h2>
        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
          {na(job.任职能力要求)}
        </p>
      </div>

      {/* 薪资原文 / 福利（可选，仅在有数据时显示） */}
      {(job.薪资原文 || job.福利信息) && (
        <div className="card p-6">
          <h2 className="text-base font-semibold text-brand-600 mb-3">薪资与福利</h2>
          <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-4">
            {job.薪资原文 && <InfoRow label="薪资原文" value={job.薪资原文} />}
            {(job.薪资下限 != null || job.薪资上限 != null) && (
              <InfoRow
                label="薪资范围"
                value={`${job.薪资下限 ?? '?'} – ${job.薪资上限 ?? '?'} ${job.薪资单位 ?? ''}`.trim()}
              />
            )}
            {job.福利信息 && <InfoRow label="福利信息" value={job.福利信息} full />}
          </dl>
        </div>
      )}

      {/* 代表企业 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">代表企业</h2>
        {job.代表企业 && job.代表企业.length > 0 ? (
          <ul className="space-y-1.5">
            {job.代表企业.map((c, i) => (
              <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                <span className="text-brand-300 mt-0.5">●</span>
                {c}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-400">暂无数据</p>
        )}
      </div>

      {/* 数据来源 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">数据来源</h2>
        <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-4">
          <InfoRow label="数据来源" value={joinList(job.数据来源)} />
          <InfoRow label="采集日期" value={na(job.数据采集日期)} />
          <InfoRow
            label="合并记录数"
            value={job._合并记录数 != null ? `${job._合并记录数} 条` : '暂无数据'}
          />
        </dl>
        <p className="mt-4 text-xs text-slate-400">
          本岗位信息由多条同源数据聚合去重所得，仅供分析参考，不作为求职决策唯一依据。
        </p>
      </div>
    </div>
  )
}
