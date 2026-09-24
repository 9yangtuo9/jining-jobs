/**
 * 数据更新脚本
 * 读取根目录 raw_jobs.json → 清洗聚合 → 输出 src/data/jobs_clean.json + src/data/jobs_stats.json
 *
 * 使用：node scripts/update-data.js
 * 前置：将新的原始数据替换为 raw_jobs.json（格式同 jobs.json：{ records: [...], data_acquisition_date: "..." }）
 */
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const IN_PATH = path.join(ROOT, 'raw_jobs.json')
const OUT_CLEAN = path.join(ROOT, 'src', 'data', 'jobs_clean.json')
const OUT_STATS = path.join(ROOT, 'src', 'data', 'jobs_stats.json')

// 标准产业链白名单
const VALID_CHAINS = new Set([
  '工程机械', '专用装备', '汽车及零部件', '新能源', '煤化工', '盐化工',
  '食品', '医药', '新一代信息技术', '造纸和纸制品', '纺织服装',
  '轻工', '煤电', '精细化工', '事业单位', '其他',
])
// 字符串归一化：去除首尾空白，防止 " 电话客服" 这类脏分类混入
function norm(v) {
  return typeof v === 'string' ? v.trim() : (v == null ? '' : v)
}

// 重新归类规则（按顺序匹配，命中即止）
const RECLASSIFY_RULES = [
  ['煤化工', ['煤化工', '煤化']],
  ['盐化工', ['盐化工', '氯碱']],
  ['精细化工', ['化工', '化学', '精细', '中控', '化工与制药', '化学类']],
  ['医药', ['医药', '药业', '制药', '药学', '中药', '生物医学', '生物医学工程']],
  ['食品', ['食品', '饮品', '饮料', '植物生产', '农学']],
  ['汽车及零部件', ['汽车', '零部件', '汽配', '商用车', '新能源车']],
  ['新能源', ['新能源', '光伏', '储能', '锂电', '电池', '发电装备', '绿色能源']],
  ['煤电', ['煤电', '电力', '煤矿', '采掘', '地质']],
  ['造纸和纸制品', ['造纸', '纸业', '纸制品']],
  ['纺织服装', ['纺织', '服装', '服饰', '针织', '布业', '手套']],
  ['新一代信息技术', ['信息', '数据', '网络', '软件', '主播', '传媒', '互联网',
    '大数据', '计算机', '电子商务', '电竞', '弹幕', '电子信息',
    '电气', '自动化', '电子商务类']],
  ['专用装备', ['专用设备', 'PLC', '农业机械', '技术工程师']],
  ['工程机械', ['机械', '重工', '挖掘', '起重', '机加', '工艺工程师', '机械设计',
    '机械研发', '机械工程师', '数控', '质检', '仓库管理', '生产管理',
    '生产计划', '班组长', '生产主管', '技术研发', '产品质量', '车间']],
  ['轻工', ['轻工', '建材', '商贸', '业务员', '销售', '导购', '门店',
    '外贸', '业务', '会计', '行政', '文员', '客服', '市场营销', '业务拓展']],
]

// ---------- 单条记录清洗 ----------
function cleanJobName(name) {
  if (!name) return { name: '', welfare: '' }
  // 原始数据中部分岗位名称形如「工作地点 | 岗位名（福利）」，取 | 之后的真实岗位名
  let raw = norm(name)
  if (raw.includes('|')) {
    const parts = raw.split('|').map(s => s.trim()).filter(Boolean)
    raw = parts[parts.length - 1] || raw
  }
  const welfareParts = []
  const cleaned = raw.replace(/[（(]([^）)]*)[）)]/g, (_, inner) => {
    welfareParts.push(inner)
    return ''
  }).replace(/[+·、,\s]+$/, '').trim()
  const welfare = welfareParts.filter(p => p.trim()).join('、')
  return { name: cleaned || raw, welfare }
}

function standardizeEdu(edu) {
  if (!edu || ['—', '-', ''].includes(edu)) return null
  if (edu.includes('博士')) return '博士'
  if (edu.includes('硕士') || edu.includes('研究生')) return '硕士'
  if (edu.includes('本科') || edu.includes('学士')) return '本科'
  if (edu.includes('专科') || edu.includes('大专') || edu.includes('高职')) return '大专'
  if (edu.includes('高中') || edu.includes('中专') || edu.includes('中职')) return '高中及以下'
  if (edu.includes('不限')) return '不限'
  return null
}

function standardizeMajor(major) {
  const m = norm(major)
  if (!m || ['—', '-', '不限'].includes(m)) return null
  return m
}

