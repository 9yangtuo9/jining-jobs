# -*- coding: utf-8 -*-
"""
采集汶上县2026春风行动招聘会岗位汇总(用 HTTP 绕过 HTTPS 的 403 封锁)。
策略:
  1) 用站内搜索接口查"春风行动 招聘会"
  2) 定位详情页后, 若为 HTML 表格直接解析; 若为附件则下载并解析
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
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(DATA_DIR, "wenshang_jobfair_raw.json")

BASE = "http://www.wenshang.gov.cn"
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


def search_site(keyword):
    """尝试多种政务站点常见搜索接口。"""
    candidates = [
        # 雷火式站群搜索
        f"{BASE}/search/?q={requests.utils.quote(keyword)}",
        f"{BASE}/search.html?q={requests.utils.quote(keyword)}",
        f"{BASE}/zwgk/search/?q={requests.utils.quote(keyword)}",
        # 全文检索接口
        f"{BASE}/module/search/jump.do?keyword={requests.utils.quote(keyword)}",
    ]
    for u in candidates:
        try:
            r = get(u)
            print(f"  搜索尝试 {u} -> HTTP {r.status_code} ({len(r.content)}B)")
            if r.status_code == 200 and len(r.content) > 500:
                return r
        except Exception as e:
            print(f"    错误: {e}")
    return None


def find_links_in_homepage():
    """从首页找出就业/人社/春风行动相关栏目链接。"""
    r = get(BASE + "/")
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        href = a["href"]
        if any(k in txt for k in ["就业", "人社", "招聘", "春风", "公示公告", "通知公告"]):
            if href.startswith("/"):
                href = BASE + href
            elif not href.startswith("http"):
                href = BASE + "/" + href
            links.append((txt, href))
    # 去重
    seen = set()
    uniq = []
    for t, h in links:
        if h not in seen:
            seen.add(h)
            uniq.append((t, h))
    return uniq


def crawl_jobfair():
    print("=" * 60)
    print("[汶上县] 春风行动招聘会岗位采集")
    print("=" * 60)

    # 1) 尝试搜索接口
    print("\n[1] 站内搜索 '春风行动 招聘会'")
    sr = search_site("春风行动 招聘会")
    search_hits = []
    if sr is not None:
        soup = BeautifulSoup(sr.text, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            if "春风" in txt or "招聘" in txt:
                href = a["href"]
                if href.startswith("/"):
                    href = BASE + href
                search_hits.append((txt, href))
        print(f"  搜索结果候选: {len(search_hits)} 条")
        for t, h in search_hits[:10]:
            print(f"    {t} -> {h}")

    # 2) 从首页找就业/招聘栏目
    print("\n[2] 首页就业/人社/招聘栏目链接")
    home_links = find_links_in_homepage()
    print(f"  候选栏目: {len(home_links)} 条")
    for t, h in home_links[:15]:
        print(f"    {t} -> {h}")

    # 3) 遍历候选链接, 寻找含"春风行动"+"岗位"的页面
    print("\n[3] 深入候选栏目查找春风行动岗位汇总")
    candidates = search_hits + home_links
    visited = set()
    jobfair_pages = []
    for txt, href in candidates:
        if href in visited:
            continue
        visited.add(href)
        try:
            r = get(href)
            if r.status_code != 200:
                continue
            text = r.text
            # 判定页面是否含春风行动 + 岗位/企业
            if "春风行动" in text and ("岗位" in text or "企业" in text or "招聘" in text):
                # 进一步确认是否为岗位汇总(含表格或多条岗位)
                jobfair_pages.append((txt, href, r))
                print(f"  [命中] {txt} -> {href}")
                if len(jobfair_pages) >= 5:
                    break
        except Exception as e:
            print(f"    访问 {href} 失败: {e}")

    # 4) 从命中的页面提取岗位表格
    print(f"\n[4] 从 {len(jobfair_pages)} 个命中页提取表格/附件")
    all_records = []
    report = {"pages": [], "records": []}
    for txt, href, r in jobfair_pages:
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        attachments = []
        # 附件链接
        for a in soup.find_all("a", href=True):
            at = a.get("href", "")
            if any(at.lower().endswith(ext) for ext in [".pdf", ".xls", ".xlsx", ".doc", ".docx"]):
                if at.startswith("/"):
                    at = BASE + at
                attachments.append((a.get_text(strip=True), at))
        print(f"\n  页面: {txt}\n  URL: {href}\n  表格数: {len(tables)}, 附件: {len(attachments)}")
        page_info = {"title": txt, "url": href, "tables": [], "attachments": attachments}

        for ti, tbl in enumerate(tables):
            rows = tbl.find_all("tr")
            if len(rows) < 2:
                continue
            header = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
            data_rows = []
            for row in rows[1:]:
                cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                if any(cells):
                    data_rows.append(cells)
            print(f"    表{ti+1}: {len(data_rows)}行, 表头({len(header)}列): {header}")
            if len(header) >= 3 and len(data_rows) >= 1:
                page_info["tables"].append({"header": header, "nrows": len(data_rows)})
                for dr in data_rows[:20]:
                    rec = {header[i]: dr[i] if i < len(dr) else "" for i in range(len(header))}
                    rec["来源页"] = href
                    all_records.append(rec)
        report["pages"].append(page_info)

    # 5) 若有附件, 记录链接供后续下载
    print(f"\n[5] 汇总: 采集记录 {len(all_records)} 条")
    report["records"] = all_records
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {OUTPUT_PATH}")
    if all_records:
        print("\n  前3条样本:")
        for r in all_records[:3]:
            print(f"  {json.dumps(r, ensure_ascii=False)}")
    else:
        print("\n  [说明] 未能从汶上县官网提取到春风行动岗位汇总表数据(可能页面无表格或未命中)。")


if __name__ == "__main__":
    crawl_jobfair()
