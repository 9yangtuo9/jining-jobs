# -*- coding: utf-8 -*-
"""
采集济宁直聘网(www.jiningzhipin.com)首页在招岗位。
字段: 岗位名称 / 公司 / 区域 / 薪资范围 / 发布时间 / 详情链接
服务端渲染, 无需登录。
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
OUTPUT_PATH = os.path.join(DATA_DIR, "jiningzhipin_jobs_raw.json")

BASE = "https://www.jiningzhipin.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": BASE + "/",
}


def parse_jobs(html, source_url):
    soup = BeautifulSoup(html, "html.parser")
    records = []
    rows = soup.select(".recruit-list__row")
    for row in rows:
        # 岗位名称 + 链接
        job_link = row.select_one(".recruit-list__job-link")
        job_name = job_link.get_text(strip=True) if job_link else ""
        href = job_link["href"] if job_link and job_link.has_attr("href") else ""
        if href and href.startswith("/"):
            href = BASE + href
        # 公司
        company_el = row.select_one(".recruit-list__cell--company")
        company = company_el.get_text(strip=True) if company_el else ""
        # 区域
        region_el = row.select_one(".recruit-list__cell--region")
        region = region_el.get_text(strip=True) if region_el else ""
        # 薪资
        salary_el = row.select_one(".recruit-list__cell--salary")
        salary = salary_el.get_text(strip=True) if salary_el else ""
        # 发布时间
        time_el = row.select_one(".recruit-list__cell--time")
        pub_time = time_el.get_text(strip=True) if time_el else ""
        # 分类
        cat_el = row.select_one(".recruit-list__category")
        category = cat_el.get_text(strip=True) if cat_el else ""

        if job_name or company:
            records.append({
                "岗位名称": job_name,
                "公司名称": company,
                "区域": region,
                "薪资范围": salary,
                "发布时间": pub_time,
                "岗位分类": category,
                "详情链接": href,
                "来源URL": source_url,
            })
    return records


def fetch_with_retry(url, retries=3):
    for i in range(retries):
        try:
            time.sleep(1.5)
            r = requests.get(url, headers=HEADERS, timeout=30, verify=False)
            if r.status_code == 200:
                return r
            print(f"  尝试{i+1}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  尝试{i+1} 错误: {e}")
        time.sleep(2)
    return None


def main():
    print("=" * 60)
    print("[济宁直聘网] 在招岗位采集")
    print("=" * 60)

    all_records = []
    # 首页
    print("\n[1] 抓取首页")
    r = fetch_with_retry(BASE + "/")
    if r is None:
        print("  首页抓取失败, 退出")
        return
    print(f"  HTTP 200, {len(r.content)}B")
    jobs = parse_jobs(r.text, BASE + "/")
    print(f"  首页岗位: {len(jobs)} 条")
    all_records.extend(jobs)

    # 尝试翻页(若存在分页接口)。直聘网列表常见分页路径
    # 先尝试首页第2页
    page_urls = [
        f"{BASE}/index/index/p/2.html",
        f"{BASE}/index/index/p/2",
        f"{BASE}/?p=2",
    ]
    print("\n[2] 尝试翻页(第2页)")
    found_page2 = False
    for pu in page_urls:
        r2 = fetch_with_retry(pu)
        if r2 and r2.status_code == 200 and len(r2.content) > 5000:
            jobs2 = parse_jobs(r2.text, pu)
            if jobs2:
                print(f"  {pu}: 岗位 {len(jobs2)} 条")
                # 去重(与首页岗位名+公司均相同则视为重复)
                existing = {(j["岗位名称"], j["公司名称"]) for j in all_records}
                new = [j for j in jobs2 if (j["岗位名称"], j["公司名称"]) not in existing]
                if new:
                    all_records.extend(new)
                    found_page2 = True
                    break
            print(f"  {pu}: 无新岗位")
        else:
            print(f"  {pu}: HTTP {r2.status_code if r2 else '失败'}")

    if not found_page2:
        print("  未找到翻页接口, 仅采集首页岗位。")

    # 标准化薪资为年薪均值(万元)估算
    for j in all_records:
        j["年薪均值（万元）估算"] = estimate_annual_salary(j["薪资范围"])

    print(f"\n[3] 济宁直聘网共采集岗位: {len(all_records)} 条")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"records": all_records, "source": BASE}, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {OUTPUT_PATH}")
    print("\n  前8条样本:")
    for r in all_records[:8]:
        print(f"  {json.dumps(r, ensure_ascii=False)}")


def estimate_annual_salary(salary_text):
    """从'4000-10000元/月'估算年薪均值(万元)。
    周(周结)按50周/年, 月按12月/年。"""
    if not salary_text or salary_text == "薪资待遇":
        return None
    # 月薪范围
    m = re.search(r"(\d{3,6})\s*[-—~至]\s*(\d{3,6})\s*元?/?月", salary_text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return round((lo + hi) / 2 * 12 / 10000, 2)
    # 周薪范围(周结)
    m = re.search(r"(\d{3,6})\s*[-—~至]\s*(\d{3,6})\s*元?/?周", salary_text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return round((lo + hi) / 2 * 50 / 10000, 2)
    # 单一月薪
    m = re.search(r"(\d{3,6})\s*元?/?月", salary_text)
    if m:
        return round(int(m.group(1)) * 12 / 10000, 2)
    return None


if __name__ == "__main__":
    main()