function standardizeStar(star) {
  if (!star || ['—', '-'].includes(star)) return null
  const m = star.match(/(\d)\s*星/)
  return m ? `${m[1]}星` : null
}

function parseSalaryFromAbility(text) {
  if (!text) return null
  const m = text.match(/薪资[:：]\s*([^|]+)/)
  return m ? m[1].trim() : null
}

function parseSalaryFields(salaryRaw) {
  if (!salaryRaw) return { lo: null, hi: null, unit: null, annual: null, isMonthly: false }
  let unit = null
  if (/元\/月|\/月/.test(salaryRaw)) unit = '元/月'
  else if (/元\/周|\/周/.test(salaryRaw)) unit = '元/周'
  else if (/元\/日|\/日|\/天/.test(salaryRaw)) unit = '元/日'
  else if (/元\/年|\/年/.test(salaryRaw)) unit = '元/年'
  else unit = salaryRaw.includes('月') ? '元/月' : null

  let lo, hi
  const m = salaryRaw.match(/(\d{3,6})\s*[-—~至]\s*(\d{3,6})/)
  if (m) { lo = parseInt(m[1]); hi = parseInt(m[2]) }
  else {
    const m2 = salaryRaw.match(/(\d{3,6})/)
    if (m2) { lo = hi = parseInt(m2[1]) }
    else return { lo: null, hi: null, unit, annual: null, isMonthly: false }
  }

  let annual = null
  const isMonthly = unit === '元/月'
  if (isMonthly) annual = Math.round(((lo + hi) / 2 * 12 / 10000) * 100) / 100
  else if (unit === '元/年') annual = Math.round(((lo + hi) / 2 / 10000) * 100) / 100
  return { lo, hi, unit, annual, isMonthly }
}

function reclassifyChain(jobName, major, source, currentChain) {
  // source 可能是字符串或数组（已聚合数据再清洗时）
  const srcStr = Array.isArray(source) ? source.join('|') : (source || '')
  if (srcStr.startsWith('济宁市属事业单位')) return '事业单位'
  // 归一化后命中白名单才保留；白名单之外（含带空格的脏值）一律按关键词重新归类
  const cur = norm(currentChain)
  if (VALID_CHAINS.has(cur)) return cur
  const text = `${jobName || ''} ${Array.isArray(major) ? major.join(' ') : (major || '')}`
  for (const [chain, kws] of RECLASSIFY_RULES) {
    for (const kw of kws) {
      if (text.includes(kw)) return chain
    }
  }
  return '其他'
}

function cleanRecord(r) {
  const { name: jobName, welfare } = cleanJobName(r['岗位名称'] || '')
  // 学历/专业可能是数组（已聚合数据再清洗时），取第一个
  const rawEdu = Array.isArray(r['学历要求']) ? r['学历要求'][0] : r['学历要求']
  const rawMajor = Array.isArray(r['专业要求']) ? r['专业要求'][0] : r['专业要求']
  const edu = standardizeEdu(rawEdu)
  const major = standardizeMajor(rawMajor)
  const star = standardizeStar(r['紧缺星级'])
  let exp = r['工作经验年数']
  if (['—', '-', ''].includes(exp)) exp = null
  let repCompany = r['代表企业']
  if (Array.isArray(repCompany)) repCompany = repCompany[0] || null
  if (!repCompany || ['—', '-', ''].includes(repCompany)) repCompany = null
  const source = Array.isArray(r['数据来源']) ? r['数据来源'][0] : (r['数据来源'] || '')
  const curChain = r['所属产业链'] || ''
  const chain = reclassifyChain(jobName, major, source, curChain)

  let salaryRaw = null
  let annual = r['年薪均值（万元）']
  let annualEstimated = null
  let salaryLo = null, salaryHi = null, salaryUnit = null

  if (source === '济宁直聘网') {
    salaryRaw = parseSalaryFromAbility(r['任职能力要求'] || '')
    const { lo, hi, unit, annual: estAnnual, isMonthly } = parseSalaryFields(salaryRaw)
    salaryLo = lo; salaryHi = hi; salaryUnit = unit
    if (estAnnual !== null) { annual = estAnnual; annualEstimated = true }
    else { annual = null; annualEstimated = null }
  } else if (source === '蓝皮书2026版') {
    if (annual !== null) annualEstimated = false
  } else {
    if (annual === null) annualEstimated = null
  }

  let ability = r['任职能力要求'] || ''
  if (source === '济宁直聘网') {
    ability = ability.replace(/\s*\|\s*(区域|薪资|发布|链接)[:：][^|]*/g, '').trim()
    ability = ability.replace(/^(区域|薪资|发布|链接)[:：][^|]*\s*\|?\s*/, '').trim()
    if (ability && ['五险', '福利', '培训', '住宿', '补贴', '提成', '假期'].some(k => ability.includes(k))) {
      const w = welfare ? `${welfare}、${ability}` : ability
      return {
        '岗位名称': jobName, '所属产业链': chain, '紧缺星级': star,
        '学历要求': edu, '专业要求': major, '任职能力要求': null,
        '年薪均值（万元）': annual, '年薪是否估算': annualEstimated,
        '工作经验年数': exp, '代表企业': repCompany, '数据来源': source,
        '数据采集日期': r['数据采集日期'], '薪资原文': salaryRaw,
        '薪资下限': salaryLo, '薪资上限': salaryHi, '薪资单位': salaryUnit,
        '福利信息': w || null,
      }
    }
  }

  return {
    '岗位名称': jobName, '所属产业链': chain, '紧缺星级': star,
    '学历要求': edu, '专业要求': major, '任职能力要求': ability || null,
    '年薪均值（万元）': annual, '年薪是否估算': annualEstimated,
    '工作经验年数': exp, '代表企业': repCompany, '数据来源': source,
    '数据采集日期': r['数据采集日期'], '薪资原文': salaryRaw,
    '薪资下限': salaryLo, '薪资上限': salaryHi, '薪资单位': salaryUnit,
    '福利信息': welfare || null,
  }
}

