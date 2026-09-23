# -*- coding: utf-8 -*-
"""检查蓝皮书 PDF 表格结构，输出每个表格的表头和前2行数据，便于确定字段映射。"""
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "bluebook_tables_raw.json")

with open(RAW_PATH, "r", encoding="utf-8") as f:
    blocks = json.load(f)

print(f"表格块总数: {len(blocks)}\n")
print("=" * 80)

# 只打印前 10 个表格块（含表格的）的结构概览
shown = 0
for b in blocks:
    rows = b.get("rows", [])
    if not rows:
        continue
    print(f"\n[页 {b['page']} / 表 {b['table_index']}] 行数={len(rows)}")
    # 打印表头
    header = rows[0]
    print(f"  表头({len(header)}列): {header}")
    # 打印第1条数据
    if len(rows) > 1:
        print(f"  数据1: {rows[1]}")
    if len(rows) > 2:
        print(f"  数据2: {rows[2]}")
    shown += 1
    if shown >= 12:
        break

print("\n" + "=" * 80)
print("说明: 共抓到表格块，先看前12个判断字段一致性。")
