# -*- coding: utf-8 -*-
"""访问济宁直聘网岗位详情页, 补充发布时间/学历/经验/福利等字段。"""
import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_PATH = os.path.join(DATA_DIR, "jiningzhipin_jobs_raw.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "jiningzhipin_jobs_enriched.json")

BASE = "https://www.jiningzhipin.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": BASE + "/",
}


def fetch_detail(url):
    time.sleep(1.5)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def parse_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    info = {"发布时间": "", "学历要求": "", "经验要求": "", "福利": "", "岗位描述": ""}
    # 发布时间常见于 .job-time / .publish-time / 含日期文本
    for sel in [".job-time", ".publish-time", ".time", ".date", ".job-detail__time"]:
        el = soup.select_one(sel)
        if el:
            t = el.get_text(strip=True)
            m = re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日|\d+天前|今天|昨天", t)
            if m:
                info["发布时间"] = m.group()
                break
    # 正文里搜日期
    if not info["发布时间"]:
        txt = soup.get_text(" ", strip=True)
        m = re.search(r"(20\d{2}[-/年]\d{1,2}[-/月]\d{1,2})", txt)
        if m:
            info["发布时间"] = m.group(1)
        else:
            m = re.search(r"(今天|昨天|\d+天前)", txt)
            if m:
                info["发布时间"] = m.group(1)

    # 学历/经验: 常在 .job-tags / .job-info 的标签
    tags = [t.get_text(strip=True) for t in soup.select(".tag-item, .job-tag, .info-tag, .job-detail__tag")]
    for tg in tags:
        if any(k in tg for k in ["学历", "大专", "本科", "硕士", "高中", "不限"]):
            info["学历要求"] = tg
        elif re.search(r"\d+[-\d]*年|经验", tg):
            info["经验要求"] = tg
    # 福利
    welfare = [t.get_text(strip=True) for t in soup.select(".welfare, .job-welfare, .benefit, .tag-welfare")]
    if welfare:
        info["福利"] = "、".join(welfare)
    # 描述
    desc_el = soup.select_one(".job-detail__desc, .job-desc, .content, .description, #zoom")
    if desc_el:
        info["岗位描述"] = desc_el.get_text(" ", strip=True)[:300]
    # 兜底: 全文里找学历/经验关键字
    full = soup.get_text(" ", strip=True)
    if not info["学历要求"]:
        m = re.search(r"学历[：:]\s*(\S+)", full)
        if m:
            info["学历要求"] = m.group(1)
    if not info["经验要求"]:
        m = re.search(r"经验[：:]\s*(\S+)", full)
        if m:
            info["经验要求"] = m.group(1)
    return info


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data["records"]
    print(f"共 {len(records)} 条岗位, 逐条访问详情页补充字段...\n")

    for i, rec in enumerate(records):
        url = rec.get("详情链接")
        if not url or not url.startswith("http"):
            continue
        html = fetch_detail(url)
        if not html:
            print(f"  [{i+1}/{len(records)}] {rec['岗位名称'][:20]}: 详情页抓取失败")
            continue
        detail = parse_detail(html)
        rec.update(detail)
        pub = detail["发布时间"] or "—"
        print(f"  [{i+1}/{len(records)}] {rec['岗位名称'][:20]} | 发布:{pub} | 学历:{detail['学历要求'][:10] or '—'}")
        # 控制总量, 避免请求过多
        if i >= 25:
            print("  ... 已抓取26条详情, 后续沿用首页数据(无发布时间)")
            break

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"records": records, "source": BASE}, f, ensure_ascii=False, indent=2)
    print(f"\n已保存(含详情): {OUTPUT_PATH}")
    filled = sum(1 for r in records if r.get("发布时间"))
    print(f"含发布时间的记录: {filled}/{len(records)}")


if __name__ == "__main__":
    main()