// ---------- 聚合 ----------
function aggregate(records) {
  const groups = new Map()
  for (const r of records) {
    const key = `${r['岗位名称']}|${r['所属产业链']}`
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(r)
  }

  const result = []
  for (const items of groups.values()) {
    // 注意：不要用 key.split('|') 反解字段——岗位名称本身可能含 |，会把名称片段误当成产业链
    const jobName = items[0]['岗位名称']
    const chain = items[0]['所属产业链']

    const majors = []
    for (const it of items) {
      if (it['专业要求'] && !majors.includes(it['专业要求'])) majors.push(it['专业要求'])
    }
    const edus = []
    for (const it of items) {
      if (it['学历要求'] && !edus.includes(it['学历要求'])) edus.push(it['学历要求'])
    }
    const sources = []
    for (const it of items) {
      if (it['数据来源'] && !sources.includes(it['数据来源'])) sources.push(it['数据来源'])
    }
    const companies = []
    for (const it of items) {
      if (it['代表企业'] && !companies.includes(it['代表企业'])) companies.push(it['代表企业'])
    }

    const firstNonNull = (field) => {
      for (const it of items) {
        if (it[field] !== null && it[field] !== undefined) return it[field]
      }
      return null
    }

    let annual = null, annualEst = null
    for (const it of items) {
      if (it['年薪均值（万元）'] !== null && it['年薪是否估算'] === false) {
        annual = it['年薪均值（万元）']; annualEst = false; break
      }
    }
    if (annual === null) {
      for (const it of items) {
        if (it['年薪均值（万元）'] !== null) {
          annual = it['年薪均值（万元）']; annualEst = it['年薪是否估算']; break
        }
      }
    }

    const abilities = items.map(it => it['任职能力要求'] || '').sort((a, b) => b.length - a.length)
    const ability = abilities[0] || null

    result.push({
      '岗位名称': jobName,
      '所属产业链': chain,
      '紧缺星级': firstNonNull('紧缺星级'),
      '学历要求': edus.length ? edus : null,
      '专业要求': majors.length ? majors : null,
      '任职能力要求': ability,
      '年薪均值（万元）': annual,
      '年薪是否估算': annualEst,
      '工作经验年数': firstNonNull('工作经验年数'),
      '代表企业': companies.length ? companies : null,
      '数据来源': sources,
      '数据采集日期': firstNonNull('数据采集日期'),
      '薪资原文': firstNonNull('薪资原文'),
      '薪资下限': firstNonNull('薪资下限'),
      '薪资上限': firstNonNull('薪资上限'),
      '薪资单位': firstNonNull('薪资单位'),
      '福利信息': firstNonNull('福利信息'),
      '_合并记录数': items.length,
    })
  }
  return result
}

