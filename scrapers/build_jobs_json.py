# -*- coding: utf-8 -*-
"""
数据清洗与统一: 读取4个数据源的原始JSON, 统一为标准岗位JSON格式, 输出 jobs.json。
同时为蓝皮书岗位补充"代表企业"字段(从汶上县招聘公告与济宁直聘网中按产业链/行业关键字匹配企业)。

统一字段:
  岗位名称 / 所属产业链 / 紧缺星级 / 学历要求 / 专业要求 / 任职能力要求 /
  年薪均值（万元） / 工作经验年数 / 代表企业 / 数据来源 / 数据采集日期
"""
import os
import re
import json
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

TODAY = date.today().isoformat()  # 2026-09-23

# 数据源文件路径
SOURCES = {
    "bluebook": os.path.join(DATA_DIR, "bluebook_directory_raw.json"),
    "hrss": os.path.join(DATA_DIR, "hrss_institution_jobs_raw.json"),
    "wenshang": os.path.join(DATA_DIR, "wenshang_notices_raw.json"),
    "jzp": os.path.join(DATA_DIR, "jiningzhipin_jobs_enriched.json"),
}

# 产业链→行业关键字映射(用于从企业名称推断所属产业链, 进而给蓝皮书岗位补代表企业)
CHAIN_KEYWORDS = {
    "工程机械": ["机械", "工程", "重工", "装备", "起重", "挖掘"],
    "专用装备": ["专用设备", "装备", "机械"],
    "汽车及零部件": ["汽车", "零部件", "车业", "汽配", "商用车"],
    "新能源汽车": ["新能源", "电池", "三电", "电动"],
    "煤化工": ["煤化工", "煤化", "万华"],
    "盐化工": ["盐化工", "氯碱"],
    "精细化工": ["化工", "化学", "精细"],
    "化工新材料": ["新材料", "化工新材"],
    "新能源": ["新能源", "光伏", "储能", "锂电"],
    "储能装备": ["储能", "电池"],
    "新一代信息技术": ["信息", "数据", "网络", "软件", "科技", "传媒", "互联网", "大数据"],
    "造纸和纸制品": ["造纸", "纸业", "纸制品"],
    "纺织服装": ["纺织", "服装", "服饰", "针织", "布业"],
    "轻工": ["轻工", "建材", "商贸", "商贸行", "食品", "工艺"],
    "食品": ["食品", "饮品", "生物", "医药"],
    "医药": ["医药", "药业", "制药", "生物医学"],
    "煤电": ["煤电", "电力", "能源", "煤矿"],
}


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guess_chain_from_company(company):
    """根据企业名称关键字推断所属产业链。"""
    if not company:
        return None
    for chain, kws in CHAIN_KEYWORDS.items():
        for kw in kws:
            if kw in company:
                return chain
    return None


def clean_str(v):
    if v is None:
        return ""
    s = str(v).strip()
    return s


def to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        m = re.search(r"[\d.]+", str(v))
        return float(m.group()) if m else None


def to_int(v):
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        m = re.search(r"\d+", str(v))
        return int(m.group()) if m else None


def normalize_bluebook(data):
    """蓝皮书岗位 → 统一格式。"""
    out = []
    for r in data.get("records", []):
        rec = {
            "岗位名称": clean_str(r.get("岗位名称")),
            "所属产业链": clean_str(r.get("所属产业链")),
            "紧缺星级": clean_str(r.get("紧缺星级")),
            "学历要求": clean_str(r.get("学历要求")),
            "专业要求": clean_str(r.get("专业要求")),
            "任职能力要求": clean_str(r.get("任职能力要求")),
            "年薪均值（万元）": to_float(r.get("年薪均值（万元）")),
            "工作经验年数": to_int(r.get("工作经验年数")),
            "代表企业": "",  # 待后续填充
            "数据来源": "蓝皮书2026版",
            "数据采集日期": TODAY,
        }
        out.append(rec)
    return out


