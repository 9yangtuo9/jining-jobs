# -*- coding: utf-8 -*-
"""
采集汶上县政府官网"招聘信息"栏目下的企业招聘公告(春风行动汇总未找到, 退而采集栏目内全部招聘公告)。
策略: 列出 art_107308 栏目分页, 逐条抓取招聘公告正文, 提取企业名称/岗位/薪资。
"""
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
OUTPUT_PATH = os.path.join(DATA_DIR, "wenshang_notices_raw.json")

BASE = "http://www.wenshang.gov.cn"
# 招聘信息栏目首页(已知公告属于 art_107308 栏目)
COL_INDEX = f"{BASE}/col/col107308/index.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": BASE + "/",
}


def get(url, **kw):
    time.sleep(1.5)
    return requests.get(url, headers=HEADERS, timeout=30, verify=False, **kw)


def collect_notice_urls():
    """从招聘栏目分页收集公告链接。"""
    urls = []
    # 政务站群栏目常用 /col/colXXX/index.html 及分页
    # 也可尝试 JS 加载的列表接口。先抓首页。
    r = get(COL_INDEX)
    print(f"栏目首页 {COL_INDEX} -> HTTP {r.status_code} ({len(r.content)}B)")
    if r.status_code != 200:
        # 尝试备用栏目路径
        for alt in [f"{BASE}/col/col107308_more.html",
                    f"{BASE}/art/2026/8/31/art_107308_2794042.html"]:
            r = get(alt)
            print(f"  备用 {alt} -> HTTP {r.status_code}")
            if r.status_code == 200:
                break
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        txt = a.get_text(strip=True)
        if "招聘" in txt or "招聘信息" in txt or "简章" in txt or "公告" in txt:
            if href.startswith("/"):
                href = BASE + href
            elif not href.startswith("http"):
                href = BASE + "/" + href
            urls.append((txt, href))
    # 去重
    seen = set()
    uniq = []
    for t, h in urls:
        if h not in seen and "/art/" in h:
            seen.add(h)
            uniq.append((t, h))
    return uniq


def parse_salary(text):
    """从文本提取薪资, 如 '月薪5000-8000元' / '年薪8-12万' / '4000-6000' """
    out = []
    # 月薪范围
    m = re.search(r"(\d{3,6})\s*[-—~至]\s*(\d{3,6})\s*元?/?(?:月)?", text)
    if m:
        out.append(f"{m.group(1)}-{m.group(2)}元/月")
    else:
        m = re.search(r"月薪\s*(\d{3,6})", text)
        if m:
            out.append(f"{m.group(1)}元/月")
    return out


def extract_jobs_from_page(html, url, title):
    """从单个招聘公告正文抽取岗位条目。"""
    soup = BeautifulSoup(html, "html.parser")
    # 正文容器(政务站常用 #zoom 或 .article 或 .content)
    body = soup.find(id="zoom") or soup.find(class_="article") or soup.find(class_="content") or soup
    text = body.get_text("\n", strip=True)
    # 招聘公告常以表格或段落呈现岗位。先尝试表格
    records = []
    for tbl in body.find_all("table"):
        rows = tbl.find_all("tr")
        if len(rows) < 2:
            continue
        header = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            if any(cells):
                rec = {header[i]: cells[i] if i < len(cells) else "" for i in range(len(header))}
                rec["来源公告"] = title
                rec["来源URL"] = url
                records.append(rec)
    # 若无表格, 用正则按岗位关键字切分段落
    if not records:
        # 找含"岗位"/"职位"+"薪资"/"月薪"的行
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        cur = None
        for ln in lines:
            if any(k in ln for k in ["岗位", "职位", "招聘"]):
                cur = {"岗位/描述": ln, "来源公告": title, "来源URL": url}
                records.append(cur)
            elif cur and any(k in ln for k in ["薪资", "月薪", "工资", "待遇", "年薪", "元/"]):
                cur["待遇"] = ln
        # 补一条: 整篇作为该企业招聘概述
        if not records:
            records.append({"招聘概述": text[:400], "来源公告": title, "来源URL": url})
    return records, text


def main():
    print("=" * 60)
    print("[汶上县] 招聘信息栏目 - 企业招聘公告采集")
    print("=" * 60)

    notice_urls = collect_notice_urls()
    print(f"\n[1] 栏目内招聘公告链接: {len(notice_urls)} 条")
    for t, h in notice_urls[:20]:
        print(f"    {t} -> {h}")

    # 已知的3条首页招聘公告(确保包含)
    known = [
        ("济宁市万有化工有限公司招聘信息", f"{BASE}/art/2026/8/31/art_107308_2794042.html"),
        ("汶上中银富登村镇银行招聘公告", f"{BASE}/art/2026/8/25/art_107308_2793904.html"),
        ("山东华准机械有限公司招聘简章", f"{BASE}/art/2026/8/25/art_107308_2793903.html"),
    ]
    seen = set(h for _, h in notice_urls)
    for t, h in known:
        if h not in seen:
            notice_urls.append((t, h))
            seen.add(h)

    # 逐条抓取
    all_records = []
    report = {"notices": [], "records": []}
    print(f"\n[2] 抓取 {len(notice_urls)} 条公告正文")
    for i, (title, url) in enumerate(notice_urls[:15]):
        try:
            r = get(url)
            if r.status_code != 200:
                print(f"  [{i+1}] {title}: HTTP {r.status_code}, 跳过")
                continue
            jobs, full_text = extract_jobs_from_page(r.text, url, title)
            # 识别企业名称(标题常含公司名)
            company = title.replace("招聘信息", "").replace("招聘公告", "").replace("招聘简章", "").strip()
            for j in jobs:
                j.setdefault("企业名称", company)
            all_records.extend(jobs)
            report["notices"].append({
                "title": title, "url": url,
                "jobs_extracted": len(jobs),
                "text_preview": full_text[:200]
            })
            print(f"  [{i+1}] {title}: 提取岗位 {len(jobs)} 条 (企业: {company})")
        except Exception as e:
            print(f"  [{i+1}] {title}: 错误 {type(e).__name__}: {e}")

    report["records"] = all_records
    print(f"\n[3] 汶上县招聘公告共采集岗位记录: {len(all_records)} 条")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {OUTPUT_PATH}")
    if all_records:
        print("\n  前5条样本:")
        for r in all_records[:5]:
            print(f"  {json.dumps(r, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
