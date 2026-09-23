// 岗位记录类型（键名与 jobs_clean.json 保持一致）
export interface JobRecord {
  岗位名称: string
  所属产业链: string
  紧缺星级: string | null
  学历要求: string[] | null
  专业要求: string[] | null
  任职能力要求: string
  '年薪均值（万元）': number | null
  年薪是否估算: boolean | null
  工作经验年数: number | null
  代表企业: string[] | null
  数据来源: string[]
  数据采集日期: string
  薪资原文: string | null
  薪资下限: number | null
  薪资上限: number | null
  薪资单位: string | null
  福利信息: string | null
  _合并记录数: number
}

export interface JobCleanFile {
  total: number
  raw_total: number
  data_acquisition_date: string
  records: JobRecord[]
}

export interface TopJob {
  岗位名称: string
  记录数: number
}

export interface JobStats {
  '总岗位数(去重后)': number
  '总记录数(去重前)': number
  '各产业链岗位数': Record<string, number>
  '各学历要求分布': Record<string, number>
  '各紧缺星级分布': Record<string, number>
  '平均年薪(万元)': number
  '有年薪数据岗位数': number
  '热门岗位TOP20': TopJob[]
  '各数据来源记录数': Record<string, number>
}