def normalize_hrss(data):
    """人社局事业单位岗位 → 统一格式。"""
    out = []
    for r in data.get("records", []):
        # 合并本科/研究生专业要求
        majors = []
        if r.get("大学本科专业要求"):
            majors.append("本科:" + clean_str(r["大学本科专业要求"]))
        if r.get("研究生专业要求"):
            majors.append("研究生:" + clean_str(r["研究生专业要求"]))
        major_str = "；".join(majors)
        ability = clean_str(r.get("其它条件要求"))
        edu = clean_str(r.get("学历要求"))
        # 事业单位招聘没有年薪/经验/星级, 这些置空
        rec = {
            "岗位名称": clean_str(r.get("岗位名称")),
            "所属产业链": "事业单位",
            "紧缺星级": "—",
            "学历要求": edu,
            "专业要求": major_str,
            "任职能力要求": ability,
            "年薪均值（万元）": None,
            "工作经验年数": None,
            "代表企业": clean_str(r.get("事业单位")),
            "数据来源": "济宁市属事业单位公开招聘2026",
            "数据采集日期": TODAY,
        }
        out.append(rec)
    return out


def normalize_wenshang(data):
    """汶上县招聘公告岗位 → 统一格式。"""
    out = []
    for r in data.get("records", []):
        job = clean_str(r.get("招聘岗位") or r.get("招聘职位") or r.get("岗位/描述"))
        company = clean_str(r.get("企业名称"))
        req = clean_str(r.get("岗位要求"))
        headcount = clean_str(r.get("招聘人数") or r.get("人数"))
        chain = guess_chain_from_company(company)
        rec = {
            "岗位名称": job,
            "所属产业链": chain or "汶上招聘",
            "紧缺星级": "—",
            "学历要求": extract_edu(req),
            "专业要求": extract_major(req),
            "任职能力要求": req,
            "年薪均值（万元）": None,
            "工作经验年数": extract_years(req),
            "代表企业": company,
            "数据来源": "汶上县招聘公告2026",
            "数据采集日期": TODAY,
        }
        # 招聘人数作为附加信息保留在 任职能力要求 末尾
        if headcount:
            rec["任职能力要求"] = (req + f"（招聘{headcount}人）") if req else f"招聘{headcount}人"
        out.append(rec)
    return out


def normalize_jzp(data):
    """济宁直聘网岗位 → 统一格式。"""
    out = []
    for r in data.get("records", []):
        company = clean_str(r.get("公司名称"))
        chain = guess_chain_from_company(company)
        job = clean_str(r.get("岗位名称"))
        # 去除首页的"推广/1楼"前缀
        job = re.sub(r"^(推广|\d+楼)\s+", "", job).strip()
        rec = {
            "岗位名称": job,
            "所属产业链": chain or "济宁直聘",
            "紧缺星级": "—",
            "学历要求": clean_str(r.get("学历要求")) or "—",
            "专业要求": "—",
            "任职能力要求": clean_str(r.get("福利")) or "—",
            "年薪均值（万元）": to_float(r.get("年薪均值（万元）估算")),
            "工作经验年数": None,
            "代表企业": company,
            "数据来源": "济宁直聘网",
            "数据采集日期": TODAY,
        }
        # 额外字段保留(区域/薪资范围/发布时间/详情链接) → 放入 任职能力要求 后
        extra = []
        if r.get("区域"):
            extra.append(f"区域:{r['区域']}")
        if r.get("薪资范围"):
            extra.append(f"薪资:{r['薪资范围']}")
        if r.get("发布时间"):
            extra.append(f"发布:{r['发布时间']}")
        if r.get("详情链接"):
            extra.append(f"链接:{r['详情链接']}")
        if extra:
            tag = " | ".join(extra)
            rec["任职能力要求"] = (rec["任职能力要求"] + " | " + tag) if rec["任职能力要求"] != "—" else tag
        out.append(rec)
    return out


def extract_edu(text):
    """从要求文本提取学历。"""
    if not text:
        return "—"
    for k in ["硕士", "研究生", "本科", "大学本科", "大专", "专科", "高职", "高中", "中专"]:
        if k in text:
            return k
    return "—"


def extract_major(text):
    """从要求文本提取专业。"""
    if not text:
        return "—"
    m = re.search(r"([a-zA-Z\u4e00-\u9fa5]{2,8})相关专业", text)
    if m:
        return m.group(1) + "相关专业"
    m = re.search(r"专业[：:]\s*([a-zA-Z\u4e00-\u9fa5、，,()（）\d]+)", text)
    if m:
        return m.group(1).rstrip("，。；,;")
    return "—"