// ---------- 统计 ----------
function buildStats(aggregated, rawCount) {
  const byChain = {}
  for (const r of aggregated) byChain[r['所属产业链']] = (byChain[r['所属产业链']] || 0) + 1
  const byEdu = {}
  for (const r of aggregated) {
    const edus = r['学历要求']
    if (edus) for (const e of edus) byEdu[e] = (byEdu[e] || 0) + 1
    else byEdu['未知'] = (byEdu['未知'] || 0) + 1
  }
  const byStar = {}
  for (const r of aggregated) {
    const s = r['紧缺星级'] || '未知'
    byStar[s] = (byStar[s] || 0) + 1
  }
  const salaries = aggregated.map(r => r['年薪均值（万元）']).filter(v => v !== null)
  const avgSalary = salaries.length ? Math.round((salaries.reduce((a, b) => a + b, 0) / salaries.length) * 100) / 100 : null

  const jobCounter = {}
  for (const r of aggregated) jobCounter[r['岗位名称']] = (jobCounter[r['岗位名称']] || 0) + (r['_合并记录数'] || 1)
  const top20 = Object.entries(jobCounter).sort((a, b) => b[1] - a[1]).slice(0, 20)
    .map(([岗位名称, 记录数]) => ({ 岗位名称, 记录数 }))

  const bySource = {}
  for (const r of aggregated) {
    for (const s of r['数据来源']) bySource[s] = (bySource[s] || 0) + (r['_合并记录数'] || 1)
  }

  // 按值降序
  const sortDesc = (obj) => Object.entries(obj).sort((a, b) => b[1] - a[1]).reduce((o, [k, v]) => { o[k] = v; return o }, {})

  return {
    '总岗位数(去重后)': aggregated.length,
    '总记录数(去重前)': rawCount,
    '各产业链岗位数': sortDesc(byChain),
    '各学历要求分布': sortDesc(byEdu),
    '各紧缺星级分布': sortDesc(byStar),
    '平均年薪(万元)': avgSalary,
    '有年薪数据岗位数': salaries.length,
    '热门岗位TOP20': top20,
    '各数据来源记录数': sortDesc(bySource),
  }
}

// ---------- 主流程 ----------
function main() {
  if (!fs.existsSync(IN_PATH)) {
    console.error(`\n[ERROR] 未找到 ${IN_PATH}`)
    console.error('请将原始数据文件放置为根目录下的 raw_jobs.json')
    console.error('格式：{ "records": [...], "data_acquisition_date": "YYYY-MM-DD" }')
    process.exit(1)
  }

  console.log('='.repeat(60))
  console.log('数据更新脚本')
  console.log('='.repeat(60))

  // 读取原始数据
  const data = JSON.parse(fs.readFileSync(IN_PATH, 'utf-8'))
  const raw = data.records
  const rawCount = raw.length
  console.log(`\n读取原始记录: ${rawCount} 条`)
  console.log(`数据采集日期: ${data.data_acquisition_date || '未标注'}`)

  // 输入校验：已清洗数据的输出文件带 raw_total 字段，原始数据没有
  if (data.raw_total !== undefined) {
    console.warn('\n[WARN] 输入文件含有 raw_total 字段，疑似“已清洗数据”。')
    console.warn('       请确认放入 raw_jobs.json 的是未经清洗的原始采集数据。')
  }

  // 1) 单条清洗
  const cleaned = raw.map(cleanRecord)
  console.log(`清洗后(未聚合): ${cleaned.length} 条`)

  // 2) 聚合去重
  const aggregated = aggregate(cleaned)
  console.log(`聚合去重后: ${aggregated.length} 条岗位 (按 岗位名称+产业链)`)

  // 3) 统计
  const stats = buildStats(aggregated, rawCount)

  // 4) 输出
  fs.writeFileSync(OUT_CLEAN, JSON.stringify({
    total: aggregated.length,
    raw_total: rawCount,
    data_acquisition_date: data.data_acquisition_date,
    records: aggregated,
  }, null, 2))
  console.log(`\n[OK] jobs_clean.json → ${OUT_CLEAN}`)

  fs.writeFileSync(OUT_STATS, JSON.stringify(stats, null, 2))
  console.log(`[OK] jobs_stats.json → ${OUT_STATS}`)

  // 5) 汇总对比
  console.log('\n' + '='.repeat(60))
  console.log('更新汇总')
  console.log('='.repeat(60))
  console.log(`去重前: ${rawCount} 条 → 去重后: ${aggregated.length} 条岗位`)
  console.log(`平均年薪: ${stats['平均年薪(万元)']} 万元`)
  console.log(`有年薪数据: ${stats['有年薪数据岗位数']}/${aggregated.length}`)
  console.log(`覆盖产业链: ${Object.keys(stats['各产业链岗位数']).length} 条`)
  console.log(`热门岗位 TOP3: ${stats['热门岗位TOP20'].slice(0, 3).map(t => `${t['岗位名称']}(${t['记录数']})`).join(', ')}`)
  console.log('\n✅ 数据更新完成，可执行 npm run build 重新打包。')
}

main()
