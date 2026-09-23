# -*- coding: utf-8 -*-
"""
第一阶段：数据清洗与标准化
输入: jobs.json (824 条)
输出:
  - jobs_clean.json     清洗+聚合后的岗位数据
  - jobs_stats.json     统计摘要
  - data_quality_report.md  清洗报告
"""
import os
import re
import json
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(ROOT, "jobs.json")
OUT_CLEAN = os.path.join(ROOT, "jobs_clean.json")
OUT_STATS = os.path.join(ROOT, "jobs_stats.json")
OUT_REPORT = os.path.join(ROOT, "data_quality_report.md")

# 标准产业链白名单
VALID_CHAINS = {"工程机械", "专用装备", "汽车及零部件", "新能源", "煤化工", "盐化工",
                 "食品", "医药", "新一代信息技术", "造纸和纸制品", "纺织服装",
                 "轻工", "煤电", "精细化工", "事业单位", "其他"}
# 需重新归类的占位产业链
PLACEHOLDER_CHAINS = {"济宁直聘", "汶上招聘"}

# 重新归类规则(按顺序匹配, 命中即止)
RECLASSIFY_RULES = [
    ("煤化工", ["煤化工", "煤化"]),
    ("盐化工", ["盐化工", "氯碱"]),
    ("精细化工", ["化工", "化学", "精细", "中控", "化工与制药", "化学类"]),
    ("医药", ["医药", "药业", "制药", "药学", "中药", "生物医学", "生物医学工程"]),
    ("食品", ["食品", "饮品", "饮料", "植物生产", "农学"]),
    ("汽车及零部件", ["汽车", "零部件", "汽配", "商用车", "新能源车"]),
    ("新能源", ["新能源", "光伏", "储能", "锂电", "电池", "发电装备", "绿色能源"]),
    ("煤电", ["煤电", "电力", "煤矿", "采掘", "地质"]),
    ("造纸和纸制品", ["造纸", "纸业", "纸制品"]),
    ("纺织服装", ["纺织", "服装", "服饰", "针织", "布业", "手套"]),
    ("新一代信息技术", ["信息", "数据", "网络", "软件", "主播", "传媒", "互联网",
                        "大数据", "计算机", "电子商务", "电竞", "弹幕", "电子信息",
                        "电气", "自动化", "电子商务类"]),
    ("专用装备", ["专用设备", "PLC", "农业机械", "技术工程师"]),
    ("工程机械", ["机械", "重工", "挖掘", "起重", "机加", "工艺工程师", "机械设计",
                  "机械研发", "机械工程师", "数控", "质检", "仓库管理", "生产管理",
                  "生产计划", "班组长", "生产主管", "技术研发", "产品质量", "车间"]),
    ("轻工", ["轻工", "建材", "商贸", "业务员", "销售", "导购", "门店",
              "外贸", "业务", "会计", "行政", "文员", "客服", "市场营销", "业务拓展"]),
]


# ---------- 单条记录清洗 ----------
def clean_job_name(name):
    """去掉括号内福利/区域/薪资等描述, 返回 (清洗后名称, 福利信息)"""
    if not name:
        return "", ""
    welfare_parts = []
    # 匹配中英文括号
    def repl(m):
        inner = m.group(1)
        welfare_parts.append(inner)
        return ""
    cleaned = re.sub(r"[（(]([^）)]*)[）)]", repl, name).strip()
    # 去掉末尾多余符号
    cleaned = re.sub(r"[+·、,\s]+$", "", cleaned).strip()
    welfare = "、".join(p for p in welfare_parts if p.strip()) if welfare_parts else ""
    return cleaned or name, welfare


def standardize_edu(edu):
    """学历统一为: 高中及以下/大专/本科/硕士/博士/不限 ; '—'/空 → null"""
    if not edu or edu in ("—", "-", ""):
        return None
    s = edu
    if "博士" in s:
        return "博士"
    if "硕士" in s:
        return "硕士"
    if "研究生" in s:  # 默认研究生=硕士
        return "硕士"
    if "本科" in s or "大学本科" in s or "学士" in s:
        return "本科"
    if "专科" in s or "大专" in s or "高职" in s:
        return "大专"
    if "高中" in s or "中专" in s or "中职" in s:
        return "高中及以下"
    if "不限" in s:
        return "不限"
    return None


