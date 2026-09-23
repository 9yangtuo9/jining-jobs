import { Link } from 'react-router-dom'
import type { JobRecord } from '../types'
import StarRating from './StarRating'
import { formatSalary, jobId } from '../data/jobs'

interface JobCardProps {
  job: JobRecord
}

export default function JobCard({ job }: JobCardProps) {
  const majors = (job.专业要求 ?? []).slice(0, 3)
  const educations = job.学历要求 ?? []
  const id = jobId(job)

  return (
    <Link
      to={`/jobs/${id}`}
      className="card card-hover p-4 block focus:outline-none focus:ring-2 focus:ring-brand-300"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-brand-700 truncate">{job.岗位名称}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{job.所属产业链}</p>
        </div>
        <StarRating star={job.紧缺星级} size="sm" />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="chip">💰 {formatSalary(job['年薪均值（万元）'])}</span>
        <span className="chip">
          🎓 {educations.length > 0 ? educations.join(' / ') : '暂无要求'}
        </span>
        {job.工作经验年数 != null && (
          <span className="chip">⏱ {job.工作经验年数} 年经验</span>
        )}
      </div>

      {majors.length > 0 && (
        <p className="mt-2 text-xs text-slate-500">
          <span className="text-slate-400">专业要求：</span>
          {majors.join('、')}
          {(job.专业要求?.length ?? 0) > 3 && (
            <span className="text-slate-400"> 等{job.专业要求?.length}个</span>
          )}
        </p>
      )}
    </Link>
  )
}
