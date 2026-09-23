# -*- coding: utf-8 -*-
"""
蓝皮书2026版 PDF 数据采集脚本
数据源: http://www.zoucheng.gov.cn/attach/0/92a9af17e661419a938e12d2121c932c.pdf
字段: 15条产业链的紧缺岗位TOP5、专业要求、紧缺星级、年薪均值、工作经验要求等
"""
import os
import sys
import json
import time
import requests
import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PDF_URL = "http://www.zoucheng.gov.cn/attach/0/92a9af17e661419a938e12d2121c932c.pdf"
PDF_PATH = os.path.join(DATA_DIR, "bluebook_2026.pdf")
OUTPUT_PATH = os.path.join(DATA_DIR, "bluebook_jobs_raw.json")


def download_pdf():
    """下载 PDF 文件"""
    print(f"[1/3] 下载 PDF: {PDF_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        time.sleep(1.5)
        resp = requests.get(PDF_URL, headers=headers, timeout=60, stream=True, verify=False)
        print(f"   HTTP 状态码: {resp.status_code}")
        print(f"   Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {resp.headers.get('Content-Length', 'N/A')}")

        if resp.status_code != 200:
            print(f"   [警告] 下载失败，状态码: {resp.status_code}")
            return False

        # 检查是否真的是 PDF
        ctype = resp.headers.get("Content-Type", "")
        if "pdf" not in ctype.lower() and not PDF_URL.endswith(".pdf"):
            print(f"   [警告] 响应非 PDF: {ctype}")
            # 打印前 200 字符看是什么
            preview = resp.content[:200]
            print(f"   响应预览: {preview!r}")
            return False

        with open(PDF_PATH, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        size_mb = os.path.getsize(PDF_PATH) / 1024 / 1024
        print(f"   [OK] 已保存: {PDF_PATH} ({size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"   [错误] 下载异常: {type(e).__name__}: {e}")
        return False


def parse_pdf_tables():
    """用 pdfplumber 解析 PDF 中的表格"""
    print(f"\n[2/3] 解析 PDF 表格: {PDF_PATH}")
    if not os.path.exists(PDF_PATH):
        print("   [错误] PDF 文件不存在，跳过解析")
        return []

    all_tables = []
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            total_pages = len(pdf.pages)
            print(f"   PDF 总页数: {total_pages}")

            for page_idx, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                    tables = page.extract_tables()
                    if tables:
                        print(f"   第 {page_idx + 1} 页: 提取到 {len(tables)} 个表格")
                        for tbl_idx, table in enumerate(tables):
                            all_tables.append({
                                "page": page_idx + 1,
                                "table_index": tbl_idx + 1,
                                "rows": table,
                                "page_text_preview": text[:300]
                            })
                    elif text.strip():
                        # 无表格但有文本，记录页面文本供后续提取
                        all_tables.append({
                            "page": page_idx + 1,
                            "table_index": 0,
                            "rows": [],
                            "page_text": text
                        })
                except Exception as e:
                    print(f"   [警告] 第 {page_idx + 1} 页解析失败: {e}")

        print(f"   [OK] 共提取表格块 {len(all_tables)} 个")
        # 保存原始结构供调试
        debug_path = os.path.join(DATA_DIR, "bluebook_tables_raw.json")
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(all_tables, f, ensure_ascii=False, indent=2)
        print(f"   原始结构已存: {debug_path}")
        return all_tables
    except Exception as e:
        print(f"   [错误] 解析异常: {type(e).__name__}: {e}")
        return []


def main():
    ok = download_pdf()
    if ok:
        parse_pdf_tables()
    else:
        print("\n[3/3] PDF 下载失败，将依赖浏览器访问方式获取蓝皮书数据。")
    print("\n蓝皮书采集流程结束。")


if __name__ == "__main__":
    main()