def standardize_major(major):
    """专业要求: '不限'/'—'/空 → null; 单个→str, 多个→list"""
    if not major or major in ("—", "-", "不限", ""):
        return None
    return major


def standardize_star(star):
    if not star or star in ("—", "-"):
        return None
    m = re.search(r"(\d)\s*星", star)
    return f"{m.group(1)}星" if m else None


def parse_salary_from_ability(text):
    """从 jzp 任职能力要求 '...薪资:4000-10000元/月...' 提取薪资原文"""
    if not text:
        return None
    m = re.search(r"薪资[:：]\s*([^\|]+)", text)
    if m:
        return m.group(1).strip()
    return None


def parse_salary_fields(salary_raw):
    """解析薪资原文 → (下限, 上限, 单位, 年薪均值估算, 是否月薪)"""
    if not salary_raw:
        return None, None, None, None, False
    s = salary_raw
    unit = None
    if "元/月" in s or "/月" in s:
        unit = "元/月"
    elif "元/周" in s or "/周" in s:
        unit = "元/周"
    elif "元/日" in s or "/日" in s or "/天" in s:
        unit = "元/日"
    elif "元/年" in s or "/年" in s:
        unit = "元/年"
    else:
        unit = "元/月" if "月" in s else None

    m = re.search(r"(\d{3,6})\s*[-—~至]\s*(\d{3,6})", s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
    else:
        m2 = re.search(r"(\d{3,6})", s)
        if m2:
            lo = hi = int(m2.group(1))
        else:
            return None, None, unit, None, False

    annual = None
    is_monthly = (unit == "元/月")
    if is_monthly:
        annual = round((lo + hi) / 2 * 12 / 10000, 2)
    elif unit == "元/年":
        annual = round((lo + hi) / 2 / 10000, 2)
    # 周结/日结/计件 → annual=None
    return lo, hi, unit, annual, is_monthly


def reclassify_chain(job_name, major, source, current_chain):
    """重新归类产业链"""
    if source.startswith("济宁市属事业单位"):
        return "事业单位"
    if current_chain not in PLACEHOLDER_CHAINS:
        # 已有真实产业链, 校验是否在白名单
        return current_chain if current_chain in VALID_CHAINS else "其他"
    text = f"{job_name or ''} {major or ''}"
    for chain, kws in RECLASSIFY_RULES:
        for kw in kws:
            if kw in text:
                return chain
    return "其他"


def clean_record(r):
    """清洗单条记录"""
    job_name, welfare = clean_job_name(r.get("岗位名称", ""))
    edu = standardize_edu(r.get("学历要求"))
    major = standardize_major(r.get("专业要求"))
    star = standardize_star(r.get("紧缺星级"))
    exp = r.get("工作经验年数")
    if exp in ("—", "-", ""):
        exp = None
    rep_company = r.get("代表企业")
    if not rep_company or rep_company in ("—", "-", ""):
        rep_company = None
    source = r.get("数据来源", "")
    cur_chain = r.get("所属产业链", "")
    chain = reclassify_chain(job_name, major, source, cur_chain)

    # 薪资处理
    salary_raw = None
    annual = r.get("年薪均值（万元）")
    annual_estimated = None
    salary_lo = salary_hi = salary_unit = None

    if source == "济宁直聘网":
        salary_raw = parse_salary_from_ability(r.get("任职能力要求", ""))
        lo, hi, unit, est_annual, is_monthly = parse_salary_fields(salary_raw)
        salary_lo, salary_hi, salary_unit = lo, hi, unit
        if est_annual is not None:
            annual = est_annual
            annual_estimated = True
        else:
            # 周结等非月薪
            annual = None
            annual_estimated = None
    elif source == "蓝皮书2026版":
        # 蓝皮书年薪为官方均值
        if annual is not None:
            annual_estimated = False
    else:
        # 事业单位/汶上 无薪资
        if annual is None:
            annual_estimated = None

    # 任职能力要求: jzp 去掉薪资/链接等打包信息
    ability = r.get("任职能力要求", "")
    if source == "济宁直聘网":
        # 去掉 "区域:..| 薪资:..| 发布:..| 链接:.."
        ability = re.sub(r"\s*\|\s*(区域|薪资|发布|链接)[:：][^\|]*", "", ability).strip()
        ability = re.sub(r"^(区域|薪资|发布|链接)[:：][^\|]*\s*\|?\s*", "", ability).strip()
        # 详情页返回的福利文本并入 福利信息
        if ability and any(k in ability for k in ["五险", "福利", "培训", "住宿", "补贴", "提成", "假期"]):
            welfare = (welfare + "、" + ability) if welfare else ability
            ability = None

    return {
        "岗位名称": job_name,
        "所属产业链": chain,
        "紧缺星级": star,
        "学历要求": edu,
        "专业要求": major,
        "任职能力要求": ability,
        "年薪均值（万元）": annual,
        "年薪是否估算": annual_estimated,
        "工作经验年数": exp,
        "代表企业": rep_company,
        "数据来源": source,
        "数据采集日期": r.get("数据采集日期"),
        "薪资原文": salary_raw,
        "薪资下限": salary_lo,
        "薪资上限": salary_hi,
        "薪资单位": salary_unit,
        "福利信息": welfare if welfare else None,
    }


# ---------- 聚合 ----------
def aggregate(records):
    """按 (岗位名称, 所属产业链) 聚合"""
    groups = defaultdict(list)
    for r in records:
        key = (r["岗位名称"], r["所属产业链"])
        groups[key].append(r)

    aggregated = []
    for (job, chain), items in groups.items():
        # 专业要求 → 数组
        majors = []
        for it in items:
            m = it.get("专业要求")
            if m and m not in majors:
                majors.append(m)
        # 学历要求 → 数组
        edus = []
        for it in items:
            e = it.get("学历要求")
            if e and e not in edus:
                edus.append(e)
        # 数据来源 → 数组
        sources = []
        for it in items:
            s = it.get("数据来源")
            if s and s not in sources:
                sources.append(s)
        # 代表企业 → 数组
        companies = []
        for it in items:
            c = it.get("代表企业")
            if c and c not in companies:
                companies.append(c)
        # 单值字段: 优先取非估算年薪, 否则首个非空
        def first_nonnull(field):
            for it in items:
                if it.get(field) is not None:
                    return it.get(field)
            return None
        # 年薪: 优先非估算(官方)
        annual = None
        annual_est = None
        for it in items:
            if it.get("年薪均值（万元）") is not None and it.get("年薪是否估算") is False:
                annual = it.get("年薪均值（万元）")
                annual_est = False
                break
        if annual is None:
            for it in items:
                if it.get("年薪均值（万元）") is not None:
                    annual = it.get("年薪均值（万元）")
                    annual_est = it.get("年薪是否估算")
                    break
        # 任职能力要求: 取最长
        ability = max((it.get("任职能力要求") or "" for it in items), key=len) or None
        # 薪资原文等: 首个非空
        salary_raw = first_nonnull("薪资原文")
        salary_lo = first_nonnull("薪资下限")
        salary_hi = first_nonnull("薪资上限")
        salary_unit = first_nonnull("薪资单位")
        welfare = first_nonnull("福利信息")

        aggregated.append({
            "岗位名称": job,
            "所属产业链": chain,
            "紧缺星级": first_nonnull("紧缺星级"),
            "学历要求": edus if edus else None,
            "专业要求": majors if majors else None,
            "任职能力要求": ability,
            "年薪均值（万元）": annual,
            "年薪是否估算": annual_est,
            "工作经验年数": first_nonnull("工作经验年数"),
            "代表企业": companies if companies else None,
            "数据来源": sources,
            "数据采集日期": first_nonnull("数据采集日期"),
            "薪资原文": salary_raw,
            "薪资下限": salary_lo,
            "薪资上限": salary_hi,
            "薪资单位": salary_unit,
            "福利信息": welfare,
            "_合并记录数": len(items),
        })
    return aggregated


def build_stats(aggregated, raw_count):
    by_chain = Counter(r["所属产业链"] for r in aggregated)
    by_edu = Counter()
    for r in aggregated:
        edus = r.get("学历要求")
        if edus:
            for e in edus:
                by_edu[e] += 1
        else:
            by_edu["未知"] += 1
    by_star = Counter(r["紧缺星级"] or "未知" for r in aggregated)
    salaries = [r["年薪均值（万元）"] for r in aggregated
                if r["年薪均值（万元）"] is not None]
    avg_salary = round(sum(salaries) / len(salaries), 2) if salaries else None
    # 热门岗位 TOP20 (按出现次数=合并记录数)
    job_counter = Counter()
    for r in aggregated:
        job_counter[r["岗位名称"]] += r.get("_合并记录数", 1)
    top20 = [{"岗位名称": j, "记录数": c} for j, c in job_counter.most_common(20)]
    by_source = Counter()
    for r in aggregated:
        for s in r["数据来源"]:
            by_source[s] += r.get("_合并记录数", 1)

    return {
        "总岗位数(去重后)": len(aggregated),
        "总记录数(去重前)": raw_count,
        "各产业链岗位数": dict(by_chain.most_common()),
        "各学历要求分布": dict(by_edu.most_common()),
        "各紧缺星级分布": dict(by_star.most_common()),
        "平均年薪(万元)": avg_salary,
        "有年薪数据岗位数": len(salaries),
        "热门岗位TOP20": top20,
        "各数据来源记录数": dict(by_source.most_common()),
    }


def field_completeness(records, fields):
    comp = {}
    n = len(records)
    for f in fields:
        nonnull = sum(1 for r in records if r.get(f) not in (None, [], ""))
        comp[f] = f"{nonnull}/{n} ({100*nonnull/n:.0f}%)" if n else "0/0"
    return comp


def main():
    with open(IN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw = data["records"]
    raw_count = len(raw)
    print(f"读取原始记录: {raw_count} 条")

    # 1) 单条清洗
    cleaned = [clean_record(r) for r in raw]
    print(f"清洗后(未聚合): {len(cleaned)} 条")

    # 2) 聚合去重
    aggregated = aggregate(cleaned)
    print(f"聚合去重后: {len(aggregated)} 条岗位 (按 岗位名称+产业链)")

    # 去掉内部字段 _合并记录数 (统计用完保留? 保留便于审计)
    # 保留

    # 3) 统计
    stats = build_stats(aggregated, raw_count)
    comp = field_completeness(aggregated, [
        "岗位名称", "所属产业链", "紧缺星级", "学历要求", "专业要求",
        "任职能力要求", "年薪均值（万元）", "工作经验年数", "代表企业",
        "薪资原文", "福利信息"])

    # 4) 输出 jobs_clean.json
    with open(OUT_CLEAN, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(aggregated),
            "raw_total": raw_count,
            "data_acquisition_date": data.get("data_acquisition_date"),
            "records": aggregated,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] jobs_clean.json: {OUT_CLEAN}")

    # 5) 输出 jobs_stats.json
    with open(OUT_STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"[OK] jobs_stats.json: {OUT_STATS}")

    # 6) 输出 data_quality_report.md
    reclassified = sum(1 for r in cleaned if r["所属产业链"] != "其他"
                       and any(r["所属产业链"] == c for c in VALID_CHAINS)
                       and raw[cleaned.index(r)]["所属产业链"] in PLACEHOLDER_CHAINS) \
        if False else 0
    placeholder_before = Counter(r["所属产业链"] for r in raw
                                 if r["所属产业链"] in PLACEHOLDER_CHAINS)
    other_count = sum(1 for r in aggregated if r["所属产业链"] == "其他")

    report = f"""# 数据清洗报告

**清洗日期**: 2026-09-23
**输入**: jobs.json ({raw_count} 条)
**输出**: jobs_clean.json ({len(aggregated)} 条去重岗位) / jobs_stats.json / data_quality_report.md

## 一、去重与聚合

| 指标 | 数量 |
|------|------|
| 去重前记录数 | {raw_count} |
| 去重后岗位数(按 岗位名称+产业链 聚合) | {len(aggregated)} |
| 合并掉的重复记录数 | {raw_count - len(aggregated)} |

聚合键: `岗位名称 + 所属产业链`。同一岗位的多个**专业要求**、**学历要求**合并为数组；
**数据来源**、**代表企业**合并为数组并去重；其余单值字段取首个非空(年薪优先取非估算的官方值)。

## 二、各数据来源记录数

| 数据来源 | 记录数 |
|----------|--------|
"""
    for s, c in stats["各数据来源记录数"].items():
        report += f"| {s} | {c} |\n"

    report += f"""
## 三、各产业链岗位数(去重后)

| 产业链 | 岗位数 |
|--------|--------|
"""
    for ch, c in stats["各产业链岗位数"].items():
        report += f"| {ch} | {c} |\n"

    report += f"""
## 四、字段完整度(去重后 {len(aggregated)} 条岗位)

| 字段 | 非空数(完整率) |
|------|----------------|
"""
    for f, v in comp.items():
        report += f"| {f} | {v} |\n"

    report += f"""
## 五、薪资字段处理情况

| 来源 | 薪资处理 |
|------|----------|
| 蓝皮书2026版 | 保留官方年薪均值, `年薪是否估算=false`, 无薪资原文 |
| 济宁直聘网 | 从任职能力要求解析`薪资原文`, 拆出`薪资下限/上限/单位`; 月薪×12估算年薪(`年薪是否估算=true`); 周结/日结年薪置 null |
| 人社局事业单位/汶上招聘 | 无薪资数据, 全部 null |

- 有年薪数据岗位: {stats['有年薪数据岗位数']}/{len(aggregated)}
- 平均年薪(万元): {stats['平均年薪(万元)']}

## 六、产业链标准化说明

- 占位产业链 `济宁直聘`/`汶上招聘` 共 {sum(placeholder_before.values())} 条, 已按岗位名+专业关键字重新归类
- 重新归类后落入 `其他` 的岗位: {other_count} 条(多为司机/装卸/美容/银行/纯服务业等无法对应制造链的岗位)
- 蓝皮书原有真实产业链(13个)均直接映射至标准白名单, 未改动

## 七、学历要求分布(去重后)

| 学历 | 岗位数 |
|------|--------|
"""
    for e, c in stats["各学历要求分布"].items():
        report += f"| {e} | {c} |\n"

    report += f"""
## 八、紧缺星级分布(去重后)

| 星级 | 岗位数 |
|------|--------|
"""
    for s, c in stats["各紧缺星级分布"].items():
        report += f"| {s} | {c} |\n"

    report += f"""
## 九、热门岗位 TOP20

| 排名 | 岗位名称 | 记录数 |
|------|----------|--------|
"""
    for i, t in enumerate(stats["热门岗位TOP20"], 1):
        report += f"| {i} | {t['岗位名称']} | {t['记录数']} |\n"

    report += f"""
## 十、发现的问题与需人工确认事项

1. **jzp 服务类岗位归类偏主观**: 司机/装卸/美容/银行/行政/客服等纯服务业无法对应15条制造产业链, 已放入`其他`; 销售/业务员/导购归入`轻工`(商贸流通)属推断, 建议人工复核。
2. **jzp 薪资估算口径**: 月薪按×12估算年薪, 未考虑年终奖/实际发放月数; 周结岗位(如装卸工2300-3000元/周)年薪置 null, 未估算。
3. **跨来源同岗位年薪冲突**: 聚合时优先取蓝皮书官方年薪(非估算); 若同岗位仅直聘网有薪资, 用估算值并标注 `年薪是否估算=true`。
4. **学历'—'→null**: 直聘网多数岗位未公示学历, 已转为 null(未知), 区别于明确的`不限`。
5. **专业要求多源合并**: 蓝皮书同岗位多专业已合并为数组; 直聘网专业为 null 不参与合并。
6. **代表企业为数组**: 聚合后代表企业为去重数组; 蓝皮书263条已匹配企业, 其余为 null。
7. **公告A缺失**: 博士专引公告官网未发布, 该来源记录为0, 无法补充高端人才岗位。
8. **岗位名称清洗**: 已去除括号内福利/区域/薪资描述并提取为`福利信息`; 个别岗位清洗后名称可能偏短, 建议抽查。

## 十一、输出文件

- `jobs_clean.json`: {len(aggregated)} 条清洗后岗位(含薪资拆分/福利/估算标记/聚合数组字段)
- `jobs_stats.json`: 统计摘要(产业链/学历/星级分布/平均年薪/热门TOP20)
- `data_quality_report.md`: 本报告
"""
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[OK] data_quality_report.md: {OUT_REPORT}")

    # 控制台汇总
    print("\n" + "=" * 60)
    print("清洗汇总")
    print("=" * 60)
    print(f"去重前: {raw_count} 条 → 去重后: {len(aggregated)} 条岗位")
    print(f"平均年薪: {stats['平均年薪(万元)']} 万元")
    print(f"落入'其他': {other_count} 条")


if __name__ == "__main__":
    main()
