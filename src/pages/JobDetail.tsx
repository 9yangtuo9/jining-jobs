import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import StarRating from '../components/StarRating'
import { findJobById, formatSalary } from '../data/jobs'
import type { JobRecord } from '../types'

// 信息行：左侧标签 + 右侧值
function InfoRow({ label, value, full }: { label: string; value: React.ReactNode; full?: boolean }) {
  return (
    <div className={`flex gap-3 ${full ? 'sm:col-span-2' : ''}`}>
      <dt className="w-28 shrink-0 text-sm text-slate-400">{label}</dt>
      <dd className="flex-1 text-sm text-slate-700">{value}</dd>
    </div>
  )
}

// 空状态提示块（引导性文案）
function EmptyHint({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg bg-slate-50 border border-slate-200 p-3.5">
      <span className="text-lg shrink-0">{icon}</span>
      <p className="text-sm text-slate-500 leading-relaxed">{text}</p>
    </div>
  )
}

// 一键复制按钮
function CopyJobNameButton({ jobName }: { jobName: string }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(jobName).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }).catch(() => {
      // fallback
      const ta = document.createElement('textarea')
      ta.value = jobName
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button
      onClick={copy}
      className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-brand-500 px-3.5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-600"
    >
      {copied ? '✓ 已复制' : '📋 一键复制岗位名称'}
    </button>
  )
}

// 复制公司名按钮 + Toast
function CopyCompanyButton({ companyName }: { companyName: string }) {
  const [toast, setToast] = useState(false)
  function copy() {
    navigator.clipboard.writeText(companyName).then(() => {
      setToast(true)
      setTimeout(() => setToast(false), 2500)
    }).catch(() => {
      const ta = document.createElement('textarea')
      ta.value = companyName
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setToast(true)
      setTimeout(() => setToast(false), 2500)
    })
  }
  return (
    <>
      <button
        onClick={copy}
        className="ml-2 inline-flex items-center gap-1 rounded-md border border-brand-300 px-2 py-0.5 text-xs font-medium text-brand-500 transition-colors hover:bg-brand-50"
      >
        📋 复制公司名
      </button>
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 rounded-lg bg-slate-800 px-4 py-2.5 text-sm text-white shadow-lg">
          公司名称已复制，请去招聘APP粘贴搜索
        </div>
      )}
    </>
  )
}

// 如何应聘模块
function ApplyGuide({ companyName, jobName }: { companyName: string | null; jobName: string }) {
  const query = companyName ?? jobName
  const links = [
    { label: '去BOSS直聘搜索', url: `https://www.zhipin.com/web/geek/job?query=${encodeURIComponent(query)}`, color: 'bg-emerald-500 hover:bg-emerald-600' },
    { label: '去企查查查询公司电话', url: `https://www.qcc.com/web/search?key=${encodeURIComponent(query)}`, color: 'bg-amber-500 hover:bg-amber-600' },
    { label: '去百度搜索该公司官网', url: `https://www.baidu.com/s?wd=${encodeURIComponent(query)}+官网`, color: 'bg-blue-500 hover:bg-blue-600' },
  ]
  return (
    <div className="card p-6 border-brand-200 bg-brand-50/30">
      <h2 className="text-base font-semibold text-brand-600 mb-3">如何应聘</h2>
      <p className="text-sm text-slate-600 leading-relaxed">
        由于隐私保护，本站不直接提供HR联系方式。建议您复制公司名称，前往以下平台搜索并投递：
      </p>
      <div className="mt-4 flex flex-wrap gap-2.5">
        {links.map((l) => (
          <a
            key={l.label}
            href={l.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center gap-1.5 rounded-lg ${l.color} px-4 py-2 text-sm font-medium text-white transition-colors`}
          >
            {l.label}
            <span className="text-xs opacity-75">↗</span>
          </a>
        ))}
      </div>
      <p className="mt-4 text-xs text-slate-400">
        ⚠️ 求职请认准官方招聘平台，谨防收费陷阱和虚假招聘。
      </p>
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
  const hasCompanies = job.代表企业 && job.代表企业.length > 0
  const hasMajors = job.专业要求 && job.专业要求.length > 0
  const hasAbility = job.任职能力要求 && job.任职能力要求.trim() !== ''
  const hasSalaryDetail = job.薪资原文 || job.福利信息

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
          <InfoRow
            label="学历要求"
            value={
              job.学历要求 && job.学历要求.length > 0
                ? job.学历要求.join(' / ')
                : <span className="text-slate-400">不限</span>
            }
          />
          <InfoRow
            label="工作经验"
            value={exp != null ? `${exp} 年` : <span className="text-slate-400">不限</span>}
          />
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
                ? <span className="text-slate-400">未标注</span>
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
        {hasMajors ? (
          <div className="flex flex-wrap gap-2">
            {job.专业要求!.map((m, i) => (
              <span key={i} className="chip">{m}</span>
            ))}
          </div>
        ) : (
          <EmptyHint
            icon="🎓"
            text="该岗位未限定具体专业要求，通常表示接受相关专业背景的求职者。建议您结合自身专业方向，对照所属产业链的岗位特征准备求职。"
          />
        )}
      </div>

      {/* 任职能力要求 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">任职能力要求</h2>
        {hasAbility ? (
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
            {job.任职能力要求}
          </p>
        ) : (
          <EmptyHint
            icon="📋"
            text="该岗位暂未公布详细任职能力要求。建议您复制岗位名称，前往招聘平台搜索同类岗位的能力要求描述作为参考。"
          />
        )}
      </div>

      {/* 薪资与福利 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">薪资与福利</h2>
        {hasSalaryDetail ? (
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
        ) : (
          <EmptyHint
            icon="💰"
            text="该岗位薪资信息以「年薪均值」或「面议」形式呈现，暂无额外的月薪原文和福利详情。建议您在面试时与招聘方确认具体薪资结构和福利待遇。"
          />
        )}
      </div>

      {/* 代表企业 */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-base font-semibold text-brand-600">代表企业</h2>
          {hasCompanies && <CopyCompanyButton companyName={job.代表企业![0]} />}
        </div>
        {hasCompanies ? (
          <ul className="space-y-1.5">
            {job.代表企业!.map((c, i) => (
              <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                <span className="text-brand-300 mt-0.5">●</span>
                {c}
              </li>
            ))}
          </ul>
        ) : (
          <div>
            <EmptyHint
              icon="🏢"
              text="该岗位为济宁市重点产业紧缺岗位，暂未指定具体招聘企业。建议您复制岗位名称，前往招聘平台搜索相关企业。"
            />
            <CopyJobNameButton jobName={job.岗位名称} />
          </div>
        )}
      </div>

      {/* 如何应聘 */}
      <ApplyGuide
        companyName={hasCompanies ? job.代表企业![0] : null}
        jobName={job.岗位名称}
      />

      {/* 数据来源 */}
      <div className="card p-6">
        <h2 className="text-base font-semibold text-brand-600 mb-3">数据来源</h2>
        <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-4">
          <InfoRow label="数据来源" value={job.数据来源.join('、')} />
          <InfoRow label="采集日期" value={job.数据采集日期 ?? '—'} />
          <InfoRow
            label="合并记录数"
            value={job._合并记录数 != null ? `${job._合并记录数} 条` : '—'}
          />
        </dl>
        <p className="mt-4 text-xs text-slate-400">
          本岗位信息由多条同源数据聚合去重所得，仅供分析参考，不作为求职决策唯一依据。
        </p>
      </div>
    </div>
  )
}