def extract_years(text):
    """从要求文本提取工作年限。"""
    if not text:
        return None
    m = re.search(r"(\d+)\s*[-~]\s*(\d+)\s*年", text)
    if m:
        return int(m.group(2))
    m = re.search(r"(\d+)\s*年", text)
    if m:
        return int(m.group(1))
    return None


def fill_representative_companies(bluebook_records, wenshang_records, jzp_records):
    """为蓝皮书岗位按产业链匹配代表企业(汶上+直聘网企业)。"""
    # 按 产业链 聚合企业
    chain_to_companies = {}
    for rec in wenshang_records + jzp_records:
        chain = rec.get("所属产业链")
        comp = rec.get("代表企业")
        if chain and comp:
            chain_to_companies.setdefault(chain, [])
            if comp not in chain_to_companies[chain]:
                chain_to_companies[chain].append(comp)

    # 蓝皮书岗位: 取该产业链下最多3家企业
    for rec in bluebook_records:
        chain = rec.get("所属产业链")
        if chain and chain in chain_to_companies:
            comps = chain_to_companies[chain][:3]
            rec["代表企业"] = "、".join(comps)

    # 统计有多少蓝皮书记录被填充
    filled = sum(1 for r in bluebook_records if r["代表企业"])
    return filled


def main():
    print("=" * 60)
    print("数据清洗与统一 → jobs.json")
    print("=" * 60)

    bb_data = load_json(SOURCES["bluebook"])
    hrss_data = load_json(SOURCES["hrss"])
    ws_data = load_json(SOURCES["wenshang"])
    jzp_data = load_json(SOURCES["jzp"])

    bb = normalize_bluebook(bb_data) if bb_data else []
    hrss = normalize_hrss(hrss_data) if hrss_data else []
    ws = normalize_wenshang(ws_data) if ws_data else []
    jzp = normalize_jzp(jzp_data) if jzp_data else []

    print(f"蓝皮书: {len(bb)} 条")
    print(f"人社局事业单位: {len(hrss)} 条")
    print(f"汶上县招聘公告: {len(ws)} 条")
    print(f"济宁直聘网: {len(jzp)} 条")

    # 为蓝皮书补代表企业
    filled = fill_representative_companies(bb, ws, jzp)
    print(f"\n蓝皮书岗位已补代表企业: {filled}/{len(bb)} 条")

    all_records = bb + hrss + ws + jzp
    print(f"\n统一后总记录数: {len(all_records)}")

    # 字段完整性统计
    fields = ["岗位名称", "所属产业链", "紧缺星级", "学历要求", "专业要求",
              "任职能力要求", "年薪均值（万元）", "工作经验年数", "代表企业"]
    completeness = {}
    for f in fields:
        nonempty = sum(1 for r in all_records if r.get(f) not in (None, "", "—"))
        completeness[f] = f"{nonempty}/{len(all_records)} ({100*nonempty/len(all_records):.0f}%)"

    # 按 数据来源 分组统计
    by_source = {}
    for r in all_records:
        s = r["数据来源"]
        by_source.setdefault(s, 0)
        by_source[s] += 1

    # 输出 jobs.json
    jobs_path = os.path.join(BASE_DIR, "jobs.json")
    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(all_records),
            "data_acquisition_date": TODAY,
            "records": all_records,
            "summary": {
                "by_source": by_source,
                "field_completeness": completeness,
            }
        }, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 已保存: {jobs_path}")

    # 输出字段完整性快照
    print("\n字段完整性:")
    for f, v in completeness.items():
        print(f"  {f}: {v}")
    print("\n按数据源:")
    for s, c in by_source.items():
        print(f"  {s}: {c} 条")

    print(f"\n首条样本(蓝皮书): {json.dumps(all_records[0], ensure_ascii=False)}")
    if len(bb) < len(all_records):
        # 找一条事业单位
        inst = next((r for r in all_records if r["数据来源"].startswith("济宁市属")), None)
        if inst:
            print(f"样本(事业单位): {json.dumps(inst, ensure_ascii=False)}")
        jz = next((r for r in all_records if r["数据来源"] == "济宁直聘网"), None)
        if jz:
            print(f"样本(直聘网): {json.dumps(jz, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
