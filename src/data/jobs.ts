import cleanDataRaw from './jobs_clean.json'
import statsRaw from './jobs_stats.json'
import type { JobCleanFile, JobStats, JobRecord } from '../types'

// 运行时加载本地 JSON（Vite 原生支持 JSON import）
export const cleanData = cleanDataRaw as unknown as JobCleanFile
export const stats = statsRaw as unknown as JobStats

export const jobs: JobRecord[] = cleanData.records

// 工具：紧缺星级 -> 数字
export function starToNumber(star: string | null): number | null {
  if (!star) return null
  const m = star.match(/(\d)/)
  return m ? parseInt(m[1], 10) : null
}

// 工具：年薪显示
export function formatSalary(v: number | null): string {
  if (v == null) return '面议'
  return `${v.toFixed(2)} 万元/年`
}

// 稳定 ID：基于岗位名称 + 所属产业链的哈希，数组顺序变化也不影响
function djb2(str: string): string {
  let h = 5381
  for (let i = 0; i < str.length; i++) h = (h * 33) ^ str.charCodeAt(i)
  return (h >>> 0).toString(16)
}

export function jobId(job: JobRecord): string {
  return djb2(`${job.岗位名称}|${job.所属产业链}`)
}

export function findJobById(id: string): JobRecord | undefined {
  return jobs.find((j) => jobId(j) === id)
}

// 最高年薪（用于滑块上限）
export const MAX_SALARY = Math.ceil(
  Math.max(...jobs.map((j) => j['年薪均值（万元）'] ?? 0)),
)
