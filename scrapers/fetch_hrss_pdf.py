# -*- coding: utf-8 -*-
"""
采集济宁市属事业单位公开招聘岗位汇总表 PDF (公告B)
来源: 济宁市人社局官网 hrss.jining.gov.cn
公告A(博士专引)官网未找到, 本脚本仅处理公告B。
"""
import os
import re
import json
import time
import requests
import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PDF_URL = ("https://hrss.jining.gov.cn/module/download/downfile.jsp?classid=0"
           "&showname=%E9%99%84%E4%BB%B61%EF%BC%9A2026%E5%B9%B4%E5%BA%A6%E6%B5%8E"
           "%E5%AE%81%E5%B8%82%E5%B1%9E%E4%BA%8B%E4%B8%9A%E5%8D%95%E4%BD%8D%E5%85%AC"
           "%E5%BC%80%E6%8B%9B%E8%81%98%E5%88%9D%E7%BA%A7%E7%BB%BC%E5%90%88%E7%B1%BB"
           "%E4%BA%BA%E5%91%98%E5%B2%97%E4%BD%8D%E6%B1%87%E6%80%BB%E8%A1%A8.pdf"
           "&filename=566c19e3bedd4043b7786ffb15540704.pdf")
PDF_PATH = os.path.join(DATA_DIR, "hrss_2026_institution_jobs.pdf")
OUTPUT_PATH = os.path.join(DATA_DIR, "hrss_institution_jobs_raw.json")
ANNOUNCE_URL = "https://hrss.jining.gov.cn/art/2026/1/22/art_71291_2718366.html"


def download_pdf():
    print(f"[1/3] 下载事业单位岗位汇总表 PDF")
    print(f"   公告页: {ANNOUNCE_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": ANNOUNCE_URL,
    }
    try:
        time.sleep(1.5)
        resp = requests.get(PDF_URL, headers=headers, timeout=60, stream=True, verify=False)
        print(f"   HTTP {resp.status_code} | Content-Type: {resp.headers.get('Content-Type')}")
        if resp.status_code != 200:
            print(f"   [警告] 下载失败")
            return False
        with open(PDF_PATH, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        size_kb = os.path.getsize(PDF_PATH) / 1024
        print(f"   [OK] 已保存 ({size_kb:.1f} KB): {PDF_PATH}")
        return True
    except Exception as e:
        print(f"   [错误] {type(e).__name__}: {e}")
        return False


def clean_cell(c):
    if c is None:
        return ""
    return str(c).replace("\n", "").replace("\r", "").strip()


def parse_pdf():
    print(f"\n[2/3] 解析 PDF 表格")
    if not os.path.exists(PDF_PATH):
        return []
    records = []
    raw_tables = []
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"   总页数: {total}")
        for pi, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for ti, tbl in enumerate(tables):
                if not tbl:
                    continue
                header = [clean_cell(c) for c in tbl[0]]
                raw_tables.append({"page": pi + 1, "table": ti + 1,
                                   "header": header,
                                   "nrows": len(tbl) - 1})
                # 打印表头便于映射
                print(f"   第{pi+1}页 表{ti+1}: {len(tbl)-1}行, 表头({len(header)}列): {header}")

    # 查找含"岗位"/"招聘单位"/"学历"等关键字的表格作为主表
    if not raw_tables:
        print("   [警告] 未提取到表格")
        return []

    # 选列数最多且含"岗位名称"的表头作为标准表头
    main = max(raw_tables, key=lambda t: len(t["header"]))
    print(f"\n   标准表头({len(main['header'])}列): {main['header']}")

    # 重新提取所有页的岗位表数据(同一表头跨多页)
    with pdfplumber.open(PDF_PATH) as pdf:
        for pi, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                header = [clean_cell(c) for c in tbl[0]]
                # 仅处理与标准表头列数一致的表(避免噪声)
                if len(header) != len(main["header"]):
                    continue
                for row in tbl[1:]:
                    cells = [clean_cell(c) for c in row]
                    if not any(cells):
                        continue
                    rec = {header[i]: cells[i] if i < len(cells) else ""
                           for i in range(len(header))}
                    rec["页码"] = pi + 1
                    records.append(rec)

    print(f"\n[3/3] 提取记录数: {len(records)} (合并{len(raw_tables)}个表格块)")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"records": records, "header": main["header"],
                   "announce_url": ANNOUNCE_URL}, f, ensure_ascii=False, indent=2)
    print(f"   已保存: {OUTPUT_PATH}")
    print(f"\n   前3条样本:")
    for r in records[:3]:
        print(f"   {json.dumps(r, ensure_ascii=False)}")
    return records


def main():
    if download_pdf():
        parse_pdf()
    else:
        print("\n下载失败, 无法解析。")
    print("\n人社局事业单位岗位采集流程结束。")


if __name__ == "__main__":
    main()
